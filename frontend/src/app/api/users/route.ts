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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
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
    }))
    
    return NextResponse.json(users)
  } catch (e: any) {
    console.error('DB GET Error', e)
    // If DB fails (e.g. locally), return empty array so UI doesn't crash completely
    return NextResponse.json([], { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  try {
    await ensureDb()
    const user = await req.json()
    
    // UPSERT logic
    const query = `
      INSERT INTO users (id, name, email, role, plan, avatar, last_active, conversation_count, is_developer)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
      ON CONFLICT (email) DO UPDATE SET
        name = EXCLUDED.name,
        role = EXCLUDED.role,
        plan = EXCLUDED.plan,
        avatar = EXCLUDED.avatar,
        last_active = EXCLUDED.last_active,
        is_developer = EXCLUDED.is_developer
      RETURNING *;
    `
    
    const values = [
      user.id,
      user.name,
      user.email,
      user.role || 'user',
      user.plan || 'free',
      user.avatar || \`https://api.dicebear.com/7.x/avataaars/svg?seed=\${encodeURIComponent(user.name || 'User')}\`,
      user.lastActive || 'Just now',
      user.conversationCount || 0,
      user.isDeveloper || false
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
    }
    
    return NextResponse.json({ success: true, user: savedUser })
  } catch (e: any) {
    console.error('DB POST Error', e)
    return NextResponse.json({ success: false, error: e.message }, { status: 500 })
  }
}
