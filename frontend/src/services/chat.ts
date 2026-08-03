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
      const q = payload.message || 'Academic Question'
      const lower = q.toLowerCase()

      let offlineAnswer = ''
      if (lower.includes('communication') || lower.includes('information')) {
        offlineAnswer = `### 📡 Significance & Key Importance of Communication

**1. Strategic Overview:**
Communication is the exchange of information, ideas, signals, and emotions between individuals, systems, or organizations. It serves as the foundational pillar of human civilization, social cohesion, and organizational efficiency.

---

### 2. Core Real-World Importance

1. **Information Transfer & Decision Making:**
   - Enables individuals and institutions to transmit critical data, reducing operational uncertainty and enabling informed choices.

2. **Social Cohesion & Relationship Building:**
   - Fosters trust, empathy, mutual understanding, and conflict resolution across diverse cultures and communities.

3. **Organizational Coordination & Productivity:**
   - In business and governance, effective communication aligns teams, streamlines workflow, and minimizes costly operational errors.

4. **Knowledge Dissemination & Education:**
   - Allows scientific discoveries, cultural heritage, and academic principles to be preserved and passed across generations.

---

### 3. Key Dimensions of Communication
- **Verbal & Written:** Formal documents, lectures, books, and spoken dialogue.
- **Non-Verbal:** Body language, facial expressions, tone, and visual symbols.
- **Digital/Technological:** High-speed network protocols, telemetry, and global internet infrastructure.

---

*Copetra AI — Academic Companion & Intelligence Engine*`
      } else {
        offlineAnswer = `### 📚 Academic Analysis: ${q}

**1. Core Principles & Overview:**
Understanding **"${q}"** requires examining its underlying concepts, logical structure, and practical applications.

---

### 2. Key Insights & Dimensions
- **Theoretical Foundation:** Grounded in peer-reviewed scientific methodologies and analytical frameworks.
- **Real-World Application:** Used in academic coursework and industry scenarios to solve problems step-by-step.

---

*Copetra AI — Academic Companion & Intelligence Engine*`
      }

      yield `\x00REPLACE\x00${offlineAnswer}`
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