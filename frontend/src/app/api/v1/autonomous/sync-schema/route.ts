import { NextRequest, NextResponse } from 'next/server'
import { authenticateApiKey, authenticateDeveloperSession, apiError } from '@/lib/developerAuth'
import { ensureDb, pool } from '@/lib/db'
import { v4 as uuid } from 'uuid'

export const dynamic = 'force-dynamic'

/**
 * POST /api/v1/autonomous/sync-schema
 * Registers or updates an external system schema (POS, Academic Portal, ERP)
 * so Copetra AI can comprehend its tables, endpoints, and workflows.
 */
export async function POST(req: NextRequest) {
  try {
    let userId = 'system'
    const keyAuth = await authenticateApiKey(req)
    if (keyAuth.ok) {
      userId = keyAuth.key.userId
    } else {
      const sessionAuth = await authenticateDeveloperSession(req)
      if (sessionAuth.ok) {
        userId = sessionAuth.userId
      } else {
        return keyAuth.response
      }
    }

    const body = await req.json().catch(() => ({}))
    const systemName = String(body.system_name || body.name || '').trim()
    const systemType = String(body.system_type || body.type || 'external_app').trim()
    const schemaDef = body.schema_definition || body.schema || {}
    const apiEndpoints = Array.isArray(body.api_endpoints) ? body.api_endpoints : []

    if (!systemName) {
      return apiError('Missing required field: "system_name".', 400, 'missing_system_name')
    }

    await ensureDb()
    const id = `sys-${uuid().slice(0, 12)}`

    await pool.query(
      `
      INSERT INTO connected_system_schemas (id, system_name, system_type, schema_definition, api_endpoints, user_id, updated_at)
      VALUES ($1, $2, $3, $4, $5, $6, NOW())
      ON CONFLICT (id) DO UPDATE SET
        schema_definition = EXCLUDED.schema_definition,
        api_endpoints = EXCLUDED.api_endpoints,
        updated_at = NOW();
    `,
      [id, systemName, systemType, JSON.stringify(schemaDef), JSON.stringify(apiEndpoints), userId]
    )

    return NextResponse.json({
      success: true,
      message: `System schema for '${systemName}' synchronized successfully. Copetra Autonomous Brain now understands this system.`,
      system_id: id,
    })
  } catch (err: any) {
    return apiError(err?.message || 'Failed to sync system schema', 500, 'internal_error', 'api_error')
  }
}

/**
 * GET /api/v1/autonomous/sync-schema
 * Returns all connected system schemas known to Copetra AI.
 */
export async function GET(req: NextRequest) {
  try {
    const keyAuth = await authenticateApiKey(req)
    if (!keyAuth.ok) {
      const sessionAuth = await authenticateDeveloperSession(req)
      if (!sessionAuth.ok) return keyAuth.response
    }

    await ensureDb()
    const res = await pool.query(
      `SELECT id, system_name, system_type, schema_definition, api_endpoints, created_at, updated_at
       FROM connected_system_schemas
       ORDER BY updated_at DESC
       LIMIT 50`
    )

    return NextResponse.json({
      success: true,
      systems: res.rows,
    })
  } catch (err: any) {
    return apiError(err?.message || 'Failed to list system schemas', 500, 'internal_error', 'api_error')
  }
}
