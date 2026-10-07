import { NextRequest, NextResponse } from 'next/server'
import { createHash } from 'crypto'
import { ensureDb, pool } from '@/lib/db'

export const dynamic = 'force-dynamic'

const MASTER_ADMIN_EMAIL = 'pj0040280@gmail.com'
const MASTER_ADMIN_PASS_HASH = 'e86f78a8a3caf0b60d8e74e5942aa6d86dc150cd3c03338aef25b7d2d7e3acc7'

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

/**
 * POST /api/auth/login
 * Validates user credentials against stored SHA-256 password hash
 */
export async function POST(req: NextRequest) {
  try {
    await ensureDb()
    const body = await req.json().catch(() => ({}))
    const rawEmail = String(body.email || '').trim().toLowerCase()
    const password = String(body.password || '').trim()

    if (!rawEmail || !password) {
      return NextResponse.json(
        { success: false, message: 'Please provide both email and password.' },
        { status: 400 }
      )
    }

    const inputHash = createHash('sha256').update(password).digest('hex')

    // 1. Check Master Admin
    if (rawEmail === MASTER_ADMIN_EMAIL && inputHash === MASTER_ADMIN_PASS_HASH) {
      const adminRes = await pool.query(
        `SELECT * FROM users WHERE LOWER(email) = $1 LIMIT 1`,
        [MASTER_ADMIN_EMAIL]
      )
      const adminRow = adminRes.rows[0] || {
        id: 'u-admin-master',
        name: 'Admin at pjcopetranovax',
        email: MASTER_ADMIN_EMAIL,
        role: 'admin',
        plan: 'premium',
        is_developer: true,
      }
      return NextResponse.json({
        success: true,
        user: {
          ...mapUser(adminRow),
          role: 'admin',
          plan: 'premium',
          isDeveloper: true,
          adminKey: inputHash,
        },
      })
    }

    // 2. Query normal user
    const userResult = await pool.query(
      `SELECT * FROM users WHERE LOWER(email) = $1 LIMIT 1`,
      [rawEmail]
    )

    if (userResult.rows.length === 0) {
      return NextResponse.json(
        {
          success: false,
          code: 'user_not_found',
          message: 'Akaunti haipatikani. Tafadhali jisajili / Account not found. Please register first.',
        },
        { status: 404 }
      )
    }

    const userRow = userResult.rows[0]

    // 3. Verify password
    if (userRow.password_hash) {
      if (userRow.password_hash !== inputHash) {
        return NextResponse.json(
          {
            success: false,
            code: 'invalid_password',
            message: 'Nenosiri si sahihi. Jaribu tena au bonyeza "Forgot Password" / Incorrect password. Please try again or click "Forgot Password" to reset.',
          },
          { status: 401 }
        )
      }
    } else {
      // First-time legacy login: persist this password hash for future logins
      await pool.query(
        `UPDATE users SET password_hash = $1 WHERE LOWER(email) = $2`,
        [inputHash, rawEmail]
      ).catch(() => {})
    }

    // Update last_active
    await pool.query(
      `UPDATE users SET last_active = 'Active Now' WHERE LOWER(email) = $1`,
      [rawEmail]
    ).catch(() => {})

    return NextResponse.json({
      success: true,
      user: mapUser(userRow),
    })
  } catch (error: any) {
    console.error('[AUTH LOGIN ERROR]', error)
    return NextResponse.json(
      { success: false, message: error?.message || 'Server error during login.' },
      { status: 500 }
    )
  }
}
