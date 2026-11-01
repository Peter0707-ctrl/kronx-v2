#!/usr/bin/env node
/**
 * Kronx / Copetra System API Key & Secret Generator
 *
 * Generates cryptographically secure API Key and Secret pairs for machine-to-machine
 * systems and microservices without requiring user accounts.
 *
 * Usage:
 *   node scripts/generate-system-keys.js
 *   node scripts/generate-system-keys.js "Payment Service"
 *   node scripts/generate-system-keys.js "Billing Engine" --count=3
 *   node scripts/generate-system-keys.js "ERP System" --save-db
 *   npm run keys:generate
 */

const crypto = require('crypto')
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

function generateSystemCredentials(systemName) {
  const id = `sys_${crypto.randomUUID()}`
  const keyEntropy = crypto.randomBytes(20).toString('hex')
  const secretEntropy = crypto.randomBytes(32).toString('hex')

  const apiKey = `cpk_sys_${keyEntropy}`
  const apiSecret = `cps_sec_${secretEntropy}`
  const secretHash = crypto.createHash('sha256').update(apiSecret).digest('hex')
  const secretPrefix = apiSecret.slice(0, 12)

  return {
    id,
    systemName,
    apiKey,
    apiSecret,
    secretHash,
    secretPrefix,
    createdAt: new Date().toISOString()
  }
}

async function main() {
  const args = process.argv.slice(2)
  const isSaveDb = args.includes('--save-db')
  const countArg = args.find((a) => a.startsWith('--count='))
  const count = countArg ? parseInt(countArg.split('=')[1], 10) || 1 : 1

  const positionalArgs = args.filter((a) => !a.startsWith('--'))
  const baseSystemName = positionalArgs.length > 0 ? positionalArgs.join(' ') : 'External Service Integration'

  console.log('='.repeat(70))
  console.log('       KRONX SYSTEM API KEY & SECRET CREDENTIAL GENERATOR       ')
  console.log('='.repeat(70))
  console.log(`Generating ${count} credential set(s) for: "${baseSystemName}"\n`)

  const generatedList = []
  for (let i = 1; i <= count; i++) {
    const name = count > 1 ? `${baseSystemName} #${i}` : baseSystemName
    generatedList.push(generateSystemCredentials(name))
  }

  generatedList.forEach((cred, idx) => {
    console.log(`--- [CREDENTIAL #${idx + 1}: ${cred.systemName}] ---`)
    console.log(`System ID:      ${cred.id}`)
    console.log(`API Key:        ${cred.apiKey}`)
    console.log(`API Secret:     ${cred.apiSecret}`)
    console.log(`SHA-256 Hash:   ${cred.secretHash}`)
    console.log(`(Store the secret safely now. The server will only store its SHA-256 hash.)\n`)
  })

  console.log('='.repeat(70))
  console.log('                     .ENV INTEGRATION FORMAT                     ')
  console.log('='.repeat(70))
  generatedList.forEach((cred, idx) => {
    const slug = cred.systemName.toUpperCase().replace(/[^A-Z0-9]/g, '_')
    console.log(`# ${cred.systemName}`)
    console.log(`${slug}_API_KEY=${cred.apiKey}`)
    console.log(`${slug}_API_SECRET=${cred.apiSecret}\n`)
  })

  console.log('='.repeat(70))
  console.log('                     DIRECT SQL INSERT STATEMENTS                 ')
  console.log('='.repeat(70))
  generatedList.forEach((cred) => {
    console.log(`INSERT INTO system_api_keys (id, system_name, api_key, api_secret_hash, secret_prefix, permissions, is_active)`)
    console.log(`VALUES ('${cred.id}', '${cred.systemName.replace(/'/g, "''")}', '${cred.apiKey}', '${cred.secretHash}', '${cred.secretPrefix}', '["*"]'::jsonb, TRUE);\n`)
  })

  if (isSaveDb) {
    console.log('='.repeat(70))
    console.log('               SAVING DIRECTLY TO DATABASE (--save-db)           ')
    console.log('='.repeat(70))
    const rootDir = path.resolve(__dirname, '..')
    const envLocal = loadEnvFile(path.join(rootDir, '.env.local'))
    const envDefault = loadEnvFile(path.join(rootDir, '.env'))
    const connectionString =
      process.env.DATABASE_URL ||
      envLocal.DATABASE_URL ||
      envDefault.DATABASE_URL ||
      'postgresql://postgres:TdoGwPBGGbhiWgarnDevahuPxoehQspt@postgres.railway.internal:5432/railway'

    const pool = new Pool({ connectionString, connectionTimeoutMillis: 8000 })
    try {
      const client = await pool.connect()
      try {
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

        for (const cred of generatedList) {
          await client.query(
            `INSERT INTO system_api_keys (id, system_name, api_key, api_secret_hash, secret_prefix, permissions, is_active)
             VALUES ($1, $2, $3, $4, $5, $6, TRUE)
             ON CONFLICT (api_key) DO NOTHING`,
            [cred.id, cred.systemName, cred.apiKey, cred.secretHash, cred.secretPrefix, JSON.stringify(['*'])]
          )
          console.log(`[DB] Saved credential for "${cred.systemName}" (ID: ${cred.id})`)
        }
        console.log('All credentials successfully written to PostgreSQL system_api_keys table.')
      } finally {
        client.release()
      }
    } catch (err) {
      console.error('[DB ERROR] Could not save to database:', err.message)
      console.log('Note: You can still run the SQL INSERT statements above directly in your DB client or pgAdmin / Railway.')
    } finally {
      await pool.end().catch(() => {})
    }
  }

  console.log('='.repeat(70))
  console.log('                      HOW TO CALL FROM ANY SYSTEM                 ')
  console.log('='.repeat(70))
  const sample = generatedList[0]
  console.log(`
Option 1: Using Headers (Recommended for Microservices & Webhooks)
curl -X POST https://your-domain.com/api/gateway \\
  -H "Content-Type: application/json" \\
  -H "x-api-key: ${sample.apiKey}" \\
  -H "x-api-secret: ${sample.apiSecret}" \\
  -d '{"messages": [{"role": "user", "content": "Hello Kronx"}]}'

Option 2: Using HTTP Basic Auth
curl -X POST https://your-domain.com/api/gateway \\
  -u "${sample.apiKey}:${sample.apiSecret}" \\
  -H "Content-Type: application/json" \\
  -d '{"messages": [{"role": "user", "content": "Hello Kronx"}]}'

Option 3: Using Bearer Token (API Key only)
curl -X POST https://your-domain.com/api/gateway \\
  -H "Authorization: Bearer ${sample.apiKey}" \\
  -H "Content-Type: application/json" \\
  -d '{"messages": [{"role": "user", "content": "Hello Kronx"}]}'
`)
}

main().catch(console.error)
