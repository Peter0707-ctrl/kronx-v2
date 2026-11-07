import { NextRequest, NextResponse } from 'next/server'
import {
  authenticateApiKey,
  authenticateDeveloperSession,
  apiError,
  checkPerKeyRateLimit,
} from '@/lib/developerAuth'
import {
  auditEndpointSecurity,
  auditInternalPlatformPosture,
  auditSourceCodeSecurity,
} from '@/lib/securityAuditor'

export const dynamic = 'force-dynamic'

/**
 * POST /api/v1/security/audit
 * Performs non-destructive defensive penetration auditing:
 * - targetUrl: Inspects HTTP security headers, TLS/HSTS, CSP, CORS, cookies, and server banners.
 * - code / query: Performs OWASP Top 10 & CWE static vulnerability analysis (SAST).
 * - internal: Audits Copetra's internal security posture and vault status.
 */
export async function POST(req: NextRequest) {
  try {
    let userId = 'anonymous'
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

    if (!checkPerKeyRateLimit(`sec_audit:${userId}`, 20)) {
      return apiError(
        'Security audit rate limit exceeded (max 20 audits per minute).',
        429,
        'rate_limit_exceeded'
      )
    }

    const body = await req.json().catch(() => ({}))
    const targetUrl = String(body.target_url || body.targetUrl || body.url || '').trim()
    const codeSnippet = String(body.code || body.codeSnippet || body.sql || body.query || '').trim()
    const label = String(body.label || 'target_source').trim()

    if (targetUrl) {
      const report = await auditEndpointSecurity(targetUrl)
      return NextResponse.json({ success: report.ok, report })
    }

    if (codeSnippet) {
      const report = auditSourceCodeSecurity(codeSnippet, label)
      return NextResponse.json({ success: report.ok, report })
    }

    const report = await auditInternalPlatformPosture()
    return NextResponse.json({ success: report.ok, report })
  } catch (err: any) {
    return apiError(err?.message || 'Security audit failed', 500, 'internal_error', 'api_error')
  }
}

/**
 * GET /api/v1/security/audit
 * Returns live internal platform security posture report.
 */
export async function GET(req: NextRequest) {
  try {
    const keyAuth = await authenticateApiKey(req)
    if (!keyAuth.ok) {
      const sessionAuth = await authenticateDeveloperSession(req)
      if (!sessionAuth.ok) return keyAuth.response
    }

    const report = await auditInternalPlatformPosture()
    return NextResponse.json({ success: true, report })
  } catch (err: any) {
    return apiError(err?.message || 'Security posture check failed', 500, 'internal_error', 'api_error')
  }
}
