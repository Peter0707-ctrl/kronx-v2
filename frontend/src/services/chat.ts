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
  // 100% Direct API response from backend route /api/chat
  try {
    const text = await sendMessage(payload)
    yield `\x00REPLACE\x00${text}`
  } catch (err) {
    console.warn('[Copetra API Retry Triggered]', err)
    // Automatic 1-second retry against live API
    await new Promise(r => setTimeout(r, 1000))
    const retryText = await sendMessage(payload)
    yield `\x00REPLACE\x00${retryText}`
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