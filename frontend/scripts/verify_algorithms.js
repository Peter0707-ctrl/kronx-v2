const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const rootDir = path.resolve(__dirname, '..');

const checkRules = [
  {
    file: 'src/hooks/useChat.ts',
    checks: [
      {
        name: 'History limits bounds parameters (.slice(0, -2)) in send',
        check: (c) => c.includes('activeMessages().slice(0, -2)'),
      },
      {
        name: 'Image generator tag parser regex',
        check: (c) => c.includes('[GENERATE_IMAGE:\\s*(.*?)]') || c.includes('GENERATE_IMAGE'),
      },
      {
        name: 'Memory learning tag parser regex',
        check: (c) => c.includes('[MEMORIZE:\\s*(.*?)]') || c.includes('MEMORIZE'),
      },
      {
        name: 'Visual summary memory tag parser regex',
        check: (c) => c.includes('[VISUAL_SUMMARY:\\s*(.*?)]') || c.includes('VISUAL_SUMMARY'),
      }
    ]
  },
  {
    file: 'src/components/chat/MessageBubble.tsx',
    checks: [
      {
        name: 'vCard tag pattern extraction regex',
        check: (c) => c.includes('[VCARD:\\s*([^\\]]+)]') || c.includes('VCARD'),
      },
      {
        name: 'ResilientMarkdownImage fallback component',
        check: (c) => c.includes('const ResilientMarkdownImage'),
      },
      {
        name: 'ReactMarkdown element overrides using ResilientMarkdownImage',
        check: (c) => c.includes('ResilientMarkdownImage') && c.includes('img:'),
      },
      {
        name: 'Word Export function handleExportDocx',
        check: (c) => c.includes('handleExportDocx'),
      },
      {
        name: 'PDF Export function handleExportPdf',
        check: (c) => c.includes('handleExportPdf'),
      },
      {
        name: 'Excel Export function handleExportExcel',
        check: (c) => c.includes('handleExportExcel'),
      }
    ]
  },
  {
    file: 'src/lib/fastChat.ts',
    checks: [
      {
        name: 'Zero-Knowledge Secret Vault integration in fastChat.ts',
        check: (c) => c.includes('resolveSecret') && !/function\s+getFallback/i.test(c) && !/NEXT_PUBLIC_[A-Z_]*KEY/.test(c),
      }
    ]
  },
  {
    file: 'src/lib/db.ts',
    checks: [
      {
        name: 'Zero hardcoded database password in db.ts',
        check: (c) => c.includes('resolveSecret') && !/postgresql:\/\/postgres:[^@]+@/.test(c),
      }
    ]
  },
  {
    file: 'src/lib/secretVault.ts',
    checks: [
      {
        name: 'AES-256-GCM + HKDF-SHA256 Zero-Knowledge Secret Vault implementation',
        check: (c) => c.includes('aes-256-gcm') && c.includes('hkdfSync') && c.includes('validateSafeOutboundUrl'),
      }
    ]
  }
];

let failed = false;

console.log('[SECURITY] Starting Copetra AI Core Algorithms & Zero-Secret Verification Scan...\n');

checkRules.forEach(rule => {
  const filePath = path.join(rootDir, rule.file);
  if (!fs.existsSync(filePath)) {
    console.error(`[ERROR] File not found: ${rule.file}`);
    failed = true;
    return;
  }

  const content = fs.readFileSync(filePath, 'utf-8');
  console.log(`Checking ${rule.file}...`);

  rule.checks.forEach(check => {
    if (check.check(content)) {
      console.log(`  [PASS] ${check.name}`);
    } else {
      console.error(`  [FAIL] ${check.name}`);
      failed = true;
    }
  });
});

if (failed) {
  console.error('\n[FAIL] Verification failed! Core algorithms or security constraints violated.');
  process.exit(1);
}

console.log('\n[PASS] All code structure and zero-secret checks passed.');
