import withPWAInit from 'next-pwa'

const withPWA = withPWAInit({
  dest: 'public',
  disable: process.env.NODE_ENV === 'development',
  register: true,
  skipWaiting: true,
  reloadOnOnline: true,
  cacheOnFrontEndNav: false,
})

const cspDirective = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com",
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "font-src 'self' data: https://fonts.gstatic.com",
  "img-src 'self' data: blob: https:",
  "media-src 'self' data: blob:",
  "connect-src 'self' https: wss:",
  "worker-src 'self' blob:",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
  "upgrade-insecure-requests",
].join('; ')

const securityHeaders = [
  // 1. Content Security Policy (CSP): Mitigate XSS, clickjacking, and unauthorized script injection
  {
    key: 'Content-Security-Policy',
    value: cspDirective,
  },
  // 2. Man-in-the-Middle (MITM) Protection: Enforce strict HTTPS encryption & preload HSTS
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=63072000; includeSubDomains; preload',
  },
  // 3. Clickjacking Protection: Prevent site from being embedded in unauthorized malicious iframes
  {
    key: 'X-Frame-Options',
    value: 'DENY',
  },
  // 4. MIME-Sniffing Protection: Force browsers to strictly adhere to declared content types
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff',
  },
  // 5. Cross-Site Scripting (XSS) Protection
  {
    key: 'X-XSS-Protection',
    value: '1; mode=block',
  },
  // 6. Referrer Privacy Policy: Prevent leaking sensitive tokens in HTTP referrer headers
  {
    key: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin',
  },
  // 7. Device Security & Permissions Policy
  {
    key: 'Permissions-Policy',
    value: 'camera=(self), microphone=(self), geolocation=(self), payment=(), usb=(), browsing-topics=()',
  },
  // 8. Cross-Origin Isolation & Cross-Domain Policy Lockdown
  {
    key: 'Cross-Origin-Opener-Policy',
    value: 'same-origin',
  },
  {
    key: 'X-Permitted-Cross-Domain-Policies',
    value: 'none',
  },
  {
    key: 'X-DNS-Prefetch-Control',
    value: 'off',
  },
]

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Prevent server fingerprinting (never send X-Powered-By: Next.js)
  poweredByHeader: false,
  // Never emit browser source maps (.js.map) in production so core algorithms cannot be reverse-engineered
  productionBrowserSourceMaps: false,
  // Disable built-in image optimizer server to eliminate remote image DoS and SSRF vectors
  images: {
    unoptimized: true,
  },
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production' ? { exclude: ['error'] } : false,
  },
  webpack: (config, { dev }) => {
    config.resolve.alias.canvas = false
    if (!dev) {
      config.devtool = false
    }
    return config
  },
  async headers() {
    return [
      {
        source: '/sw.js',
        headers: [
          ...securityHeaders,
          { key: 'Cache-Control', value: 'no-cache, no-store, must-revalidate' },
          { key: 'Pragma', value: 'no-cache' },
          { key: 'Expires', value: '0' },
          { key: 'Content-Type', value: 'application/javascript; charset=utf-8' },
        ],
      },
      {
        source: '/api/v1/:path*',
        headers: [
          ...securityHeaders,
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET, POST, OPTIONS' },
          { key: 'Access-Control-Allow-Headers', value: 'Content-Type, Authorization, x-api-key, X-Api-Key' },
          { key: 'Cache-Control', value: 'no-store, max-age=0' },
        ],
      },
      {
        source: '/api/gateway',
        headers: [
          ...securityHeaders,
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'POST, OPTIONS' },
          { key: 'Access-Control-Allow-Headers', value: 'Content-Type, Authorization, x-api-key, X-Api-Key' },
          { key: 'Cache-Control', value: 'no-store, max-age=0' },
        ],
      },
      {
        source: '/api/:path*',
        headers: [
          ...securityHeaders,
          { key: 'Cache-Control', value: 'no-store, max-age=0' },
        ],
      },
      {
        source: '/:path*',
        headers: [
          ...securityHeaders,
          { key: 'Cache-Control', value: 'no-cache, no-store, must-revalidate' },
          { key: 'Pragma', value: 'no-cache' },
          { key: 'Expires', value: '0' },
        ],
      },
    ]
  },
}

export default withPWA(nextConfig)
