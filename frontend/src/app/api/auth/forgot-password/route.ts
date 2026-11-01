import { NextRequest, NextResponse } from 'next/server'
import { ensureDb, pool } from '@/lib/db'

export const dynamic = 'force-dynamic'

/**
 * POST /api/auth/forgot-password
 * Initiates the password recovery workflow by generating a secure 6-digit OTP code
 */
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

    // Generate secure 6-digit verification code
    const resetCode = Math.floor(100000 + Math.random() * 900000).toString()
    // Expires in 15 minutes
    const expiresAt = new Date(Date.now() + 15 * 60 * 1000)

    await pool.query(
      `UPDATE users
       SET reset_code = $1, reset_code_expires = $2
       WHERE LOWER(email) = $3`,
      [resetCode, expiresAt, rawEmail]
    )

    console.log(`[AUTH] Password reset requested for ${rawEmail}. Code: ${resetCode}`)

    return NextResponse.json({
      success: true,
      message: 'Nambari ya uhakiki imetolewa kikamilifu / Verification code generated successfully.',
      code: resetCode,
      email: user.email,
      expiresAt: expiresAt.toISOString(),
    })
  } catch (error: any) {
    console.error('[AUTH FORGOT PASSWORD ERROR]', error)
    return NextResponse.json(
      { success: false, message: error?.message || 'Server error while generating reset code.' },
      { status: 500 }
    )
  }
}
