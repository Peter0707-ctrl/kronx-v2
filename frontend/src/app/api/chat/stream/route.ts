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

const GROQ_API_KEYS = groqApiKeys()

function matchGreeting(query: string): string | null {
  return matchSimpleGreeting(query)
}

type HistoryMessage = { role: 'user' | 'ai' | 'assistant'; content: string }

function parseMessageContent(text: string, isVisionModel: boolean = true): any {
  const imageRegex = /\[IMAGE:\s*(data:image\/[^\]]+)\]/gi
  const images: string[] = []
  
  // Always sanitize memory blocks from non-personal queries to prevent memory stickiness
  const isPersonalQuery = /\b(my name|who am i|my project|my background|my memory|remember|my email)\b/i.test(text)
  let cleanText = text
  if (!isPersonalQuery) {
    cleanText = cleanText.replace(/\[PERSISTENT USER BRAIN MEMORY\][\s\S]*/gi, '').trim()
  }

  let match
  while ((match = imageRegex.exec(text)) !== null) {
    images.push(match[1].trim())
    cleanText = cleanText.replace(match[0], '').trim()
  }

  if (images.length === 0) {
    if (text.includes('DOCUMENT ATTACHED:') && text.trim().startsWith('[')) {
      return `${cleanText}\n\n[INSTRUCTION]: Please provide a DEEP, DETAILED, COMPREHENSIVE analysis of what is discussed in this document. Break down all key topics, technical features, and action items in detail.`
    }
    return cleanText
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
  webSearchResults: string | null = null,
  clientContext?: { time?: string; date?: string; timezone?: string; location?: string },
  conversationalDirective?: string
): any[] {
  let systemPrompt = getModeSystemPrompt(mode)
  if (conversationalDirective) {
    systemPrompt += conversationalDirective
  }
  if (clientContext?.time) {
    systemPrompt += `\n\n[REAL-TIME USER ENVIRONMENT & CLOCK CONTEXT]:\n- Exact Current Time: ${clientContext.time}\n- Current Date: ${clientContext.date || ''}\n- Timezone: ${clientContext.timezone || 'Africa/Dar_es_Salaam'}\n- User Location: ${clientContext.location || 'Tanzania'}\nAlways provide the exact real-time clock and date with clear numbers when asked, and append the wall clock tag: [WALL_CLOCK: time="${clientContext.time}", date="${clientContext.date}", timezone="${clientContext.timezone}", location="${clientContext.location}"] at the end of the response.`
  }
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
      // Always prune past document contents from historical turns so only the currently active document is analyzed
      if (content.includes('DOCUMENT ATTACHED:') || content.includes('Document Content:')) {
        const match = content.match(/\[([A-Z\s]+DOCUMENT ATTACHED:[^\]]+)\]/i)
        const docHeader = match ? match[1] : 'Prior Document'
        const userText = content.replace(/\[[A-Z\s]+DOCUMENT ATTACHED:[\s\S]*/gi, '').trim()
        content = userText ? `${userText} (${docHeader})` : `[${docHeader}]`
      }
      content = content.replace(/\[IMAGE:\s*data:image\/[^\]]+\]/gi, '[Image previously attached and analyzed]')
      if (content.length > 1000) {
        content = content.substring(0, 800) + '... [Historical text shortened]'
      }
      messages.push({ role: 'user', content: parseMessageContent(content, isVisionModel) })
    } else if ((h.role === 'ai' || h.role === 'assistant') && h.content) {
      let content = h.content
      const isRecent = (len - i) <= 6
      if (!isRecent && content.length > 1200) {
        content = content.substring(0, 1000) + '... [Historical response shortened]'
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
    const needsSearch = /\b(latest news|breaking news|live score|today's weather|current price of|who is the current (president|prime minister|ceo)|tournament results? (2025|2026)|match score|election results? (2025|2026)|search the web for|what is the date today|today's date)\b/i.test(lower)
    if (!needsSearch) return null

    let searchSnippet = ''

    // 1. Wikipedia API Search for live encyclopedia accuracy
    try {
      const wikiRes = await fetch(`https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(cleanQuery)}&utf8=&format=json&origin=*`, {
        headers: { 'User-Agent': 'CopetraAI/2.0 (Academic Search Engine)' }
      })
      if (wikiRes.ok) {
        const wikiData = await wikiRes.json()
        const searchResults = wikiData?.query?.search || []
        if (searchResults.length > 0) {
          searchSnippet += searchResults.slice(0, 3).map((s: any) => {
            const cleanSnippet = s.snippet.replace(/<[^>]*>?/gm, '')
            return `[Fact Context - ${s.title}]: ${cleanSnippet}`
          }).join('\n\n')
        }
      }
    } catch (e) {
      console.warn('Wikipedia API fetch warning:', e)
    }

    // 2. DuckDuckGo Instant API Search
    try {
      const ddgRes = await fetch(`https://api.duckduckgo.com/?q=${encodeURIComponent(cleanQuery)}&format=json&no_redirect=1&no_html=1&skip_disambig=1`, {
        headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' }
      })
      if (ddgRes.ok) {
        const ddgData = await ddgRes.json()
        if (ddgData.AbstractText) {
          searchSnippet += `\n\n[Live Context - ${ddgData.Heading || 'DuckDuckGo'}]: ${ddgData.AbstractText}`
        }
      }
    } catch (e) {
      console.warn('DuckDuckGo fetch warning:', e)
    }

    return searchSnippet ? searchSnippet.trim() : null
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
    const body = await req.json()
    message = body.message || ''
    mode = body.mode || 'Friend'
    history = body.history || []
    if (body.timezone) timezone = body.timezone
    if (body.user_time) userTime = body.user_time
    if (body.user_date) userDate = body.user_date
    if (body.location) location = body.location
  } catch (e) {
    return NextResponse.json({ error: 'Invalid JSON request' }, { status: 400 })
  }

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

  const encoder = new TextEncoder()

  // CRITICAL: Skip web search entirely when a document is attached.
  // Running web search on a document message causes random Wikipedia/web results
  // to be injected instead of the AI analyzing the actual uploaded document.
  const isDocumentMessage = /\[(WORD|PDF|EXCEL|POWERPOINT|TEXT|CODE)\s+DOCUMENT ATTACHED:/i.test(message) ||
    message.includes('DOCUMENT ATTACHED:') || message.includes('FILE ATTACHED:')
  const greetingReply = matchGreeting(message)
  const webSearchResults =
    greetingReply || isDocumentMessage || !needsLiveWebSearch(message)
      ? null
      : await fetchWebSearch(message)

  const stream = new ReadableStream({
    async start(controller) {
      if (!message.trim()) {
        controller.enqueue(encoder.encode('data: Please provide a question or document.\n\n'))
        controller.enqueue(encoder.encode('data: [DONE]\n\n'))
        controller.close()
        return
      }

      controller.enqueue(encoder.encode(': pjkronx-stream-open\n\n'))

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
      const conversationalDirective = intentResult.promptDirective || (mode === 'Friend' ? `\n\n[FRIEND & COMPANION MODE ACTIVE]:\nRespond with deep human warmth, active listening, and conversational flow. Avoid rigid bullet points for personal dialogue.` : '')
      const dynamicTemperature = isConversationalOrEmotional ? 0.68 : 0.35

      // Greetings-only instant response: fires ONLY when message is a pure greeting.
      // If user adds a question or topic after the greeting, it goes to the LLM instead.
      const greetingReply = matchGreeting(cleanUserMessage || message)
      if (greetingReply) {
        const clean = greetingReply.replace(/\r/g, '').replace(/\n/g, '\\n')
        controller.enqueue(encoder.encode(`data: ${clean}\n\n`))
        controller.enqueue(encoder.encode('data: [DONE]\n\n'))
        controller.close()
        return
      }

      // Deterministic Academic & Math & Code & Real-Time Clock Solver: Instant 10/10 Accurate Response
      // Never intercept emotional, advice, or conversational questions with rigid formulas
      if (!isConversationalOrEmotional) {
        const detSolution = solveDeterministically(cleanUserMessage || message, mode, 'en', clientContext)
        if (detSolution.matched && detSolution.answer) {
          const clean = detSolution.answer.replace(/\r/g, '').replace(/\n/g, '\\n')
          controller.enqueue(encoder.encode(`data: ${clean}\n\n`))
          controller.enqueue(encoder.encode('data: [DONE]\n\n'))
          controller.close()
          return
        }
      }

      // Image Generation Request in Chat: Instant Neural Canvas Renderer
      const imgGen = matchImageGenerationRequest(cleanUserMessage || message)
      if (imgGen.isImageGen && imgGen.markdown) {
        const clean = imgGen.markdown.replace(/\r/g, '').replace(/\n/g, '\\n')
        controller.enqueue(encoder.encode(`data: ${clean}\n\n`))
        controller.enqueue(encoder.encode('data: [DONE]\n\n'))
        controller.close()
        return
      }

      let streamedAny = false
      const hasAttachedImage = message.includes('[IMAGE:')

      // Function to call Gemini Multimodal Vision / Academic Reasoning
      async function tryGemini(): Promise<boolean> {
        const geminiKeys = geminiApiKeys()
        for (const gKey of geminiKeys) {
          const geminiModels = [
            'gemini-3.6-flash',
            'gemini-3.7-flash',
            'gemini-flash-latest',
            'gemini-3.5-flash',
            'gemini-2.5-flash',
            'gemini-2.0-flash'
          ]
          for (const gModel of geminiModels) {
            try {
              const abortCtrl = new AbortController()
              const timeoutId = setTimeout(() => abortCtrl.abort(), 25000)
              const gUrl = `https://generativelanguage.googleapis.com/v1beta/models/${gModel}:generateContent`
              
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

              parts.push({
                text: `${getModeSystemPrompt(mode)}${conversationalDirective}${timeContextPrompt}\n\n${promptText}`
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

              const gRes = await fetch(gUrl, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'X-goog-api-key': gKey
                },
                body: JSON.stringify({
                  contents: [{ role: 'user', parts }],
                  generationConfig: { temperature: dynamicTemperature, maxOutputTokens: 2048 }
                }),
                signal: abortCtrl.signal,
                cache: 'no-store'
              })
              clearTimeout(timeoutId)
              if (gRes.ok) {
                const gData = await gRes.json()
                const rawText = gData.candidates?.[0]?.content?.parts?.[0]?.text
                const cleanTextResult = cleanAiResponse(rawText || '')
                if (cleanTextResult) {
                  const clean = cleanTextResult.replace(/\r/g, '').replace(/\n/g, '\\n')
                  controller.enqueue(encoder.encode(`data: ${clean}\n\n`))
                  return true
                }
              }
            } catch { }
          }
        }
        return false
      }

      // If user uploaded an image, execute Google Gemini Multimodal Vision FIRST
      if (hasAttachedImage) {
        streamedAny = await tryGemini()
        if (streamedAny) {
          controller.enqueue(encoder.encode('data: [DONE]\n\n'))
          controller.close()
          return
        }
      }

      // Provider: Groq Cloud (Ultra Fast for Text, Math, Science & Code)
      if (!streamedAny) {
        const keys = groqApiKeys()
        for (const apiKey of keys) {
          if (streamedAny) break

          const groqMessages = buildGroqMessages(message, mode, history, true, webSearchResults, clientContext, conversationalDirective)
          const isDocument = message.includes('DOCUMENT ATTACHED:') || message.includes('FILE ATTACHED:')
          const models = preferFastGroqModels({
            vision: false,
            document: isDocument,
            long: isDocument || message.length > 800,
          })

          for (const model of models) {
            if (streamedAny) break
            try {
              const currentGroqMessages = buildGroqMessages(message, mode, history, false, webSearchResults, clientContext, conversationalDirective)
              const abortCtrl = new AbortController()
              const isLargeModel = /120b|70b|90b|27b/.test(model)
              const timeoutMs = isDocument
                ? (isLargeModel ? 25000 : 15000)
                : (isLargeModel ? 20000 : 12000)
              const timeoutId = setTimeout(() => abortCtrl.abort(), timeoutMs)

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
                  max_completion_tokens: 2048,
                  temperature: dynamicTemperature,
                  top_p: 0.9,
                  stream: true,
                }),
                signal: abortCtrl.signal,
                cache: 'no-store',
              })

              clearTimeout(timeoutId)

              if (groqRes.ok && groqRes.body) {
                const reader = groqRes.body.getReader()
                const decoder = new TextDecoder()
                let buffer = ''
                let hasStarted = false

                try {
                  while (true) {
                    const { done, value } = await reader.read()
                    if (done) break

                    buffer += decoder.decode(value, { stream: true })
                    const lines = buffer.split('\n')
                    buffer = lines.pop() || ''

                    for (const line of lines) {
                      const trimmed = line.trim()
                      if (!trimmed || trimmed === 'data: [DONE]') continue
                      if (trimmed.startsWith('data: ')) {
                        try {
                          const json = JSON.parse(trimmed.slice(6))
                          const delta = json.choices?.[0]?.delta?.content
                          if (delta) {
                            hasStarted = true
                            const clean = delta.replace(/\r/g, '').replace(/\n/g, '\\n')
                            controller.enqueue(encoder.encode(`data: ${clean}\n\n`))
                          }
                        } catch { }
                      }
                    }
                  }

                  if (hasStarted) {
                    streamedAny = true
                    break
                  }
                } catch { }
              }
            } catch { }
          }
        }
      }

      // Provider 2: Google Gemini Cloud fallback if not already executed
      if (!streamedAny && !hasAttachedImage) {
        streamedAny = await tryGemini()
        if (streamedAny) {
          controller.enqueue(encoder.encode('data: [DONE]\n\n'))
          controller.close()
          return
        }
      }

      // Provider 3: OpenAI Cloud
      if (!streamedAny) {
        const oKeys = openAiApiKeys()
        for (const oKey of oKeys) {
          if (streamedAny) break
          try {
            const abortCtrl = new AbortController()
            const timeoutId = setTimeout(() => abortCtrl.abort(), 15000)
            const openAiSys = getModeSystemPrompt(mode) + conversationalDirective + (clientContext?.time ? `\n\n[REAL-TIME USER ENVIRONMENT & CLOCK CONTEXT]: Exact Current Time: ${clientContext.time}, Date: ${clientContext.date}, Timezone: ${clientContext.timezone}, Location: ${clientContext.location}. Append [WALL_CLOCK: time="${clientContext.time}", date="${clientContext.date}", timezone="${clientContext.timezone}", location="${clientContext.location}"]` : '')
            const oRes = await fetch('https://api.openai.com/v1/chat/completions', {
              method: 'POST',
              headers: { 'Authorization': `Bearer ${oKey}`, 'Content-Type': 'application/json' },
              body: JSON.stringify({
                model: 'gpt-4o-mini',
                messages: [{ role: 'system', content: openAiSys }, { role: 'user', content: message }],
                temperature: dynamicTemperature,
                max_tokens: 2048
              }),
              signal: abortCtrl.signal,
              cache: 'no-store'
            })
            clearTimeout(timeoutId)
            if (oRes.ok) {
              const oData = await oRes.json()
              const rawText = oData.choices?.[0]?.message?.content
              const cleanText = cleanAiResponse(rawText || '')
              if (cleanText) {
                const clean = cleanText.replace(/\r/g, '').replace(/\n/g, '\\n')
                controller.enqueue(encoder.encode(`data: ${clean}\n\n`))
                streamedAny = true
                break
              }
            }
          } catch { }
        }
      }

      // Provider 4: Ollama (Railway Private Network & Local)
      if (!streamedAny) {
        const ollamaHosts = [
          process.env.OLLAMA_URL,
          process.env.OLLAMA_HOST,
          'http://ollama.railway.internal:11434',
          'http://ollama:11434',
          'http://127.0.0.1:11434'
        ].filter(Boolean) as string[]

        for (const host of ollamaHosts) {
          if (streamedAny) break
          try {
            const abortCtrl = new AbortController()
            const timeoutId = setTimeout(() => abortCtrl.abort(), 12000)
            const oRes = await fetch(`${host}/api/generate`, {
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
            if (oRes.ok) {
              const oData = await oRes.json()
              const rawText = oData.response
              const cleanText = cleanAiResponse(rawText || '')
              if (cleanText) {
                const clean = cleanText.replace(/\r/g, '').replace(/\n/g, '\\n')
                controller.enqueue(encoder.encode(`data: ${clean}\n\n`))
                streamedAny = true
                break
              }
            }
          } catch { }
        }
      }

      // Provider 5: Backend Master Agent
      if (!streamedAny) {
        try {
          const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'
          const abortCtrl = new AbortController()
          const timeoutId = setTimeout(() => abortCtrl.abort(), 15000)

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
              const cleanText = cleanAiResponse(data.answer)
              const clean = cleanText.replace(/\r/g, '').replace(/\n/g, '\\n')
              controller.enqueue(encoder.encode(`data: ${clean}\n\n`))
              streamedAny = true
            }
          }
        } catch { }
      }

      // Final transparent notification if network is down
      if (!streamedAny) {
        const fallbackMsg = `I couldn't generate a reliable answer for this request at this moment. Please check your network connection and try again.`
        const clean = fallbackMsg.replace(/\r/g, '').replace(/\n/g, '\\n')
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
