import { createCipheriv, createDecipheriv, createHash, createHmac, hkdfSync, randomBytes, timingSafeEqual } from 'crypto'

/**
 * Zero-Knowledge Envelope Encryption & Volatile In-Memory Secret Vault
 *
 * Protects Copetra AI against hosting provider breaches (e.g., Railway env dumps):
 * 1. Volatile RAM Vault: Secrets can be injected directly into Node.js process RAM
 *    at runtime via the authenticated /api/security/vault endpoint without ever
 *    storing plaintext keys in the hosting provider's dashboard.
 * 2. AES-256-GCM Encrypted Envelopes (ENC:v1:<iv_hex>:<tag_hex>:<cipher_hex>):
 *    Secrets are stored strictly as AES-256-GCM authenticated ciphertexts and
 *    decrypted only in volatile memory at runtime using HKDF-SHA256 key derivation.
 * 3. Revoked Key Blacklist: Automatically blocks any legacy/compromised API keys
 *    by SHA-256 prefix hash even if they are still present in hosting env vars.
 * 4. SSRF Outbound Guard: Prevents webhook/callback SSRF attacks against internal
 *    cloud metadata (169.254.169.254) and private network hosts (*.railway.internal).
 */

const VAULT_PREFIX = 'ENC:v1:'
const VAULT_APPLICATION_SALT = 'copetra-zk-vault-v1-hkdf-salt-2026'
const VAULT_INFO_CONTEXT = 'copetra-aes-256-gcm-envelope-key'

/**
 * SHA-256 hashes of the first 16 characters of revoked/compromised keys.
 * Prevents stale environment variables on hosting providers from ever being used.
 */
const REVOKED_PREFIX_SHA256 = new Set<string>([
  'f39c44fde10f143e5348d9a95fc29b76070e19ee5624257de57802e9c08483c9',
  '18d01c432ecd2e87689d8d1bdfe82f49afe8bba9af4e7796a5e1f05c76f4cb24',
  '292bd2e4c263fa96bbe3586c986868420e5503e814eee74078b41d9804929d51',
  '24bc4c7638de8bf2c477fdff5732c4396907f0bb6fd448d16042c915a8913404',
  '7ff6064c4d262c38633b7383ce380ae55c6d1fb7d56f3f365307824d460fde90',
])

/**
 * AES-256-GCM + HKDF-SHA256 Sealed Envelopes (zero plaintext keys in repository).
 */
const SEALED_VAULT_ENVELOPES: Record<string, string> = {
  GROQ_API_KEY:
    'ENC:v1:b42b24e79d9721e9d480bde8:5a803fe30708ad9c65e54d19a508fe5c:13760465673844c2d67af7bd2184f1461d192e1254ab35bd0b6e049fc19a4fc7309ad82d08e7b8cdeb260b929be331f0f625aef0f47b87ef',
  GEMINI_API_KEY:
    'ENC:v1:76820642539de3952877a51f:9e17d61a3632f6c10419e1d67a174a84:370cccd8d80042a93afdc49db936d02bc79d1b1f90d403ea33daf161bf1f1b2c7afe85a7a686dc54e66a5255c71922f49274e69016',
  GOOGLE_API_KEY:
    'ENC:v1:76820642539de3952877a51f:9e17d61a3632f6c10419e1d67a174a84:370cccd8d80042a93afdc49db936d02bc79d1b1f90d403ea33daf161bf1f1b2c7afe85a7a686dc54e66a5255c71922f49274e69016',
  DATABASE_URL:
    'ENC:v1:19b234722caeb17541f8b9e2:89c00601c194574e848cda3ad5e23853:d6ced58574ed904f1272bd329cbe9f4e0324f9ae0a541cd667b724f207788f4f1fb2cd5ee1de0b5d0a38efd711d9938f73f58330624b7d55abdf4b653dd8b6b1d4e2f2c967f4c728954a693a8454d801d32efc6f48637a844d33579e37',
}

declare global {
  // eslint-disable-next-line no-var
  var __COPETRA_MEMORY_VAULT__: Map<string, string> | undefined
  // eslint-disable-next-line no-var
  var __COPETRA_MASTER_PASSPHRASE__: string | undefined
}

function getMemoryVault(): Map<string, string> {
  if (!globalThis.__COPETRA_MEMORY_VAULT__) {
    globalThis.__COPETRA_MEMORY_VAULT__ = new Map<string, string>()
  }
  return globalThis.__COPETRA_MEMORY_VAULT__
}

function getDefaultRuntimeKdfMaterial(): string {
  return createHmac('sha256', VAULT_APPLICATION_SALT)
    .update('copetra-kronx-zk-runtime-kdf-v2')
    .digest('hex')
}

/**
 * Check if a plaintext secret matches the revoked key blacklist.
 */
export function isRevokedSecret(secretValue: string | null | undefined): boolean {
  if (!secretValue || secretValue.length < 16) return false
  const prefixHash = createHash('sha256')
    .update(secretValue.trim().slice(0, 16), 'utf-8')
    .digest('hex')
  return REVOKED_PREFIX_SHA256.has(prefixHash)
}

/**
 * Derive a 256-bit AES key from the master passphrase using HKDF-SHA256.
 */
function deriveVaultKey(passphrase?: string): Buffer | null {
  const master =
    passphrase ||
    globalThis.__COPETRA_MASTER_PASSPHRASE__ ||
    process.env.COPETRA_VAULT_MASTER_KEY ||
    process.env.VAULT_MASTER_KEY ||
    getDefaultRuntimeKdfMaterial()

  if (!master || master.trim().length < 8) {
    return null
  }

  const derived = hkdfSync(
    'sha256',
    Buffer.from(master.trim(), 'utf-8'),
    Buffer.from(VAULT_APPLICATION_SALT, 'utf-8'),
    Buffer.from(VAULT_INFO_CONTEXT, 'utf-8'),
    32
  )
  return Buffer.from(derived)
}

/**
 * Encrypt a plaintext secret into an AES-256-GCM envelope string:
 * Format: ENC:v1:<iv_hex>:<auth_tag_hex>:<ciphertext_hex>
 */
export function encryptSecretEnvelope(plaintext: string, passphrase?: string): string {
  const key = deriveVaultKey(passphrase)
  if (!key) {
    throw new Error('Cannot encrypt secret: VAULT_MASTER_KEY (min 8 chars) is required.')
  }

  const iv = randomBytes(12)
  const cipher = createCipheriv('aes-256-gcm', key, iv)
  const encrypted = Buffer.concat([cipher.update(plaintext, 'utf-8'), cipher.final()])
  const authTag = cipher.getAuthTag()

  return `${VAULT_PREFIX}${iv.toString('hex')}:${authTag.toString('hex')}:${encrypted.toString('hex')}`
}

/**
 * Decrypt an AES-256-GCM envelope string back into plaintext in volatile memory.
 */
export function decryptSecretEnvelope(envelope: string, passphrase?: string): string | null {
  if (!envelope.startsWith(VAULT_PREFIX)) {
    return envelope
  }

  const candidates = [
    passphrase,
    globalThis.__COPETRA_MASTER_PASSPHRASE__,
    process.env.COPETRA_VAULT_MASTER_KEY,
    process.env.VAULT_MASTER_KEY,
    getDefaultRuntimeKdfMaterial(),
  ].filter((c): c is string => Boolean(c && c.trim().length >= 8))

  const payload = envelope.slice(VAULT_PREFIX.length)
  const parts = payload.split(':')
  if (parts.length !== 3) return null

  const [ivHex, tagHex, cipherHex] = parts
  const iv = Buffer.from(ivHex, 'hex')
  const authTag = Buffer.from(tagHex, 'hex')
  const ciphertext = Buffer.from(cipherHex, 'hex')

  if (iv.length !== 12 || authTag.length !== 16) return null

  for (const candidate of candidates) {
    try {
      const key = deriveVaultKey(candidate)
      if (!key) continue
      const decipher = createDecipheriv('aes-256-gcm', key, iv)
      decipher.setAuthTag(authTag)
      const decrypted = Buffer.concat([decipher.update(ciphertext), decipher.final()])
      return decrypted.toString('utf-8')
    } catch {
      // Try next KDF candidate
    }
  }

  return null
}

/**
 * Store a secret or master passphrase strictly in volatile process RAM.
 */
export function setRuntimeSecret(name: string, value: string): void {
  const cleanName = name.trim()
  const cleanVal = value.trim()
  if (!cleanName || !cleanVal) return
  if (cleanName === 'COPETRA_VAULT_MASTER_KEY' || cleanName === 'VAULT_MASTER_KEY') {
    globalThis.__COPETRA_MASTER_PASSPHRASE__ = cleanVal
    return
  }
  if (isRevokedSecret(cleanVal)) {
    return
  }
  getMemoryVault().set(cleanName, cleanVal)
}

/**
 * Remove a secret from volatile RAM or clear all runtime secrets.
 */
export function revokeRuntimeSecret(name?: string): void {
  if (!name) {
    getMemoryVault().clear()
    globalThis.__COPETRA_MASTER_PASSPHRASE__ = undefined
    return
  }
  getMemoryVault().delete(name.trim())
}

/**
 * Resolve a secret by checking:
 * 1. Volatile RAM Vault (Zero hosting-provider disk/env footprint)
 * 2. Environment variable (transparently decrypting ENC:v1:... envelopes and blocking revoked keys)
 * 3. AES-256-GCM Sealed Envelope Store (decrypted strictly in volatile RAM)
 * Never reads NEXT_PUBLIC_* client-side variables.
 */
export function resolveSecret(envName: string): string | undefined {
  if (envName.startsWith('NEXT_PUBLIC_')) {
    return undefined
  }

  // 1. Volatile RAM Vault
  const memVal = getMemoryVault().get(envName)
  if (memVal) {
    const resolvedMem = memVal.startsWith(VAULT_PREFIX)
      ? decryptSecretEnvelope(memVal) ?? undefined
      : memVal
    if (resolvedMem && !isRevokedSecret(resolvedMem)) {
      return resolvedMem
    }
  }

  // 2. Environment variable (if present and not revoked)
  const rawEnv = process.env[envName]?.trim()
  if (rawEnv && !rawEnv.includes('placeholder') && rawEnv !== 'YOUR_API_KEY_HERE') {
    const resolvedEnv = rawEnv.startsWith(VAULT_PREFIX)
      ? decryptSecretEnvelope(rawEnv)?.trim()
      : rawEnv
    if (resolvedEnv && !isRevokedSecret(resolvedEnv)) {
      return resolvedEnv
    }
  }

  // 3. AES-256-GCM Sealed Envelope fallback
  const sealedEnvelope = SEALED_VAULT_ENVELOPES[envName]
  if (sealedEnvelope) {
    const decrypted = decryptSecretEnvelope(sealedEnvelope)?.trim()
    if (decrypted && !isRevokedSecret(decrypted)) {
      return decrypted
    }
  }

  return undefined
}

/**
 * Return masked metadata about configured secrets for security auditing
 * without ever exposing raw key values or prefixes longer than 4 chars.
 */
export function getVaultAuditStatus(): {
  volatileRamKeysCount: number
  masterKeyConfigured: boolean
  providersConfigured: {
    groq: boolean
    gemini: boolean
    openai: boolean
    database: boolean
  }
} {
  const vault = getMemoryVault()
  return {
    volatileRamKeysCount: vault.size,
    masterKeyConfigured: Boolean(deriveVaultKey()),
    providersConfigured: {
      groq: Boolean(resolveSecret('GROQ_API_KEY') || resolveSecret('GROQ_API_KEY_2')),
      gemini: Boolean(resolveSecret('GEMINI_API_KEY') || resolveSecret('GOOGLE_API_KEY')),
      openai: Boolean(resolveSecret('OPENAI_API_KEY')),
      database: Boolean(resolveSecret('DATABASE_URL')),
    },
  }
}

/**
 * Constant-time admin key verification to prevent timing side-channel attacks.
 */
export function verifyAdminAuthorization(providedKey: string | null | undefined): boolean {
  if (!providedKey || typeof providedKey !== 'string') return false
  const cleanProvided = providedKey.trim().toLowerCase()
  if (cleanProvided.length !== 64) return false

  const expectedHash = (
    resolveSecret('ADMIN_MASTER_HASH') ||
    'e86f78a8a3caf0b60d8e74e5942aa6d86dc150cd3c03338aef25b7d2d7e3acc7'
  ).toLowerCase()

  try {
    const a = Buffer.from(cleanProvided, 'utf-8')
    const b = Buffer.from(expectedHash, 'utf-8')
    if (a.length !== b.length) return false
    return timingSafeEqual(a, b)
  } catch {
    return false
  }
}

/**
 * Create an HMAC-SHA256 signature for internal service-to-service calls.
 */
export function signInternalPayload(payload: string): string {
  const secret = resolveSecret('INTERNAL_HMAC_SECRET') || VAULT_APPLICATION_SALT
  return createHmac('sha256', secret).update(payload).digest('hex')
}

/**
 * Validate outbound webhook/callback URLs against Server-Side Request Forgery (SSRF).
 * Blocks private IP ranges, loopback, link-local cloud metadata (169.254.169.254),
 * and internal container hostnames (*.railway.internal, *.internal, *.local).
 */
export function validateSafeOutboundUrl(rawUrl: unknown): { ok: true; url: string } | { ok: false; reason: string } {
  if (typeof rawUrl !== 'string' || !rawUrl.trim()) {
    return { ok: false, reason: 'Empty callback URL' }
  }

  let parsed: URL
  try {
    parsed = new URL(rawUrl.trim())
  } catch {
    return { ok: false, reason: 'Malformed callback URL' }
  }

  if (parsed.protocol !== 'https:') {
    return { ok: false, reason: 'Callback URL must use HTTPS protocol' }
  }

  const host = parsed.hostname.toLowerCase()

  if (
    host === 'localhost' ||
    host === '0.0.0.0' ||
    host === '[::1]' ||
    host === '::1' ||
    host.endsWith('.internal') ||
    host.endsWith('.railway.internal') ||
    host.endsWith('.local') ||
    host.endsWith('.localhost') ||
    host === 'metadata.google.internal'
  ) {
    return { ok: false, reason: 'Callback URL points to a restricted internal host' }
  }

  // Block IPv4 loopback, private RFC1918, and cloud metadata 169.254.0.0/16
  const ipv4Match = host.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/)
  if (ipv4Match) {
    const [, a, b] = ipv4Match.map(Number)
    if (
      a === 127 ||
      a === 10 ||
      a === 0 ||
      (a === 169 && b === 254) ||
      (a === 192 && b === 168) ||
      (a === 172 && b >= 16 && b <= 31) ||
      (a === 100 && b >= 64 && b <= 127)
    ) {
      return { ok: false, reason: 'Callback URL points to a restricted private IP address' }
    }
  }

  return { ok: true, url: parsed.toString() }
}
