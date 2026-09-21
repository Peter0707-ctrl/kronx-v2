import { NextRequest, NextResponse } from 'next/server'

import {
  groqApiKeys,
  geminiApiKeys,
  openAiApiKeys,
  matchSimpleGreeting,
  needsLiveWebSearch,
  preferFastGroqModels,
  cleanAiResponse,
  solveDeterministically,
  matchImageGenerationRequest,
  detectEmotionAndConversationalIntent
} from '@/lib/fastChat'

import { getModeSystemPrompt } from '@/lib/copetraSystemPrompt'

export const dynamic = 'force-dynamic'
export const revalidate = 0

function matchGreeting(query: string): string | null {
  return matchSimpleGreeting(query)
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
  webSearchResults: string | null = null,
  clientContext?: { time?: string; date?: string; timezone?: string; location?: string },
  conversationalDirective?: string
): { role: string; content: any }[] {
  let systemPrompt = getModeSystemPrompt(mode)
  if (conversationalDirective) {
    systemPrompt += conversationalDirective
  }
  if (clientContext?.time) {
    systemPrompt += `\n\n[REAL-TIME USER ENVIRONMENT & CLOCK CONTEXT]:\n- Exact Current Time: ${clientContext.time}\n- Current Date: ${clientContext.date || ''}\n- Timezone: ${clientContext.timezone || 'Africa/Dar_es_Salaam'}\n- User Location: ${clientContext.location || 'Tanzania'}\nAlways provide the exact real-time clock and date with clear numbers when asked, and append the wall clock tag: [WALL_CLOCK: time="${clientContext.time}", date="${clientContext.date}", timezone="${clientContext.timezone}", location="${clientContext.location}"] at the end of the response.`
  }
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
      // Always prune past document contents from historical turns so only the currently active document is analyzed
      if (content.includes('DOCUMENT ATTACHED:') || content.includes('Document Content:')) {
        const match = content.match(/\[([A-Z\s]+DOCUMENT ATTACHED:[^\]]+)\]/i)
        const docHeader = match ? match[1] : 'Prior Document'
        const userText = content.replace(/\[[A-Z\s]+DOCUMENT ATTACHED:[\s\S]*/gi, '').trim()
        content = userText ? `${userText} (${docHeader})` : `[${docHeader}]`
      }
      content = content.replace(/\[IMAGE:\s*data:image\/[^\]]+\]/gi, '[Image previously attached and analyzed]')
      if (content.length > 500) {
        content = content.substring(0, 300) + '... [Historical text shortened for context efficiency]'
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

  const isPersonalQuery = /\b(my name|who am i|my project|my background|my memory|remember|my email)\b/i.test(message)
  let cleanMessage = message
  if (!isPersonalQuery) {
    cleanMessage = cleanMessage.replace(/\[PERSISTENT USER BRAIN MEMORY\][\s\S]*/gi, '').trim()
  }
  messages.push({ role: 'user', content: parseMessageContent(cleanMessage) })
  return messages
}

const GROQ_API_KEYS = groqApiKeys()

async function callGroq(
  message: string,
  mode: string,
  history: HistoryMessage[] = [],
  webSearchResults: string | null = null,
  clientContext?: { time?: string; date?: string; timezone?: string; location?: string },
  conversationalDirective?: string,
  dynamicTemperature: number = 0.35
): Promise<string | null> {
  const keys = groqApiKeys()
  if (keys.length === 0) return null

  const groqMessages = buildGroqMessages(message, mode, history, webSearchResults, clientContext, conversationalDirective)
  
  const hasVision = groqMessages.some(m => Array.isArray(m.content)) || message.includes('[IMAGE:')
  const isDocument = message.includes('DOCUMENT ATTACHED:') || message.includes('FILE ATTACHED:')

  const models = preferFastGroqModels({
    vision: hasVision,
    document: isDocument,
    long: isDocument || message.length > 800,
  })

  for (const apiKey of keys) {
    for (const model of models) {
      try {
        const controller = new AbortController()
        const timeoutMs = model.includes('120b') || model.includes('70b') || model.includes('90b') ? 20000 : 12000
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

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
            max_completion_tokens: 2048,
            temperature: dynamicTemperature,
            top_p: 0.9,
            stream: false,
            ...(model.includes('gpt-oss') ? { reasoning_effort: 'low' } : {}),
          }),
          signal: controller.signal,
          cache: 'no-store',
        })

        clearTimeout(timeoutId)

        if (res.ok) {
          const data = await res.json()
          let text = data.choices?.[0]?.message?.content?.trim()
          if (text) {
            text = cleanAiResponse(text)
            if (text) return text
          }
        }
      } catch (e) {
        console.warn(`Groq key or model ${model} failed, trying next. Error:`, e)
      }
    }
  }
  return null
}

async function callGemini(
  message: string,
  mode: string,
  clientContext?: { time?: string; date?: string; timezone?: string; location?: string },
  conversationalDirective?: string,
  dynamicTemperature: number = 0.35
): Promise<string | null> {
  const keys = geminiApiKeys()
  for (const key of keys) {
    const models = [
      'gemini-3.6-flash',
      'gemini-3.7-flash',
      'gemini-flash-latest',
      'gemini-3.5-flash',
      'gemini-2.5-flash',
      'gemini-2.0-flash'
    ]
    for (const model of models) {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 20000)
        const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`
        
        // Build multimodal contents with inline_data for attached images
        const parts: any[] = []
        const imageMatch = message.match(/\[IMAGE:\s*(data:image\/([a-zA-Z0-9+]+);base64,([^\]\s]+))\s*\]/i)
        const cleanText = message.replace(/\[IMAGE:[\s\S]*?\]/gi, '').trim()

        const promptText = cleanText
          ? `Please examine the attached image carefully and answer the user query with high precision.\n\nUser Question: ${cleanText}`
          : `Please examine the attached image thoroughly, detailing all visual elements, UI components, text, metrics, and key data shown.`

        const timeContextPrompt = clientContext?.time
          ? `\n\n[REAL-TIME USER ENVIRONMENT & CLOCK CONTEXT]:\n- Exact Current Time: ${clientContext.time}\n- Current Date: ${clientContext.date}\n- Timezone: ${clientContext.timezone}\n- Location: ${clientContext.location}\nWhen answering time or location questions, provide the exact time and append: [WALL_CLOCK: time="${clientContext.time}", date="${clientContext.date}", timezone="${clientContext.timezone}", location="${clientContext.location}"]\n`
          : ''

        const directivePrompt = conversationalDirective ? `${conversationalDirective}\n\n` : ''

        parts.push({
          text: `${getModeSystemPrompt(mode)}${directivePrompt}${timeContextPrompt}\n\n${promptText}`
        })

        if (imageMatch) {
          const rawSub = imageMatch[2].toLowerCase()
          const mimeType = `image/${rawSub === 'jpg' ? 'jpeg' : rawSub}`
          parts.push({
            inline_data: {
              mime_type: mimeType,
              data: imageMatch[3]
            }
          })
        }

        const res = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-goog-api-key': key
          },
          body: JSON.stringify({
            contents: [{ role: 'user', parts }],
            generationConfig: { temperature: dynamicTemperature, maxOutputTokens: 2048 }
          }),
          signal: controller.signal,
          cache: 'no-store'
        })
        clearTimeout(timeoutId)
        if (res.ok) {
          const data = await res.json()
          const raw = data.candidates?.[0]?.content?.parts?.[0]?.text
          const clean = cleanAiResponse(raw || '')
          if (clean) return clean
        }
      } catch { }
    }
  }
  return null
}

async function callOpenAi(
  message: string,
  mode: string,
  clientContext?: { time?: string; date?: string; timezone?: string; location?: string },
  conversationalDirective?: string,
  dynamicTemperature: number = 0.35
): Promise<string | null> {
  const keys = openAiApiKeys()
  for (const key of keys) {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 12000)
      let openAiSys = getModeSystemPrompt(mode)
      if (conversationalDirective) {
        openAiSys += conversationalDirective
      }
      if (clientContext?.time) {
        openAiSys += `\n\n[REAL-TIME USER ENVIRONMENT & CLOCK CONTEXT]: Exact Current Time: ${clientContext.time}, Date: ${clientContext.date}, Timezone: ${clientContext.timezone}, Location: ${clientContext.location}. Append [WALL_CLOCK: time="${clientContext.time}", date="${clientContext.date}", timezone="${clientContext.timezone}", location="${clientContext.location}"]`
      }
      const res = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${key}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'gpt-4o-mini',
          messages: [{ role: 'system', content: openAiSys }, { role: 'user', content: message }],
          temperature: dynamicTemperature,
          max_tokens: 2048
        }),
        signal: controller.signal,
        cache: 'no-store'
      })
      clearTimeout(timeoutId)
      if (res.ok) {
        const data = await res.json()
        const raw = data.choices?.[0]?.message?.content
        const clean = cleanAiResponse(raw || '')
        if (clean) return clean
      }
    } catch { }
  }
  return null
}

async function callOllama(message: string, mode: string): Promise<string | null> {
  const hosts = [
    process.env.OLLAMA_URL,
    process.env.OLLAMA_HOST,
    'http://ollama.railway.internal:11434',
    'http://ollama:11434',
    'http://127.0.0.1:11434'
  ].filter(Boolean) as string[]

  for (const host of hosts) {
    try {
      const abortCtrl = new AbortController()
      const timeoutId = setTimeout(() => abortCtrl.abort(), 10000)
      const res = await fetch(`${host}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'llama3:latest',
          prompt: `${getModeSystemPrompt(mode)}\n\nUser Question: ${message}\n\nAnswer:`,
          stream: false
        }),
        signal: abortCtrl.signal,
        cache: 'no-store'
      })
      clearTimeout(timeoutId)
      if (res.ok) {
        const data = await res.json()
        const clean = cleanAiResponse(data.response || '')
        if (clean) return clean
      }
    } catch { }
  }
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
    const needsSearch = /\b(latest news|breaking news|live score|today's weather|current price of|who is the current (president|prime minister|ceo)|tournament results? (2025|2026)|match score|election results? (2025|2026)|search the web for|what is the date today|today's date)\b/i.test(lower)
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
  let timezone = 'Africa/Dar_es_Salaam'
  let userTime = ''
  let userDate = ''
  let location = 'Tanzania, East Africa'

  try {
    const body = await req.json().catch(() => ({}))
    message = body.message || ''
    mode = body.mode || 'Friend'
    history = body.history || []
    if (body.timezone) timezone = body.timezone
    if (body.user_time) userTime = body.user_time
    if (body.user_date) userDate = body.user_date
    if (body.location) location = body.location
  } catch { }

  if (!userTime) {
    try {
      userTime = new Date().toLocaleTimeString('en-US', { timeZone: timezone, hour12: true })
    } catch {
      userTime = new Date().toLocaleTimeString('en-US', { hour12: true })
    }
  }
  if (!userDate) {
    try {
      userDate = new Date().toLocaleDateString('en-US', { timeZone: timezone, weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
    } catch {
      userDate = new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
    }
  }
  if (!location) {
    location = timezone.includes('Dar_es_Salaam') || timezone.includes('Nairobi') ? 'Tanzania, East Africa' : timezone
  }

  const clientContext = {
    time: userTime,
    date: userDate,
    timezone,
    location
  }

  if (!message) return NextResponse.json({ response: 'Please provide a message.' }, { status: 400 })

  // Sanitize user message from background memory headers
  const cleanUserMessage = message
    .replace(/\[PERSISTENT USER BRAIN MEMORY[\s\S]*/gi, '')
    .replace(/\[FEEDBACK HISTORY[\s\S]*/gi, '')
    .replace(/\[REAL-TIME VERIFIED WEB SEARCH DATA[\s\S]*/gi, '')
    .replace(/\[MEMORIZE:.*?\]/gi, '')
    .replace(/\[VISUAL_SUMMARY:.*?\]/gi, '')
    .trim()

  // Emotional & Conversational Intent Detection: Activates Human Empathy & Adaptive Temperature
  const intentResult = detectEmotionAndConversationalIntent(cleanUserMessage || message)
  const isConversationalOrEmotional = intentResult.isConversational || mode === 'Friend'
  const conversationalDirective = intentResult.promptDirective || (mode === 'Friend' ? `\n\n[FRIEND & COMPANION MODE ACTIVE]:\nRespond as an authentic brother and loyal confidant ('bro', 'ndugu yangu'). NEVER assume the user is talking about school, exams, or homework unless explicitly requested. If the user shares feelings or is upset, invite them to tell their story: 'Nisimulie kilichokwaza leo—kama kilivyo, bila kuficha. Nipo hapa kukusikiliza.'` : '')
  // Adaptive Temperature: 0.7 for natural, warm, human conversation (like ChatGPT)
  const dynamicTemperature = mode === 'Developer' || mode === 'Academic' ? 0.35 : 0.70

  // Image Generation Request in Chat: Instant Neural Canvas Renderer
  const imgGen = matchImageGenerationRequest(cleanUserMessage || message)
  if (imgGen.isImageGen && imgGen.markdown) {
    return NextResponse.json({ response: imgGen.markdown })
  }

  const hasAttachedImage = message.includes('[IMAGE:')

  // If user uploaded an image, execute Google Gemini Multimodal Vision FIRST
  if (hasAttachedImage) {
    const geminiAnswer = await callGemini(message, mode, clientContext, conversationalDirective, dynamicTemperature)
    if (geminiAnswer) return NextResponse.json({ response: geminiAnswer })
  }

  // 1. Try Direct Groq call (Fastest path for text/code/math)
  const isDocumentMessage = /\[(WORD|PDF|EXCEL|POWERPOINT|TEXT|CODE)\s+DOCUMENT ATTACHED:/i.test(message) ||
    message.includes('DOCUMENT ATTACHED:') || message.includes('FILE ATTACHED:')

  const webSearchResults = isDocumentMessage ? null : await fetchWebSearch(message)
  const groqAnswer = await callGroq(message, mode, history, webSearchResults, clientContext, conversationalDirective, dynamicTemperature)
  if (groqAnswer) return NextResponse.json({ response: groqAnswer })

  // 2. Try Direct Google Gemini
  if (!hasAttachedImage) {
    const geminiAnswer = await callGemini(message, mode, clientContext, conversationalDirective, dynamicTemperature)
    if (geminiAnswer) return NextResponse.json({ response: geminiAnswer })
  }

  // 3. Try Direct OpenAI
  const openAiAnswer = await callOpenAi(message, mode, clientContext, conversationalDirective, dynamicTemperature)
  if (openAiAnswer) return NextResponse.json({ response: openAiAnswer })

  // 4. Try Ollama (Railway Internal & Local)
  const ollamaAnswer = await callOllama(message, mode)
  if (ollamaAnswer) return NextResponse.json({ response: ollamaAnswer })

  // 5. Try Backend Master Agent
  try {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'
    const abortCtrl = new AbortController()
    const timeoutId = setTimeout(() => abortCtrl.abort(), 8000)

    const backendRes = await fetch(`${backendUrl}/api/copetra/task`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-ID': 'tenant_default',
        'X-User-ID': 'user_default',
      },
      body: JSON.stringify({
        message: message,
        mode: mode,
        detail_level: 'DETAILED',
      }),
      signal: abortCtrl.signal,
    })
    clearTimeout(timeoutId)

    if (backendRes.ok) {
      const data = await backendRes.json()
      if (data.answer) {
        return NextResponse.json({
          response: cleanAiResponse(data.answer),
          artifacts: data.artifacts
        })
      }
    }
  } catch { }

  return NextResponse.json({
    response: `I couldn't generate a reliable answer for this request at this moment. Please check your network connection and try again.`
  })
}

