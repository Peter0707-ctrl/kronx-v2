import { v4 as uuidv4 } from 'uuid'
import {
  groqApiKeys,
  lastUserText,
  matchSimpleGreeting,
  preferFastGroqModels,
} from './fastChat'

export type ChatMessage = { role: string; content: string }

/** Fast model first; larger model only as fallback for long / complex prompts. */
function groqModelsFor(messages: ChatMessage[], maxTokens: number): string[] {
  const last = lastUserText(messages)
  const vision = messages.some((m) => /\[IMAGE:|image_url/i.test(String(m.content || '')))
  const document = /DOCUMENT ATTACHED:|FILE ATTACHED:/i.test(last)
  const long = last.length > 800 || maxTokens > 2048
  return preferFastGroqModels({ vision, document, long })
}

function groqKeys(): string[] {
  return groqApiKeys()
}

function upstreamTimeoutMs(wantStream: boolean, fastModel: boolean): number {
  const fromEnv = Number(
    wantStream
      ? process.env.GATEWAY_STREAM_TIMEOUT_MS
      : process.env.GATEWAY_UPSTREAM_TIMEOUT_MS
  )
  if (Number.isFinite(fromEnv) && fromEnv > 0) return fromEnv
  if (fastModel) return wantStream ? 45_000 : 25_000
  return wantStream ? 90_000 : 60_000
}

function defaultMaxTokens(): number {
  const fromEnv = Number(process.env.GATEWAY_DEFAULT_MAX_TOKENS)
  if (Number.isFinite(fromEnv) && fromEnv > 0) return fromEnv
  return 2048
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function greetingAsGroqStream(text: string): Response {
  const encoder = new TextEncoder()
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      const chunk = {
        id: `chatcmpl-${uuidv4()}`,
        object: 'chat.completion.chunk',
        created: Math.floor(Date.now() / 1000),
        model: 'copetra-ai',
        choices: [{ index: 0, delta: { content: text }, finish_reason: null }],
      }
      controller.enqueue(encoder.encode(`data: ${JSON.stringify(chunk)}\n\n`))
      controller.enqueue(encoder.encode('data: [DONE]\n\n'))
      controller.close()
    },
  })
  return new Response(stream, {
    headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache' },
  })
}

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

/** Granted developers: no app-side cap. Others capped at 4096 (if ever allowed). */
export function resolveMaxTokens(requested: unknown, unlimited = true): number {
  const n = typeof requested === 'number' ? requested : parseInt(String(requested ?? ''), 10)
  const raw = Number.isFinite(n) && n > 0 ? Math.floor(n) : defaultMaxTokens()
  if (unlimited) return raw
  return Math.min(Math.max(raw, 1), 4096)
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
  const wantStream = opts.stream === true
  const greeting = matchSimpleGreeting(lastUserText(opts.messages))
  if (greeting) {
    if (wantStream) {
      return { ok: true, stream: true, response: greetingAsGroqStream(greeting) }
    }
    return {
      ok: true,
      stream: false,
      text: greeting,
      usage: { prompt_tokens: 0, completion_tokens: greeting.length, total_tokens: greeting.length },
    }
  }

  const keys = groqKeys()
  if (keys.length === 0) {
    return {
      ok: false,
      status: 503,
      message: 'AI provider is not configured on this server (missing GROQ_API_KEY).',
      code: 'provider_not_configured',
    }
  }

  const hasSystem = opts.messages.some((m) => m.role === 'system')
  const formatted = hasSystem
    ? opts.messages
    : [{ role: 'system', content: SYSTEM_PROMPT }, ...opts.messages]
  const temperature = typeof opts.temperature === 'number' ? opts.temperature : 0.5
  const maxTokens = resolveMaxTokens(opts.maxTokens, opts.unlimited !== false)
  const models = groqModelsFor(opts.messages, maxTokens)

  let lastStatus = 0
  let lastDetail = ''
  let sawAuthFailure = false
  let rateLimitHits = 0

  for (const apiKey of keys) {
    for (const model of models) {
      const timeoutMs = upstreamTimeoutMs(wantStream, model.includes('8b') || model.includes('instant'))
      for (let attempt = 1; attempt <= 2; attempt++) {
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
              break
            }

            if (res.status === 429) {
              rateLimitHits++
              if (attempt < 2) {
                await sleep(400 * attempt)
                continue
              }
              continue
            }

            if ([502, 503, 504].includes(res.status) && attempt < 2) {
              await sleep(400 * attempt)
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

          lastDetail = 'empty completion content'
        } catch (err: any) {
          lastDetail =
            err?.name === 'TimeoutError' || err?.name === 'AbortError'
              ? `timeout after ${timeoutMs}ms`
              : String(err?.message || err)

          if (attempt < 2) {
            await sleep(400 * attempt)
            continue
          }
        }
      }

      if (sawAuthFailure) break
    }
  }

  if (rateLimitHits > 0) {
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
    message: `All upstream AI providers failed or timed out (${lastDetail || 'no detail'}). Please retry.`,
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

/** If streaming fails, automatically retry as a single non-stream completion. */
export async function createCompletionWithFallback(opts: {
  messages: ChatMessage[]
  temperature?: number
  maxTokens?: number
  stream?: boolean
  unlimited?: boolean
}): Promise<
  | { ok: true; stream: true; response: Response }
  | { ok: true; stream: false; text: string; usage: Record<string, number>; fellBack?: boolean }
  | { ok: false; status: number; message: string; code: string }
> {
  const wantStream = opts.stream === true
  const first = await createCompletion(opts)

  if (first.ok || !wantStream) {
    return first
  }

  if (first.code === 'upstream_timeout' || first.code === 'rate_limited' || first.status >= 502) {
    const fallback = await createCompletion({ ...opts, stream: false })
    if (fallback.ok && !fallback.stream) {
      return { ...fallback, fellBack: true }
    }
  }

  return first
}
