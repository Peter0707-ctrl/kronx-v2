import { v4 as uuidv4 } from 'uuid'

/** Prefer a fast model first so chat stays responsive; fall back to larger models. */
const GROQ_MODELS = [
  'llama-3.1-8b-instant',
  'llama-3.3-70b-versatile',
]

function groqKeys(): string[] {
  const keys = [process.env.GROQ_API_KEY, process.env.GROQ_API_KEY_2].filter(
    (k): k is string => Boolean(k && k.trim() && !k.includes('placeholder'))
  )
  return [...new Set(keys)]
}

function upstreamTimeoutMs(wantStream: boolean): number {
  const fromEnv = Number(
    wantStream
      ? process.env.GATEWAY_STREAM_TIMEOUT_MS
      : process.env.GATEWAY_UPSTREAM_TIMEOUT_MS
  )
  if (Number.isFinite(fromEnv) && fromEnv > 0) return fromEnv
  return wantStream ? 60000 : 90000
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
  unlimited?: boolean
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
      message: 'AI provider is not configured on this server (missing GROQ_API_KEY).',
      code: 'provider_not_configured',
    }
  }

  const formatted = [{ role: 'system', content: SYSTEM_PROMPT }, ...opts.messages]
  const temperature = typeof opts.temperature === 'number' ? opts.temperature : 0.5
  // Granted / unlimited API users: no app-side token cap (provider still enforces model max).
  const requested = typeof opts.maxTokens === 'number' ? opts.maxTokens : opts.unlimited ? 8192 : 2048
  const maxTokens = opts.unlimited ? Math.max(requested, 1) : Math.min(Math.max(requested, 1), 8192)
  const wantStream = opts.stream === true
  const timeoutMs = upstreamTimeoutMs(wantStream)

  let lastStatus = 0
  let lastDetail = ''
  let sawAuthFailure = false
  let sawRateLimit = false

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
          signal: AbortSignal.timeout(timeoutMs),
        })

        if (!res.ok) {
          lastStatus = res.status
          lastDetail = await res.text().catch(() => '')
          if (res.status === 401 || res.status === 403) {
            sawAuthFailure = true
            break // try next key, skip remaining models for this bad key
          }
          if (res.status === 429) {
            sawRateLimit = true
            continue
          }
          continue
        }

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
      } catch (err: any) {
        lastDetail = err?.name === 'TimeoutError' || err?.name === 'AbortError'
          ? `timeout after ${timeoutMs}ms`
          : String(err?.message || err)
        // try next model/key
      }
    }
  }

  if (sawRateLimit) {
    return {
      ok: false,
      status: 429,
      message: 'Upstream AI provider rate-limited the request. Please retry shortly.',
      code: 'rate_limited',
    }
  }

  if (sawAuthFailure && lastStatus) {
    return {
      ok: false,
      status: 502,
      message: 'Upstream AI provider authentication failed. Check GROQ_API_KEY on the server.',
      code: 'provider_auth_failed',
    }
  }

  return {
    ok: false,
    status: 504,
    message: `All upstream AI providers failed or timed out (${lastDetail || 'no detail'}). Retry with stream:true or try again in a few seconds.`,
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
