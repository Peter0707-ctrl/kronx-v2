import { NextRequest } from 'next/server'

export const dynamic = 'force-dynamic'
export const revalidate = 0

// ── KNOWLEDGE BASE (Instant, Zero-latency answers) ──
const KNOWLEDGE_BASE: Record<string, string> = {
  "president of tanzania": `**President of Tanzania (2025/2026):**\n\nThe current President of the United Republic of Tanzania is **Samia Suluhu Hassan**, who took office on **March 19, 2021**, following the death of President John Pombe Magufuli. She is the **first female president** in Tanzania's history and in East Africa.\n\n**Cabinet & Key Ministers (Hassan Administration):**\n- **Vice President:** Philip Mpango\n- **Prime Minister:** Kassim Majaliwa\n- **Minister of Finance:** Dr. Mwigulu Nchemba\n- **Minister of Foreign Affairs:** January Makamba\n- **Minister of Health:** Ummy Mwalimu\n- **Minister of Education:** Prof. Adolf Mkenda\n\n*Source: Copetra Knowledge Engine*`,
  "rais wa tanzania": `**Rais wa Tanzania (2025/2026):**\n\nRais wa sasa wa Jamhuri ya Muungano wa Tanzania ni **Samia Suluhu Hassan**, aliyeapishwa tarehe **19 Machi 2021** baada ya kifo cha Rais John Pombe Magufuli.\n\n*Chanzo: Copetra Knowledge Engine*`,
  "capital of tanzania": `**Capital of Tanzania:**\n\nTanzania has two capitals:\n- **Dodoma** – The official legislative and administrative capital (since 1996)\n- **Dar es Salaam** – The largest city and former capital, still the commercial and economic hub`,
}

const GREETINGS: Record<string, string> = {
  "hello": `Hello! 👋 Welcome to **Copetra AI**, your AI Assistant and Academic Companion engineered by PJ Copetranova.\n\nHow can I help you today?`,
  "hi": `Hi there! 👋 I am **Copetra AI**. What can I help you with today?`,
  "hey": `Hey! 👋 Welcome to **Copetra AI**! How can I assist you?`,
  "habari": `Habari! 👋 Karibu **Copetra AI**! Je, ninaweza kukusaidia nini leo?`,
  "mambo": `Poa sana! 👋 Karibu **Copetra AI**! Una swali gani leo?`,
  "jambo": `Jambo! 👋 Karibu **Copetra AI**! Nikusaidie nini?`,
  "good morning": `Good morning! ☀️ Welcome to **Copetra AI**! How can I help today?`,
  "good afternoon": `Good afternoon! 🌤️ Welcome to **Copetra AI**! What can I help you with?`,
  "good evening": `Good evening! 🌙 Welcome to **Copetra AI**! How can I assist you tonight?`,
  "who are you": `I am **Copetra AI**, an elite AI Assistant and Academic Companion engineered by PJ Copetranova. I specialize in academic analysis, software development, research, and real-time problem solving.`,
  "wewe ni nani": `Mimi ni **Copetra AI**, Msaidizi wa Kitaaluma aliyebuniwa na PJ Copetranova. Ninasaidia katika masomo, programu, na utafiti.`
}

function searchInstantAnswers(query: string): string | null {
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
      return 'You are Copetra AI in ACADEMIC RESEARCH MODE. Provide rigorous academic analysis, university thesis-level depth, structured definitions, and step-by-step explanations with clear headings and bullet points.'
    case 'Developer':
      return 'You are Copetra AI in SENIOR DEVELOPER MODE. Provide production-ready software code, optimal algorithms, clear syntax highlighting, and architectural best practices.'
    case 'Tutor':
      return 'You are Copetra AI in PERSONAL TUTOR MODE. Break down complex topics with clear step-by-step explanations, helpful analogies, and practice questions.'
    case 'Creative':
      return 'You are Copetra AI in CREATIVE ENGINE MODE. Provide innovative, engaging, imaginative, and eloquently crafted responses.'
    default:
      return 'You are Copetra AI, an elite AI Assistant and Academic Companion engineered by PJ Copetranova. Answer clearly, accurately, and thoroughly. Use markdown formatting.'
  }
}

// ── LIVE WIKIPEDIA REST API FALLBACK ──
async function fetchWikipediaSummary(query: string): Promise<string | null> {
  try {
    const searchUrl = `https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(query)}&format=json`
    const searchRes = await fetch(searchUrl, { headers: { 'User-Agent': 'Copetra-AI/2.0' }, cache: 'no-store' })
    if (!searchRes.ok) return null
    const searchData = await searchRes.json()
    if (!searchData.query?.search?.length) return null
    const topTitle = searchData.query.search[0].title
    const summaryUrl = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(topTitle)}`
    const summaryRes = await fetch(summaryUrl, { headers: { 'User-Agent': 'Copetra-AI/2.0' }, cache: 'no-store' })
    if (!summaryRes.ok) return null
    const summaryData = await summaryRes.json()
    if (summaryData.extract) {
      return `### 🌐 ${topTitle}\n\n${summaryData.extract}\n\n*Source: Live Wikipedia REST API*`
    }
  } catch (err) {
    console.error('Wikipedia fallback error:', err)
  }
  return null
}

export async function POST(req: NextRequest) {
  let message = ''
  let mode = 'Friend'

  try {
    const body = await req.json().catch(() => ({}))
    message = body.message || ''
    mode = body.mode || 'Friend'
  } catch (e) {
    console.error('Stream request parsing error:', e)
  }

  if (!message) message = 'Hello'

  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    async start(controller) {
      // Always send keep-alive immediately
      controller.enqueue(encoder.encode(': pjkronx-stream-open\n\n'))

      // 1. Instant KB / Greeting check
      const instant = searchInstantAnswers(message)
      if (instant) {
        const clean = instant.replace(/\r/g, '').replace(/\n/g, '\\n')
        controller.enqueue(encoder.encode(`data: ${clean}\n\n`))
        controller.enqueue(encoder.encode('data: [DONE]\n\n'))
        controller.close()
        return
      }

      // 2. Ollama streaming (llama3.2:3b)
      const ollamaHost = process.env.OLLAMA_URL || 'http://127.0.0.1:11434'
      const systemPrompt = getModeSystemPrompt(mode)
      const fullPrompt = `${systemPrompt}\n\nUser: ${message}\n\nAssistant:`
      let streamedAny = false

      try {
        const controller2 = new AbortController()
        const timeout = setTimeout(() => controller2.abort(), 25000)

        const ollamaRes = await fetch(`${ollamaHost}/api/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            model: 'llama3.2:3b',
            prompt: fullPrompt,
            stream: true,
          }),
          signal: controller2.signal,
        })

        clearTimeout(timeout)

        if (ollamaRes.ok && ollamaRes.body) {
          const reader = ollamaRes.body.getReader()
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
              if (!trimmed) continue
              try {
                const parsed = JSON.parse(trimmed)
                const token = parsed.response
                if (token) {
                  streamedAny = true
                  const clean = token.replace(/\r/g, '').replace(/\n/g, '\\n')
                  controller.enqueue(encoder.encode(`data: ${clean}\n\n`))
                }
                if (parsed.done) break
              } catch { }
            }
          }
        }
      } catch (err) {
        console.log('[Ollama stream] not reachable, falling back to Wikipedia')
      }

      // 3. Wikipedia live fallback if Ollama didn't respond
      if (!streamedAny) {
        try {
          const wikiText = await fetchWikipediaSummary(message)
          if (wikiText) {
            const clean = wikiText.replace(/\r/g, '').replace(/\n/g, '\\n')
            controller.enqueue(encoder.encode(`data: ${clean}\n\n`))
            streamedAny = true
          }
        } catch (e) {
          console.error('Wikipedia fallback error:', e)
        }
      }

      // 4. Last resort minimal response
      if (!streamedAny) {
        const fallback = `I am **Copetra AI**. I received your question: "${message}". The AI engine is warming up — please try again in a moment.`.replace(/\n/g, '\\n')
        controller.enqueue(encoder.encode(`data: ${fallback}\n\n`))
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
