import { v4 as uuidv4 } from 'uuid'

const GROQ_MODELS = ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768']

function groqKeys(): string[] {
  const keys = [
    process.env.GROQ_API_KEY,
    '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',
    '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',
  ].filter(Boolean) as string[]
  return keys
}

export type ChatMessage = { role: string; content: string }

export function normalizeMessages(body: Record<string, unknown>): ChatMessage[] {
  const raw = body.messages
  if (Array.isArray(raw) && raw.length > 0) {
    return raw.map((m: any) => ({
      role: String(m.role || 'user'),
      content: typeof m.content === 'string' ? m.content : JSON.stringify(m.content),
    }))
  }
  const legacy = body.message || body.prompt || body.query
  if (typeof legacy === 'string' && legacy.trim()) {
    return [{ role: 'user', content: legacy.trim() }]
  }
  return []
}

const SYSTEM_PROMPT = `You are Copetra AI, an elite academic AI assistant powered by PJ Copetranova.
Provide clear, accurate, technically rigorous, and well-structured responses.`

export async function createCompletion(opts: {
  messages: ChatMessage[]
  temperature?: number
  maxTokens?: number
  stream?: boolean
}): Promise<
  | { ok: true; stream: true; response: Response }
  | { ok: true; stream: false; text: string; usage: Record<string, number> }
  | { ok: false; status: number; message: string; code: string }
> {
  const keys = groqKeys()
  if (keys.length === 0) {
    return {
      ok: false,
      status: 503,
      message: 'AI provider is not configured on this server.',
      code: 'provider_not_configured',
    }
  }

  const formatted = [{ role: 'system', content: SYSTEM_PROMPT }, ...opts.messages]
  const temperature = typeof opts.temperature === 'number' ? opts.temperature : 0.5
  const maxTokens = typeof opts.maxTokens === 'number' ? opts.maxTokens : 2048
  const wantStream = opts.stream === true

  for (const apiKey of keys) {
    for (const model of GROQ_MODELS) {
      try {
        const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${apiKey}`,
          },
          body: JSON.stringify({
            model,
            messages: formatted,
            temperature,
            max_tokens: maxTokens,
            stream: wantStream,
          }),
          signal: AbortSignal.timeout(wantStream ? 20000 : 25000),
        })

        if (!res.ok) continue

        if (wantStream && res.body) {
          return { ok: true, stream: true, response: res }
        }

        const data = await res.json()
        const text = data.choices?.[0]?.message?.content || ''
        if (text) {
          return {
            ok: true,
            stream: false,
            text,
            usage: data.usage || { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
          }
        }
      } catch {
        // try next model/key
      }
    }
  }

  return {
    ok: false,
    status: 504,
    message: 'All upstream AI providers failed or timed out.',
    code: 'upstream_timeout',
  }
}

export function toOpenAiChatResponse(opts: {
  model: string
  text: string
  usage: Record<string, number>
  developerId: string
  projectName: string
}) {
  return {
    id: `chatcmpl-${uuidv4()}`,
    object: 'chat.completion',
    created: Math.floor(Date.now() / 1000),
    model: opts.model,
    choices: [
      {
        index: 0,
        message: { role: 'assistant', content: opts.text },
        finish_reason: 'stop',
      },
    ],
    usage: opts.usage,
    // Convenience aliases for non-OpenAI clients
    response: opts.text,
    status: 'success',
    developer_id: opts.developerId,
    project: opts.projectName,
  }
}

export function wrapProviderStreamAsOpenAi(
  providerResponse: Response,
  model: string
): ReadableStream<Uint8Array> {
  const reader = providerResponse.body!.getReader()
  const decoder = new TextDecoder()
  const encoder = new TextEncoder()
  const created = Math.floor(Date.now() / 1000)
  const chatId = uuidv4()
  let buffer = ''

  return new ReadableStream({
    async start(controller) {
      try {
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
            if (dataStr === '[DONE]') {
              controller.enqueue(encoder.encode('data: [DONE]\n\n'))
              continue
            }
            try {
              const parsed = JSON.parse(dataStr)
              const content = parsed.choices?.[0]?.delta?.content || ''
              const finishReason = parsed.choices?.[0]?.finish_reason || null
              const chunk = {
                id: `chatcmpl-${chatId}`,
                object: 'chat.completion.chunk',
                created,
                model,
                choices: [{ index: 0, delta: { content }, finish_reason: finishReason }],
              }
              controller.enqueue(encoder.encode(`data: ${JSON.stringify(chunk)}\n\n`))
            } catch {
              // skip bad chunk
            }
          }
        }
        controller.close()
      } catch (err) {
        controller.error(err)
      }
    },
  })
}
