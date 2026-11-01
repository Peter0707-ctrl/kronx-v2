#!/usr/bin/env node
/**
 * Copetra AI Zero-Knowledge Secret Envelope Generator (AES-256-GCM + HKDF-SHA256)
 *
 * Usage:
 *   node scripts/encrypt_secret.js "<MASTER_PASSPHRASE>" "<PLAINTEXT_API_KEY>"
 *
 * Output:
 *   ENC:v1:<iv_hex>:<auth_tag_hex>:<ciphertext_hex>
 */

const crypto = require('crypto')

const VAULT_PREFIX = 'ENC:v1:'
const VAULT_APPLICATION_SALT = 'copetra-zk-vault-v1-hkdf-salt-2026'
const VAULT_INFO_CONTEXT = 'copetra-aes-256-gcm-envelope-key'

function deriveKey(passphrase) {
  return Buffer.from(
    crypto.hkdfSync(
      'sha256',
      Buffer.from(passphrase.trim(), 'utf-8'),
      Buffer.from(VAULT_APPLICATION_SALT, 'utf-8'),
      Buffer.from(VAULT_INFO_CONTEXT, 'utf-8'),
      32
    )
  )
}

function encryptSecret(passphrase, plaintext) {
  const key = deriveKey(passphrase)
  const iv = crypto.randomBytes(12)
  const cipher = crypto.createCipheriv('aes-256-gcm', key, iv)
  const encrypted = Buffer.concat([cipher.update(plaintext, 'utf-8'), cipher.final()])
  const tag = cipher.getAuthTag()
  return `${VAULT_PREFIX}${iv.toString('hex')}:${tag.toString('hex')}:${encrypted.toString('hex')}`
}

function decryptSecret(passphrase, envelope) {
  const key = deriveKey(passphrase)
  const [ivHex, tagHex, cipherHex] = envelope.slice(VAULT_PREFIX.length).split(':')
  const decipher = crypto.createDecipheriv('aes-256-gcm', key, Buffer.from(ivHex, 'hex'))
  decipher.setAuthTag(Buffer.from(tagHex, 'hex'))
  const decrypted = Buffer.concat([
    decipher.update(Buffer.from(cipherHex, 'hex')),
    decipher.final(),
  ])
  return decrypted.toString('utf-8')
}

if (require.main === module) {
  const [, , passphrase, secret] = process.argv
  if (!passphrase || !secret || passphrase.length < 8) {
    console.error('Usage: node scripts/encrypt_secret.js "<MASTER_PASSPHRASE_MIN_8_CHARS>" "<RAW_SECRET>"')
    process.exit(1)
  }
  const envelope = encryptSecret(passphrase, secret)
  const verified = decryptSecret(passphrase, envelope)
  if (verified !== secret) {
    console.error('Verification failed!')
    process.exit(1)
  }
  console.log(envelope)
}

module.exports = { encryptSecret, decryptSecret }
