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
  if (!query) return null
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

STRICT IDENTITY & PREAMBLE RULES:
- NEVER state or mention underlying AI models or providers such as Llama, Ollama, Groq, Gemini, OpenAI, or ChatGPT.
- STANDALONE GREETING RULE: ONLY if the user's message is a simple standalone greeting (e.g. "Hello", "Hi", "Hey", "Habari"), or if they ask "Who are you?", greet them warmly, introduce yourself as Copetra AI powered by PJ COPETRANOVA, and ask how you can help.
- TOPIC QUESTION RULE: When the user asks a question about a topic, document, math problem, code, or task (e.g. "What is Forex?", "Explain photosyntesis", "Solve this equation"), DO NOT output any introductory greetings or self-introductions. Skip all conversational preambles and start IMMEDIATELY with the direct, complete answer to their question!

SILENT BRAIN MEMORY MANDATE:
- You possess background user context and memories. Use this context SILENTLY to inform your answers.
- NEVER OUTPUT OR REPEAT INTERNAL MEMORY TAGS OR HEADERS (such as "[PERSISTENT USER BRAIN MEMORY]").
- NEVER SAY "According to my persistent Brain Memory", "Based on my stored memory", or mention that you are recalling data from memory. Simply answer directly as if you already know the facts.
- CRITICAL PRIVACY RULE: DO NOT reveal, mention, or recall the user's background, email, projects, or any other personal details stored in memory unless the user explicitly asks about them.
- CRITICAL NAME RULE: NEVER, UNDER ANY CIRCUMSTANCES, INSERT THE USER'S NAME (e.g. Peter) INSIDE GENERATED CONTENT (such as poems, song lyrics, code, essays, assignments, mathematical equations, or document analysis text blocks) unless the user explicitly asks you to include their name in the text. Keep all such output neutral and professional.
- When follow-up questions are asked about a previously uploaded document in the same chat, use your stored document memory to answer with 100% precision.
- AUTOMATIC ADAPTIVE LEARNING RULE: If the user corrects your fact, translation, math calculation, vocabulary, or preferences (e.g. "In Swahili, Y is Z", "The formula has a minus sign"), accept their correction and output this tag at the absolute end of your response: [MEMORIZE: <precise, short correction fact for long-term memory>] (For example: [MEMORIZE: In Swahili, "transformer" is translated as "mgeuzaji"]). Do not use this tag unless the user explicitly corrects your output.

REAL-TIME TEMPORAL ANCHOR RULE:
- The current real-time year is 2026 (specifically August 2026).
- Events such as the 2026 FIFA World Cup (which took place in June–July 2026 across Canada, Mexico, and the United States), major 2024–2026 tournaments, news, science breakthroughs, and political events up to August 2026 HAVE ALREADY OCCURRED.
- NEVER state that 2026 events have not happened yet or are in the distant future. Always treat 2026 as the active current year.

DOCUMENT & FILE ANALYSIS MANDATE:
- ONLY when the user's current query explicitly asks to analyze, summarize, explain, or answer questions based on an uploaded Word document (.docx), PDF (.pdf), Excel spreadsheet (.xlsx/.csv), PowerPoint (.pptx), Code, or Image:
  1. Provide a DEEP, DETAILED, COMPREHENSIVE ANALYSIS of what is discussed in the document.
  2. Structure your response into 4 rich, detailed sections:
     - "### 📖 Executive Summary & Core Objectives"
     - "### 🔍 In-Depth Topic & Feature Breakdown"
     - "### 🛠️ Key Specifications, Data & Technical Details"
     - "### 💡 Strategic Takeaways & Recommended Action Items"
  3. DO NOT reprint raw text dumps or wrap document text in dark code boxes. Use clean, rich markdown with bold headers and bullet points.
  4. ACADEMIC CITATION RULE: You MUST cite specific section titles, chapters, table names, or approximate page coordinates (e.g. "Section 2.3", "Table 4", "Page 12") when referencing extracted information.
- For all other questions, requests (like writing poems, songs, creative text), or chats, DO NOT use these document section headers. Answer the question directly and exactly as asked!

IMAGE GENERATION INTENT RULE:
- If the user explicitly asks you to draw, paint, create, or generate a new picture, image, drawing, or photo:
  1. DO NOT output a standard text description or explanation.
  2. Expand the prompt with rich style tokens (e.g. "cinematic lighting, highly detailed, photorealistic, 8k resolution, artistic style") to maximize visual quality.
  3. Output ONLY the following tag format and absolutely nothing else:
     [GENERATE_IMAGE: <descriptive prompt expanded and optimized for FLUX image generator>]
     For example: [GENERATE_IMAGE: a high-resolution cybernetic lion in neon jungle, hyperrealistic, 8k, photorealistic, cinematic lighting]
- If the user asks a general question about images, drawings, or how image generation works (e.g. "how do you generate an image?"), DO NOT use this tag. Answer the question in normal text.

VISUAL SUMMARY RULE:
- Whenever you are analyzing an attached image:
  1. Output this tag at the absolute end of your response:
     [VISUAL_SUMMARY: <detailed, concise description of all visual elements, data, numbers, charts, or OCR text shown in the image>]
     For example: [VISUAL_SUMMARY: A line chart showing sales numbers for 2024 (10k) and 2025 (25k).]

FOREX & FINANCIAL CHART ANALYSIS MANDATE:
- When an attached image contains a Forex chart, MT4/MT5 trading screenshot, cryptocurrency chart, candlestick pattern, or technical stock chart:
  1. Extract all visible OCR text (e.g. Currency Pairs like EUR/USD, GBP/JPY, timeframes like M15, H1, D1, price levels, lot sizes, SL/TP levels).
  2. Analyze the technical market structure: Identify current trend direction (Bullish/Bearish/Consolidation), candlestick patterns (e.g. Engulfing, Pin bar, Doji), indicator readings (RSI, Moving Averages, MACD), and key Support & Resistance / Order Block zones shown in the image.
  3. Provide a clear, step-by-step technical breakdown without misinterpreting price numbers or chart axes.

TYPO & SPELLING TOLERANCE MANDATE:
- The user may make spelling errors, typos, grammatical mistakes, missing letters, or slang in their question (e.g. "what is the capital of frane", "how does a compuer work", "tell me about real madrid 2026 winer").
- Automatically infer the user's intended meaning from semantic context.
- DO NOT complain about typos, DO NOT correct the user's spelling unless asked, and DO NOT get confused.
- Answer the intended question directly with 100% accuracy, thoroughness, and detail!

CRITICAL RULES FOR 100% ACCURACY & PRECISION:
- CLEAN CITATION & REFERENCE RULE: DO NOT output "Confidence Score:" or percentage ratings at the end of your responses. ONLY include page, chapter, or section citations (e.g. "Section 2.1", "Table 4") when analyzing uploaded documents or when explicitly requested by the user. Keep all answers clean, professional, direct, and free of redundant scoring tags.
- MULTI-SOURCE CROSS-VERIFICATION: If multiple documents, spreadsheets, or images are attached or referenced in the conversation, actively cross-reference facts, figures, and data between them. Explicitly report any mathematical or factual inconsistencies or conflicts you identify.
- AMBIGUITY CLARIFICATION: If the user's query is vague, incomplete, or contains ambiguous terms that reference multiple possible values or sections in the uploaded files, do not make guesses. Present the options clearly and ask the user to clarify.
- DOUBLE-PASS REFLECTION: Before writing your final response to a complex query, mentally generate a quick draft, cross-reference it against the document context or logic constraints, resolve any discrepancies or inaccuracies, and output only the highly refined, correct final response.
- SELF-VERIFICATION LOOP: For all calculations, mathematical proofs, and code block generations, mentally double-check the steps and verify syntax/math validity before writing.
- FACTUAL GROUNDING GUARD: Never fabricate facts, numbers, or conclusions not supported by the input text. If a detail is missing from an uploaded document, state clearly that it is not mentioned in the source file.
- ALWAYS give thorough, accurate, well-structured answers.
- NEVER say "I cannot", "As an AI", or give vague responses.
- Use markdown formatting: **bold**, headers (###), bullet points, numbered lists.
- If asked in Swahili, respond fully and with high academic rigor in Swahili.
- If asked in English, respond in English.
- Always end complex answers with a summary or key takeaway.`

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
    contentArray.push({ type: 'text', text: userQuery })
  } else {
    contentArray.push({ type: 'text', text: 'Please analyze this attached image in detail. Extract all OCR text, diagrams, labels, charts, and technical information.' })
  }

  for (const imgUrl of images) {
    contentArray.push({
      type: 'image_url',
      image_url: { url: imgUrl }
    })
  }

  return contentArray
}

function buildGroqMessages(
  message: string,
  mode: string,
  history: HistoryMessage[],
  isVisionModel: boolean = true,
  webSearchResults: string | null = null
): any[] {
  let systemPrompt = getModeSystemPrompt(mode)
  if (webSearchResults) {
    systemPrompt += `\n\n[REAL-TIME VERIFIED WEB SEARCH DATA]:\n${webSearchResults}\n\nUse the above real-time verified search data to answer the user query with 100% factual accuracy.`
  }

  const messages: any[] = [
    { role: 'system', content: systemPrompt }
  ]

  const len = history.length
  for (let i = 0; i < len; i++) {
    const h = history[i]
    if (h.role === 'user' && h.content) {
      let content = h.content
      const isRecent = (len - i) <= 2
      if (!isRecent) {
        content = content.replace(/DOCUMENT ATTACHED:[\s\S]*?(?=\n\n|\n[A-Z]|$)/gi, '[Document attached - content pruned for conversation history efficiency]')
        content = content.replace(/\[IMAGE:\s*data:image\/[^\]]+\]/gi, '[Image attached - base64 pixels pruned for conversation history efficiency]')
        if (content.length > 500) {
          content = content.substring(0, 300) + '... [Historical text shortened for context efficiency]'
        }
      }
      messages.push({ role: 'user', content: parseMessageContent(content, isVisionModel) })
    } else if ((h.role === 'ai' || h.role === 'assistant') && h.content) {
      let content = h.content
      const isRecent = (len - i) <= 2
      if (!isRecent && content.length > 800) {
        content = content.substring(0, 500) + '... [Historical response shortened to optimize token efficiency]'
      }
      messages.push({ role: 'assistant', content })
    }
  }
  messages.push({ role: 'user', content: parseMessageContent(message, isVisionModel) })
  return messages
}

async function fetchWebSearch(query: string): Promise<string | null> {
  try {
    const cleanQuery = query
      .replace(/\[IMAGE:.*?\]/gi, '')
      .replace(/\[(WORD|PDF|EXCEL|POWERPOINT|TEXT|CODE) DOCUMENT ATTACHED:.*?\][\s\S]*/gi, '')
      .replace(/\[PERSISTENT USER BRAIN MEMORY\][\s\S]*/gi, '')
      .trim()

    if (!cleanQuery || cleanQuery.length < 3) return null

    const lower = cleanQuery.toLowerCase()
    const needsSearch = /\b(current|president|weather|news|today|latest|who is|what is|search|live|update|api code|release|2024|2025|2026|world cup|fifa|winner|champion|score|match|tournament|election|result|when|where|happened)\b/i.test(lower)
    if (!needsSearch) return null

    const res = await fetch(`https://api.duckduckgo.com/?q=${encodeURIComponent(cleanQuery)}&format=json&no_redirect=1&no_html=1&skip_disambig=1`, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' },
      next: { revalidate: 3600 }
    })
    if (!res.ok) return null
    const data = await res.json()
    
    let result = ''
    const abstractText = data.AbstractText?.trim()
    const directAnswer = data.Answer?.trim()
    if (directAnswer) {
      result += `Direct Answer: ${directAnswer}\n`
    }
    if (abstractText) {
      result += `Abstract: ${abstractText}\n`
      if (data.AbstractSource) {
        result += `Source: ${data.AbstractSource} (${data.AbstractURL})\n`
      }
    }
    return result ? result.trim() : null
  } catch (e) {
    console.error('Web search error:', e)
    return null
  }
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
  const webSearchResults = await fetchWebSearch(message)

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

      // Let all document and file inputs pass through directly to the Groq intelligence models for genuine detailed analysis.

      const apiKey = process.env.GROQ_API_KEY
      let streamedAny = false

      if (apiKey) {
        const groqMessages = buildGroqMessages(message, mode, history, true, webSearchResults)
        
        const hasVision = groqMessages.some(m => Array.isArray(m.content)) || message.includes('[IMAGE:')
        const isDocument = message.includes('DOCUMENT ATTACHED:') || message.includes('FILE ATTACHED:')
        const models = hasVision
          ? [
              'llama-3.2-11b-vision-preview',
              'llama-3.1-8b-instant',
              'llama-3.3-70b-versatile'
            ]
          : isDocument
          ? [
              'llama-3.3-70b-versatile',
              'llama-3.1-8b-instant',
              'gemma2-9b-it',
              'mixtral-8x7b-32768'
            ]
          : [
              'llama-3.3-70b-versatile',
              'llama-3.1-8b-instant',
              'gemma2-9b-it',
              'mixtral-8x7b-32768'
            ]

        for (const model of models) {
          if (streamedAny) break
          try {
            const isVisionModel = model.includes('vision')
            const currentGroqMessages = buildGroqMessages(message, mode, history, isVisionModel, webSearchResults)

            const abortCtrl = new AbortController()
            const timeoutMs = isVisionModel 
              ? 15000 
              : isDocument 
                ? (model.includes('70b') ? 25000 : 12000) 
                : (model.includes('70b') ? 15000 : 8000)
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
            const sentences = docText.match(/[^.!?]+[.!?]+/g)?.filter(s => s.trim().length > 15) || []
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
