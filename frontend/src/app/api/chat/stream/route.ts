import { NextRequest } from 'next/server'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const GREETINGS: Record<string, string> = {
  "hello": `Hello! 👋 Welcome to **Copetra AI**!\n\nI'm your AI Assistant and Academic Companion, engineered by PJ Copetranova and powered by **Llama 3.3 (70B)**. I can help you with:\n\n- 📚 Academic research & analysis\n- 💻 Software development & coding\n- 🧮 Mathematics & science problems\n- ✍️ Essay & thesis writing\n- 🌍 General knowledge questions\n\nWhat would you like to explore today?`,
  "hi": `Hi there! 👋 I am **Copetra AI**, powered by Llama 3.3 (70B).\n\nWhat can I help you with today?`,
  "hey": `Hey! 👋 Welcome to **Copetra AI**! How can I assist?`,
  "habari": `Habari! 👋 Karibu **Copetra AI**!\n\nNinaweza kukusaidia katika masomo, programu, na utafiti. Una swali gani leo?`,
  "mambo": `Poa sana! 👋 Karibu **Copetra AI**! Una swali gani?`,
  "jambo": `Jambo! 👋 Karibu **Copetra AI**!`,
  "who are you": `I am **Copetra AI** 🤖 — an elite AI Assistant engineered by **PJ Copetranova**, powered by **Llama 3.3 (70B)** on Groq's GPU infrastructure.\n\nHow can I help you today?`,
  "wewe ni nani": `Mimi ni **Copetra AI** 🤖 — msaidizi wa AI aliyebuniwa na **PJ Copetranova**, nikitumia **Llama 3.3 (70B)**.`,
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
  const base = `You are Copetra AI, an elite AI Assistant and Academic Companion engineered by PJ Copetranova. You are powered by Llama 3.3 (70B).

CRITICAL RULES:
- ALWAYS give thorough, accurate, well-structured answers
- NEVER say "I cannot", "As an AI", or give vague responses
- Use markdown formatting: **bold**, headers (###), bullet points, numbered lists
- If asked about a topic, provide deep, detailed knowledge
- If asked in Swahili, respond fully in Swahili
- If asked in English, respond in English
- Always end complex answers with a summary or key takeaway`

  switch (mode) {
    case 'Academic':
      return `${base}\n\nMODE: ACADEMIC RESEARCH\n- Write at university thesis level with rigorous analysis\n- Structure: Introduction → Core Concepts → Analysis → Examples → Conclusion\n- Include relevant theories, frameworks, and academic perspectives\n- Use proper terminology and comprehensive coverage`
    case 'Developer':
      return `${base}\n\nMODE: SENIOR SOFTWARE DEVELOPER\n- Provide complete, production-ready, working code\n- Always include: code explanation, usage examples, edge cases\n- Follow best practices, clean code, and SOLID principles\n- Include error handling in all code examples`
    case 'Tutor':
      return `${base}\n\nMODE: PERSONAL TUTOR\n- Break down complex topics into simple, digestible steps\n- Use real-world analogies and relatable examples\n- Address common misconceptions proactively\n- Use encouraging, supportive language`
    case 'Creative':
      return `${base}\n\nMODE: CREATIVE ENGINE\n- Be imaginative, innovative, and engaging\n- Use vivid language, metaphors, and storytelling`
    default:
      return `${base}\n\nMODE: GENERAL ASSISTANT\n- Answer directly and comprehensively\n- Provide context, examples, and explanations\n- Match depth of answer to complexity of the question`
  }
}

type HistoryMessage = { role: 'user' | 'ai' | 'assistant'; content: string }

function parseMessageContent(text: string): any {
  const imageRegex = /\[IMAGE: (data:image\/[a-zA-Z]+;base64,[^\]]+)\]/g
  const images: string[] = []
  let cleanText = text

  let match
  while ((match = imageRegex.exec(text)) !== null) {
    images.push(match[1])
    cleanText = cleanText.replace(match[0], '').trim()
  }

  if (images.length === 0) {
    return text
  }

  const contentArray: any[] = []
  if (cleanText) {
    contentArray.push({ type: 'text', text: cleanText })
  } else {
    contentArray.push({ type: 'text', text: 'Please analyze this image.' })
  }

  for (const img of images) {
    contentArray.push({ type: 'image_url', image_url: { url: img } })
  }

  return contentArray
}

function buildGroqMessages(
  message: string,
  mode: string,
  history: HistoryMessage[] = []
): { role: string; content: any }[] {
  const messages: { role: string; content: any }[] = [
    { role: 'system', content: getModeSystemPrompt(mode) }
  ]
  const recentHistory = history.slice(-6)
  for (const h of recentHistory) {
    if (h.role === 'user') {
      messages.push({ role: 'user', content: parseMessageContent(h.content) })
    } else if ((h.role === 'ai' || h.role === 'assistant') && h.content) {
      messages.push({ role: 'assistant', content: h.content })
    }
  }
  messages.push({ role: 'user', content: parseMessageContent(message) })
  return messages
}

export async function POST(req: NextRequest) {
  let message = '', mode = 'Friend'
  let history: HistoryMessage[] = []

  try {
    const body = await req.json().catch(() => ({}))
    message = body.message || ''
    mode = body.mode || 'Friend'
    history = body.history || []
  } catch { }

  if (!message) message = 'Hello'

  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    async start(controller) {
      controller.enqueue(encoder.encode(': pjkronx-stream-open\n\n'))

      const instant = searchInstant(message)
      if (instant) {
        const clean = instant.replace(/\r/g, '').replace(/\n/g, '\\n')
        controller.enqueue(encoder.encode(`data: ${clean}\n\n`))
        controller.enqueue(encoder.encode('data: [DONE]\n\n'))
        controller.close()
        return
      }

      const apiKey = process.env.GROQ_API_KEY
      let streamedAny = false

      if (apiKey) {
        const groqMessages = buildGroqMessages(message, mode, history)
        
        // If any message has an array content (which means it contains an image), force the Vision model
        const hasVision = groqMessages.some(m => Array.isArray(m.content))
        
        const models = hasVision 
          ? ['llama-3.2-90b-vision-preview', 'llama-3.2-11b-vision-preview']
          : ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'gemma2-9b-it']

        for (const model of models) {
          if (streamedAny) break
          try {
            const abortCtrl = new AbortController()
            const timeoutMs = model.includes('70b') || model.includes('90b') ? 30000 : 20000
            setTimeout(() => abortCtrl.abort(), timeoutMs)

            const groqRes = await fetch('https://api.groq.com/openai/v1/chat/completions', {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                model,
                messages: groqMessages,
                max_tokens: 2048,
                temperature: 0.7,
                top_p: 0.9,
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
        const msg = `**Copetra AI** is experiencing a temporary issue. Please try again in a moment.`.replace(/\n/g, '\\n')
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
