import { NextRequest, NextResponse } from 'next/server'
import { ensureDb } from '@/lib/db'
import { verifyAdminAuthorization } from '@/lib/secretVault'

export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  const adminKey = req.headers.get('x-admin-key')
  if (!verifyAdminAuthorization(adminKey)) {
    return NextResponse.json(
      { error: 'Forbidden: Administrator authorization required.' },
      { status: 403 }
    )
  }

  try {
    const startTime = Date.now()
    await ensureDb()

    return NextResponse.json({
      success: true,
      status: 'migrated',
      message: 'Database schema and migrations verified successfully.',
      duration_ms: Date.now() - startTime,
      timestamp: new Date().toISOString(),
    })
  } catch {
    return NextResponse.json(
      {
        success: false,
        status: 'error',
        error: 'Database migration failed',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    )
  }
}

export async function POST(req: NextRequest) {
  return GET(req)
}
