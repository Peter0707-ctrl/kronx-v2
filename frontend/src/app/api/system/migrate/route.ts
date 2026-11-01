import { NextResponse } from 'next/server'
import { ensureDb, pool } from '@/lib/db'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    const startTime = Date.now()
    await ensureDb()

    const usersCount = await pool.query('SELECT COUNT(*)::int AS count FROM users;')
    const keysCount = await pool.query('SELECT COUNT(*)::int AS count FROM api_keys;')
    const systemKeysCount = await pool.query('SELECT COUNT(*)::int AS count FROM system_api_keys;')
    const adminCheck = await pool.query("SELECT id, email, role, plan FROM users WHERE role = 'admin' LIMIT 5;")

    return NextResponse.json({
      success: true,
      status: 'migrated',
      message: 'Database schema and migrations verified successfully.',
      duration_ms: Date.now() - startTime,
      stats: {
        users_count: usersCount.rows[0]?.count ?? 0,
        api_keys_count: keysCount.rows[0]?.count ?? 0,
        system_api_keys_count: systemKeysCount.rows[0]?.count ?? 0,
        admin_accounts: adminCheck.rows,
      },
      schema: {
        tables: ['users', 'api_keys', 'system_api_keys'],
        indexes: ['idx_api_keys_user_id', 'idx_api_keys_api_key', 'idx_system_api_keys_api_key'],
      },
      timestamp: new Date().toISOString(),
    })
  } catch (error: any) {
    console.error('[MIGRATE API ERROR]', error)
    return NextResponse.json(
      {
        success: false,
        status: 'error',
        error: error.message || 'Database migration failed',
        code: error.code || null,
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    )
  }
}

export async function POST() {
  return GET()
}
