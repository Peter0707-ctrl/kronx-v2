import { NextRequest, NextResponse } from 'next/server'
import { Pool } from 'pg'

export const dynamic = 'force-dynamic'

const connectionString = process.env.DATABASE_URL || 'postgresql://postgres:TdoGwPBGGbhiWgarnDevahuPxoehQspt@postgres.railway.internal:5432/railway'

const pool = new Pool({
  connectionString,
})

// Initialize DB table if it doesn't exist
async function initDb() {
  const client = await pool.connect()
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS users (
        id VARCHAR(255) PRIMARY KEY,
        name VARCHAR(255),
        email VARCHAR(255) UNIQUE,
        role VARCHAR(50),
        plan VARCHAR(50),
        avatar VARCHAR(255),
        last_active VARCHAR(255),
        conversation_count INTEGER,
        is_developer BOOLEAN DEFAULT FALSE,
        expires_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `)
    
    // Ensure expires_at column exists for existing tables
    await client.query(`
      ALTER TABLE users ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP NULL;
    `)
    
    // Ensure api_key and callback_url columns exist
    await client.query(`
      ALTER TABLE users ADD COLUMN IF NOT EXISTS api_key VARCHAR(255);
    `)
    await client.query(`
      ALTER TABLE users ADD COLUMN IF NOT EXISTS callback_url VARCHAR(255);
    `)

    // Insert default admin if not exists
    const checkAdmin = await client.query(`SELECT id FROM users WHERE id = 'u-admin-master'`)
    if (checkAdmin.rowCount === 0) {
      await client.query(`
        INSERT INTO users (id, name, email, role, plan, avatar, last_active, conversation_count, is_developer)
        VALUES (
          'u-admin-master',
          'Admin at pjcopetranovax',
          'pj0040280@gmail.com',
          'admin',
          'premium',
          'https://api.dicebear.com/7.x/avataaars/svg?seed=Admin',
          'Active Now',
          1,
          true
        )
      `)
    }
  } finally {
    client.release()
  }
}

// Call initDb on first load (lazy initialization)
let dbInitialized = false
async function ensureDb() {
  if (!dbInitialized) {
    await initDb()
    dbInitialized = true
  }
}

export async function GET() {
  try {
    await ensureDb()
    
    // Auto-expire subscriptions older than 30 days for non-admin accounts
    await pool.query(`
      UPDATE users 
      SET plan = 'free', expires_at = NULL 
      WHERE plan != 'free' 
        AND role != 'admin' 
        AND expires_at IS NOT NULL 
        AND expires_at < NOW();
    `)

    const result = await pool.query('SELECT * FROM users ORDER BY created_at ASC')
    
    // Map snake_case from DB to camelCase for frontend
    const users = result.rows.map(row => ({
      id: row.id,
      name: row.name,
      email: row.email,
      role: row.role,
      plan: row.plan,
      avatar: row.avatar,
      lastActive: row.last_active,
      conversationCount: row.conversation_count,
      isDeveloper: row.is_developer,
      expiresAt: row.expires_at,
      apiKey: row.api_key,
      callbackUrl: row.callback_url,
    }))
    
    return NextResponse.json(users)
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
    // Master Admin Password Hash: Admin@123
    const isAdminRequest = adminKeyHeader === 'e86f78a8a3caf0b60d8e74e5942aa6d86dc150cd3c03338aef25b7d2d7e3acc7'

    const emailLower = (user.email || '').toLowerCase().trim()
    const isMasterAdminEmail = emailLower === 'pj0040280@gmail.com'

    let targetRole = user.role || 'user'
    let targetPlan = user.plan || 'free'
    let targetIsDeveloper = user.isDeveloper || false

    if (isMasterAdminEmail) {
      targetRole = 'admin'
      targetPlan = 'premium'
      targetIsDeveloper = true
    } else if (!isAdminRequest) {
      // Not master admin email, and not an approved admin request
      // Check if user already exists in DB to prevent escalation
      const existing = await pool.query('SELECT role, plan, is_developer FROM users WHERE LOWER(email) = $1', [emailLower])
      if (existing.rows.length > 0) {
        // Preserve existing values to prevent any modification to role/plan/developer status
        targetRole = existing.rows[0].role || 'user'
        targetPlan = existing.rows[0].plan || 'free'
        targetIsDeveloper = existing.rows[0].is_developer || false
      } else {
        // New user registration - force free tier and user role
        targetRole = 'user'
        targetPlan = 'free'
        targetIsDeveloper = false
      }
    }

    // Calculate 30-day monthly expiration date for paid subscriptions
    let expiresAt: Date | null = null
    if (targetPlan && targetPlan !== 'free') {
      expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
    }
    
    // UPSERT logic with api_key and callback_url
    const query = `
      INSERT INTO users (id, name, email, role, plan, avatar, last_active, conversation_count, is_developer, expires_at, api_key, callback_url)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
      ON CONFLICT (email) DO UPDATE SET
        name = EXCLUDED.name,
        role = EXCLUDED.role,
        plan = EXCLUDED.plan,
        avatar = EXCLUDED.avatar,
        last_active = EXCLUDED.last_active,
        is_developer = EXCLUDED.is_developer,
        expires_at = EXCLUDED.expires_at,
        api_key = EXCLUDED.api_key,
        callback_url = EXCLUDED.callback_url
      RETURNING *;
    `
    
    const values = [
      user.id,
      user.name,
      emailLower,
      targetRole,
      targetPlan,
      user.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(user.name || 'User')}`,
      user.lastActive || 'Just now',
      user.conversationCount || 0,
      targetIsDeveloper,
      expiresAt,
      user.apiKey || null,
      user.callbackUrl || null
    ]
    
    const result = await pool.query(query, values)
    const row = result.rows[0]
    
    const savedUser = {
      id: row.id,
      name: row.name,
      email: row.email,
      role: row.role,
      plan: row.plan,
      avatar: row.avatar,
      lastActive: row.last_active,
      conversationCount: row.conversation_count,
      isDeveloper: row.is_developer,
      expiresAt: row.expires_at,
      apiKey: row.api_key,
      callbackUrl: row.callback_url
    }
    
    return NextResponse.json({ success: true, user: savedUser })
  } catch (e: any) {
    console.error('DB POST Error', e)
    return NextResponse.json({ success: false, error: e.message }, { status: 500 })
  }
}
