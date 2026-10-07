import { NextRequest, NextResponse } from 'next/server'
import { createHash } from 'crypto'
import { ensureDb, pool } from '@/lib/db'

export const dynamic = 'force-dynamic'

/**
 * POST /api/auth/reset-password
 * Verifies the 6-digit code and securely updates the user's password
 */
export async function POST(req: NextRequest) {
  try {
    await ensureDb()
    const body = await req.json().catch(() => ({}))
    const rawEmail = String(body.email || '').trim().toLowerCase()
    const code = String(body.code || '').trim()
    const newPassword = String(body.newPassword || body.password || '').trim()

    if (!rawEmail || !rawEmail.includes('@')) {
      return NextResponse.json(
        { success: false, message: 'Please provide a valid email address.' },
        { status: 400 }
      )
    }

    if (!code || code.length < 4) {
      return NextResponse.json(
        { success: false, message: 'Please provide the 6-digit verification code.' },
        { status: 400 }
      )
    }

    if (!newPassword || newPassword.length < 4) {
      return NextResponse.json(
        { success: false, message: 'New password must be at least 4 characters.' },
        { status: 400 }
      )
    }

    const userResult = await pool.query(
      `SELECT id, name, email, reset_code, reset_code_expires FROM users WHERE LOWER(email) = $1 LIMIT 1`,
      [rawEmail]
    )

    if (userResult.rows.length === 0) {
      return NextResponse.json(
        { success: false, message: 'Account not found with this email address.' },
        { status: 404 }
      )
    }

    const user = userResult.rows[0]

    if (!user.reset_code) {
      return NextResponse.json(
        { success: false, message: 'Hakuna nambari ya uhakiki iliyoombwa / No active reset request found for this account.' },
        { status: 400 }
      )
    }

    if (String(user.reset_code).trim() !== code) {
      return NextResponse.json(
        { success: false, message: 'Nambari ya uhakiki si sahihi / Invalid verification code.' },
        { status: 400 }
      )
    }

    if (user.reset_code_expires && new Date() > new Date(user.reset_code_expires)) {
      return NextResponse.json(
        { success: false, message: 'Nambari ya uhakiki imeisha muda wake / Verification code has expired. Please request a new one.' },
        { status: 400 }
      )
    }

    // Compute SHA-256 hash of new password
    const newHash = createHash('sha256').update(newPassword).digest('hex')

    await pool.query(
      `UPDATE users
       SET password_hash = $1, reset_code = NULL, reset_code_expires = NULL
       WHERE LOWER(email) = $2`,
      [newHash, rawEmail]
    )

    console.log(`[AUTH] Password successfully reset for ${rawEmail}`)

    return NextResponse.json({
      success: true,
      message: 'Nenosiri jipya limewekwa kikamilifu! Sasa unaweza kuingia / New password has been set successfully! You can now sign in.',
    })
  } catch (error: any) {
    console.error('[AUTH RESET PASSWORD ERROR]', error)
    return NextResponse.json(
      { success: false, message: error?.message || 'Server error while resetting password.' },
      { status: 500 }
    )
  }
}
