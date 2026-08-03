import { NextRequest } from 'next/server'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const GREETINGS: Record<string, string> = {
  "hello": `Hello! 👋 Welcome to **Copetra AI**, your AI Assistant engineered by PJ Copetranova. How can I help you today?`,
  "hi": `Hi there! 👋 I am **Copetra AI**. What can I help you with?`,
  "hey": `Hey! 👋 Welcome to **Copetra AI**! How can I assist?`,
  "habari": `Habari! 👋 Karibu **Copetra AI**! Ninaweza kukusaidia nini?`,
  "mambo": `Poa! 👋 Karibu **Copetra AI**!`,
  "jambo": `Jambo! 👋 Karibu **Copetra AI**!`,
  "who are you": `I am **Copetra AI**, an elite AI Assistant and Academic Companion engineered by PJ Copetranova, powered by **Llama 3.2** via Groq.`,
}

function searchInstant(query: string): string | null {
  const q = query.toLowerCase().trim()
  if (GREETINGS[q]) return GREETINGS[q]
  for (const [k, v] of Object.entries(GREETINGS)) {
    if (q === k || q.startsWith(k + ' ') || q.endsWith(' ' + k)) return v
  }
  return null
}

function getModeSystemPrompt(mode: string): string {
  switch (mode) {
    case 'Academic':
      return 'You are Copetra AI in ACADEMIC RESEARCH MODE. Provide rigorous academic analysis with structured headings, definitions, and step-by-step explanations. Use markdown formatting.'
    case 'Developer':
      return 'You are Copetra AI in SENIOR DEVELOPER MODE. Provide production-ready code with best practices and clear explanations.'
    case 'Tutor':
      return 'You are Copetra AI in PERSONAL TUTOR MODE. Explain topics clearly with analogies, examples, and practice questions.'
    case 'Creative':
      return 'You are Copetra AI in CREATIVE MODE. Provide imaginative, engaging, and eloquent responses.'
    default:
      return 'You are Copetra AI, an elite AI Assistant and Academic Companion engineered by PJ Copetranova. Answer clearly, accurately and thoroughly using markdown formatting with headings and bullet points.'
  }
}

export async function POST(req: NextRequest) {
  let message = '', mode = 'Friend'
  try {
    const body = await req.json().catch(() => ({}))
    message = body.message || ''
    mode = body.mode || 'Friend'
  } catch { }

  if (!message) message = 'Hello'

  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    async start(controller) {
      // Keep-alive immediately
      controller.enqueue(encoder.encode(': pjkronx-stream-open\n\n'))

      // 1. Instant greetings
      const instant = searchInstant(message)
      if (instant) {
        const clean = instant.replace(/\r/g, '').replace(/\n/g, '\\n')
        controller.enqueue(encoder.encode(`data: ${clean}\n\n`))
        controller.enqueue(encoder.encode('data: [DONE]\n\n'))
        controller.close()
        return
      }

      // 2. Groq streaming — Llama 3.2 on GPU
      const apiKey = process.env.GROQ_API_KEY
      let streamedAny = false

      if (apiKey) {
        const models = ['llama-3.1-8b-instant', 'llama3-8b-8192', 'gemma2-9b-it', 'llama-3.3-70b-versatile']
        const systemPrompt = getModeSystemPrompt(mode)

        for (const model of models) {
          if (streamedAny) break
          try {
            const abortCtrl = new AbortController()
            setTimeout(() => abortCtrl.abort(), 25000)

            const groqRes = await fetch('https://api.groq.com/openai/v1/chat/completions', {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                model,
                messages: [
                  { role: 'system', content: systemPrompt },
                  { role: 'user', content: message },
                ],
                max_tokens: 1024,
                temperature: 0.7,
                stream: true,
              }),
              signal: abortCtrl.signal,
              cache: 'no-store',
            })

            if (groqRes.ok && groqRes.body) {
              const reader = groqRes.body.getReader()
              const decoder = new TextDecoder('utf-8')
              let buffer = ''

              while (true) {
                const { done, value } = await reader.read()
                if (done) break
                buffer += decoder.decode(value, { stream: true })
                const lines = buffer.split('\n')
                buffer = lines.pop() ?? ''

                for (const line of lines) {
                  const trimmed = line.trim()
                  if (!trimmed.startsWith('data: ')) continue
                  const jsonStr = trimmed.slice(6)
                  if (jsonStr === '[DONE]') break
                  try {
                    const parsed = JSON.parse(jsonStr)
                    const token = parsed.choices?.[0]?.delta?.content
                    if (token) {
                      streamedAny = true
                      const clean = token.replace(/\r/g, '').replace(/\n/g, '\\n')
                      controller.enqueue(encoder.encode(`data: ${clean}\n\n`))
                    }
                  } catch { }
                }
              }
            }
          } catch (e) {
            console.error(`Groq stream ${model} error:`, e)
          }
        }
      }

      // 3. Wikipedia fallback
      if (!streamedAny) {
        try {
          const searchRes = await fetch(
            `https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(message)}&format=json`,
            { headers: { 'User-Agent': 'Copetra-AI/2.0' }, cache: 'no-store' }
          )
          if (searchRes.ok) {
            const searchData = await searchRes.json()
            const topTitle = searchData.query?.search?.[0]?.title
            if (topTitle) {
              const summaryRes = await fetch(
                `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(topTitle)}`,
                { headers: { 'User-Agent': 'Copetra-AI/2.0' }, cache: 'no-store' }
              )
              if (summaryRes.ok) {
                const data = await summaryRes.json()
                if (data.extract) {
                  const text = `### 🌐 ${topTitle}\n\n${data.extract}\n\n*Source: Wikipedia*`
                  const clean = text.replace(/\r/g, '').replace(/\n/g, '\\n')
                  controller.enqueue(encoder.encode(`data: ${clean}\n\n`))
                  streamedAny = true
                }
              }
            }
          }
        } catch { }
      }

      if (!streamedAny) {
        const msg = `**Copetra AI** — Please add your GROQ_API_KEY in Railway environment variables to enable AI responses.`.replace(/\n/g, '\\n')
        controller.enqueue(encoder.encode(`data: ${msg}\n\n`))
      }

      controller.enqueue(encoder.encode('data: [DONE]\n\n'))
      controller.close()
    }
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache, no-transform',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',
    }
  })
}
