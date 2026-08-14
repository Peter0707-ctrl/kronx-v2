import { randomBytes } from 'crypto'
import { NextRequest } from 'next/server'
import { ensureDb, pool } from './db'

export type ApiKeyRecord = {
  id: string
  userId: string
  projectName: string
  keyPrefix: string
  apiKey: string
  callbackUrl: string | null
  isActive: boolean
  lastUsedAt: string | null
  createdAt: string
  userEmail?: string
  userName?: string
  isDeveloper?: boolean
  apiUnlimitedTokens?: boolean
  role?: string
}

export function generateApiKeyValue() {
  return `cpk_${randomBytes(24).toString('hex')}`
}

export function extractBearerOrApiKey(req: NextRequest): string | null {
  const auth = req.headers.get('authorization') || req.headers.get('Authorization')
  if (auth?.toLowerCase().startsWith('bearer ')) {
    const token = auth.slice(7).trim()
    if (token) return token
  }
  const headerKey = req.headers.get('x-api-key') || req.headers.get('X-Api-Key')
  return headerKey?.trim() || null
}

export function apiError(
  message: string,
  status: number,
  code: string,
  type = 'invalid_request_error'
) {
  return Response.json(
    { error: { message, type, code } },
    { status }
  )
}

/** Authenticate a public API request via developer API key. */
export async function authenticateApiKey(req: NextRequest): Promise<
  | { ok: true; key: ApiKeyRecord }
  | { ok: false; response: Response }
> {
  await ensureDb()
  const apiKey = extractBearerOrApiKey(req)

  if (!apiKey) {
    return {
      ok: false,
      response: apiError(
        'Missing API key. Send Authorization: Bearer <key> or x-api-key: <key>.',
        401,
        'missing_api_key'
      ),
    }
  }

  const result = await pool.query(
    `SELECT
       k.id, k.user_id, k.project_name, k.key_prefix, k.api_key, k.callback_url,
       k.is_active, k.last_used_at, k.created_at,
       u.email AS user_email, u.name AS user_name, u.is_developer, u.role,
       COALESCE(u.api_unlimited_tokens, TRUE) AS api_unlimited_tokens
     FROM api_keys k
     JOIN users u ON u.id = k.user_id
     WHERE k.api_key = $1
     LIMIT 1`,
    [apiKey]
  )

  if (result.rows.length === 0) {
    return {
      ok: false,
      response: apiError('Invalid API key.', 403, 'invalid_api_key'),
    }
  }

  const row = result.rows[0]
  if (!row.is_active) {
    return {
      ok: false,
      response: apiError('This API key has been revoked.', 403, 'key_revoked'),
    }
  }
  if (!row.is_developer && row.role !== 'admin') {
    return {
      ok: false,
      response: apiError(
        'Developer access is not granted for this account. Ask an admin to enable API access.',
        403,
        'developer_not_granted'
      ),
    }
  }

  // Touch last_used_at (fire-and-forget)
  pool
    .query(`UPDATE api_keys SET last_used_at = NOW() WHERE id = $1`, [row.id])
    .catch(() => {})

  return {
    ok: true,
    key: {
      id: row.id,
      userId: row.user_id,
      projectName: row.project_name,
      keyPrefix: row.key_prefix,
      apiKey: row.api_key,
      callbackUrl: row.callback_url,
      isActive: row.is_active,
      lastUsedAt: row.last_used_at,
      createdAt: row.created_at,
      userEmail: row.user_email,
      userName: row.user_name,
      isDeveloper: row.is_developer,
      role: row.role,
      apiUnlimitedTokens:
        Boolean(row.api_unlimited_tokens) || Boolean(row.is_developer) || row.role === 'admin',
    },
  }
}

/** Authenticate a logged-in developer managing their own keys. */
export async function authenticateDeveloperSession(req: NextRequest): Promise<
  | { ok: true; userId: string; email: string; isDeveloper: boolean; role: string }
  | { ok: false; response: Response }
> {
  await ensureDb()
  const userId = req.headers.get('x-user-id')?.trim()
  const email = req.headers.get('x-user-email')?.toLowerCase().trim()

  if (!userId || !email) {
    return {
      ok: false,
      response: apiError('Missing session headers (x-user-id, x-user-email).', 401, 'missing_session'),
    }
  }

  const result = await pool.query(
    `SELECT id, email, is_developer, role FROM users WHERE id = $1 AND LOWER(email) = $2 LIMIT 1`,
    [userId, email]
  )

  if (result.rows.length === 0) {
    return {
      ok: false,
      response: apiError('User not found.', 404, 'user_not_found'),
    }
  }

  const user = result.rows[0]
  if (!user.is_developer && user.role !== 'admin') {
    return {
      ok: false,
      response: apiError(
        'Developer access is not granted. Contact an admin to enable API access.',
        403,
        'developer_not_granted'
      ),
    }
  }

  return {
    ok: true,
    userId: user.id,
    email: user.email,
    isDeveloper: Boolean(user.is_developer) || user.role === 'admin',
    role: user.role,
  }
}
