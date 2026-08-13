'use client'

import { useEffect, useState, type CSSProperties } from 'react'
import { useKronxStore } from '@/store/useKronxStore'

const API_BASE =
  process.env.NEXT_PUBLIC_SITE_URL ||
  'https://miraculous-forgiveness-production-10d4.up.railway.app'

type ApiKeyRow = {
  id: string
  projectName: string
  keyPrefix: string
  apiKey: string
  callbackUrl?: string | null
  isActive: boolean
  lastUsedAt?: string | null
  createdAt?: string
}

type DocTab = 'overview' | 'auth' | 'chat' | 'errors' | 'examples'

export default function DeveloperPanel() {
  const { user, language, setDeveloperMode } = useKronxStore()
  const sw = language === 'sw'

  const [keys, setKeys] = useState<ApiKeyRow[]>([])
  const [loading, setLoading] = useState(false)
  const [projectName, setProjectName] = useState('')
  const [callbackUrl, setCallbackUrl] = useState('')
  const [creating, setCreating] = useState(false)
  const [freshKey, setFreshKey] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [docTab, setDocTab] = useState<DocTab>('overview')
  const [codeTab, setCodeTab] = useState<'curl' | 'js' | 'python' | 'php'>('curl')
  const [testPrompt, setTestPrompt] = useState('Explain artificial intelligence in one sentence.')
  const [testOutput, setTestOutput] = useState<string | null>(null)
  const [testing, setTesting] = useState(false)
  const [streamChecked, setStreamChecked] = useState(false)
  const [selectedKeyId, setSelectedKeyId] = useState<string>('')
  const [toast, setToast] = useState<string | null>(null)

  const granted = Boolean(user?.isDeveloper || user?.role === 'admin')

  const sessionHeaders = (): HeadersInit => ({
    'Content-Type': 'application/json',
    'x-user-id': user?.id || '',
    'x-user-email': user?.email || '',
  })

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 2800)
  }

  const loadKeys = async () => {
    if (!granted || !user?.id) return
    setLoading(true)
    try {
      const res = await fetch('/api/developer/keys', { headers: sessionHeaders() })
      const data = await res.json()
      if (res.ok) {
        setKeys(data.keys || [])
        if (!selectedKeyId && data.keys?.[0]) setSelectedKeyId(data.keys[0].id)
      }
    } catch (e) {
      console.warn(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Refresh developer flag from server (admin grant source of truth)
    if (!user?.email) return
    fetch('/api/users')
      .then((r) => r.json())
      .then((list: any[]) => {
        const me = Array.isArray(list)
          ? list.find((u) => (u.email || '').toLowerCase() === user.email.toLowerCase())
          : null
        if (me && typeof me.isDeveloper === 'boolean') {
          setDeveloperMode(Boolean(me.isDeveloper) || user.role === 'admin')
        }
      })
      .catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.email])

  useEffect(() => {
    loadKeys()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [granted, user?.id])

  const createKey = async () => {
    if (!projectName.trim()) {
      showToast(sw ? 'Andika jina la project' : 'Enter a project name')
      return
    }
    setCreating(true)
    setFreshKey(null)
    try {
      const res = await fetch('/api/developer/keys', {
        method: 'POST',
        headers: sessionHeaders(),
        body: JSON.stringify({
          projectName: projectName.trim(),
          callbackUrl: callbackUrl.trim() || null,
        }),
      })
      const data = await res.json()
      if (!res.ok) {
        showToast(data?.error?.message || 'Failed to create key')
        return
      }
      setFreshKey(data.key.apiKey)
      setProjectName('')
      setCallbackUrl('')
      useKronxStore.setState((s) => ({
        user: s.user ? { ...s.user, apiKey: data.key.apiKey, isDeveloper: true } : null,
      }))
      await loadKeys()
      setSelectedKeyId(data.key.id)
      showToast(sw ? 'API key imetengenezwa!' : 'API key created — copy it now')
    } catch (e: any) {
      showToast(e.message)
    } finally {
      setCreating(false)
    }
  }

  const revokeKey = async (id: string) => {
    if (!confirm(sw ? 'Batilisha API key hii?' : 'Revoke this API key?')) return
    const res = await fetch('/api/developer/keys', {
      method: 'DELETE',
      headers: sessionHeaders(),
      body: JSON.stringify({ id }),
    })
    if (res.ok) {
      if (freshKey) setFreshKey(null)
      await loadKeys()
      showToast(sw ? 'Key imebatilishwa' : 'Key revoked')
    }
  }

  const activeKeys = keys.filter((k) => k.isActive)
  const exampleKey = freshKey || 'cpk_YOUR_API_KEY'
  const endpointGateway = `${API_BASE}/api/gateway`
  const endpointOpenAI = `${API_BASE}/api/v1/chat/completions`

  const snippets = {
    curl: `curl -X POST ${endpointGateway} \\
  -H "Authorization: Bearer ${exampleKey}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "copetra-ai",
    "messages": [{"role": "user", "content": "Explain quantum computing briefly."}],
    "stream": false
  }'`,
    js: `// Node.js / browser fetch
const res = await fetch('${endpointGateway}', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ${exampleKey}',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'copetra-ai',
    messages: [{ role: 'user', content: 'Hello Copetra' }],
    stream: false
  })
});
const data = await res.json();
console.log(data.choices[0].message.content);

// OpenAI SDK compatible:
// baseURL: '${API_BASE}/api/v1'
// apiKey: '${exampleKey}'
// path: chat.completions → /api/v1/chat/completions`,
    python: `import requests

res = requests.post(
    "${endpointGateway}",
    headers={
        "Authorization": "Bearer ${exampleKey}",
        "Content-Type": "application/json",
    },
    json={
        "model": "copetra-ai",
        "messages": [{"role": "user", "content": "Hello Copetra"}],
    },
    timeout=60,
)
print(res.json()["choices"][0]["message"]["content"])

# OpenAI SDK:
# from openai import OpenAI
# client = OpenAI(api_key="${exampleKey}", base_url="${API_BASE}/api/v1")`,
    php: `<?php
$ch = curl_init('${endpointGateway}');
curl_setopt_array($ch, [
  CURLOPT_POST => true,
  CURLOPT_HTTPHEADER => [
    'Authorization: Bearer ${exampleKey}',
    'Content-Type: application/json',
  ],
  CURLOPT_POSTFIELDS => json_encode([
    'model' => 'copetra-ai',
    'messages' => [['role' => 'user', 'content' => 'Hello Copetra']],
  ]),
  CURLOPT_RETURNTRANSFER => true,
]);
$response = curl_exec($ch);
curl_close($ch);
echo $response;`,
  }

  const runTest = async () => {
    setTesting(true)
    setTestOutput(null)
    try {
      const keyToUse = freshKey
      if (!keyToUse) {
        setTestOutput(
          sw
            ? 'Tengeneza key mpya kwanza ili kujaribu (secret huonyeshwa mara moja tu).'
            : 'Create a new key first to test (the full secret is only shown once).'
        )
        return
      }
      const res = await fetch('/api/gateway', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${keyToUse}`,
        },
        body: JSON.stringify({
          model: 'copetra-ai',
          messages: [{ role: 'user', content: testPrompt }],
          stream: streamChecked,
        }),
      })

      if (streamChecked && res.body) {
        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let out = ''
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''
          for (const line of lines) {
            const clean = line.trim()
            if (!clean.startsWith('data: ')) continue
            const dataStr = clean.slice(6)
            if (dataStr === '[DONE]') continue
            try {
              const parsed = JSON.parse(dataStr)
              out += parsed.choices?.[0]?.delta?.content || ''
              setTestOutput(out)
            } catch {
              /* skip */
            }
          }
        }
      } else {
        const data = await res.json()
        setTestOutput(JSON.stringify(data, null, 2))
      }
    } catch (e: any) {
      setTestOutput(e.message)
    } finally {
      setTesting(false)
    }
  }

  if (!granted) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div
          style={{
            background: 'linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%)',
            border: '1px solid #fdba74',
            borderRadius: 16,
            padding: 20,
          }}
        >
          <h3 style={{ margin: '0 0 8px', color: '#9a3412', fontSize: 17, fontWeight: 800 }}>
            {sw ? 'Ruhusa ya Developer inahitajika' : 'Developer access required'}
          </h3>
          <p style={{ margin: 0, color: '#c2410c', fontSize: 13, lineHeight: 1.6 }}>
            {sw
              ? 'Admin lazima akupe ruhusa ya API kwanza. Baada ya kupewa, utaweza kutengeneza API keys nyingi kwa project zako na kuunganisha mifumo yako.'
              : 'An admin must grant you Developer API access first. Once approved, you can create multiple project API keys and integrate Copetra into your systems.'}
          </p>
          <p style={{ margin: '12px 0 0', color: '#9a3412', fontSize: 12, fontWeight: 700 }}>
            Base URL: {API_BASE}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18, position: 'relative' }}>
      {toast && (
        <div
          style={{
            position: 'sticky',
            top: 0,
            zIndex: 5,
            background: '#0f172a',
            color: '#38bdf8',
            padding: '10px 14px',
            borderRadius: 10,
            fontSize: 12.5,
            fontWeight: 700,
          }}
        >
          {toast}
        </div>
      )}

      {/* Header */}
      <div
        style={{
          background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)',
          borderRadius: 16,
          padding: 20,
          border: '1px solid #bae6fd',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10 }}>
          <h3 style={{ margin: 0, color: '#0c4a6e', fontSize: 17, fontWeight: 800 }}>
            Copetra Developer API
          </h3>
          <span
            style={{
              fontSize: 11,
              background: '#10b981',
              color: '#fff',
              padding: '3px 10px',
              borderRadius: 12,
              fontWeight: 700,
            }}
          >
            {sw ? '✓ Ruhusa imepewa' : '✓ Access granted'}
          </span>
        </div>
        <p style={{ margin: '8px 0 0', color: '#0369a1', fontSize: 13, lineHeight: 1.55 }}>
          {sw
            ? 'Tengeneza API keys kwa kila project, kisha unganisha mifumo yako kwa base URL hii.'
            : 'Create an API key per project, then call Copetra from any system using this base URL.'}
        </p>
        <code
          style={{
            display: 'block',
            marginTop: 10,
            background: '#fff',
            border: '1px solid #bae6fd',
            borderRadius: 8,
            padding: '8px 10px',
            fontSize: 12,
            color: '#0f172a',
            wordBreak: 'break-all',
          }}
        >
          {API_BASE}
        </code>
      </div>

      {/* Create key */}
      <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 14, padding: 16 }}>
        <div style={{ fontWeight: 800, fontSize: 14, color: '#0f172a', marginBottom: 10 }}>
          {sw ? 'Tengeneza API Key mpya' : 'Create project API key'}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <input
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder={sw ? 'Jina la project (mf. School Portal)' : 'Project name (e.g. School Portal)'}
            style={inputStyle}
          />
          <input
            value={callbackUrl}
            onChange={(e) => setCallbackUrl(e.target.value)}
            placeholder={sw ? 'Webhook URL (si lazima)' : 'Optional default webhook URL'}
            style={inputStyle}
          />
          <button
            onClick={createKey}
            disabled={creating}
            style={{
              ...btnPrimary,
              opacity: creating ? 0.7 : 1,
              cursor: creating ? 'wait' : 'pointer',
            }}
          >
            {creating
              ? sw
                ? 'Inatengeneza…'
                : 'Creating…'
              : sw
                ? '+ Tengeneza Key'
                : '+ Create API Key'}
          </button>
        </div>

        {freshKey && (
          <div
            style={{
              marginTop: 12,
              background: '#052e16',
              borderRadius: 10,
              padding: 12,
              border: '1px solid #16a34a',
            }}
          >
            <div style={{ color: '#86efac', fontSize: 11, fontWeight: 700, marginBottom: 6 }}>
              {sw
                ? 'Nakili sasa — secret inaonekana mara moja tu'
                : 'Copy now — full secret is shown only once'}
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <code style={{ flex: 1, color: '#4ade80', fontSize: 12, wordBreak: 'break-all' }}>
                {freshKey}
              </code>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(freshKey)
                  setCopied(true)
                  setTimeout(() => setCopied(false), 2000)
                }}
                style={{
                  background: copied ? '#16a34a' : '#14532d',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 8,
                  padding: '6px 12px',
                  fontWeight: 700,
                  fontSize: 12,
                  cursor: 'pointer',
                }}
              >
                {copied ? '✓ Copied' : 'Copy'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Keys list */}
      <div>
        <div style={{ fontWeight: 800, fontSize: 14, color: '#0f172a', marginBottom: 8 }}>
          {sw ? `API Keys zako (${activeKeys.length})` : `Your API keys (${activeKeys.length})`}
        </div>
        {loading ? (
          <div style={{ color: '#64748b', fontSize: 13 }}>Loading…</div>
        ) : keys.length === 0 ? (
          <div style={{ color: '#64748b', fontSize: 13, padding: 12, background: '#f8fafc', borderRadius: 10 }}>
            {sw ? 'Hakuna keys bado.' : 'No keys yet. Create one for your first project.'}
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {keys.map((k) => (
              <div
                key={k.id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  gap: 10,
                  alignItems: 'center',
                  padding: '12px 14px',
                  borderRadius: 12,
                  border: '1px solid #e2e8f0',
                  background: k.isActive ? '#fff' : '#f8fafc',
                  opacity: k.isActive ? 1 : 0.65,
                }}
              >
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: 800, fontSize: 13, color: '#0f172a' }}>{k.projectName}</div>
                  <div style={{ fontSize: 11.5, color: '#64748b', fontFamily: 'monospace' }}>
                    {k.keyPrefix}… · {k.isActive ? 'active' : 'revoked'}
                  </div>
                </div>
                {k.isActive && (
                  <button
                    onClick={() => revokeKey(k.id)}
                    style={{
                      background: '#fef2f2',
                      color: '#dc2626',
                      border: '1px solid #fecaca',
                      borderRadius: 8,
                      padding: '6px 10px',
                      fontSize: 11,
                      fontWeight: 700,
                      cursor: 'pointer',
                      flexShrink: 0,
                    }}
                  >
                    {sw ? 'Batilisha' : 'Revoke'}
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Documentation */}
      <div style={{ border: '1px solid #e2e8f0', borderRadius: 14, overflow: 'hidden' }}>
        <div
          style={{
            background: '#0f172a',
            padding: '10px 12px',
            display: 'flex',
            gap: 6,
            flexWrap: 'wrap',
          }}
        >
          {(
            [
              ['overview', sw ? 'Muhtasari' : 'Overview'],
              ['auth', 'Auth'],
              ['chat', 'Chat API'],
              ['errors', 'Errors'],
              ['examples', sw ? 'Mifano' : 'Examples'],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              onClick={() => setDocTab(id)}
              style={{
                background: docTab === id ? '#0284c7' : 'transparent',
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                padding: '6px 10px',
                fontSize: 11.5,
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              {label}
            </button>
          ))}
        </div>

        <div style={{ padding: 16, background: '#fff', fontSize: 13, color: '#334155', lineHeight: 1.65 }}>
          {docTab === 'overview' && (
            <div>
              <p style={{ marginTop: 0 }}>
                Copetra exposes an <strong>OpenAI-compatible</strong> HTTP API so other systems can send chat
                requests using your project API keys.
              </p>
              <ul style={{ paddingLeft: 18, margin: '8px 0' }}>
                <li>
                  <strong>Base URL:</strong> <code>{API_BASE}</code>
                </li>
                <li>
                  <strong>Primary endpoint:</strong> <code>POST /api/gateway</code>
                </li>
                <li>
                  <strong>OpenAI alias:</strong> <code>POST /api/v1/chat/completions</code>
                </li>
                <li>
                  <strong>Model id:</strong> <code>copetra-ai</code>
                </li>
              </ul>
              <p style={{ marginBottom: 0 }}>
                Flow: Admin grants Developer access → you create a key per project → your system calls the API with
                that key.
              </p>
            </div>
          )}

          {docTab === 'auth' && (
            <div>
              <p style={{ marginTop: 0 }}>Send your API key on every request using either header:</p>
              <pre style={preStyle}>{`Authorization: Bearer cpk_...\nx-api-key: cpk_...`}</pre>
              <p>
                Keys look like <code>cpk_…</code>. Each key belongs to one project. Revoked keys return{' '}
                <code>403 key_revoked</code>.
              </p>
              <p style={{ marginBottom: 0 }}>
                Accounts without admin-granted developer access receive <code>403 developer_not_granted</code>.
              </p>
            </div>
          )}

          {docTab === 'chat' && (
            <div>
              <p style={{ marginTop: 0 }}>
                <strong>POST</strong> <code>{endpointGateway}</code>
              </p>
              <p>Request body:</p>
              <pre style={preStyle}>{`{
  "model": "copetra-ai",
  "messages": [
    { "role": "user", "content": "Your question" }
  ],
  "stream": false,
  "temperature": 0.5,
  "max_tokens": 2048,
  "callback_url": "https://your.app/webhook"   // optional async
}`}</pre>
              <p>Success response (non-stream):</p>
              <pre style={preStyle}>{`{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "model": "copetra-ai",
  "choices": [{ "message": { "role": "assistant", "content": "..." } }],
  "usage": { "prompt_tokens": 12, "completion_tokens": 40, "total_tokens": 52 },
  "response": "...",
  "developer_id": "u-...",
  "project": "School Portal"
}`}</pre>
              <p style={{ marginBottom: 0 }}>
                Set <code>stream: true</code> for Server-Sent Events (OpenAI chunk format). With{' '}
                <code>callback_url</code> and <code>stream: false</code>, the API returns <code>202 Accepted</code>{' '}
                and POSTs the result to your webhook.
              </p>
            </div>
          )}

          {docTab === 'errors' && (
            <div>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5 }}>
                <thead>
                  <tr>
                    <th style={thStyle}>Code</th>
                    <th style={thStyle}>HTTP</th>
                    <th style={thStyle}>Meaning</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ['missing_api_key', '401', 'No Authorization / x-api-key'],
                    ['invalid_api_key', '403', 'Key not found'],
                    ['key_revoked', '403', 'Key was revoked'],
                    ['developer_not_granted', '403', 'Admin has not granted API access'],
                    ['empty_payload', '400', 'No messages / prompt'],
                    ['provider_not_configured', '503', 'Server missing GROQ_API_KEY'],
                    ['upstream_timeout', '504', 'AI providers failed'],
                  ].map(([code, http, meaning]) => (
                    <tr key={code}>
                      <td style={tdStyle}>
                        <code>{code}</code>
                      </td>
                      <td style={tdStyle}>{http}</td>
                      <td style={tdStyle}>{meaning}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {docTab === 'examples' && (
            <div>
              <div style={{ display: 'flex', gap: 6, marginBottom: 10, flexWrap: 'wrap' }}>
                {(['curl', 'js', 'python', 'php'] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setCodeTab(t)}
                    style={{
                      background: codeTab === t ? '#0284c7' : '#f1f5f9',
                      color: codeTab === t ? '#fff' : '#0f172a',
                      border: 'none',
                      borderRadius: 8,
                      padding: '5px 10px',
                      fontSize: 11,
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      cursor: 'pointer',
                    }}
                  >
                    {t}
                  </button>
                ))}
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(snippets[codeTab])
                    showToast(sw ? 'Msimbo umenakiliwa' : 'Snippet copied')
                  }}
                  style={{
                    marginLeft: 'auto',
                    background: '#0f172a',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 8,
                    padding: '5px 10px',
                    fontSize: 11,
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  Copy
                </button>
              </div>
              <pre style={{ ...preStyle, background: '#090d16', color: '#38bdf8' }}>{snippets[codeTab]}</pre>
              <p style={{ fontSize: 12, color: '#64748b', marginBottom: 0 }}>
                OpenAI SDK base URL: <code>{API_BASE}/api/v1</code> → uses{' '}
                <code>{endpointOpenAI}</code>
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Live tester */}
      <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: 14, padding: 16 }}>
        <div style={{ fontWeight: 800, color: '#166534', marginBottom: 8, fontSize: 13.5 }}>
          {sw ? 'Jaribio la Gateway' : 'Live gateway test'}
        </div>
        <div style={{ display: 'flex', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
          <input
            value={testPrompt}
            onChange={(e) => setTestPrompt(e.target.value)}
            style={{ ...inputStyle, flex: 1, minWidth: 180 }}
          />
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#166534', fontWeight: 700 }}>
            <input type="checkbox" checked={streamChecked} onChange={(e) => setStreamChecked(e.target.checked)} />
            Stream
          </label>
          <button onClick={runTest} disabled={testing} style={{ ...btnPrimary, background: '#16a34a' }}>
            {testing ? '…' : sw ? 'Jaribu' : 'Test'}
          </button>
        </div>
        {testOutput && (
          <pre
            style={{
              margin: 0,
              padding: 12,
              borderRadius: 10,
              background: '#090d16',
              color: '#4ade80',
              fontSize: 12,
              maxHeight: 220,
              overflow: 'auto',
              whiteSpace: 'pre-wrap',
            }}
          >
            {testOutput}
          </pre>
        )}
      </div>
    </div>
  )
}

const inputStyle: CSSProperties = {
  width: '100%',
  padding: '11px 12px',
  borderRadius: 10,
  border: '1px solid #cbd5e1',
  background: '#fff',
  fontSize: 13,
  color: '#0f172a',
  boxSizing: 'border-box',
}

const btnPrimary: CSSProperties = {
  background: 'linear-gradient(135deg, #0284c7, #0369a1)',
  color: '#fff',
  border: 'none',
  borderRadius: 10,
  padding: '11px 16px',
  fontWeight: 700,
  fontSize: 13,
}

const preStyle: CSSProperties = {
  background: '#f1f5f9',
  borderRadius: 10,
  padding: 12,
  overflow: 'auto',
  fontSize: 11.5,
  lineHeight: 1.5,
}

const thStyle: CSSProperties = {
  textAlign: 'left',
  borderBottom: '1px solid #e2e8f0',
  padding: '6px 4px',
  color: '#0f172a',
}

const tdStyle: CSSProperties = {
  borderBottom: '1px solid #f1f5f9',
  padding: '6px 4px',
  verticalAlign: 'top',
}
