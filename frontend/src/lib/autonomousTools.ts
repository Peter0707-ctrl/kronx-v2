import { ensureDb, pool } from './db'
import { resolveSecret, validateSafeOutboundUrl } from './secretVault'
import { v4 as uuid } from 'uuid'

/**
 * Sensitive column blacklist - never exposed via autonomous schema introspection or queries
 */
const SENSITIVE_COLUMNS = [
  'password_hash',
  'api_secret_hash',
  'secret_vault',
  'encrypted_envelope',
  'admin_master_hash',
]

const RESTRICTED_TABLES = [
  'secret_vault',
]

/**
 * 1. Introspect Database Schema and Connected System Schemas
 * Gives Copetra AI a comprehensive understanding of the whole system safely.
 */
export async function introspectDatabaseSchema(): Promise<{
  ok: boolean
  tables: Record<string, Array<{ column: string; type: string }>>
  connectedSystems: Array<{ id: string; systemName: string; systemType: string; schema: any }>
}> {
  try {
    await ensureDb()

    const colsRes = await pool.query(`
      SELECT table_name, column_name, data_type
      FROM information_schema.columns
      WHERE table_schema = 'public'
      ORDER BY table_name, ordinal_position;
    `)

    const tables: Record<string, Array<{ column: string; type: string }>> = {}
    for (const r of colsRes.rows) {
      const tbl = r.table_name
      const col = r.column_name
      if (RESTRICTED_TABLES.includes(tbl) || SENSITIVE_COLUMNS.includes(col)) {
        continue
      }
      if (!tables[tbl]) tables[tbl] = []
      tables[tbl].push({ column: col, type: r.data_type })
    }

    const connectedRes = await pool.query(`
      SELECT id, system_name, system_type, schema_definition
      FROM connected_system_schemas
      ORDER BY created_at DESC
      LIMIT 20;
    `)

    const connectedSystems = connectedRes.rows.map((r) => ({
      id: r.id,
      systemName: r.system_name,
      systemType: r.system_type,
      schema: r.schema_definition,
    }))

    return { ok: true, tables, connectedSystems }
  } catch (err: any) {
    return { ok: false, tables: {}, connectedSystems: [] }
  }
}

/**
 * 2. Safe Read-Only SQL Query Runner
 * Executes SELECT queries inside an isolated READ ONLY transaction with strict statement timeout.
 */
export async function runSafeReadonlySql(rawSql: string): Promise<{
  ok: boolean
  rows?: any[]
  rowCount?: number
  error?: string
}> {
  if (!rawSql || typeof rawSql !== 'string') {
    return { ok: false, error: 'SQL query must be a non-empty string.' }
  }

  const trimmed = rawSql.trim()
  const lower = trimmed.toLowerCase()

  // Strict whitelist: Only SELECT or WITH (common table expressions) allowed
  if (!lower.startsWith('select') && !lower.startsWith('with')) {
    return {
      ok: false,
      error: 'Security Policy Violation: Only read-only SELECT or WITH statements are allowed.',
    }
  }

  // Dangerous keywords check
  const dangerousKeywords = [
    'insert',
    'update',
    'delete',
    'drop',
    'alter',
    'truncate',
    'create',
    'grant',
    'revoke',
    'vacuum',
    'copy',
    'execute',
    'pg_sleep',
    'shutdown',
  ]

  for (const kw of dangerousKeywords) {
    const rx = new RegExp(`\\b${kw}\\b`, 'i')
    if (rx.test(lower)) {
      return {
        ok: false,
        error: `Security Policy Violation: Keyword '${kw.toUpperCase()}' is forbidden in autonomous queries.`,
      }
    }
  }

  // Table & Column blacklists
  for (const tbl of RESTRICTED_TABLES) {
    if (new RegExp(`\\b${tbl}\\b`, 'i').test(lower)) {
      return {
        ok: false,
        error: `Security Policy Violation: Table '${tbl}' cannot be accessed.`,
      }
    }
  }

  for (const col of SENSITIVE_COLUMNS) {
    if (new RegExp(`\\b${col}\\b`, 'i').test(lower)) {
      return {
        ok: false,
        error: `Security Policy Violation: Column '${col}' is protected and cannot be selected.`,
      }
    }
  }

  await ensureDb()
  const client = await pool.connect()

  try {
    await client.query('BEGIN READ ONLY')
    await client.query('SET LOCAL statement_timeout = 3000')

    // Append limit if not already limited
    let queryToRun = trimmed
    if (!lower.includes('limit')) {
      queryToRun = `${queryToRun} LIMIT 100`
    }

    const res = await client.query(queryToRun)
    await client.query('COMMIT')

    // Scrub any accidental sensitive values before returning
    const safeRows = res.rows.map((row) => {
      const sanitized: Record<string, any> = {}
      for (const [k, v] of Object.entries(row)) {
        if (SENSITIVE_COLUMNS.includes(k.toLowerCase())) continue
        sanitized[k] = v
      }
      return sanitized
    })

    return { ok: true, rows: safeRows, rowCount: res.rowCount || 0 }
  } catch (err: any) {
    await client.query('ROLLBACK').catch(() => {})
    return { ok: false, error: err.message || 'SQL execution failed.' }
  } finally {
    client.release()
  }
}

/**
 * 3. Search and Read Live Internet Content
 * Grants Copetra AI live internet capability with SSRF isolation.
 */
export async function searchAndReadInternet(query: string): Promise<{
  ok: boolean
  query: string
  results: Array<{ title: string; snippet: string; url: string }>
  error?: string
}> {
  if (!query || typeof query !== 'string') {
    return { ok: false, query: '', results: [], error: 'Search query is required.' }
  }

  try {
    const cleanQuery = encodeURIComponent(query.trim())
    const ddgUrl = `https://api.duckduckgo.com/?q=${cleanQuery}&format=json&no_html=1&skip_disambig=1`

    const res = await fetch(ddgUrl, {
      headers: { 'User-Agent': 'CopetraAutonomousAI/2026.11' },
      signal: AbortSignal.timeout(6000),
    })

    if (!res.ok) {
      return { ok: false, query, results: [], error: `Search provider returned status ${res.status}` }
    }

    const data = await res.json()
    const results: Array<{ title: string; snippet: string; url: string }> = []

    if (data.AbstractText) {
      results.push({
        title: data.Heading || query,
        snippet: data.AbstractText,
        url: data.AbstractURL || '',
      })
    }

    if (Array.isArray(data.RelatedTopics)) {
      for (const t of data.RelatedTopics.slice(0, 5)) {
        if (t.Text && t.FirstURL) {
          results.push({
            title: t.Text.slice(0, 60),
            snippet: t.Text,
            url: t.FirstURL,
          })
        }
      }
    }

    return { ok: true, query, results }
  } catch (err: any) {
    return { ok: false, query, results: [], error: err.message || 'Web search failed.' }
  }
}

/**
 * 4. Learn and Save Synthesized Skill
 * Automatically records procedural skills, workflow templates, or business formulas.
 */
export async function learnAndSaveSkill(opts: {
  skillName: string
  description: string
  triggerPattern: string
  executionLogic: string
}): Promise<{ ok: boolean; skillId?: string; error?: string }> {
  try {
    await ensureDb()
    const id = `skill-${uuid().slice(0, 12)}`

    await pool.query(
      `
      INSERT INTO autonomous_skills (id, skill_name, description, trigger_pattern, execution_logic, success_count)
      VALUES ($1, $2, $3, $4, $5, 1)
      ON CONFLICT (skill_name) DO UPDATE SET
        description = EXCLUDED.description,
        trigger_pattern = EXCLUDED.trigger_pattern,
        execution_logic = EXCLUDED.execution_logic,
        success_count = autonomous_skills.success_count + 1;
    `,
      [id, opts.skillName.trim(), opts.description.trim(), opts.triggerPattern.trim(), opts.executionLogic.trim()]
    )

    return { ok: true, skillId: id }
  } catch (err: any) {
    return { ok: false, error: err.message || 'Failed to save skill.' }
  }
}

/**
 * 5. Call External Connected System API (POS, Academic Portal, ERP)
 * Securely calls external APIs using registered credentials and SSRF checks.
 */
export async function callConnectedSystemApi(opts: {
  endpointUrl: string
  method?: 'GET' | 'POST' | 'PUT'
  payload?: any
  headers?: Record<string, string>
}): Promise<{ ok: boolean; status?: number; data?: any; error?: string }> {
  const urlCheck = validateSafeOutboundUrl(opts.endpointUrl)
  if (!urlCheck.ok) {
    return { ok: false, error: `SSRF Policy Blocked: ${urlCheck.reason}` }
  }

  try {
    const method = opts.method || 'POST'
    const res = await fetch(urlCheck.url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'CopetraConnectedGateway/2026.11',
        ...(opts.headers || {}),
      },
      body: method !== 'GET' ? JSON.stringify(opts.payload || {}) : undefined,
      signal: AbortSignal.timeout(8000),
    })

    const text = await res.text()
    let data: any
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }

    return { ok: res.ok, status: res.status, data }
  } catch (err: any) {
    return { ok: false, error: err.message || 'System call failed.' }
  }
}

/**
 * 6. Autonomous Self-Defense: Auto-Quarantine Threat and Revoke Keys
 * Immediately shields system from repeated attack attempts.
 */
export async function securitySelfDefense(opts: {
  targetType: 'ip' | 'api_key' | 'user_email'
  targetValue: string
  reason: string
}): Promise<{ ok: boolean; quarantined: boolean }> {
  try {
    await ensureDb()
    const id = `quar-${uuid().slice(0, 12)}`

    await pool.query(
      `
      INSERT INTO security_quarantine (id, target_type, target_value, reason, threat_score, quarantined_until)
      VALUES ($1, $2, $3, $4, 1, NOW() + INTERVAL '24 hours')
    `,
      [id, opts.targetType, opts.targetValue, opts.reason]
    )

    if (opts.targetType === 'api_key') {
      await pool.query(`UPDATE api_keys SET is_active = FALSE WHERE api_key = $1`, [opts.targetValue])
      await pool.query(`UPDATE system_api_keys SET is_active = FALSE WHERE api_key = $1`, [opts.targetValue])
    }

    return { ok: true, quarantined: true }
  } catch (err) {
    return { ok: false, quarantined: false }
  }
}
