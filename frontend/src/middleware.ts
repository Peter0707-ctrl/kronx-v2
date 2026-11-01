import { NextRequest, NextResponse } from 'next/server'

/**
 * Copetra AI Edge Web Application Firewall (WAF), Rate Limiter & Security Headers Middleware
 */

const BLOCKED_SCANNER_PATTERNS = [
  /\.env(\..+)?$/i,
  /\.git(\/.*)?$/i,
  /\.aws(\/.*)?$/i,
  /\.ssh(\/.*)?$/i,
  /\.vscode(\/.*)?$/i,
  /\.idea(\/.*)?$/i,
  /\.php(\/.*)?$/i,
  /\.js\.map$/i,
  /\.css\.map$/i,
  /\/wp-admin/i,
  /\/wp-login/i,
  /\/wp-content/i,
  /\/wp-includes/i,
  /\/xmlrpc\.php/i,
  /\/phpmyadmin/i,
  /\/pma/i,
  /\/adminer/i,
  /\/cgi-bin/i,
  /\/actuator/i,
  /\/eval-stdin/i,
  /\/vendor\/phpunit/i,
  /\/\.ds_store/i,
  /\/server-status/i,
  /\/config\.json$/i,
]

const ALLOWED_METHODS = new Set(['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])

const PUBLIC_DEVELOPER_API_PREFIXES = [
  '/api/v1/',
  '/api/gateway',
  '/api/images',
  '/api/health',
]

// In-memory sliding window rate limiter per Edge isolate
const rateLimitStore = new Map<string, { count: number; windowStart: number }>()
const WINDOW_MS = 60_000

function checkRateLimit(key: string, maxRequests: number): boolean {
  const now = Date.now()
  if (rateLimitStore.size > 5000) {
    rateLimitStore.forEach((v, k) => {
      if (now - v.windowStart > WINDOW_MS) rateLimitStore.delete(k)
    })
  }
  const entry = rateLimitStore.get(key)
  if (!entry || now - entry.windowStart > WINDOW_MS) {
    rateLimitStore.set(key, { count: 1, windowStart: now })
    return true
  }
  entry.count += 1
  return entry.count <= maxRequests
}

function getClientIp(req: NextRequest): string {
  const xff = req.headers.get('x-forwarded-for')
  if (xff) return xff.split(',')[0].trim()
  return req.headers.get('x-real-ip') || '127.0.0.1'
}

function isTrustedInternalOrigin(origin: string, host: string): boolean {
  try {
    const parsed = new URL(origin)
    const originHost = parsed.host.toLowerCase()
    const currentHost = host.toLowerCase()
    if (originHost === currentHost) return true
    if (
      originHost.startsWith('localhost:') ||
      originHost.startsWith('127.0.0.1:') ||
      originHost === 'localhost' ||
      originHost === '127.0.0.1'
    ) {
      return true
    }
    if (originHost.endsWith('.up.railway.app') || originHost.endsWith('copetra.ai')) {
      return true
    }
    return false
  } catch {
    return false
  }
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const method = request.method.toUpperCase()

  // 1. Enforce allowed HTTP verbs
  if (!ALLOWED_METHODS.has(method)) {
    return new NextResponse('Method Not Allowed', { status: 405 })
  }

  // 2. Block Path Traversal & Null-Byte Injection
  const rawUrl = request.url
  if (
    rawUrl.includes('..') ||
    rawUrl.includes('%2e%2e') ||
    rawUrl.includes('%2E%2E') ||
    rawUrl.includes('%00')
  ) {
    return new NextResponse('Forbidden: Malicious Path Traversal Blocked', { status: 403 })
  }

  // 3. Block Vulnerability Scanners, Source Map Probes (.js.map), and PHP/WP/Env Probes
  for (const pattern of BLOCKED_SCANNER_PATTERNS) {
    if (pattern.test(pathname)) {
      return new NextResponse('Forbidden: Access Denied', { status: 403 })
    }
  }

  // 4. API Protection: Rate Limiting & Origin Verification
  if (pathname.startsWith('/api/')) {
    const ip = getClientIp(request)
    const isSensitiveRoute =
      pathname.startsWith('/api/security/') ||
      pathname.startsWith('/api/users') ||
      pathname.startsWith('/api/test') ||
      pathname.startsWith('/api/developer/keys')

    const limit = isSensitiveRoute ? 30 : 90
    const bucketKey = `${ip}:${isSensitiveRoute ? 'sensitive' : 'api'}`

    if (!checkRateLimit(bucketKey, limit)) {
      return NextResponse.json(
        { error: 'Too Many Requests: Rate limit exceeded. Please wait 60 seconds.' },
        {
          status: 429,
          headers: { 'Retry-After': '60' },
        }
      )
    }

    const isPublicDeveloperRoute = PUBLIC_DEVELOPER_API_PREFIXES.some((prefix) =>
      pathname === prefix || pathname.startsWith(prefix)
    )

    const origin = request.headers.get('origin')
    const host = request.headers.get('host') || ''

    if (!isPublicDeveloperRoute && origin && !isTrustedInternalOrigin(origin, host)) {
      return NextResponse.json(
        { error: 'Forbidden: Untrusted Cross-Origin Request' },
        { status: 403 }
      )
    }

    if (method === 'OPTIONS') {
      const preflight = new NextResponse(null, { status: 204 })
      if (isPublicDeveloperRoute) {
        preflight.headers.set('Access-Control-Allow-Origin', origin || '*')
      } else if (origin && isTrustedInternalOrigin(origin, host)) {
        preflight.headers.set('Access-Control-Allow-Origin', origin)
      }
      preflight.headers.set('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
      preflight.headers.set(
        'Access-Control-Allow-Headers',
        'Content-Type, Authorization, x-api-key, X-Api-Key, x-user-id, x-user-email, x-admin-key'
      )
      preflight.headers.set('Access-Control-Max-Age', '86400')
      return preflight
    }
  }

  const response = NextResponse.next()

  // 5. Inject Hardened Security Headers on Every Response
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')
  response.headers.set('X-XSS-Protection', '1; mode=block')
  response.headers.set('X-Permitted-Cross-Domain-Policies', 'none')
  response.headers.set('X-DNS-Prefetch-Control', 'off')
  response.headers.set('Cross-Origin-Opener-Policy', 'same-origin')
  response.headers.set(
    'Permissions-Policy',
    'camera=(self), microphone=(self), geolocation=(self), payment=(), usb=(), browsing-topics=()'
  )

  return response
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|icons/|sw.js).*)'],
}
