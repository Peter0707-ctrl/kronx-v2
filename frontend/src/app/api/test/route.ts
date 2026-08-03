import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function GET() {
  const ollamaHost = process.env.OLLAMA_URL || 'http://ollama.railway.internal:11434'

  try {
    const controller = new AbortController()
    setTimeout(() => controller.abort(), 25000)

    const res = await fetch(`${ollamaHost}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'llama3.2:3b',
        prompt: 'In one sentence, what is the importance of the food chain?',
        stream: false,
        options: { num_predict: 80, temperature: 0.5 }
      }),
      signal: controller.signal,
    })

    if (res.ok) {
      const data = await res.json()
      return NextResponse.json({
        status: 'SUCCESS ✅',
        model: 'llama3.2:3b',
        ollama_host: ollamaHost,
        answer: data.response?.trim() || 'No response text',
      })
    }
    return NextResponse.json({ status: `HTTP ERROR ${res.status} ❌`, ollama_host: ollamaHost })
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e)
    return NextResponse.json({ status: 'FAILED ❌', error: msg, ollama_host: ollamaHost })
  }
}
