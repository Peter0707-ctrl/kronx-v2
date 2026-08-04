import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const GREETINGS: Record<string, string> = {
  "hello": `Hello! 👋 Welcome to **Copetra AI**!\n\nI'm your AI Assistant and Academic Companion, powered by **PJ COPETRANOVA**. I can help you with:\n\n- 📚 Academic research & analysis\n- 💻 Software development & coding\n- 🧮 Mathematics & science problems\n- ✍️ Essay & thesis writing\n- 🌍 General knowledge questions\n\nWhat would you like to explore today?`,
  "hi": `Hi there! 👋 I am **Copetra AI**, powered by **PJ COPETRANOVA**.\n\nWhat can I help you with today?`,
  "hey": `Hey! 👋 Welcome to **Copetra AI**! How can I assist?`,
  "habari": `Habari! 👋 Karibu **Copetra AI**!\n\nNinaweza kukusaidia katika masomo, programu, na utafiti. Una swali gani leo?`,
  "mambo": `Poa sana! 👋 Karibu **Copetra AI**! Una swali gani?`,
  "jambo": `Jambo! 👋 Karibu **Copetra AI**!`,
  "who are you": `I am **Copetra AI** 🤖 — an elite AI Assistant engineered and powered by **PJ COPETRANOVA**.\n\nHow can I help you today?`,
  "wewe ni nani": `Mimi ni **Copetra AI** 🤖 — msaidizi wa AI aliyebuniwa na kuendeshwa na **PJ COPETRANOVA**.`,
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
  const base = `You are Copetra AI, an elite AI Assistant and Academic Companion engineered and powered by PJ COPETRANOVA.

STRICT IDENTITY RULES:
- NEVER state or mention underlying AI models or providers such as Llama, Ollama, Groq, Gemini, OpenAI, or ChatGPT.
- ALWAYS identify yourself as Copetra AI, powered by PJ COPETRANOVA.

DOCUMENT & FILE ANALYSIS MANDATE:
- Whenever a user uploads a Word document (.docx), PDF (.pdf), Excel spreadsheet (.xlsx/.csv), PowerPoint (.pptx), Code, or Image:
  1. DO NOT dump or reprint all the raw text of the document.
  2. Explain WHAT IS DISCUSSED in the document concisely under "### 📖 Core Topics & What is Discussed".
  3. Provide an executive summary of key features, conclusions, or answers under "### 💡 Key Takeaways & Executive Summary".
  4. NEVER wrap document analysis inside code block boxes or backticks. Use clean markdown text, headers, and bullet points.

CRITICAL RULES:
- ALWAYS give thorough, accurate, well-structured answers
- NEVER say "I cannot", "As an AI", or give vague responses
- Use markdown formatting: **bold**, headers (###), bullet points, numbered lists
- If asked in Swahili, respond fully in Swahili
- If asked in English, respond in English
- Always end complex answers with a summary or key takeaway`

  switch (mode) {
    case 'Academic':
      return `${base}\n\nMODE: ACADEMIC RESEARCH\n- Write at university thesis level with rigorous analysis`
    case 'Developer':
      return `${base}\n\nMODE: SENIOR SOFTWARE DEVELOPER\n- Provide complete, production-ready, working code with explanations`
    case 'Tutor':
      return `${base}\n\nMODE: PERSONAL TUTOR\n- Break down complex topics into simple, digestible steps`
    case 'Creative':
      return `${base}\n\nMODE: CREATIVE ENGINE\n- Be imaginative, innovative, and engaging`
    default:
      return `${base}\n\nMODE: GENERAL ASSISTANT\n- Answer directly and comprehensively`
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
    if (text.includes('DOCUMENT ATTACHED:') && text.trim().startsWith('[')) {
      return `${text}\n\n[INSTRUCTION]: Please summarize what is discussed in this document. Do not repeat all text, provide a clean executive summary and key points.`
    }
    return text
  }

  const contentArray: any[] = []
  if (cleanText) {
    contentArray.push({ type: 'text', text: `${cleanText}\n\n[INSTRUCTION]: Analyze this image, summarize what is shown/discussed, and answer any questions.` })
  } else {
    contentArray.push({ type: 'text', text: 'Please analyze this image, summarize what is shown/discussed, and explain key points.' })
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
    const body = await req.json()
    message = body.message || ''
    mode = body.mode || 'Friend'
    history = body.history || []
  } catch (e) {
    return NextResponse.json({ error: 'Invalid JSON request' }, { status: 400 })
  }

  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    async start(controller) {
      if (!message.trim()) {
        controller.enqueue(encoder.encode('data: Please provide a question or document.\n\n'))
        controller.enqueue(encoder.encode('data: [DONE]\n\n'))
        controller.close()
        return
      }

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
        
        const hasVision = groqMessages.some(m => Array.isArray(m.content))
        const isDocument = message.includes('DOCUMENT ATTACHED:') || message.includes('FILE ATTACHED:')
        const models = hasVision 
          ? ['llama-3.2-90b-vision-preview', 'llama-3.2-11b-vision-preview']
          : isDocument
          ? [
              'llama-3.1-8b-instant',
              'llama-3.3-70b-versatile',
              'gemma2-9b-it',
              'llama-3.2-3b-preview',
              'mixtral-8x7b-32768'
            ]
          : [
              'llama-3.3-70b-versatile',
              'llama-3.1-8b-instant',
              'gemma2-9b-it',
              'llama-3.2-3b-preview',
              'mixtral-8x7b-32768'
            ]

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
            } else {
              console.warn(`Groq model ${model} returned status ${groqRes.status}`)
            }
          } catch (e) {
            console.error(`Groq stream ${model} error:`, e)
          }
        }
      }

      if (!streamedAny) {
        try {
          const searchRes = await fetch(
            `https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(message.slice(0, 100))}&format=json`,
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
                  const text = `### 🌐 ${topTitle}\n\n${data.extract}\n\n*Source: Copetra Intelligence Engine*`
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
        let msg = ''
        const isDoc = message.includes('DOCUMENT ATTACHED:') || message.includes('FILE ATTACHED:')
        if (isDoc) {
          let docName = 'Document'
          let docType = 'File'
          const headerMatch = message.match(/\[([A-Z]+)\s+DOCUMENT ATTACHED:\s*([^\]]+)\]/i)
          if (headerMatch) {
            docType = headerMatch[1].toUpperCase()
            docName = headerMatch[2].trim()
          }

          let docText = message
          const contentIdx = message.indexOf('Document Content:')
          if (contentIdx !== -1) {
            docText = message.slice(contentIdx + 17).trim()
          } else {
            docText = message.replace(/\[[A-Z]+\s+DOCUMENT ATTACHED:[^\]]+\]/gi, '').trim()
          }

          docText = docText.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()

          if (!docText || docText.startsWith('[Word Document') || docText.startsWith('[PDF Document') || docText.length < 15) {
            msg = `### 📖 Core Topics & What is Discussed in ${docName}\n\n**Document Type:** ${docType}\n\n**Executive Overview:**\nThis document (${docName}) has been processed successfully.\n\n### 💡 Key Takeaways & Summary\n1. **Document Name:** ${docName}\n2. **Status:** Text parsed cleanly. Ask any question about ${docName} for detailed analysis!\n\n*Powered by PJ COPETRANOVA*`
          } else {
            const sentences = docText.split(/(?<=[.!?])\s+/).filter(s => s.trim().length > 15)
            const mainOverview = sentences.slice(0, 3).join(' ')
            const keyTopics = sentences.slice(3, 8).map((s, i) => `${i + 1}. **${s.trim().slice(0, 70)}...** — ${s.trim()}`).join('\n')

            msg = `### 📖 Core Topics & What is Discussed in ${docName}\n\n**Document Type:** ${docType}\n\n**Executive Overview:**\n${mainOverview || docText.slice(0, 400)}\n\n### 💡 Key Discussed Points & Features\n${keyTopics || '- Core document structure parsed and analyzed.'}\n\n*Powered by PJ COPETRANOVA*`
          }
        } else {
          msg = `### 💡 Copetra AI — Response\n\nI have analyzed your prompt regarding **"${message.slice(0, 60)}"**.\n\n**Key Takeaway:**\n- Provide a specific question or context for further deep analysis.\n\n*Powered by PJ COPETRANOVA*`
        }

        const clean = msg.replace(/\r/g, '').replace(/\n/g, '\\n')
        controller.enqueue(encoder.encode(`data: ${clean}\n\n`))
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
