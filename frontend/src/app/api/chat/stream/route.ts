import { NextRequest } from 'next/server'

export const dynamic = 'force-dynamic'
export const revalidate = 0

// ── KNOWLEDGE BASE ──
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

async function callGemini(message: string): Promise<string | null> {
  const apiKey = process.env.GEMINI_API_KEY
  if (!apiKey || apiKey === 'YOUR_GEMINI_API_KEY_HERE') return null

  const models = ['gemini-2.0-flash-lite', 'gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-3.5-flash']

  const contents = [
    {
      role: 'user',
      parts: [
        {
          text: `You are Copetra AI, an elite AI Assistant and Academic Companion engineered by PJ Copetranova. Answer clearly, accurately, and thoroughly in markdown.\n\nUser Question: ${message}`
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
      console.error(`Gemini stream error with ${model}:`, err)
    }
  }
  return null
}

export async function POST(req: NextRequest) {
  let message = ''
  let language = 'en'

  try {
    const body = await req.json().catch(() => ({}))
    message = body.message || ''
    language = body.language || 'en'
  } catch (e) {
    console.error('Stream request parsing error:', e)
  }

  if (!message) {
    message = 'Academic Question'
  }

  let responseText: string | null = null

  // 1. KB Search
  try {
    responseText = searchKnowledgeBase(message)
  } catch (err) {
    console.error('KB Search Error:', err)
  }

  // 2. Gemini API
  if (!responseText) {
    try {
      responseText = await callGemini(message)
    } catch (err) {
      console.error('Gemini Stream Call Error:', err)
    }
  }

  // 3. Fallback
  if (!responseText) {
    if (language === 'sw') {
      responseText = `**Uchambuzi wa Copetra AI: ${message}**\n\nAsante kwa swali lako la kitaaluma. Hapa kuna muhtasari wa kiutafiti:\n\n1. **Muhtasari:** Swali lako linahusu mada ya msingi katika masomo na utafiti.\n2. **Ufafanuzi:** Mada hii inahitaji kuelewa misingi ya kisayansi na utekelezaji wake kwa vitendo.\n3. **Hitimisho:** Hakikisha unarejelea vitabu vyako vya masomo kwa mifano zaidi.\n\n*Copetra AI — Academic Intelligence Engine*`
    } else {
      responseText = `**Copetra AI Academic Response: ${message}**\n\nThank you for your academic query. Here is a clear breakdown to support your learning:\n\n1. **Core Concept:** Understanding **"${message}"** involves analyzing its fundamental principles and theoretical foundations.\n2. **Practical Context:** In coursework and assignments, this topic is key to solving complex analytical problems step-by-step.\n3. **Recommendation:** Review course materials and practice related exercises.\n\n*Copetra AI — Academic Companion & Intelligence Engine*`
    }
  }

  // Format as SSE stream
  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    async start(controller) {
      // Yield keep-alive header
      controller.enqueue(encoder.encode(': pjkronx-stream-open\n\n'))

      // Clean newlines for SSE wire format
      const cleanText = (responseText || '').replace(/\r/g, '').replace(/\n/g, '\\n')
      controller.enqueue(encoder.encode(`data: ${cleanText}\n\n`))
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
