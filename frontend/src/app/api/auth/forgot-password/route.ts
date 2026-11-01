import { NextRequest, NextResponse } from 'next/server'
import { randomInt } from 'crypto'
import { ensureDb, pool } from '@/lib/db'
import { verifyAdminAuthorization } from '@/lib/secretVault'

export const dynamic = 'force-dynamic'

const MASTER_ADMIN_EMAIL = 'pj0040280@gmail.com'

export async function POST(req: NextRequest) {
  try {
    await ensureDb()
    const body = await req.json().catch(() => ({}))
    const rawEmail = String(body.email || '').trim().toLowerCase()

    if (!rawEmail || !rawEmail.includes('@')) {
      return NextResponse.json(
        { success: false, message: 'Please provide a valid email address.' },
        { status: 400 }
      )
    }

    const isAdminRequest = verifyAdminAuthorization(req.headers.get('x-admin-key'))

    // Prevent unauthenticated password reset requests against the Master Admin account
    if (rawEmail === MASTER_ADMIN_EMAIL && !isAdminRequest) {
      return NextResponse.json(
        {
          success: false,
          message: 'Master Administrator password cannot be reset without hardware/master key verification.',
        },
        { status: 403 }
      )
    }

    const userResult = await pool.query(
      `SELECT id, name, email FROM users WHERE LOWER(email) = $1 LIMIT 1`,
      [rawEmail]
    )

    if (userResult.rows.length === 0) {
      return NextResponse.json(
        {
          success: false,
          message: 'Hakuna akaunti iliyopatikana na barua pepe hii / No account registered with this email address.',
        },
        { status: 404 }
      )
    }

    const user = userResult.rows[0]
    const resetCode = randomInt(100000, 999999).toString()
    const expiresAt = new Date(Date.now() + 15 * 60 * 1000)

    await pool.query(
      `UPDATE users
       SET reset_code = $1, reset_code_expires = $2
       WHERE LOWER(email) = $3`,
      [resetCode, expiresAt, rawEmail]
    )

    return NextResponse.json({
      success: true,
      message: 'Nambari ya uhakiki imetolewa kikamilifu / Verification code generated.',
      ...(isAdminRequest ? { code: resetCode } : {}),
      email: user.email,
      expiresAt: expiresAt.toISOString(),
    })
  } catch {
    return NextResponse.json(
      { success: false, message: 'Server error while generating reset code.' },
      { status: 500 }
    )
  }
}
