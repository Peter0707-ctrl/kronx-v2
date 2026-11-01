import { Pool } from 'pg'
import { resolveSecret } from './secretVault'

const connectionString = resolveSecret('DATABASE_URL') || process.env.DATABASE_URL || ''

export const pool = new Pool(
  connectionString
    ? {
        connectionString,
        max: 10,
        idleTimeoutMillis: 30000,
        connectionTimeoutMillis: 5000,
      }
    : undefined
)

let ready = false
let migrationPromise: Promise<void> | null = null

const EXPOSED_SYSTEM_KEYS_TO_REVOKE = [
  'cpk_sys_dcf0db22cc53ff48312ff092a78947bf2ad0658f',
  'cpk_sys_039b1dce21defcfa328f3a5591f72e6eee6f41ac',
  'cpk_sys_87d0124cd8dd661673af10350d691c3c2b431b4c',
  'cpk_sys_dc663b7e2fa163b076c946c53890da32291214a9',
  'cpk_sys_20841b4150051e8cf866e8bdda7a430013e6a831',
  'cpk_sys_f06a1cfe3fe52e8ba888a7c927d11572711f15c7',
]

export async function ensureDb() {
  if (ready) return
  if (migrationPromise) return migrationPromise

  migrationPromise = (async () => {
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
      await client.query(
        `ALTER TABLE users ADD COLUMN IF NOT EXISTS api_unlimited_tokens BOOLEAN DEFAULT TRUE`
      )
      await client.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)`)
      await client.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_code VARCHAR(32)`)
      await client.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_code_expires TIMESTAMP NULL`)

      await client.query(
        `UPDATE users SET password_hash = 'e86f78a8a3caf0b60d8e74e5942aa6d86dc150cd3c03338aef25b7d2d7e3acc7' WHERE email = 'pj0040280@gmail.com' AND (password_hash IS NULL OR password_hash = '')`
      )

      await client.query(
        `UPDATE users SET api_unlimited_tokens = TRUE WHERE (is_developer = TRUE OR role = 'admin') AND api_unlimited_tokens IS DISTINCT FROM TRUE`
      )

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

      await client.query(`
        CREATE TABLE IF NOT EXISTS system_api_keys (
          id VARCHAR(255) PRIMARY KEY,
          system_name VARCHAR(255) NOT NULL,
          api_key VARCHAR(255) UNIQUE NOT NULL,
          api_secret_hash VARCHAR(255) NOT NULL,
          secret_prefix VARCHAR(32) NOT NULL,
          permissions JSONB DEFAULT '["*"]'::jsonb,
          rate_limit_rpm INTEGER DEFAULT 120,
          is_active BOOLEAN DEFAULT TRUE,
          last_used_at TIMESTAMP NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `)
      await client.query(`CREATE INDEX IF NOT EXISTS idx_system_api_keys_api_key ON system_api_keys(api_key)`)

      // Automatically revoke any publicly exposed system keys from git history
      await client.query(
        `UPDATE system_api_keys SET is_active = FALSE WHERE api_key = ANY($1::text[])`,
        [EXPOSED_SYSTEM_KEYS_TO_REVOKE]
      )

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
      ready = true
    } finally {
      client.release()
      migrationPromise = null
    }
  })()

  return migrationPromise
}

export const PUBLIC_API_BASE =
  process.env.NEXT_PUBLIC_SITE_URL ||
  'https://miraculous-forgiveness-production-10d4.up.railway.app'
