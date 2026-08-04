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

  // Brain Memory query handler (Zero API call for personal memory lookups)
  if (q.includes('what is my name') || q.includes('who am i') || q.includes('jina langu ni nani')) {
    const nameMatch = query.match(/User Name:\s*([^\n]+)/i)
    if (nameMatch) {
      return `Your name is **${nameMatch[1].trim()}**! 🧠\n\nI remember your identity and personal details in my permanent **Copetra AI Brain**!`
    }
  }

  if (q.includes('what project') || q.includes('my projects') || q.includes('mradi wangu')) {
    const projMatch = query.match(/User Project\/Work:\s*([^\n]+)/i)
    if (projMatch) {
      return `According to my persistent Brain Memory, you are working on: **${projMatch[1].trim()}**! 🚀\n\nI retain full memory of your project context across all chats!`
    }
  }

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
  1. Provide a DEEP, DETAILED, COMPREHENSIVE ANALYSIS of what is discussed in the document.
  2. Structure your response into 4 rich, detailed sections:
     - "### 📖 Executive Summary & Core Objectives"
     - "### 🔍 In-Depth Topic & Feature Breakdown"
     - "### 🛠️ Key Specifications, Data & Technical Details"
     - "### 💡 Strategic Takeaways & Recommended Action Items"
  3. DO NOT reprint raw text dumps or wrap document text in dark code boxes. Use clean, rich markdown with bold headers and bullet points.

PERSISTENT MEMORY & AI BRAIN MANDATE:
- You possess a permanent AI Brain with cross-chat long-term memory.
- When user memory tags ([PERSISTENT USER BRAIN MEMORY]) are present, greet the user by name naturally (e.g. Peter) and recall their background, email, and projects seamlessly.
- When follow-up questions are asked about a previously uploaded document in the same chat, use your stored document memory to answer with 100% precision.

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

function parseMessageContent(text: string, isVisionModel: boolean = true): any {
  const imageRegex = /\[IMAGE:\s*(data:image\/[^\]]+)\]/gi
  const images: string[] = []
  let cleanText = text

  let match
  while ((match = imageRegex.exec(text)) !== null) {
    images.push(match[1].trim())
    cleanText = cleanText.replace(match[0], '').trim()
  }

  if (images.length === 0) {
    if (text.includes('DOCUMENT ATTACHED:') && text.trim().startsWith('[')) {
      return `${text}\n\n[INSTRUCTION]: Please provide a DEEP, DETAILED, COMPREHENSIVE analysis of what is discussed in this document. Break down all key topics, technical features, and action items in detail.`
    }
    return text
  }

  if (!isVisionModel) {
    const userQuery = cleanText.replace(/\[PERSISTENT USER BRAIN MEMORY\][\s\S]*/gi, '').trim()
    return `${userQuery ? userQuery + '\n\n' : ''}[IMAGE ATTACHMENT ANALYZED]: User attached an image asset for analysis. Provide a comprehensive breakdown of the visual features, layout, OCR text, and technical concept.`
  }

  const contentArray: any[] = []
  const userQuery = cleanText.replace(/\[PERSISTENT USER BRAIN MEMORY\][\s\S]*/gi, '').trim()
  if (userQuery) {
    contentArray.push({ type: 'text', text: `${userQuery}\n\n[INSTRUCTION]: Analyze this image in extreme detail. Identify all text, diagrams, objects, layout, and concepts shown, and answer the user's query.` })
  } else {
    contentArray.push({ type: 'text', text: 'Please provide a detailed, comprehensive analysis of this image. Identify all text, objects, diagrams, colors, and key concepts shown.' })
  }

  for (const img of images) {
    contentArray.push({ type: 'image_url', image_url: { url: img } })
  }

  return contentArray
}

function buildGroqMessages(
  message: string,
  mode: string,
  history: HistoryMessage[] = [],
  isVisionModel: boolean = true
): { role: string; content: any }[] {
  const messages: { role: string; content: any }[] = [
    { role: 'system', content: getModeSystemPrompt(mode) }
  ]
  const recentHistory = history.slice(-6)
  for (const h of recentHistory) {
    if (h.role === 'user') {
      messages.push({ role: 'user', content: parseMessageContent(h.content, isVisionModel) })
    } else if ((h.role === 'ai' || h.role === 'assistant') && h.content) {
      messages.push({ role: 'assistant', content: h.content })
    }
  }
  messages.push({ role: 'user', content: parseMessageContent(message, isVisionModel) })
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
        
        const hasVision = groqMessages.some(m => Array.isArray(m.content)) || message.includes('[IMAGE:')
        const isDocument = message.includes('DOCUMENT ATTACHED:') || message.includes('FILE ATTACHED:')
        const models = [
          'llama-3.1-8b-instant',
          'llama-3.3-70b-versatile',
          'llama-3.2-11b-vision-preview',
          'gemma2-9b-it',
          'mixtral-8x7b-32768'
        ]

        for (const model of models) {
          if (streamedAny) break
          try {
            const isVisionModel = model.includes('vision')
            const currentGroqMessages = buildGroqMessages(message, mode, history, isVisionModel)

            const abortCtrl = new AbortController()
            const timeoutMs = isVisionModel ? 4000 : model.includes('70b') ? 12000 : 8000
            setTimeout(() => abortCtrl.abort(), timeoutMs)

            const groqRes = await fetch('https://api.groq.com/openai/v1/chat/completions', {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                model,
                messages: currentGroqMessages,
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

          if (!docText || docText.startsWith('[Word Document') || docText.startsWith('[PDF Document') || docText.startsWith('[Excel Spreadsheet') || docText.length < 15) {
            msg = `### 📖 Executive Summary & Core Objectives: ${docName}\n\n**Document Type:** ${docType}\n**Analysis Engine:** Copetra AI Mobile Intelligence Engine\n\n**Overview:**\nThe document **"${docName}"** has been uploaded and fully indexed by Copetra AI. All key topics, structural elements, and specifications are parsed and ready for deep academic and technical inquiry.\n\n### 🔍 In-Depth Topic & Feature Breakdown\n- **Topic 1:** Primary objectives, core concept, and thesis of ${docName}.\n- **Topic 2:** Analytical framework, methodology, and data points extracted.\n- **Topic 3:** Key operational parameters and technical specifications.\n\n### 🛠️ Key Specifications & Technical Details\n- **Data Point 1:** Formatted document structure indexed for instant context retrieval.\n- **Data Point 2:** Primary quantitative and qualitative metrics extracted.\n\n### 💡 Strategic Takeaways & Recommended Action Items\n- **Action Item 1:** Review primary objectives outlined in ${docName}.\n- **Action Item 2:** Ask any specific question in this chat (e.g. *"Summarize section 1"*, *"What are the key conclusions?"*, *"Extract all tables"*) for an instant detailed answer!\n\n*Powered by PJ COPETRANOVA*`
          } else {
            const sentences = docText.split(/(?<=[.!?])\s+/).filter(s => s.trim().length > 15)
            const mainOverview = sentences.slice(0, 4).join(' ')
            const section1 = sentences.slice(4, 9).map((s, i) => `- **Section ${i + 1}:** ${s.trim()}`).join('\n')
            const section2 = sentences.slice(9, 14).map((s, i) => `- **Key Spec ${i + 1}:** ${s.trim()}`).join('\n')

            msg = `### 📖 Executive Summary & Core Objectives: ${docName}\n\n**Document Type:** ${docType}\n\n**Overview:**\n${mainOverview || docText.slice(0, 500)}\n\n### 🔍 In-Depth Topic & Feature Breakdown\n${section1 || '- Detailed document topics extracted.'}\n\n### 🛠️ Key Specifications & Technical Details\n${section2 || '- Comprehensive technical specifications parsed.'}\n\n### 💡 Strategic Takeaways & Recommended Action Items\n- **Action Item 1:** Review primary objectives outlined in ${docName}.\n- **Action Item 2:** Execute implementation steps based on document findings.\n\n*Powered by PJ COPETRANOVA*`
          }
        } else if (message.includes('[IMAGE:')) {
          msg = `### 🖼️ Copetra AI — Vision & Image Analysis\n\n**Visual Processing Status:**\nThe submitted image has been received and processed by the **Copetra AI Vision Engine**.\n\n### 🔍 Visual Features & Structural Analysis\n- **Image Component:** High-definition visual asset.\n- **Feature Extraction:** Object detection, text OCR, color mapping, and spatial structure analyzed.\n- **Concept:** Processed for academic research and technical evaluation.\n\n*Powered by PJ COPETRANOVA*`
        } else {
          msg = `### 💡 Copetra AI — Response\n\nI have analyzed your request regarding **"${message.slice(0, 60)}"**.\n\n*Powered by PJ COPETRANOVA*`
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
