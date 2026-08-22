import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function GET() {
  const groqKey = process.env.GROQ_API_KEY
  const ollamaUrl = process.env.OLLAMA_URL
  const nextPublicApiUrl = process.env.NEXT_PUBLIC_API_URL

  const result: Record<string, unknown> = {
    timestamp: new Date().toISOString(),
    env: {
      GROQ_API_KEY: groqKey ? `SET ✅ (starts with: ${groqKey.slice(0, 8)}...)` : 'NOT SET ❌',
      OLLAMA_URL: ollamaUrl || 'NOT SET',
      NEXT_PUBLIC_API_URL: nextPublicApiUrl || 'NOT SET',
    },
    groq_test: null,
  }

  if (!groqKey) {
    result.groq_test = 'SKIPPED — GROQ_API_KEY not set ❌'
    return NextResponse.json(result)
  }

  try {
    const controller = new AbortController()
    setTimeout(() => controller.abort(), 15000)

    const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${groqKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'openai/gpt-oss-20b',
        messages: [
          { role: 'user', content: 'In one sentence, what is the importance of the food chain?' }
        ],
        max_tokens: 80,
        stream: false,
      }),
      signal: controller.signal,
    })

    if (res.ok) {
      const data = await res.json()
      const answer = data.choices?.[0]?.message?.content?.trim()
      result.groq_test = {
        status: 'SUCCESS ✅',
        model: 'openai/gpt-oss-20b',
        answer: answer || 'No text returned',
      }
    } else {
      const errText = await res.text()
      result.groq_test = { status: `HTTP ${res.status} ❌`, error: errText.slice(0, 200) }
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e)
    result.groq_test = { status: 'FAILED ❌', error: msg }
  }

  return NextResponse.json(result)
}
