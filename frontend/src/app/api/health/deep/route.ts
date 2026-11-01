import { NextRequest, NextResponse } from 'next/server'
import { verifyAdminAuthorization } from '@/lib/secretVault'

export const dynamic = 'force-dynamic'

/** Protected diagnostic probe. Never exposes internal hostnames or environment variables publicly. */
export async function GET(req: NextRequest) {
  const adminKey = req.headers.get('x-admin-key')
  if (!verifyAdminAuthorization(adminKey)) {
    return NextResponse.json(
      { ok: true, service: 'copetra-core', status: 'healthy', timestamp: new Date().toISOString() },
      { status: 200 }
    )
  }

  return NextResponse.json(
    {
      ok: true,
      service: 'copetra-core',
      status: 'healthy',
      inference_cluster: 'isolated',
      timestamp: new Date().toISOString(),
    },
    { status: 200 }
  )
}
