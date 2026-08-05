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
  if (GREETINGS[q]) return GREETINGS[q]
  for (const [k, v] of Object.entries(GREETINGS)) {
    if (q === k || q.startsWith(k + ' ') || q.endsWith(' ' + k)) return v
  }
  for (const [k, v] of Object.entries(KNOWLEDGE_BASE)) {
    if (q.includes(k)) return v
  }
  return null
}

function getModeSystemPrompt(mode: string): string {
  const base = `You are Copetra AI, an elite AI Assistant and Academic Companion engineered and powered by PJ COPETRANOVA.

STRICT IDENTITY RULES:
- NEVER state or mention underlying AI models or providers such as Llama, Ollama, Groq, Gemini, OpenAI, or ChatGPT.
- ALWAYS identify yourself as Copetra AI, powered by PJ COPETRANOVA.

DOCUMENT & FILE ANALYSIS MANDATE:
- ONLY when the user's current query explicitly asks to analyze, summarize, explain, or answer questions based on an uploaded Image, Word document (.docx), PDF (.pdf), Excel spreadsheet (.xlsx/.csv), PowerPoint (.pptx), or Code file:
  1. FIRST: State the CORE CONCEPT, subject matter, or data structure inside the file under "### 📖 Core Document Concept & Overview".
  2. SECOND: Automatically execute ALL instructions, solve ALL questions/equations, debug ALL code, or complete all assignments contained inside the file under "### ✍️ Executed Solutions & Step-by-Step Response".
- For all other questions, requests (like writing poems, songs, creative text), or chats, DO NOT use these document section headers. Answer the question directly and exactly as asked!

CRITICAL RULES:
- ALWAYS give thorough, accurate, well-structured answers
- CRITICAL PRIVACY RULE: DO NOT reveal, mention, or recall the user's background, email, projects, or any other personal details stored in memory unless the user explicitly asks about them. Treat database details as background context only.
- CRITICAL NAME RULE: NEVER, UNDER ANY CIRCUMSTANCES, INSERT THE USER'S NAME (e.g. Peter) INSIDE GENERATED CONTENT (such as poems, song lyrics, code, essays, assignments, mathematical equations, or document analysis text blocks) unless the user explicitly asks you to include their name in the text. Keep all such output neutral and professional.
- NEVER say "I cannot", "As an AI", or give vague responses
- Use markdown formatting: **bold**, headers (###), bullet points, numbered lists
- If asked in Swahili, respond fully in Swahili
- If asked in English, respond in English
- Always end complex answers with a summary or key takeaway`

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
  history: HistoryMessage[] = []
): { role: string; content: any }[] {
  const systemPrompt = getModeSystemPrompt(mode)
  const messages: { role: string; content: any }[] = [
    { role: 'system', content: systemPrompt }
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

async function callGroq(
  message: string,
  mode: string,
  history: HistoryMessage[] = []
): Promise<string | null> {
  const apiKey = process.env.GROQ_API_KEY
  if (!apiKey) return null

  const groqMessages = buildGroqMessages(message, mode, history)
  
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
      const timeoutMs = model.includes('70b') || model.includes('90b') ? 6000 : 3000
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
          temperature: 0.7,
          top_p: 0.9,
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

  const groqAnswer = await callGroq(message, mode, history)
  if (groqAnswer) return NextResponse.json({ response: groqAnswer })

  const wikiAnswer = await fetchWikipedia(message)
  if (wikiAnswer) return NextResponse.json({ response: wikiAnswer })

  return NextResponse.json({
    response: `**Copetra AI** is experiencing a temporary issue. Please try again in a moment.`
  })
}
