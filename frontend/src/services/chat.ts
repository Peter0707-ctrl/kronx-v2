import { KronxMode, Language, Message } from '@/types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

export interface ChatRequest {
  message: string
  mode: KronxMode
  language: Language
  conversation_id: string
  history: { role: 'user' | 'ai'; content: string }[]
}

export async function sendMessage(payload: ChatRequest): Promise<string> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err?.detail ?? `API error ${res.status}`)
  }

  const data = await res.json()
  return (data.response ?? data.message ?? '') as string
}

export async function* streamMessage(
  payload: ChatRequest
): AsyncGenerator<string> {
  let receivedContent = false

  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 10000)

    const response = await fetch(`${API_BASE}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok || !response.body) {
      const fallbackText = await sendMessage(payload)
      yield `\x00REPLACE\x00${fallbackText}`
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const readPromise = reader.read()
      const timeoutPromise = new Promise<{ done: boolean; value?: Uint8Array }>((_, reject) =>
        setTimeout(() => reject(new Error('Stream read stall timeout')), 10000)
      )

      const { done, value } = (await Promise.race([readPromise, timeoutPromise])) as {
        done: boolean
        value?: Uint8Array
      }

      if (done) break

      if (value) {
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (trimmed.startsWith(':') || !trimmed) continue
          if (!trimmed.startsWith('data: ')) continue

          const dataStr = trimmed.slice(6)
          if (dataStr === '[DONE]') return

          const token = dataStr.replace(/\\n/g, '\n')
          if (token) {
            receivedContent = true
            yield token
          }
        }
      }
    }

    if (!receivedContent) {
      const fallbackText = await sendMessage(payload)
      yield `\x00REPLACE\x00${fallbackText}`
    }
  } catch (err) {
    console.warn('[Copetra Real-Time Stream Fallback Triggered]', err)
    try {
      const fallbackText = await sendMessage(payload)
      yield `\x00REPLACE\x00${fallbackText}`
    } catch (directErr) {
      console.error('[Copetra Direct Fetch Error]', directErr)
      yield `\x00REPLACE\x00Connection error. Please try again.`
    }
  }
}

export function buildHistory(
  messages: Message[],
  limit = 8
): { role: 'user' | 'ai'; content: string }[] {
  return messages
    .slice(-limit)
    .map(m => ({ role: m.role, content: m.content }))
}