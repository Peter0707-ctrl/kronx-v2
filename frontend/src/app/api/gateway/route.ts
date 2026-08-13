import { NextRequest } from 'next/server'
import { authenticateApiKey, apiError } from '@/lib/developerAuth'
import {
  createCompletion,
  normalizeMessages,
  toOpenAiChatResponse,
  wrapProviderStreamAsOpenAi,
} from '@/lib/gateway'

export const dynamic = 'force-dynamic'
export const maxDuration = 60

/**
 * Copetra Developer API Gateway
 * POST /api/gateway
 *
 * Auth: Authorization: Bearer <cpk_...>  OR  x-api-key: <cpk_...>
 * Body (OpenAI-compatible):
 *   { model?, messages: [{role, content}], stream?, temperature?, max_tokens?, callback_url? }
 */
export async function POST(req: NextRequest) {
  try {
    const auth = await authenticateApiKey(req)
    if (!auth.ok) return auth.response

    const body = await req.json().catch(() => ({}))
    const messages = normalizeMessages(body)

    if (messages.length === 0) {
      return apiError(
        'Provide "messages" (OpenAI style) or legacy "message" / "prompt".',
        400,
        'empty_payload'
      )
    }

    const stream = body.stream === true
    const model = typeof body.model === 'string' && body.model ? body.model : 'copetra-ai'
    const temperature = typeof body.temperature === 'number' ? body.temperature : 0.5
    const maxTokens = typeof body.max_tokens === 'number' ? body.max_tokens : 2048
    const callbackUrl =
      body.callback_url || body.callbackUrl || body.webhook_url || body.webhookUrl || auth.key.callbackUrl

    // Async webhook mode
    if (callbackUrl && !stream) {
      void (async () => {
        const result = await createCompletion({ messages, temperature, maxTokens, stream: false })
        const answer =
          result.ok && result.stream === false ? result.text : 'Generation failed.'

        await fetch(String(callbackUrl), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'User-Agent': 'Copetra-AI-Callback/2.0',
          },
          body: JSON.stringify({
            event: 'copetra.chat.completion',
            status: result.ok ? 'success' : 'error',
            developer_id: auth.key.userId,
            project: auth.key.projectName,
            key_id: auth.key.id,
            messages,
            response: answer,
            timestamp: new Date().toISOString(),
          }),
        }).catch((err) => console.error('[Callback webhook]', err))
      })()

      return Response.json(
        {
          status: 'accepted',
          event: 'copetra.chat.queued',
          message: 'Request accepted. Response will be POSTed to your callback URL.',
          callback_url: callbackUrl,
          developer_id: auth.key.userId,
          project: auth.key.projectName,
          timestamp: new Date().toISOString(),
        },
        { status: 202 }
      )
    }

    const result = await createCompletion({ messages, temperature, maxTokens, stream })

    if (!result.ok) {
      return apiError(result.message, result.status, result.code, 'api_error')
    }

    if (result.stream) {
      const readable = wrapProviderStreamAsOpenAi(result.response, model)
      return new Response(readable, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache, no-transform',
          Connection: 'keep-alive',
        },
      })
    }

    return Response.json(
      toOpenAiChatResponse({
        model,
        text: result.text,
        usage: result.usage,
        developerId: auth.key.userId,
        projectName: auth.key.projectName,
      })
    )
  } catch (error: any) {
    console.error('[gateway]', error)
    return apiError(error?.message || 'Internal Server Error', 500, 'internal_error', 'api_error')
  }
}
