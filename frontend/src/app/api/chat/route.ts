import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'
export const revalidate = 0

// ── TANZANIA & GENERAL KNOWLEDGE BASE ──
const KNOWLEDGE_BASE: Record<string, string> = {
  "president of tanzania": `**President of Tanzania (2025/2026):**\n\nThe current President of the United Republic of Tanzania is **Samia Suluhu Hassan**, who took office on **March 19, 2021**, following the death of President John Pombe Magufuli. She is the **first female president** in Tanzania's history and in East Africa.\n\n**Cabinet & Key Ministers (Hassan Administration):**\n- **Vice President:** Philip Mpango\n- **Prime Minister:** Kassim Majaliwa\n- **Minister of Finance:** Dr. Mwigulu Nchemba\n- **Minister of Foreign Affairs:** January Makamba\n- **Minister of Health:** Ummy Mwalimu\n- **Minister of Education:** Prof. Adolf Mkenda\n- **Minister of Agriculture:** Hussein Bashe\n- **Minister of Home Affairs:** Hamad Masauni\n- **Minister of Defense:** Stergomena Tax\n- **Attorney General:** Eliezer Feleshi\n\n**Background:**\nSamia Suluhu Hassan was born on **January 27, 1960**, in Zanzibar. She served as Vice President from 2015 to 2021 before ascending to the presidency.\n\n*Source: Copetra Knowledge Engine*`,

  "rais wa tanzania": `**Rais wa Tanzania (2025/2026):**\n\nRais wa sasa wa Jamhuri ya Muungano wa Tanzania ni **Samia Suluhu Hassan**, aliyeapishwa tarehe **19 Machi 2021** baada ya kifo cha Rais John Pombe Magufuli. Ni rais wa kwanza mwanamke katika historia ya Tanzania na Afrika Mashariki.\n\n**Viongozi Wakuu wa Serikali:**\n- **Makamu wa Rais:** Dr. Philip Mpango\n- **Waziri Mkuu:** Kassim Majaliwa\n- **Waziri wa Fedha:** Dr. Mwigulu Nchemba\n\n*Chanzo: Copetra Knowledge Engine*`,

  "waziri mkuu wa tanzania": `**Waziri Mkuu wa Tanzania:**\n\nWaziri Mkuu wa sasa wa Jamhuri ya Muungano wa Tanzania ni **Kassim Majaliwa Majaliwa**, ambaye ameshikilia wadhifu huu tangu mwaka **2015**.\n\n*Chanzo: Copetra Knowledge Engine*`,

  "samia suluhu": `**Samia Suluhu Hassan - President of Tanzania:**\n\nSamia Suluhu Hassan is the **6th President of the United Republic of Tanzania**, born on January 27, 1960, in Zanzibar. She became the first female president in Tanzania and East Africa after President John Magufuli passed away on March 17, 2021.\n\n**Key facts:**\n- First female president in Tanzania and East Africa\n- Born in Zanzibar\n- Served as Vice President 2015–2021\n- CCM party leader`,

  "capital of tanzania": `**Capital of Tanzania:**\n\nTanzania has two capitals:\n- **Dodoma** – The official legislative and administrative capital (since 1996)\n- **Dar es Salaam** – The largest city and former capital, still the commercial and economic hub`,

  "mji mkuu wa tanzania": `**Mji Mkuu wa Tanzania:**\n\nTanzania ina miji miwili ya msingi:\n- **Dodoma** – Mji mkuu rasmi wa nchi na makao makuu ya serikali\n- **Dar es Salaam** – Mji mkubwa zaidi na kituo cha biashara na uchumi`,
}

// ── CONVERSATIONAL GREETINGS ──
const GREETINGS: Record<string, string> = {
  "hello": `Hello! 👋 Welcome to **Copetra AI**, your AI Assistant and Academic Companion engineered by PJ Copetranova.\n\nHow can I help you today? Feel free to ask any academic question, programming problem, research topic, or request image generation!`,
  "hi": `Hi there! 👋 I am **Copetra AI**, engineered by PJ Copetranova.\n\nWhat topic or question can I assist you with today?`,
  "hey": `Hey! 👋 Welcome to **Copetra AI**!\n\nHow can I assist your study, research, or coding work today?`,
  "habari": `Habari! 👋 Karibu **Copetra AI**, Msaidizi wako wa Kisayansi na Kitaaluma kutoka PJ Copetranova.\n\nJe, ninaweza kukusaidia nini leo katika masomo au utafiti wako?`,
  "mambo": `Poa sana! 👋 Karibu **Copetra AI**!\n\nJe, una swali au mada gani ya masomo ungependa tuchambue pamoja leo?`,
  "jambo": `Jambo! 👋 Karibu **Copetra AI**!\n\nUnahitaji msaada gani katika masomo, programu, au utafiti leo?`,
  "good morning": `Good morning! ☀️ Welcome to **Copetra AI**!\n\nHow can I assist your academic research or projects today?`,
  "good afternoon": `Good afternoon! 🌤️ Welcome to **Copetra AI**!\n\nWhat can I help you investigate or calculate today?`,
  "good evening": `Good evening! 🌙 Welcome to **Copetra AI**!\n\nHow can I help you with your studies or questions tonight?`,
  "who are you": `I am **Copetra AI**, an elite AI Assistant and Academic Companion engineered by PJ Copetranova.\n\nI specialize in providing high-level academic analysis, software development solutions, step-by-step problem solving, and real-time research assistance. How can I help you today?`,
  "wewe ni nani": `Mimi ni **Copetra AI**, Msaidizi wa Kitaaluma na Kisayansi aliyebuniwa na PJ Copetranova.\n\nNinasaidia katika uchambuzi wa kitaaluma, kutatua matatizo ya hisabati na programu, na utafiti. Je, ungependa nisaidie nini leo?`
}

function searchKnowledgeBase(query: string): string | null {
  if (!query) return null
  const q = query.toLowerCase().trim()

  // Check Greetings first
  if (GREETINGS[q]) return GREETINGS[q]
  for (const [k, v] of Object.entries(GREETINGS)) {
    if (q === k || q.startsWith(k + ' ') || q.endsWith(' ' + k)) return v
  }

  // Check Knowledge Base
  for (const [k, v] of Object.entries(KNOWLEDGE_BASE)) {
    if (q.includes(k)) return v
  }

  return null
}

function extractKeywords(query: string): string {
  const stopWords = /\b(what|is|the|importance|of|in|and|their|dis|advantages|tell|me|about|explain|define|can|you|how|why|does|do)\b/gi
  let cleaned = query.replace(stopWords, ' ').replace(/[^\w\s]/g, ' ').replace(/\s+/g, ' ').trim()
  cleaned = cleaned.replace(/matterial/gi, 'matter')
                   .replace(/invironment/gi, 'environment')
                   .replace(/tanzanai/gi, 'tanzania')
  return cleaned || query
}

function getModeSystemPrompt(mode: string): string {
  switch (mode) {
    case 'Academic':
      return 'You are Copetra AI in ACADEMIC RESEARCH MODE. Provide rigorous academic analysis, university thesis-level depth, structured definitions, and step-by-step explanations with clear headings and bullet points.'
    case 'Developer':
      return 'You are Copetra AI in SENIOR DEVELOPER MODE. Provide production-ready software code, optimal algorithms, clear syntax highlighting, and architectural best practices.'
    case 'Tutor':
      return 'You are Copetra AI in PERSONAL TUTOR MODE. Break down complex topics with clear step-by-step explanations, helpful analogies, and practice questions.'
    case 'Creative':
      return 'You are Copetra AI in CREATIVE ENGINE MODE. Provide innovative, engaging, imaginative, and eloquently crafted responses.'
    default:
      return 'You are Copetra AI, an elite AI Assistant and Academic Companion engineered by PJ Copetranova. Answer clearly, accurately, and thoroughly. Use markdown formatting with headings and bullet points.'
  }
}

// ── OLLAMA API (Primary AI Engine) ──
async function callOllama(message: string, mode: string = 'Friend'): Promise<string | null> {
  const hosts = [
    process.env.OLLAMA_URL,
    'http://ollama.railway.internal:11434',
    'http://127.0.0.1:11434',
    'http://localhost:11434',
  ].filter(Boolean) as string[]

  const models = ['llama3.2:3b', 'llama3', 'llama3.2', 'mistral', 'gemma', 'phi3']
  const systemPrompt = getModeSystemPrompt(mode)

  for (const host of Array.from(new Set(hosts))) {
    for (const model of models) {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 20000)

        const response = await fetch(`${host}/api/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            model,
            prompt: `${systemPrompt}\n\nUser: ${message}\n\nAssistant:`,
            stream: false,
            options: {
              temperature: 0.7,
              num_predict: 1024,
            }
          }),
          signal: controller.signal,
        })

        clearTimeout(timeoutId)

        if (response.ok) {
          const data = await response.json()
          if (data.response && data.response.trim()) {
            return data.response.trim()
          }
        }
      } catch (e) {
        // Try next host/model
      }
    }
  }

  return null
}

// ── LIVE WIKIPEDIA REST API FETCHER ──
async function fetchLiveWikipediaSummary(query: string): Promise<string | null> {
  const keywords = extractKeywords(query)
  try {
    const searchUrl = `https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(keywords)}&format=json`
    const searchRes = await fetch(searchUrl, { headers: { 'User-Agent': 'Copetra-AI/2.0' }, cache: 'no-store' })
    if (searchRes.ok) {
      const searchData = await searchRes.json()
      if (searchData.query?.search?.length > 0) {
        const topTitle = searchData.query.search[0].title
        const summaryUrl = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(topTitle)}`
        const summaryRes = await fetch(summaryUrl, { headers: { 'User-Agent': 'Copetra-AI/2.0' }, cache: 'no-store' })
        if (summaryRes.ok) {
          const summaryData = await summaryRes.json()
          if (summaryData.extract) {
            return `### 🌐 ${topTitle}\n\n${summaryData.extract}\n\n*Source: Live Wikipedia REST API*`
          }
        }
      }
    }
  } catch (err) {
    console.error('Live Wikipedia API Error:', err)
  }
  return null
}

export async function POST(req: NextRequest) {
  let message = ''
  let language = 'en'
  let mode = 'Friend'

  try {
    const body = await req.json().catch(() => ({}))
    message = body.message || ''
    language = body.language || 'en'
    mode = body.mode || 'Friend'
  } catch (e) {
    console.error('Request body parsing error:', e)
  }

  if (!message) {
    return NextResponse.json({ response: 'Please provide a valid question.' }, { status: 400 })
  }

  // 1. Instant: Greetings & Knowledge Base
  const kbAnswer = searchKnowledgeBase(message)
  if (kbAnswer) {
    return NextResponse.json({ response: kbAnswer })
  }

  // 2. Ollama — Primary AI Engine (llama3.2:3b)
  try {
    const ollamaResponse = await callOllama(message, mode)
    if (ollamaResponse) {
      return NextResponse.json({ response: ollamaResponse })
    }
  } catch (err) {
    console.error('Ollama Error:', err)
  }

  // 3. Live Wikipedia REST API (fallback when Ollama is warming up)
  try {
    const wikiResponse = await fetchLiveWikipediaSummary(message)
    if (wikiResponse) {
      return NextResponse.json({ response: wikiResponse })
    }
  } catch (err) {
    console.error('Wikipedia Error:', err)
  }

  // 4. Final fallback — let user know AI is warming up
  return NextResponse.json({
    response: `I am **Copetra AI** powered by **Ollama llama3.2:3b**. The AI engine is still warming up on the server — please try again in a moment. Your question: *"${message}"*`
  })
}
