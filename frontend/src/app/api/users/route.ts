import { NextRequest, NextResponse } from 'next/server'
import { ensureDb, pool } from '@/lib/db'

export const dynamic = 'force-dynamic'

const MASTER_ADMIN_HASH = 'e86f78a8a3caf0b60d8e74e5942aa6d86dc150cd3c03338aef25b7d2d7e3acc7'

function mapUser(row: any) {
  return {
    id: row.id,
    name: row.name,
    email: row.email,
    role: row.role,
    plan: row.plan,
    avatar: row.avatar,
    lastActive: row.last_active,
    conversationCount: row.conversation_count,
    isDeveloper: row.is_developer,
    apiUnlimitedTokens: row.api_unlimited_tokens !== false,
    expiresAt: row.expires_at,
    apiKey: row.api_key,
    callbackUrl: row.callback_url,
  }
}

export async function GET() {
  try {
    await ensureDb()

    await pool.query(`
      UPDATE users
      SET plan = 'free', expires_at = NULL
      WHERE plan != 'free'
        AND role != 'admin'
        AND expires_at IS NOT NULL
        AND expires_at < NOW();
    `)

    const result = await pool.query('SELECT * FROM users ORDER BY created_at ASC')
    return NextResponse.json(result.rows.map(mapUser))
  } catch (e: any) {
    console.error('DB GET Error', e)
    return NextResponse.json([], { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  try {
    await ensureDb()
    const user = await req.json()

    const adminKeyHeader = req.headers.get('x-admin-key')
    const isAdminRequest = adminKeyHeader === MASTER_ADMIN_HASH

    const emailLower = (user.email || '').toLowerCase().trim()
    const isMasterAdminEmail = emailLower === 'pj0040280@gmail.com'

    let targetRole = user.role || 'user'
    let targetPlan = user.plan || 'free'
    let targetIsDeveloper = false

    if (isMasterAdminEmail) {
      targetRole = 'admin'
      targetPlan = 'premium'
      targetIsDeveloper = true
    } else if (isAdminRequest) {
      // Admin console may change role / plan / developer grant
      targetRole = user.role || 'user'
      targetPlan = user.plan || 'free'
      targetIsDeveloper = Boolean(user.isDeveloper)
    } else {
      // Self-service: never allow escalating role/plan/developer
      const existing = await pool.query(
        'SELECT role, plan, is_developer FROM users WHERE LOWER(email) = $1',
        [emailLower]
      )
      if (existing.rows.length > 0) {
        targetRole = existing.rows[0].role || 'user'
        targetPlan = existing.rows[0].plan || 'free'
        targetIsDeveloper = Boolean(existing.rows[0].is_developer)
      } else {
        targetRole = 'user'
        targetPlan = 'free'
        targetIsDeveloper = false
      }
    }

    let expiresAt: Date | null = null
    if (targetPlan && targetPlan !== 'free') {
      expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
    }

    const query = `
      INSERT INTO users (id, name, email, role, plan, avatar, last_active, conversation_count, is_developer, api_unlimited_tokens, expires_at, api_key, callback_url)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
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
        callback_url = COALESCE(EXCLUDED.callback_url, users.callback_url)
      RETURNING *;
    `

    // Granted developers / admins always get unlimited app-side tokens
    const unlimitedTokens =
      targetIsDeveloper || targetRole === 'admin' || user.apiUnlimitedTokens === true

    const values = [
      user.id,
      user.name,
      emailLower,
      targetRole,
      targetPlan,
      user.avatar ||
        `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(user.name || 'User')}`,
      user.lastActive || 'Just now',
      user.conversationCount || 0,
      targetIsDeveloper,
      unlimitedTokens,
      expiresAt,
      user.apiKey || null,
      user.callbackUrl || null,
    ]

    const result = await pool.query(query, values)
    return NextResponse.json({ success: true, user: mapUser(result.rows[0]) })
  } catch (e: any) {
    console.error('DB POST Error', e)
    return NextResponse.json({ success: false, error: e.message }, { status: 500 })
  }
}
