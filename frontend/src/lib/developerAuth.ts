import { randomBytes, createHash, timingSafeEqual } from 'crypto'
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
  isSystemKey?: boolean
  systemName?: string
}

export function generateApiKeyValue() {
  return `cpk_${randomBytes(24).toString('hex')}`
}

export function extractCredentials(req: NextRequest): { apiKey: string | null; apiSecret: string | null } {
  const auth = req.headers.get('authorization') || req.headers.get('Authorization')
  let apiKey: string | null = null
  let apiSecret: string | null = null

  if (auth) {
    if (auth.toLowerCase().startsWith('bearer ')) {
      const token = auth.slice(7).trim()
      if (token.includes(':')) {
        const [k, s] = token.split(':')
        apiKey = k.trim()
        apiSecret = s.trim()
      } else {
        apiKey = token
      }
    } else if (auth.toLowerCase().startsWith('basic ')) {
      try {
        const decoded = Buffer.from(auth.slice(6).trim(), 'base64').toString('utf-8')
        const colonIdx = decoded.indexOf(':')
        if (colonIdx !== -1) {
          apiKey = decoded.slice(0, colonIdx).trim()
          apiSecret = decoded.slice(colonIdx + 1).trim()
        }
      } catch {}
    }
  }

  const headerKey = req.headers.get('x-api-key') || req.headers.get('X-Api-Key')
  if (headerKey) apiKey = headerKey.trim()

  const headerSecret = req.headers.get('x-api-secret') || req.headers.get('X-Api-Secret')
  if (headerSecret) apiSecret = headerSecret.trim()

  return { apiKey, apiSecret }
}

export function extractBearerOrApiKey(req: NextRequest): string | null {
  return extractCredentials(req).apiKey
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

function mapKeyRow(row: any): ApiKeyRecord {
  const isGranted =
    Boolean(row.is_developer) || String(row.role || '').toLowerCase() === 'admin'

  return {
    id: row.id,
    userId: row.user_id,
    projectName: row.project_name,
    keyPrefix: row.key_prefix,
    apiKey: row.api_key,
    callbackUrl: row.callback_url ?? null,
    isActive: row.is_active !== false,
    lastUsedAt: row.last_used_at,
    createdAt: row.created_at,
    userEmail: row.user_email,
    userName: row.user_name,
    isDeveloper: row.is_developer,
    role: row.role,
    apiUnlimitedTokens: isGranted,
  }
}

/** Authenticate a public API request via developer API key or system credentials. */
export async function authenticateApiKey(req: NextRequest): Promise<
  | { ok: true; key: ApiKeyRecord }
  | { ok: false; response: Response }
> {
  await ensureDb()
  const { apiKey, apiSecret } = extractCredentials(req)

  if (!apiKey) {
    return {
      ok: false,
      response: apiError(
        'Missing API key. Send Authorization: Bearer <key>, x-api-key: <key>, or Authorization: Basic base64(key:secret).',
        401,
        'missing_api_key'
      ),
    }
  }

  // 1. Check Machine-to-Machine System API Keys (No user account required)
  try {
    const sysResult = await pool.query(
      `SELECT id, system_name, api_key, api_secret_hash, secret_prefix, permissions, is_active, last_used_at, created_at
       FROM system_api_keys
       WHERE api_key = $1
       LIMIT 1`,
      [apiKey]
    )

    if (sysResult.rows.length > 0) {
      const sysRow = sysResult.rows[0]
      if (sysRow.is_active === false) {
        return {
          ok: false,
          response: apiError('This system API key has been revoked.', 403, 'key_revoked'),
        }
      }

      // If an API secret is provided, verify against SHA-256 hash using timing-safe comparison
      if (apiSecret) {
        const incomingHash = createHash('sha256').update(apiSecret).digest('hex')
        const storedHash = String(sysRow.api_secret_hash || '').toLowerCase()
        const match =
          incomingHash.length === storedHash.length &&
          timingSafeEqual(Buffer.from(incomingHash), Buffer.from(storedHash))

        if (!match) {
          return {
            ok: false,
            response: apiError('Invalid API secret.', 403, 'invalid_api_secret'),
          }
        }
      }

      // Update last_used_at asynchronously
      pool
        .query(`UPDATE system_api_keys SET last_used_at = NOW() WHERE id = $1`, [sysRow.id])
        .catch(() => {})

      return {
        ok: true,
        key: {
          id: sysRow.id,
          userId: `system:${sysRow.id}`,
          projectName: sysRow.system_name,
          keyPrefix: sysRow.api_key.slice(0, 12),
          apiKey: sysRow.api_key,
          callbackUrl: null,
          isActive: true,
          lastUsedAt: sysRow.last_used_at,
          createdAt: sysRow.created_at,
          userEmail: `${sysRow.id}@system.kronx.local`,
          userName: sysRow.system_name,
          isDeveloper: true,
          role: 'system',
          apiUnlimitedTokens: true,
          isSystemKey: true,
          systemName: sysRow.system_name,
        },
      }
    }
  } catch (sysErr) {
    // Graceful fallback to user keys if table lookup fails
    console.warn('[developerAuth] system_api_keys lookup failed:', sysErr)
  }

  // 2. Check User-Bound API Keys
  const result = await pool.query(
    `SELECT
       k.id, k.user_id, k.project_name, k.key_prefix, k.api_key, k.callback_url,
       k.is_active, k.last_used_at, k.created_at,
       u.email AS user_email, u.name AS user_name, u.is_developer, u.role
     FROM api_keys k
     JOIN users u ON u.id = k.user_id
     WHERE k.api_key = $1
     LIMIT 1`,
    [apiKey]
  )

  let row = result.rows[0]

  // Legacy fallback: keys stored on users.api_key before multi-key table
  if (!row) {
    const legacy = await pool.query(
      `SELECT
         u.id AS user_id, u.email AS user_email, u.name AS user_name,
         u.is_developer, u.role, u.api_key, u.callback_url
       FROM users u
       WHERE u.api_key = $1
       LIMIT 1`,
      [apiKey]
    )
    if (legacy.rows.length > 0) {
      const u = legacy.rows[0]
      row = {
        id: `legacy-${u.user_id}`,
        user_id: u.user_id,
        project_name: 'Default Project',
        key_prefix: String(u.api_key).slice(0, 12),
        api_key: u.api_key,
        callback_url: u.callback_url,
        is_active: true,
        last_used_at: null,
        created_at: null,
        user_email: u.user_email,
        user_name: u.user_name,
        is_developer: u.is_developer,
        role: u.role,
      }
    }
  }

  if (!row) {
    return {
      ok: false,
      response: apiError('Invalid API key.', 403, 'invalid_api_key'),
    }
  }

  if (row.is_active === false) {
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

  pool
    .query(`UPDATE api_keys SET last_used_at = NOW() WHERE id = $1`, [row.id])
    .catch(() => {})

  return {
    ok: true,
    key: mapKeyRow(row),
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
