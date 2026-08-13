import { Pool } from 'pg'

const connectionString =
  process.env.DATABASE_URL ||
  'postgresql://postgres:TdoGwPBGGbhiWgarnDevahuPxoehQspt@postgres.railway.internal:5432/railway'

export const pool = new Pool({ connectionString })

let ready = false

export async function ensureDb() {
  if (ready) return

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
    await client.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP NULL`)
    await client.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS api_key VARCHAR(255)`)
    await client.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS callback_url VARCHAR(255)`)

    await client.query(`
      CREATE TABLE IF NOT EXISTS api_keys (
        id VARCHAR(255) PRIMARY KEY,
        user_id VARCHAR(255) NOT NULL,
        project_name VARCHAR(255) NOT NULL,
        key_prefix VARCHAR(64) NOT NULL,
        api_key VARCHAR(255) UNIQUE NOT NULL,
        callback_url VARCHAR(512),
        is_active BOOLEAN DEFAULT TRUE,
        last_used_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `)
    await client.query(`CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id)`)
    await client.query(`CREATE INDEX IF NOT EXISTS idx_api_keys_api_key ON api_keys(api_key)`)

    // Migrate legacy single user.api_key rows into api_keys
    await client.query(`
      INSERT INTO api_keys (id, user_id, project_name, key_prefix, api_key, callback_url, is_active)
      SELECT
        'legacy-' || u.id,
        u.id,
        'Default Project',
        LEFT(u.api_key, 12),
        u.api_key,
        u.callback_url,
        TRUE
      FROM users u
      WHERE u.api_key IS NOT NULL
        AND u.api_key <> ''
        AND NOT EXISTS (SELECT 1 FROM api_keys k WHERE k.api_key = u.api_key)
    `)

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

  ready = true
}

export const PUBLIC_API_BASE =
  process.env.NEXT_PUBLIC_SITE_URL ||
  'https://miraculous-forgiveness-production-10d4.up.railway.app'
