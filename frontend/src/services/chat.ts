import { KronxMode, Language, Message } from '@/types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://miraculous-forgiveness-production-10d4.up.railway.app'

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
  try {
    const controller = new AbortController()
    // 45-second timeout — enough for full AI response
    const timeoutId = setTimeout(() => controller.abort(), 45000)

    const response = await fetch(`${API_BASE}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok || !response.body) {
      // Fallback to standard endpoint if streaming is not supported
      const fallbackText = await sendMessage(payload)
      yield fallbackText
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    let receivedContent = false

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        const trimmed = line.trim()

        // Skip SSE comment lines (our keep-alive ping): ": pjkronx-stream-open"
        if (trimmed.startsWith(':')) continue

        // Skip empty lines (SSE uses blank lines as event separators)
        if (!trimmed) continue

        if (!trimmed.startsWith('data: ')) continue

        const dataStr = trimmed.slice(6)
        if (dataStr === '[DONE]') {
          return
        }

        // Unescape newlines from SSE wire format back to real newlines
        const token = dataStr.replace(/\\n/g, '\n')
        if (token) {
          receivedContent = true
          yield token
        }
      }
    }

    // If stream closed without any content, fallback to /api/chat
    if (!receivedContent) {
      const fallbackText = await sendMessage(payload)
      yield fallbackText
    }

  } catch (err: unknown) {
    console.warn('[Kronx Stream Fallback triggered]', err)
    // Fallback to non-streaming response on any stream error
    try {
      const fallbackText = await sendMessage(payload)
      yield fallbackText
    } catch (fallbackErr) {
      console.error('[Kronx fallback also failed]', fallbackErr)
      throw fallbackErr
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