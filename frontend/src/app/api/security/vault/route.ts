import { NextRequest, NextResponse } from 'next/server'
import {
  encryptSecretEnvelope,
  getVaultAuditStatus,
  revokeRuntimeSecret,
  setRuntimeSecret,
  verifyAdminAuthorization,
} from '@/lib/secretVault'

export const dynamic = 'force-dynamic'

/**
 * Zero-Knowledge Runtime Vault Endpoint
 * Allows the Master Administrator to inspect vault status (never raw secrets),
 * inject encrypted or volatile secrets directly into Node.js RAM without storing
 * them in the hosting provider's dashboard, or emergency-revoke runtime secrets.
 */
export async function GET(req: NextRequest) {
  const adminKey = req.headers.get('x-admin-key')
  if (!verifyAdminAuthorization(adminKey)) {
    return NextResponse.json(
      { error: 'Forbidden: Valid administrator authorization required.' },
      { status: 403 }
    )
  }

  return NextResponse.json({
    status: 'secured',
    encryption: 'AES-256-GCM + HKDF-SHA256',
    vault: getVaultAuditStatus(),
    timestamp: new Date().toISOString(),
  })
}

export async function POST(req: NextRequest) {
  const adminKey = req.headers.get('x-admin-key')
  if (!verifyAdminAuthorization(adminKey)) {
    return NextResponse.json(
      { error: 'Forbidden: Valid administrator authorization required.' },
      { status: 403 }
    )
  }

  try {
    const body = await req.json().catch(() => ({}))
    const action = String(body.action || 'inject')

    // Action 1: Encrypt a plaintext secret into an ENC:v1:... envelope without storing
    if (action === 'encrypt') {
      const secret = String(body.secret || '').trim()
      const passphrase = String(body.passphrase || '').trim() || undefined
      if (!secret) {
        return NextResponse.json({ error: 'secret is required' }, { status: 400 })
      }
      const envelope = encryptSecretEnvelope(secret, passphrase)
      return NextResponse.json({
        success: true,
        envelope,
        note: 'Store this ENC:v1:... envelope in your environment variables; raw key is never persisted.',
      })
    }

    // Action 2: Inject secrets directly into volatile Node.js process RAM
    const secrets = body.secrets
    if (!secrets || typeof secrets !== 'object') {
      return NextResponse.json(
        { error: 'Provide a "secrets" object mapping secret names to values.' },
        { status: 400 }
      )
    }

    let injectedCount = 0
    for (const [k, v] of Object.entries(secrets)) {
      if (typeof v === 'string' && v.trim()) {
        setRuntimeSecret(k, v)
        injectedCount++
      }
    }

    return NextResponse.json({
      success: true,
      injectedCount,
      vault: getVaultAuditStatus(),
    })
  } catch (err: any) {
    return NextResponse.json(
      { error: err?.message || 'Vault operation failed' },
      { status: 400 }
    )
  }
}

export async function DELETE(req: NextRequest) {
  const adminKey = req.headers.get('x-admin-key')
  if (!verifyAdminAuthorization(adminKey)) {
    return NextResponse.json(
      { error: 'Forbidden: Valid administrator authorization required.' },
      { status: 403 }
    )
  }

  const body = await req.json().catch(() => ({}))
  const keyName = typeof body.name === 'string' ? body.name.trim() : undefined

  revokeRuntimeSecret(keyName)
  return NextResponse.json({
    success: true,
    revoked: keyName || 'ALL_VOLATILE_RAM_SECRETS',
    vault: getVaultAuditStatus(),
  })
}
