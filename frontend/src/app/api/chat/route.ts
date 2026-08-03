import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'
export const revalidate = 0

// ── KNOWLEDGE BASE ──
const KNOWLEDGE_BASE: Record<string, string> = {
  "president of tanzania": `**President of Tanzania (2025/2026):**\n\nThe current President of the United Republic of Tanzania is **Samia Suluhu Hassan**, who took office on **March 19, 2021**, following the death of President John Pombe Magufuli. She is the **first female president** in Tanzania's history and in East Africa.\n\n**Cabinet & Key Ministers:**\n- **Vice President:** Philip Mpango\n- **Prime Minister:** Kassim Majaliwa\n- **Minister of Finance:** Dr. Mwigulu Nchemba\n- **Minister of Foreign Affairs:** January Makamba\n\n*Source: Copetra Knowledge Engine*`,
  "rais wa tanzania": `**Rais wa Tanzania (2025/2026):**\n\nRais wa sasa ni **Samia Suluhu Hassan**, aliyeapishwa tarehe **19 Machi 2021**. Ni rais wa kwanza mwanamke katika historia ya Tanzania na Afrika Mashariki.\n\n*Chanzo: Copetra Knowledge Engine*`,
  "capital of tanzania": `**Capital of Tanzania:**\n\n- **Dodoma** – Official legislative capital (since 1996)\n- **Dar es Salaam** – Largest city, commercial hub`,
  "samia suluhu": `**Samia Suluhu Hassan** is the **6th President of Tanzania**, born January 27, 1960 in Zanzibar. First female president in East Africa, serving since March 19, 2021.`,
}

const GREETINGS: Record<string, string> = {
  "hello": `Hello! 👋 Welcome to **Copetra AI**, your AI Assistant engineered by PJ Copetranova.\n\nHow can I help you today?`,
  "hi": `Hi there! 👋 I am **Copetra AI**. What can I help you with?`,
  "hey": `Hey! 👋 Welcome to **Copetra AI**! How can I assist?`,
  "habari": `Habari! 👋 Karibu **Copetra AI**! Je, ninaweza kukusaidia nini?`,
  "mambo": `Poa! 👋 Karibu **Copetra AI**! Una swali gani?`,
  "jambo": `Jambo! 👋 Karibu **Copetra AI**!`,
  "who are you": `I am **Copetra AI**, an elite AI Assistant and Academic Companion engineered by PJ Copetranova, powered by **Llama 3.2** via Groq.`,
  "wewe ni nani": `Mimi ni **Copetra AI**, msaidizi wa AI aliyebuniwa na PJ Copetranova.`,
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
  switch (mode) {
    case 'Academic':
      return 'You are Copetra AI in ACADEMIC RESEARCH MODE. Provide rigorous academic analysis with structured headings, definitions, and step-by-step explanations.'
    case 'Developer':
      return 'You are Copetra AI in SENIOR DEVELOPER MODE. Provide production-ready code with best practices.'
    case 'Tutor':
      return 'You are Copetra AI in PERSONAL TUTOR MODE. Explain topics clearly with analogies and examples.'
    case 'Creative':
      return 'You are Copetra AI in CREATIVE MODE. Provide imaginative and eloquent responses.'
    default:
      return 'You are Copetra AI, an elite AI Assistant and Academic Companion engineered by PJ Copetranova. Answer clearly, accurately and thoroughly using markdown formatting.'
  }
}

// ── GROQ API (Primary — Llama 3.2 on GPU, instant) ──
async function callGroq(message: string, mode: string): Promise<string | null> {
  const apiKey = process.env.GROQ_API_KEY
  if (!apiKey) return null

  const models = ['llama-3.1-8b-instant', 'llama3-8b-8192', 'gemma2-9b-it', 'llama-3.3-70b-versatile']

  for (const model of models) {
    try {
      const controller = new AbortController()
      setTimeout(() => controller.abort(), 20000)

      const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model,
          messages: [
            { role: 'system', content: getModeSystemPrompt(mode) },
            { role: 'user', content: message },
          ],
          max_tokens: 1024,
          temperature: 0.7,
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

// ── LIVE WIKIPEDIA FALLBACK ──
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
  try {
    const body = await req.json().catch(() => ({}))
    message = body.message || ''
    mode = body.mode || 'Friend'
  } catch { }

  if (!message) return NextResponse.json({ response: 'Please provide a message.' }, { status: 400 })

  // 1. Instant KB / Greeting
  const instant = searchKnowledgeBase(message)
  if (instant) return NextResponse.json({ response: instant })

  // 2. Groq — Llama 3.2 on GPU (primary)
  const groqAnswer = await callGroq(message, mode)
  if (groqAnswer) return NextResponse.json({ response: groqAnswer })

  // 3. Wikipedia fallback
  const wikiAnswer = await fetchWikipedia(message)
  if (wikiAnswer) return NextResponse.json({ response: wikiAnswer })

  return NextResponse.json({ response: `**Copetra AI** could not process your request right now. Please try again in a moment.` })
}
