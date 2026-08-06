import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'
export const revalidate = 0

const KNOWLEDGE_BASE: Record<string, string> = {
  "president of tanzania": `**President of Tanzania (2025/2026):**\n\nThe current President of the United Republic of Tanzania is **Samia Suluhu Hassan**, who took office on **March 19, 2021**, following the death of President John Pombe Magufuli. She is the **first female president** in Tanzania's history and in East Africa.\n\n**Cabinet & Key Ministers:**\n- **Vice President:** Philip Mpango\n- **Prime Minister:** Kassim Majaliwa\n- **Minister of Finance:** Dr. Mwigulu Nchemba\n- **Minister of Foreign Affairs:** January Makamba\n- **Minister of Health:** Ummy Mwalimu\n- **Minister of Education:** Prof. Adolf Mkenda\n\n*Source: Copetra Knowledge Engine*`,
  "rais wa tanzania": `**Rais wa Tanzania (2025/2026):**\n\nRais wa sasa ni **Samia Suluhu Hassan**, aliyeapishwa tarehe **19 Machi 2021**. Ni rais wa kwanza mwanamke katika historia ya Tanzania na Afrika Mashariki.\n\n*Chanzo: Copetra Knowledge Engine*`,
  "capital of tanzania": `**Capital of Tanzania:**\n\n- **Dodoma** – Official legislative capital (since 1996)\n- **Dar es Salaam** – Largest city and commercial hub`,
  "samia suluhu": `**Samia Suluhu Hassan** is the **6th President of Tanzania**, born January 27, 1960 in Zanzibar. She is the first female president in East Africa, serving since March 19, 2021.`,
  "waziri mkuu": `**Waziri Mkuu wa Tanzania:** Kassim Majaliwa Majaliwa, akishikilia wadhifu huu tangu 2015.`,
}

const GREETINGS: Record<string, string> = {
  "hello": `Hello! 👋 Welcome to **Copetra AI**!\n\nI'm your AI Assistant and Academic Companion, powered by **PJ COPETRANOVA**. I can help you with:\n\n- 📚 Academic research & analysis\n- 💻 Software development & coding\n- 🧮 Mathematics & science problems\n- ✍️ Essay & thesis writing\n- 🌍 General knowledge questions\n\nWhat would you like to explore today?`,
  "hi": `Hi there! 👋 I am **Copetra AI**, powered by **PJ COPETRANOVA**.\n\nWhat can I help you with today?`,
  "hey": `Hey! 👋 Welcome to **Copetra AI**!\n\nHow can I assist you today?`,
  "habari": `Habari! 👋 Karibu **Copetra AI**!\n\nNinaweza kukusaidia katika masomo, programu, utafiti, na maswali ya ujumla. Una swali gani leo?`,
  "mambo": `Poa sana! 👋 Karibu **Copetra AI**!\n\nUna swali au mada gani ungependa tuchunguze pamoja?`,
  "jambo": `Jambo! 👋 Karibu **Copetra AI**!\n\nNinaweza kukusaidia nini leo?`,
  "who are you": `I am **Copetra AI** 🤖 — an elite AI Assistant and Academic Companion engineered and powered by **PJ COPETRANOVA**.\n\nI am designed to give you:\n- ⚡ Instant responses\n- 🧠 Deep reasoning and analysis\n- 📖 Academic-grade answers\n- 💡 Creative problem solving\n\nHow can I help you today?`,
  "wewe ni nani": `Mimi ni **Copetra AI** 🤖 — msaidizi wa AI aliyebuniwa na kuendeshwa na **PJ COPETRANOVA**.\n\nNinaweza kukusaidia katika masomo, programu, utafiti, na zaidi. Unaitaji msaada gani?`,
  "what can you do": `I can help you with a wide range of tasks:\n\n**📚 Academic**\n- Essay and thesis writing\n- Research analysis and summaries\n- Exam preparation and explanations\n\n**💻 Development**\n- Write and debug code in any language\n- System design and architecture\n- Algorithm explanations\n\n**🧮 Science & Math**\n- Step-by-step problem solving\n- Physics, Chemistry, Biology\n- Statistics and Calculus\n\n**🌍 General Knowledge**\n- History, Geography, Politics\n- Current affairs analysis\n- Language translation\n\nWhat would you like to start with?`,
}

function searchKnowledgeBase(query: string): string | null {
  if (!query) return null
  const q = query.toLowerCase().trim()
  // ONLY return instant greeting if the query is an EXACT standalone greeting
  if (GREETINGS[q]) return GREETINGS[q]
  if (KNOWLEDGE_BASE[q]) return KNOWLEDGE_BASE[q]
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
- ONLY when the user's current query explicitly asks to analyze, summarize, explain, or answer questions based on an uploaded Image, Word document (.docx), PDF (.pdf), Excel spreadsheet (.xlsx/.csv), PowerPoint (.pptx), or Code file:
  1. FIRST: State the CORE CONCEPT, subject matter, or data structure inside the file under "### 📖 Core Document Concept & Overview".
  2. SECOND: Automatically execute ALL instructions, solve ALL questions/equations, debug ALL code, or complete all assignments contained inside the file under "### ✍️ Executed Solutions & Step-by-Step Response".
  3. ACADEMIC CITATION RULE: You MUST cite specific section titles, chapters, table names, or approximate page coordinates (e.g. "Section 2.3", "Table 4", "Page 12") when referencing extracted information.
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

STRICT INTENT & TRUTH ALIGNMENT MANDATE:
- READ THE USER'S QUESTION WITH 100% INTENT PRECISION.
- NEVER misinterpret the premise, polarity, or core objective of the question.
- NEVER give an opposite point, inverted logic, or contradictory claim.
- If the user asks a factual, technical, mathematical, or academic question, adhere strictly to verified facts and logical truths.
- Perform a mental double-check before outputting: verify that your answer directly addresses what was asked without twisting the facts or contradicting reality.

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
      return `${base}\n\nMODE: ACADEMIC RESEARCH\n- Write at university thesis level with rigorous analysis\n- Structure answers with: Introduction → Core Concepts → Analysis → Examples → Conclusion`
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
  webSearchResults: string | null = null
): { role: string; content: any }[] {
  const systemPrompt = getModeSystemPrompt(mode)
  let webSearchContext = ''
  if (webSearchResults) {
    webSearchContext = `\n\n[LIVE WEB SEARCH DATA]: The following live web search results were retrieved for this query:\n${webSearchResults}\nUse this live data to verify your facts, dates, and names and provide a 100% accurate, up-to-date response.`
  }
  const messages: { role: string; content: any }[] = [
    { role: 'system', content: systemPrompt + webSearchContext }
  ]

  const recentHistory = history.slice(-6)
  const len = recentHistory.length
  for (let i = 0; i < len; i++) {
    const h = recentHistory[i]
    if (h.role === 'user') {
      let content = h.content
      const isRecent = (len - i) <= 2
      if (!isRecent) {
        const docIdx = content.indexOf('\nDocument Content:\n')
        if (docIdx !== -1) {
          content = content.substring(0, docIdx).trim() + '\n\n[Attached Document: Content omitted from historical memory for topic clarity]'
        }
        const imgIdx = content.indexOf('\n\n[IMAGE:')
        if (imgIdx !== -1) {
          content = content.substring(0, imgIdx).trim() + '\n\n[Attached Image: Content omitted from historical memory for topic clarity]'
        }
        if (content.length > 500) {
          content = content.substring(0, 300) + '... [Historical text shortened for context efficiency]'
        }
      }
      messages.push({ role: 'user', content: parseMessageContent(content) })
    } else if ((h.role === 'ai' || h.role === 'assistant') && h.content) {
      let content = h.content
      const isRecent = (len - i) <= 2
      if (!isRecent && content.length > 800) {
        content = content.substring(0, 500) + '... [Historical response shortened to optimize token efficiency]'
      }
      messages.push({ role: 'assistant', content })
    }
  }

  messages.push({ role: 'user', content: parseMessageContent(message) })
  return messages
}

async function callGroq(
  message: string,
  mode: string,
  history: HistoryMessage[] = [],
  webSearchResults: string | null = null
): Promise<string | null> {
  const apiKey = process.env.GROQ_API_KEY
  if (!apiKey) return null

  const groqMessages = buildGroqMessages(message, mode, history, webSearchResults)
  
  const hasVision = groqMessages.some(m => Array.isArray(m.content)) || message.includes('[IMAGE:')
  const isDocument = message.includes('DOCUMENT ATTACHED:') || message.includes('FILE ATTACHED:')

  const models = hasVision
    ? ['llama-3.2-11b-vision-preview', 'llama-3.2-90b-vision-preview']
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
    try {
      const controller = new AbortController()
      const timeoutMs = model.includes('70b') || model.includes('90b') ? 20000 : 8000
      setTimeout(() => controller.abort(), timeoutMs)

      const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model,
          messages: groqMessages,
          max_tokens: 2048,
          temperature: 0.1,
          top_p: 0.1,
          stream: false,
        }),
        signal: controller.signal,
        cache: 'no-store',
      })

      if (res.ok) {
        const data = await res.json()
        const text = data.choices?.[0]?.message?.content?.trim()
        if (text) return text
      }
    } catch (e) {
      console.error(`Groq model ${model} error:`, e)
    }
  }
  return null
}

async function fetchWikipedia(query: string): Promise<string | null> {
  try {
    const searchRes = await fetch(
      `https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(query)}&format=json`,
      { headers: { 'User-Agent': 'Copetra-AI/2.0' }, cache: 'no-store' }
    )
    if (!searchRes.ok) return null
    const searchData = await searchRes.json()
    const topTitle = searchData.query?.search?.[0]?.title
    if (!topTitle) return null
    const summaryRes = await fetch(
      `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(topTitle)}`,
      { headers: { 'User-Agent': 'Copetra-AI/2.0' }, cache: 'no-store' }
    )
    if (!summaryRes.ok) return null
    const data = await summaryRes.json()
    if (data.extract) return `### 🌐 ${topTitle}\n\n${data.extract}\n\n*Source: Wikipedia*`
  } catch { }
  return null
}

async function fetchWebSearch(query: string): Promise<string | null> {
  try {
    const cleanQuery = query
      .replace(/\[IMAGE:.*?\]/gi, '')
      .replace(/\[(WORD|PDF|EXCEL|POWERPOINT|TEXT|CODE) DOCUMENT ATTACHED:.*?\][\s\S]*/gi, '')
      .replace(/\[PERSISTENT USER BRAIN MEMORY\][\s\S]*/gi, '')
      .trim()

    if (!cleanQuery || cleanQuery.length < 5) return null

    const lower = cleanQuery.toLowerCase()
    const needsSearch = /\b(current|president|weather|news|today|latest|who is|what is|search|live|update|api code|release)\b/i.test(lower)
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
    const body = await req.json().catch(() => ({}))
    message = body.message || ''
    mode = body.mode || 'Friend'
    history = body.history || []
  } catch { }

  if (!message) return NextResponse.json({ response: 'Please provide a message.' }, { status: 400 })

  const instant = searchKnowledgeBase(message)
  if (instant) return NextResponse.json({ response: instant })

  const webSearchResults = await fetchWebSearch(message)

  const groqAnswer = await callGroq(message, mode, history, webSearchResults)
  if (groqAnswer) return NextResponse.json({ response: groqAnswer })

  const wikiAnswer = await fetchWikipedia(message)
  if (wikiAnswer) return NextResponse.json({ response: wikiAnswer })

  return NextResponse.json({
    response: `**Copetra AI** is experiencing a temporary issue. Please try again in a moment.`
  })
}
