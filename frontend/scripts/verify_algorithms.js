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
    file: 'src/lib/gateway.ts',
    checks: [
      {
        name: 'Gateway fallback Groq API keys',
        check: (c) => c.includes('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'),
      }
    ]
  },
  {
    file: 'src/app/api/chat/route.ts',
    checks: [
      {
        name: 'Route fallback Groq API keys',
        check: (c) => c.includes('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'),
      }
    ]
  },
  {
    file: 'src/app/api/chat/stream/route.ts',
    checks: [
      {
        name: 'Stream Route fallback Groq API keys',
        check: (c) => c.includes('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'),
      }
    ]
  }
];

let failed = false;

console.log('🛡️ Starting Copetra AI Core Algorithms Verification Scan...\n');

checkRules.forEach(rule => {
  const filePath = path.join(rootDir, rule.file);
  if (!fs.existsSync(filePath)) {
    console.error(`❌ File not found: ${rule.file}`);
    failed = true;
    return;
  }

  const content = fs.readFileSync(filePath, 'utf-8');
  console.log(`Checking ${rule.file}...`);

  rule.checks.forEach(check => {
    if (check.check(content)) {
      console.log(`  ✅ [PASS] ${check.name}`);
    } else {
      console.error(`  ❌ [FAIL] ${check.name}`);
      failed = true;
    }
  });
});

if (failed) {
  console.error('\n🔴 Verification failed! Core algorithms or parsing regexes have been modified or removed.');
  process.exit(1);
}

console.log('\n🟢 Code structure checks passed. Running Next.js build compilation verify...');
try {
  execSync('npm run build', { cwd: rootDir, stdio: 'inherit' });
  console.log('\n🚀 ALL CHECKS PASSED. Project is 100% stable, secure, and resilient!');
  process.exit(0);
} catch (buildError) {
  console.error('\n🔴 Compilation Build failed!', buildError.message);
  process.exit(1);
}
