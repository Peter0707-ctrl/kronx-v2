import { KronxMode, Language, Message } from '@/types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

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
  return data.response as string
}

export async function* streamMessage(
  payload: ChatRequest
): AsyncGenerator<string> {
  // Use regular endpoint for clean formatted responses
  const response = await sendMessage(payload)
  // Yield the whole response at once
  yield response
}

export function buildHistory(
  messages: Message[],
  limit = 12
): { role: 'user' | 'ai'; content: string }[] {
  return messages
    .slice(-limit)
    .map(m => ({ role: m.role, content: m.content }))
}