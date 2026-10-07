import { NextRequest, NextResponse } from 'next/server'
import { randomBytes, createHash } from 'crypto'
import { v4 as uuidv4 } from 'uuid'
import { ensureDb, pool } from '@/lib/db'
import { apiError } from '@/lib/developerAuth'

export const dynamic = 'force-dynamic'

async function verifyAdminOrMaster(req: NextRequest) {
  // 1. Check MASTER_KEY / ADMIN_KEY from env
  const masterKey = process.env.SYSTEM_MASTER_KEY || process.env.ADMIN_KEY || 'kronx-master-system-2026'
  const providedMaster = req.headers.get('x-master-key') || req.headers.get('x-admin-key')
  if (providedMaster && providedMaster === masterKey) {
    return { ok: true, source: 'master_key' }
  }

  // 2. Check admin user session
  const userId = req.headers.get('x-user-id')?.trim()
  const email = req.headers.get('x-user-email')?.toLowerCase().trim()
  if (userId && email) {
    await ensureDb()
    const res = await pool.query(
      `SELECT id, role, is_developer FROM users WHERE id = $1 AND LOWER(email) = $2 LIMIT 1`,
      [userId, email]
    )
    const user = res.rows[0]
    if (user && (user.role === 'admin' || user.is_developer)) {
      return { ok: true, source: 'admin_user', userId: user.id }
    }
  }

  return {
    ok: false,
    response: apiError(
      'Unauthorized. Provide valid x-master-key or admin credentials.',
      401,
      'system_unauthorized'
    ),
  }
}

/**
 * GET /api/system/keys
 * List active machine-to-machine system API keys (secrets are never returned)
 */
export async function GET(req: NextRequest) {
  try {
    const auth = await verifyAdminOrMaster(req)
    if (!auth.ok) return auth.response

    await ensureDb()
    const res = await pool.query(`
      SELECT id, system_name, api_key, secret_prefix, permissions, rate_limit_rpm, is_active, last_used_at, created_at
      FROM system_api_keys
      ORDER BY created_at DESC
    `)

    return NextResponse.json({
      success: true,
      systems: res.rows.map((r) => ({
        id: r.id,
        systemName: r.system_name,
        apiKey: r.api_key,
        secretPrefix: `${r.secret_prefix}…`,
        permissions: r.permissions,
        rateLimitRpm: r.rate_limit_rpm,
        isActive: r.is_active,
        lastUsedAt: r.last_used_at,
        createdAt: r.created_at,
      })),
      count: res.rows.length,
    })
  } catch (err: any) {
    console.error('[system/keys GET]', err)
    return apiError(err?.message || 'Failed to list system keys', 500, 'system_keys_error')
  }
}

/**
 * POST /api/system/keys
 * Generate and register a new system API Key + API Secret pair
 * Body: { systemName: string, permissions?: string[], rateLimitRpm?: number }
 */
export async function POST(req: NextRequest) {
  try {
    const auth = await verifyAdminOrMaster(req)
    if (!auth.ok) return auth.response

    await ensureDb()
    const body = await req.json().catch(() => ({}))
    const systemName = String(body.systemName || body.system_name || '').trim()

    if (!systemName || systemName.length < 2) {
      return apiError('systemName is required (min 2 characters).', 400, 'missing_system_name')
    }

    const permissions = Array.isArray(body.permissions) ? body.permissions : ['*']
    const rateLimitRpm = typeof body.rateLimitRpm === 'number' ? body.rateLimitRpm : 120

    const id = `sys_${uuidv4()}`
    const keyEntropy = randomBytes(20).toString('hex')
    const secretEntropy = randomBytes(32).toString('hex')

    const apiKey = `cpk_sys_${keyEntropy}`
    const apiSecret = `cps_sec_${secretEntropy}`
    const secretHash = createHash('sha256').update(apiSecret).digest('hex')
    const secretPrefix = apiSecret.slice(0, 12)

    await pool.query(
      `INSERT INTO system_api_keys (id, system_name, api_key, api_secret_hash, secret_prefix, permissions, rate_limit_rpm, is_active)
       VALUES ($1, $2, $3, $4, $5, $6, $7, TRUE)`,
      [id, systemName, apiKey, secretHash, secretPrefix, JSON.stringify(permissions), rateLimitRpm]
    )

    return NextResponse.json(
      {
        success: true,
        message: 'System API key & secret generated. Save the apiSecret now; it will not be displayed again.',
        credentials: {
          id,
          systemName,
          apiKey,
          apiSecret,
          secretPrefix,
          permissions,
          rateLimitRpm,
          isActive: true,
          createdAt: new Date().toISOString(),
        },
      },
      { status: 201 }
    )
  } catch (err: any) {
    console.error('[system/keys POST]', err)
    return apiError(err?.message || 'Failed to generate system keys', 500, 'system_keys_error')
  }
}

/**
 * DELETE /api/system/keys
 * Revoke or hard delete a system key
 * Body: { id: string, hardDelete?: boolean }
 */
export async function DELETE(req: NextRequest) {
  try {
    const auth = await verifyAdminOrMaster(req)
    if (!auth.ok) return auth.response

    await ensureDb()
    const body = await req.json().catch(() => ({}))
    const id = String(body.id || '').trim()
    const hardDelete = Boolean(body.hardDelete)

    if (!id) {
      return apiError('Key id is required.', 400, 'missing_key_id')
    }

    if (hardDelete) {
      await pool.query(`DELETE FROM system_api_keys WHERE id = $1`, [id])
    } else {
      await pool.query(`UPDATE system_api_keys SET is_active = FALSE WHERE id = $1`, [id])
    }

    return NextResponse.json({ success: true, revokedId: id })
  } catch (err: any) {
    console.error('[system/keys DELETE]', err)
    return apiError(err?.message || 'Failed to revoke system key', 500, 'system_keys_error')
  }
}
