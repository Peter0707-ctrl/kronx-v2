import { NextRequest, NextResponse } from 'next/server'
import { Pool } from 'pg'
import { v4 as uuidv4 } from 'uuid'

export const dynamic = 'force-dynamic'
export const maxDuration = 60

const connectionString = process.env.DATABASE_URL || 'postgresql://postgres:TdoGwPBGGbhiWgarnDevahuPxoehQspt@postgres.railway.internal:5432/railway'

const pool = new Pool({
  connectionString,
})

const GROQ_API_KEYS = [
  process.env.GROQ_API_KEY,
  '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',
  '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',
].filter(Boolean) as string[]

export async function POST(req: NextRequest) {
  try {
    const authHeader = req.headers.get('Authorization') || req.headers.get('authorization')
    const apiKeyHeader = req.headers.get('x-api-key') || req.headers.get('X-Api-Key')
    let apiKey = ''

    if (authHeader && authHeader.startsWith('Bearer ')) {
      apiKey = authHeader.split(' ')[1].trim()
    } else if (apiKeyHeader) {
      apiKey = apiKeyHeader.trim()
    }

    if (!apiKey) {
      return NextResponse.json({
        error: {
          message: 'Unauthorized: Missing API key. Include "Authorization: Bearer <YOUR_KEY>" or "x-api-key: <YOUR_KEY>" header.',
          type: 'invalid_request_error',
          code: 'missing_api_key'
        }
      }, { status: 401 })
    }

    // Query developer by API Key in PostgreSQL
    let developer: any = null
    try {
      const res = await pool.query(
        'SELECT * FROM users WHERE api_key = $1 OR id = $1 LIMIT 1',
        [apiKey]
      )
      if (res.rows.length > 0) {
        developer = res.rows[0]
      }
    } catch (dbErr) {
      console.warn('PostgreSQL query notice:', dbErr)
    }

    // Allow key if found in DB OR matches valid kx-live format OR master admin key
    const isValidKeyFormat = apiKey.startsWith('kx-live-') || apiKey === 'Admin@123' || apiKey === 'e86f78a8a3caf0b60d8e74e5942aa6d86dc150cd3c03338aef25b7d2d7e3acc7'

    if (!developer && !isValidKeyFormat) {
      return NextResponse.json({
        error: {
          message: 'Forbidden: Invalid or unrecognized API Key. Please generate a valid key in Settings > Developer.',
          type: 'invalid_request_error',
          code: 'invalid_api_key'
        }
      }, { status: 403 })
    }

    const developerId = developer?.id || (developer?.email ? developer.email : 'dev_' + apiKey.slice(-6))

    const body = await req.json().catch(() => ({}))
    
    // Support both standard OpenAI properties (messages) and legacy properties (message, prompt, query)
    let messages = body.messages || []
    const legacyPrompt = body.message || body.prompt || body.query

    if (messages.length === 0 && legacyPrompt) {
      messages = [{ role: 'user', content: legacyPrompt }]
    }

    if (messages.length === 0) {
      return NextResponse.json({
        error: {
          message: 'Bad Request: "messages" list or legacy "message"/"prompt" parameter is required.',
          type: 'invalid_request_error',
          code: 'empty_payload'
        }
      }, { status: 400 })
    }

    const stream = body.stream === true
    const model = body.model || 'copetra-ai'
    const temperature = typeof body.temperature === 'number' ? body.temperature : 0.5
    const maxTokens = typeof body.max_tokens === 'number' ? body.max_tokens : 2048

    // Async Webhook Callback compatibility
    const requestCallbackUrl = body.callback_url || body.callbackUrl || body.webhook_url || body.webhookUrl
    const callbackUrl = requestCallbackUrl || developer?.callback_url || developer?.callbackUrl

    const systemPrompt = `You are Copetra AI, an elite academic AI assistant and developer engine powered by PJ COPETRANOVA.
Provide clear, accurate, technically rigorous, and well-structured responses.`

    const formattedMessages = [
      { role: 'system', content: systemPrompt },
      ...messages
    ]

    const groqModels = ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768']
    let activeKey = GROQ_API_KEYS[0] || ''
    let activeModel = groqModels[0]

    // ── IF ASYNCHRONOUS CALLBACK URL IS PROVIDED ──
    if (callbackUrl && !stream) {
      // Async request processing
      const handleAsyncAI = async () => {
        let answer = ''
        for (const apiKey of GROQ_API_KEYS) {
          for (const m of groqModels) {
            try {
              const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                  model: m,
                  messages: formattedMessages,
                  temperature,
                  max_tokens: maxTokens
                }),
                signal: AbortSignal.timeout(20000)
              })
              if (res.ok) {
                const data = await res.json()
                answer = data.choices?.[0]?.message?.content || ''
                if (answer) break
              }
            } catch (e) {
              // try next
            }
          }
          if (answer) break
        }

        const payload = {
          event: 'copetra.chat.completion',
          status: 'success',
          developer_id: developerId,
          messages,
          response: answer || 'Generation completed.',
          timestamp: new Date().toISOString(),
          callback_url: callbackUrl
        }

        await fetch(callbackUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'User-Agent': 'Copetra-AI-Callback-Gateway/2.0'
          },
          body: JSON.stringify(payload)
        }).catch(err => console.error('[Callback Webhook Error]:', err))
      }

      handleAsyncAI()

      return NextResponse.json({
        status: 'accepted',
        event: 'copetra.chat.queued',
        message: 'Request received successfully. Asynchronous AI response will be POSTed to your callback URL.',
        callback_url: callbackUrl,
        developer_id: developerId,
        timestamp: new Date().toISOString()
      }, { status: 202 })
    }

    // ── STREAMING COMPLETION RESPONSE ──
    if (stream) {
      let groqStreamResponse: Response | null = null

      for (const apiKey of GROQ_API_KEYS) {
        for (const m of groqModels) {
          try {
            const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`
              },
              body: JSON.stringify({
                model: m,
                messages: formattedMessages,
                temperature,
                max_tokens: maxTokens,
                stream: true
              }),
              signal: AbortSignal.timeout(15000)
            })

            if (res.ok && res.body) {
              groqStreamResponse = res
              break
            }
          } catch (e) {
            // try next model/key
          }
        }
        if (groqStreamResponse) break
      }

      if (!groqStreamResponse || !groqStreamResponse.body) {
        return NextResponse.json({
          error: {
            message: 'AI provider streaming services are currently overloaded. Please retry in a few seconds.',
            type: 'api_error',
            code: 'service_overloaded'
          }
        }, { status: 503 })
      }

      const reader = groqStreamResponse.body.getReader()
      const decoder = new TextDecoder()
      const encoder = new TextEncoder()
      const createdTimestamp = Math.floor(Date.now() / 1000)
      const chatId = uuidv4()

      let buffer = ''
      const readableStream = new ReadableStream({
        async start(controller) {
          try {
            while (true) {
              const { done, value } = await reader.read()
              if (done) break

              buffer += decoder.decode(value, { stream: true })
              const lines = buffer.split('\n')
              buffer = lines.pop() || ''

              for (const line of lines) {
                const cleanLine = line.trim()
                if (!cleanLine) continue
                if (cleanLine.startsWith('data: ')) {
                  const dataStr = cleanLine.slice(6)
                  if (dataStr === '[DONE]') {
                    controller.enqueue(encoder.encode('data: [DONE]\n\n'))
                    continue
                  }
                  try {
                    const parsed = JSON.parse(dataStr)
                    const content = parsed.choices?.[0]?.delta?.content || ''
                    const finishReason = parsed.choices?.[0]?.finish_reason || null

                    const responseChunk = {
                      id: `chatcmpl-${chatId}`,
                      object: 'chat.completion.chunk',
                      created: createdTimestamp,
                      model,
                      choices: [
                        {
                          index: 0,
                          delta: { content },
                          finish_reason: finishReason
                        }
                      ]
                    }
                    controller.enqueue(encoder.encode(`data: ${JSON.stringify(responseChunk)}\n\n`))
                  } catch (e) {
                    // parse skip
                  }
                }
              }
            }
            controller.close()
          } catch (err: any) {
            controller.error(err)
          }
        }
      })

      return new Response(readableStream, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache, no-transform',
          'Connection': 'keep-alive',
          'Content-Encoding': 'none',
        }
      })
    }

    // ── SYNCHRONOUS RESPONSE ──
    let completionText = ''
    let usageData = { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 }

    for (const apiKey of GROQ_API_KEYS) {
      for (const m of groqModels) {
        try {
          const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${apiKey}`
            },
            body: JSON.stringify({
              model: m,
              messages: formattedMessages,
              temperature,
              max_tokens: maxTokens
            }),
            signal: AbortSignal.timeout(20000)
          })

          if (res.ok) {
            const data = await res.json()
            completionText = data.choices?.[0]?.message?.content || ''
            usageData = data.usage || usageData
            if (completionText) break
          }
        } catch (e) {
          // try next
        }
      }
      if (completionText) break
    }

    if (!completionText) {
      return NextResponse.json({
        error: {
          message: 'Failed to generate response. All upstream providers timed out.',
          type: 'api_error',
          code: 'upstream_timeout'
        }
      }, { status: 504 })
    }

    const responsePayload: any = {
      id: `chatcmpl-${uuidv4()}`,
      object: 'chat.completion',
      created: Math.floor(Date.now() / 1000),
      model,
      choices: [
        {
          index: 0,
          message: {
            role: 'assistant',
            content: completionText
          },
          finish_reason: 'stop'
        }
      ],
      usage: usageData
    }

    // Retain legacy compatibility with "response" property
    responsePayload.response = completionText
    responsePayload.status = 'success'
    responsePayload.developer_id = developerId

    return NextResponse.json(responsePayload)

  } catch (error: any) {
    console.error('API Gateway Error:', error)
    return NextResponse.json({
      error: {
        message: error?.message || 'Internal Server Error',
        type: 'api_error',
        code: 'internal_error'
      }
    }, { status: 500 })
  }
}
