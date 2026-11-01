import { NextRequest, NextResponse } from 'next/server'
import { createHash } from 'crypto'
import { ensureDb, pool } from '@/lib/db'
import { verifyAdminAuthorization } from '@/lib/secretVault'

export const dynamic = 'force-dynamic'

function maskApiKey(rawKey: unknown): string | null {
  if (typeof rawKey !== 'string' || !rawKey.trim()) return null
  const clean = rawKey.trim()
  if (clean.length <= 12) return 'cpk_********'
  return `${clean.slice(0, 8)}...${clean.slice(-4)}`
}

function mapUser(row: any, includeAdminFields = false) {
  return {
    id: row.id,
    name: row.name,
    email: row.email,
    role: row.role,
    plan: row.plan,
    avatar: row.avatar,
    lastActive: row.last_active,
    conversationCount: row.conversation_count,
    isDeveloper: Boolean(row.is_developer),
    apiUnlimitedTokens: row.api_unlimited_tokens !== false,
    expiresAt: row.expires_at,
    apiKey: includeAdminFields ? maskApiKey(row.api_key) : null,
    callbackUrl: includeAdminFields ? row.callback_url : null,
  }
}

export async function GET(req: NextRequest) {
  try {
    const adminKeyHeader = req.headers.get('x-admin-key')
    const isAdminRequest = verifyAdminAuthorization(adminKeyHeader)

    const emailParam = (
      req.nextUrl.searchParams.get('email') ||
      req.headers.get('x-user-email') ||
      ''
    )
      .toLowerCase()
      .trim()

    if (!isAdminRequest && (!emailParam || !emailParam.includes('@'))) {
      return NextResponse.json(
        { error: 'Forbidden: Valid administrator authorization or user session required.' },
        { status: 403 }
      )
    }

    await ensureDb()

    await pool.query(`
      UPDATE users
      SET plan = 'free', expires_at = NULL
      WHERE plan != 'free'
        AND role != 'admin'
        AND expires_at IS NOT NULL
        AND expires_at < NOW();
    `)

    if (isAdminRequest) {
      // Return ALL users to the authenticated Master Admin — zero hidden users allowed
      const result = await pool.query('SELECT * FROM users ORDER BY created_at ASC')
      return NextResponse.json(result.rows.map((r) => mapUser(r, true)))
    }

    const single = await pool.query(
      'SELECT * FROM users WHERE LOWER(email) = $1 LIMIT 1',
      [emailParam]
    )
    return NextResponse.json(single.rows.map((r) => mapUser(r, false)))
  } catch {
    console.error('[api/users GET] Database query failed')
    return NextResponse.json([], { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  try {
    await ensureDb()
    const user = await req.json().catch(() => ({}))

    const emailLower = String(user.email || '').toLowerCase().trim()
    if (!emailLower || !emailLower.includes('@') || emailLower.length > 254) {
      return NextResponse.json({ success: false, error: 'Valid email is required' }, { status: 400 })
    }

    const adminKeyHeader = req.headers.get('x-admin-key')
    const isAdminRequest = verifyAdminAuthorization(adminKeyHeader)
    const isMasterAdminEmail = emailLower === 'pj0040280@gmail.com'

    if (isMasterAdminEmail && !isAdminRequest) {
      return NextResponse.json(
        { success: false, error: 'Forbidden: Master administrator credentials required.' },
        { status: 403 }
      )
    }

    let targetRole = 'user'
    let targetPlan = 'free'
    let targetIsDeveloper = false

    if (isMasterAdminEmail && isAdminRequest) {
      targetRole = 'admin'
      targetPlan = 'premium'
      targetIsDeveloper = true
    } else if (isAdminRequest) {
      targetRole = user.role === 'admin' ? 'admin' : 'user'
      targetPlan = ['free', 'plus', 'premium', 'pro'].includes(user.plan) ? user.plan : 'free'
      targetIsDeveloper = Boolean(user.isDeveloper)
    } else {
      const existing = await pool.query(
        'SELECT role, plan, is_developer FROM users WHERE LOWER(email) = $1 LIMIT 1',
        [emailLower]
      )
      if (existing.rows.length > 0) {
        targetRole = existing.rows[0].role || 'user'
        targetPlan = existing.rows[0].plan || 'free'
        targetIsDeveloper = Boolean(existing.rows[0].is_developer)
      }
    }

    let expiresAt: Date | null = null
    if (targetPlan && targetPlan !== 'free') {
      expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
    }

    let passHash: string | null = null
    if (user.password && typeof user.password === 'string' && user.password.trim()) {
      passHash = createHash('sha256').update(user.password.trim()).digest('hex')
    } else if (isAdminRequest && (user.passwordHash || user.password_hash)) {
      passHash = String(user.passwordHash || user.password_hash)
    }

    const safeName = String(user.name || emailLower.split('@')[0]).replace(/[<>]/g, '').slice(0, 120)
    const safeId = String(user.id || `u-${Date.now()}`).replace(/[^a-zA-Z0-9_-]/g, '').slice(0, 120)

    const query = `
      INSERT INTO users (id, name, email, role, plan, avatar, last_active, conversation_count, is_developer, api_unlimited_tokens, expires_at, api_key, callback_url, password_hash)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
      ON CONFLICT (email) DO UPDATE SET
        name = EXCLUDED.name,
        role = EXCLUDED.role,
        plan = EXCLUDED.plan,
        avatar = EXCLUDED.avatar,
        last_active = EXCLUDED.last_active,
        is_developer = EXCLUDED.is_developer,
        api_unlimited_tokens = EXCLUDED.api_unlimited_tokens,
        expires_at = EXCLUDED.expires_at,
        api_key = COALESCE(EXCLUDED.api_key, users.api_key),
        callback_url = COALESCE(EXCLUDED.callback_url, users.callback_url),
        password_hash = COALESCE(users.password_hash, EXCLUDED.password_hash)
      RETURNING *;
    `

    const unlimitedTokens =
      targetIsDeveloper || targetRole === 'admin' || (isAdminRequest && user.apiUnlimitedTokens === true)

    const values = [
      safeId,
      safeName,
      emailLower,
      targetRole,
      targetPlan,
      user.avatar ||
        `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(safeName || 'User')}`,
      'Active Now',
      Number.isFinite(Number(user.conversationCount)) ? Number(user.conversationCount) : 0,
      targetIsDeveloper,
      unlimitedTokens,
      expiresAt,
      null,
      null,
      passHash,
    ]

    const result = await pool.query(query, values)
    return NextResponse.json({ success: true, user: mapUser(result.rows[0], isAdminRequest) })
  } catch {
    console.error('[api/users POST] Database write failed')
    return NextResponse.json({ success: false, error: 'Operation failed' }, { status: 500 })
  }
}
