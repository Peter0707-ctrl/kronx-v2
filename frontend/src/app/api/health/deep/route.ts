import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

/** Slow diagnostic probe for Ollama hosts. Do not call this from chat wake-up. */
export async function GET() {
  const ollamaHosts = [
    process.env.OLLAMA_URL,
    'http://ollama.railway.internal:11434',
    'http://127.0.0.1:11434',
    'http://localhost:11434',
  ].filter(Boolean) as string[]

  const results: Record<string, unknown> = {
    timestamp: new Date().toISOString(),
    env_OLLAMA_URL: process.env.OLLAMA_URL || 'NOT SET',
    env_NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'NOT SET',
    ollama_tests: [],
  }

  for (const host of ollamaHosts) {
    try {
      const controller = new AbortController()
      setTimeout(() => controller.abort(), 2000)
      const res = await fetch(`${host}/api/tags`, { signal: controller.signal })
      if (res.ok) {
        const data = await res.json()
        const models = data.models?.map((m: { name: string }) => m.name) || []
        ;(results.ollama_tests as unknown[]).push({ host, status: 'REACHABLE ', models })
      } else {
        ;(results.ollama_tests as unknown[]).push({ host, status: `HTTP ${res.status} ` })
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      ;(results.ollama_tests as unknown[]).push({ host, status: `FAILED `, error: msg })
    }
  }

  return NextResponse.json(results, { status: 200 })
}
