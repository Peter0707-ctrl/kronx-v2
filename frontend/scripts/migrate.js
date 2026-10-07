/**
 * Standalone Database Migration Script for Copetra / Kronx
 *
 * Usage:
 *   node scripts/migrate.js
 *   node scripts/migrate.js --url="postgresql://user:pass@host:5432/dbname"
 *   npm run db:migrate
 */

const fs = require('fs')
const path = require('path')
const { Pool } = require('pg')

function loadEnvFile(filePath) {
  if (!fs.existsSync(filePath)) return {}
  const content = fs.readFileSync(filePath, 'utf-8')
  const env = {}
  for (const line of content.split('\n')) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) continue
    const eqIdx = trimmed.indexOf('=')
    if (eqIdx !== -1) {
      const key = trimmed.slice(0, eqIdx).trim()
      let val = trimmed.slice(eqIdx + 1).trim()
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1)
      }
      env[key] = val
    }
  }
  return env
}

async function runMigration() {
  console.log('\n======================================================')
  console.log('       COPETRA / KRONX DATABASE MIGRATION RUNNER      ')
  console.log('======================================================\n')

  // Load envs
  const rootDir = path.resolve(__dirname, '..')
  const envLocal = loadEnvFile(path.join(rootDir, '.env.local'))
  const envDefault = loadEnvFile(path.join(rootDir, '.env'))

  // Parse CLI args
  const argUrl = process.argv.find((a) => a.startsWith('--url='))?.split('=')[1]

  const connectionString =
    argUrl ||
    process.env.DATABASE_URL ||
    envLocal.DATABASE_URL ||
    envDefault.DATABASE_URL ||
    'postgresql://postgres:TdoGwPBGGbhiWgarnDevahuPxoehQspt@postgres.railway.internal:5432/railway'

  const maskedUrl = connectionString.replace(/:([^:@]+)@/, ':****@')
  console.log(`[1/5] Target Database: ${maskedUrl}`)

  const pool = new Pool({
    connectionString,
    connectionTimeoutMillis: 10000,
  })

  let client
  try {
    console.log('[2/5] Establishing database connection...')
    client = await pool.connect()
    console.log('      Connected successfully!')

    console.log('\n[3/5] Applying schema migrations...')

    // 1. Users table
    console.log('      - Ensuring table "users"...')
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

    // 2. Add columns if not exist
    console.log('      - Verifying user schema columns (expires_at, api_key, callback_url, api_unlimited_tokens)...')
    await client.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP NULL;`)
    await client.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS api_key VARCHAR(255);`)
    await client.query(`ALTER TABLE users ADD COLUMN IF NOT EXISTS callback_url VARCHAR(255);`)
    await client.query(
      `ALTER TABLE users ADD COLUMN IF NOT EXISTS api_unlimited_tokens BOOLEAN DEFAULT TRUE;`
    )

    // 3. Update permissions
    console.log('      - Updating developer & admin unlimited tokens...')
    await client.query(
      `UPDATE users SET api_unlimited_tokens = TRUE WHERE (is_developer = TRUE OR role = 'admin') AND api_unlimited_tokens IS DISTINCT FROM TRUE;`
    )

    // 4. API keys table
    console.log('      - Ensuring table "api_keys"...')
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

    // 5. Indexes
    console.log('      - Ensuring indexes on "api_keys"...')
    await client.query(`CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);`)
    await client.query(`CREATE INDEX IF NOT EXISTS idx_api_keys_api_key ON api_keys(api_key);`)

    // 5b. System API keys table (Account-less Machine-to-Machine keys)
    console.log('      - Ensuring table "system_api_keys"...')
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
    await client.query(`CREATE INDEX IF NOT EXISTS idx_system_api_keys_api_key ON system_api_keys(api_key);`)

    // 6. Migrate legacy keys
    console.log('      - Migrating legacy user api_keys...')
    const legacyMigrationRes = await client.query(`
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
    if (legacyMigrationRes.rowCount > 0) {
      console.log(`        Migrated ${legacyMigrationRes.rowCount} legacy key(s).`)
    }

    // 7. Seed master admin
    console.log('      - Checking Master Admin account...')
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
        );
      `)
      console.log('        Master Admin seeded successfully.')
    } else {
      console.log('        Master Admin already exists.')
    }

    console.log('\n[4/5] Verifying database integrity...')
    const usersCountRes = await client.query(`SELECT COUNT(*)::int AS count FROM users;`)
    const keysCountRes = await client.query(`SELECT COUNT(*)::int AS count FROM api_keys;`)

    console.log(`      Total Users in DB:    ${usersCountRes.rows[0].count}`)
    console.log(`      Total API Keys in DB: ${keysCountRes.rows[0].count}`)

    console.log('\n[5/5] Migration completed successfully! \u2705\n')
  } catch (err) {
    console.error('\n[MIGRATION ERROR] \u274c Failed to run database migration:')
    console.error(err.message)
    if (err.code === 'ECONNREFUSED') {
      console.error('\nTip: The database host refused the connection.')
      console.error('If you are testing against Railway PostgreSQL, use the public connection string:')
      console.error('  npm run db:migrate -- --url="postgresql://..."')
      console.error('Or set DATABASE_URL in your environment or .env.local.\n')
    }
    process.exit(1)
  } finally {
    if (client) client.release()
    await pool.end()
  }
}

runMigration()
