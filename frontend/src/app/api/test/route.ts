import { NextRequest, NextResponse } from 'next/server'
import { getVaultAuditStatus, verifyAdminAuthorization } from '@/lib/secretVault'

export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  const adminKey = req.headers.get('x-admin-key')
  if (!verifyAdminAuthorization(adminKey)) {
    return NextResponse.json(
      { error: 'Forbidden: Diagnostic endpoint requires administrator authentication.' },
      { status: 403 }
    )
  }

  const vaultStatus = getVaultAuditStatus()
  return NextResponse.json({
    timestamp: new Date().toISOString(),
    status: 'operational',
    security_mode: 'zero-knowledge-vault',
    providers_ready: vaultStatus.providersConfigured,
  })
}
