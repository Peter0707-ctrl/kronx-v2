import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'
export const revalidate = 0

// ── TANZANIA & GENERAL KNOWLEDGE BASE ──
const KNOWLEDGE_BASE: Record<string, string> = {
  "president of tanzania": `**President of Tanzania (2025/2026):**\n\nThe current President of the United Republic of Tanzania is **Samia Suluhu Hassan**, who took office on **March 19, 2021**, following the death of President John Pombe Magufuli. She is the **first female president** in Tanzania's history and in East Africa.\n\n**Cabinet & Key Ministers (Hassan Administration):**\n- **Vice President:** Philip Mpango\n- **Prime Minister:** Kassim Majaliwa\n- **Minister of Finance:** Dr. Mwigulu Nchemba\n- **Minister of Foreign Affairs:** January Makamba\n- **Minister of Health:** Ummy Mwalimu\n- **Minister of Education:** Prof. Adolf Mkenda\n- **Minister of Agriculture:** Hussein Bashe\n- **Minister of Home Affairs:** Hamad Masauni\n- **Minister of Defense:** Stergomena Tax\n- **Attorney General:** Eliezer Feleshi\n\n**Background:**\nSamia Suluhu Hassan was born on **January 27, 1960**, in Zanzibar. She served as Vice President from 2015 to 2021 before ascending to the presidency. Her administration has focused on economic recovery, diplomatic engagement, COVID-19 response, and attracting foreign investment to Tanzania.\n\n*Source: Kronex Knowledge Engine*`,

  "rais wa tanzania": `**Rais wa Tanzania (2025/2026):**\n\nRais wa sasa wa Jamhuri ya Muungano wa Tanzania ni **Samia Suluhu Hassan**, aliyeapishwa tarehe **19 Machi 2021** baada ya kifo cha Rais John Pombe Magufuli. Ni rais wa kwanza mwanamke katika historia ya Tanzania na Afrika Mashariki.\n\n**Viongozi Wakuu wa Serikali:**\n- **Makamu wa Rais:** Dr. Philip Mpango\n- **Waziri Mkuu:** Kassim Majaliwa\n- **Waziri wa Fedha:** Dr. Mwigulu Nchemba\n- **Waziri wa Mambo ya Nje:** January Makamba\n- **Waziri wa Elimu:** Prof. Adolf Mkenda\n\n*Chanzo: Kronex Knowledge Engine*`,

  "waziri mkuu wa tanzania": `**Waziri Mkuu wa Tanzania:**\n\nWaziri Mkuu wa sasa wa Jamhuri ya Muungano wa Tanzania ni **Kassim Majaliwa Majaliwa**, ambaye ameshikilia wadhifu huu tangu mwaka **2015**.\n\n**Rais wa Tanzania:** Samia Suluhu Hassan (tangu Machi 2021)\n**Makamu wa Rais:** Philip Mpango\n\n*Chanzo: Kronex Knowledge Engine*`,

  "samia suluhu": `**Samia Suluhu Hassan - President of Tanzania:**\n\nSamia Suluhu Hassan is the **6th President of the United Republic of Tanzania**, born on January 27, 1960, in Zanzibar. She became the first female president in Tanzania and East Africa after President John Magufuli passed away on March 17, 2021.\n\n**Key facts:**\n- First female president in Tanzania and East Africa\n- Born in Zanzibar\n- Served as Vice President 2015–2021\n- CCM party leader\n- Her administration focuses on: economic revival, tourism, foreign investment, and social development`,

  "capital of tanzania": `**Capital of Tanzania:**\n\nTanzania has two capitals:\n- **Dodoma** – The official legislative and administrative capital (since 1996)\n- **Dar es Salaam** – The largest city and former capital, still the commercial and economic hub`,

  "mji mkuu wa tanzania": `**Mji Mkuu wa Tanzania:**\n\nTanzania ina miji miwili ya msingi:\n- **Dodoma** – Mji mkuu rasmi wa nchi na makao makuu ya serikali\n- **Dar es Salaam** – Mji mkubwa zaidi na kituo cha biashara na uchumi`,
}

function searchKnowledgeBase(query: string): string | null {
  if (!query) return null
  const q = query.toLowerCase().trim()
  for (const [key, value] of Object.entries(KNOWLEDGE_BASE)) {
    if (q.includes(key)) {
      return value
    }
  }
  return null
}

// ── DUCKDUCKGO + WIKIPEDIA WEB SEARCH ──
async function webSearch(query: string): Promise<string | null> {
  try {
    const cleanQuery = encodeURIComponent(query.trim())
    const ddgUrl = `https://api.duckduckgo.com/?q=${cleanQuery}&format=json&no_redirect=1&no_html=1&skip_disambig=1`
    const res = await fetch(ddgUrl, { headers: { 'User-Agent': 'Kronex-AI/2.0' }, cache: 'no-store' })
    if (res.ok) {
      const data = await res.json()
      const abstractText = data.AbstractText || data.Answer || data.Definition
      if (abstractText && abstractText.length > 30) {
        return `**Live Web Search Result for "${query}":**\n\n${abstractText}\n\n*Source: ${data.AbstractSource || 'DuckDuckGo Web Search'}*`
      }
    }
  } catch (err) {
    console.error('Web search error:', err)
  }

  // Wikipedia fallback
  try {
    const topic = query.replace(/\b(who is|what is|tell me about|explain|define)\b/gi, '').trim()
    if (topic.length > 2) {
      const wikiUrl = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(topic)}`
      const wikiRes = await fetch(wikiUrl, { headers: { 'User-Agent': 'Kronex-AI/2.0' }, cache: 'no-store' })
      if (wikiRes.ok) {
        const wikiData = await wikiRes.json()
        if (wikiData.extract && wikiData.extract.length > 40) {
          return `**${wikiData.title}** (Wikipedia Summary):\n\n${wikiData.extract}\n\n*Full article: ${wikiData.content_urls?.desktop?.page || ''}*`
        }
      }
    }
  } catch (err) {
    console.error('Wikipedia search error:', err)
  }

  return null
}

// ── GEMINI API CALL ──
async function callGemini(message: string, mode: string = 'Friend'): Promise<string | null> {
  const apiKey = process.env.GEMINI_API_KEY
  if (!apiKey) return null

  // Models with verified active quota (gemini-flash-latest, gemini-3.5-flash-lite, etc.)
  const models = [
    'gemini-flash-latest',
    'gemini-3.5-flash-lite',
    'gemini-3.1-flash-lite',
    'gemini-flash-lite-latest'
  ]

  let modeInstruction = "You are Copetra AI, an elite AI Assistant and Academic Companion engineered by PJ Copetranova. Answer clearly, accurately, and thoroughly in markdown."

  if (mode === 'Academic') {
    modeInstruction = "You are Copetra AI in ACADEMIC RESEARCH MODE. Provide rigorous academic analysis, university thesis-level depth, structured definitions, and step-by-step proofs."
  } else if (mode === 'Developer') {
    modeInstruction = "You are Copetra AI in SENIOR DEVELOPER MODE. Provide production-ready software code, optimal algorithms, clear syntax highlighting, and architectural best practices."
  } else if (mode === 'Tutor') {
    modeInstruction = "You are Copetra AI in PERSONAL TUTOR MODE. Break down complex topics with clear step-by-step explanations, helpful analogies, and practice questions."
  } else if (mode === 'Creative') {
    modeInstruction = "You are Copetra AI in CREATIVE ENGINE MODE. Provide innovative, engaging, imaginative, and eloquently crafted responses."
  }

  const contents = [
    {
      role: 'user',
      parts: [
        {
          text: `${modeInstruction}\n\nUser Question: ${message}`
        }
      ]
    }
  ]

  for (const model of models) {
    try {
      const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contents, generationConfig: { maxOutputTokens: 2048, temperature: 0.7 } }),
        cache: 'no-store'
      })

      if (response.ok) {
        const data = await response.json()
        const candidateText = data.candidates?.[0]?.content?.parts?.[0]?.text
        if (candidateText) {
          return candidateText
        }
      }
    } catch (err) {
      console.error(`Error with model ${model}:`, err)
    }
  }
  return null
}

// ── HEURISTIC ACADEMIC ANSWER GENERATOR ──
function generateStructuredAnswer(query: string, language: string = 'en'): string {
  const q = query ? query.trim() : 'Academic Query'
  const isSw = language === 'sw'

  if (isSw) {
    return `**Uchambuzi wa Copetra AI: ${q}**\n\nAsante kwa swali lako la kitaaluma. Hapa kuna majibu ya kina na yaliyopangiliwa vizuri:\n\n### 1. Dhana Kuu (Overview)\n- Swali lako linahusu somo la msingi lenye athari kubwa kitaaluma.\n- **Muhtasari:** ${q} ni mada inayohitaji uelewa wa kina wa misingi ya kiutendaji na kanuni zake.\n\n### 2. Maelezo ya Kina\n1. **Msingi:** Kila kipengele cha mada hii kimejengwa juu ya misingi ya kisayansi na kitaaluma.\n2. **Utekelezaji:** Katika utafiti na masomo, kuelewa mada hii kunasaidia kutatua matatizo mbalimbali kwa ufasaha.\n\n### 3. Hitimisho & Ushauri wa Masomo\nIli kufanya vizuri zaidi katika masomo yako kuhusu mada hii:\n- Hakikisha unasoma mifano zaidi ya vitendo.\n- Weka kipaumbele kwenye kuelewa misingi badala ya kushika kwa kichwa tu.\n\n*Copetra AI — Academic Intelligence Engine*`
  }

  return `**Copetra AI Academic Response: ${q}**\n\nThank you for your academic query. Here is a clear, structured breakdown to assist your learning:\n\n### 1. Core Concept & Definition\n- Your question regarding **"${q}"** represents a key topic in academic studies.\n- **Key Overview:** Understanding this topic requires analyzing its core principles, practical applications, and theoretical foundation.\n\n### 2. Key Breakdown & Analysis\n1. **Fundamental Principle:** The core idea behind this topic is centered around structured logic and verified methodologies.\n2. **Practical Application:** In assignments, exams, and real-world scenarios, this knowledge is applied to solve complex analytical problems step-by-step.\n3. **Key Components:** Always ensure you break down the problem into smaller manageable parts before synthesizing your final answer.\n\n### 3. Academic Guidance\n- **Study Tip:** Review related coursework, practice problem-solving steps, and verify key terminology.\n- Feel free to ask Copetra AI follow-up questions or request specific calculations and image generation!\n\n*Copetra AI — Academic Companion & Intelligence Engine*`
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

  let responseText: string | null = null

  // 1. Check Knowledge Base
  try {
    const kbAnswer = searchKnowledgeBase(message)
    if (kbAnswer) {
      return NextResponse.json({ response: kbAnswer })
    }
  } catch (err) {
    console.error('KB Search Error:', err)
  }

  // 2. Gemini API
  try {
    responseText = await callGemini(message, mode)
  } catch (err) {
    console.error('Gemini Call Error:', err)
  }

  if (responseText) {
    return NextResponse.json({ response: responseText })
  }

  // 3. Try Web Search
  try {
    const webAnswer = await webSearch(message)
    if (webAnswer) {
      return NextResponse.json({ response: webAnswer })
    }
  } catch (err) {
    console.error('Web Search Error:', err)
  }

  // 4. Structured Fallback Answer
  const fallback = generateStructuredAnswer(message, language)
  return NextResponse.json({ response: fallback })
}
