import { NextRequest, NextResponse } from 'next/server'
import { v4 as uuidv4 } from 'uuid'
import { ensureDb, pool } from '@/lib/db'
import {
  authenticateDeveloperSession,
  generateApiKeyValue,
  apiError,
} from '@/lib/developerAuth'

export const dynamic = 'force-dynamic'

function mapKey(row: any, includeSecret = false) {
  return {
    id: row.id,
    projectName: row.project_name,
    keyPrefix: row.key_prefix,
    apiKey: includeSecret ? row.api_key : `${row.key_prefix}…`,
    callbackUrl: row.callback_url,
    isActive: row.is_active,
    lastUsedAt: row.last_used_at,
    createdAt: row.created_at,
  }
}

/** List API keys for the authenticated developer. */
export async function GET(req: NextRequest) {
  try {
    const auth = await authenticateDeveloperSession(req)
    if (!auth.ok) return auth.response

    await ensureDb()
    const result = await pool.query(
      `SELECT id, project_name, key_prefix, api_key, callback_url, is_active, last_used_at, created_at
       FROM api_keys
       WHERE user_id = $1
       ORDER BY created_at DESC`,
      [auth.userId]
    )

    return NextResponse.json({
      keys: result.rows.map((r) => mapKey(r, false)),
      count: result.rows.length,
    })
  } catch (e: any) {
    console.error('[developer/keys GET]', e)
    return apiError(e?.message || 'Failed to list keys', 500, 'internal_error', 'api_error')
  }
}

/** Create a new project API key. Returns the full secret once. */
export async function POST(req: NextRequest) {
  try {
    const auth = await authenticateDeveloperSession(req)
    if (!auth.ok) return auth.response

    const body = await req.json().catch(() => ({}))
    const projectName = String(body.projectName || body.project_name || '').trim()
    const callbackUrl = body.callbackUrl || body.callback_url || null

    if (!projectName || projectName.length < 2) {
      return apiError('projectName is required (min 2 characters).', 400, 'missing_project_name')
    }
    if (projectName.length > 80) {
      return apiError('projectName must be 80 characters or fewer.', 400, 'project_name_too_long')
    }

    const existing = await pool.query(
      `SELECT COUNT(*)::int AS c FROM api_keys WHERE user_id = $1 AND is_active = TRUE`,
      [auth.userId]
    )
    if ((existing.rows[0]?.c || 0) >= 20) {
      return apiError('Maximum of 20 active API keys per account.', 400, 'key_limit_reached')
    }

    const apiKey = generateApiKeyValue()
    const id = `key_${uuidv4()}`
    const keyPrefix = apiKey.slice(0, 12)

    await pool.query(
      `INSERT INTO api_keys (id, user_id, project_name, key_prefix, api_key, callback_url, is_active)
       VALUES ($1, $2, $3, $4, $5, $6, TRUE)`,
      [id, auth.userId, projectName, keyPrefix, apiKey, callbackUrl]
    )

    // Keep legacy column in sync with newest key for older UI pieces
    await pool.query(`UPDATE users SET api_key = $1, is_developer = TRUE WHERE id = $2`, [
      apiKey,
      auth.userId,
    ])

    return NextResponse.json(
      {
        success: true,
        message: 'API key created. Copy it now — the full secret is only shown once.',
        key: {
          id,
          projectName,
          keyPrefix,
          apiKey,
          callbackUrl,
          isActive: true,
          createdAt: new Date().toISOString(),
        },
      },
      { status: 201 }
    )
  } catch (e: any) {
    console.error('[developer/keys POST]', e)
    return apiError(e?.message || 'Failed to create key', 500, 'internal_error', 'api_error')
  }
}

/** Revoke (soft-delete) or hard-delete an API key. Body: { id, hardDelete? } */
export async function DELETE(req: NextRequest) {
  try {
    const auth = await authenticateDeveloperSession(req)
    if (!auth.ok) return auth.response

    const body = await req.json().catch(() => ({}))
    const id = String(body.id || '').trim()
    const hardDelete = Boolean(body.hardDelete)

    if (!id) {
      return apiError('Key id is required.', 400, 'missing_key_id')
    }

    const owned = await pool.query(
      `SELECT id FROM api_keys WHERE id = $1 AND user_id = $2 LIMIT 1`,
      [id, auth.userId]
    )
    if (owned.rows.length === 0) {
      return apiError('API key not found.', 404, 'key_not_found')
    }

    if (hardDelete) {
      await pool.query(`DELETE FROM api_keys WHERE id = $1 AND user_id = $2`, [id, auth.userId])
    } else {
      await pool.query(
        `UPDATE api_keys SET is_active = FALSE WHERE id = $1 AND user_id = $2`,
        [id, auth.userId]
      )
    }

    return NextResponse.json({ success: true, revoked: id })
  } catch (e: any) {
    console.error('[developer/keys DELETE]', e)
    return apiError(e?.message || 'Failed to revoke key', 500, 'internal_error', 'api_error')
  }
}
