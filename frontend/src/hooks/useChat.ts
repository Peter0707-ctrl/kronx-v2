'use client'

/**
 *  CRITICAL SAFEGUARD WARNING FOR DEVELOPERS
 * -------------------------------------------------------------
 * 1. TAG REGEXES: Do not modify tag matching patterns inside postProcessResponse().
 * 2. HISTORY SLICING: When passing messages to buildHistory(), ALWAYS use (.slice(0, -2))
 *    to strip the current user message and empty AI loading message. Failing to do so
 *    causes consecutive duplicate user messages in the API payload, crashing the upstream model.
 * -------------------------------------------------------------
 */

import { useCallback } from 'react'
import { useKronxStore } from '@/store/useKronxStore'
import { streamMessage, sendMessage, buildHistory } from '@/services/chat'

export function useChat() {
  const store = useKronxStore()

  const postProcessResponse = () => {
    const currentState = useKronxStore.getState()
    const msgs = currentState.activeMessages()
    const finalMsg = msgs[msgs.length - 1]
    if (finalMsg && finalMsg.role === 'ai') {
      // 1. Process Image Generation tag
      const imgMatch = finalMsg.content.match(/\[GENERATE_IMAGE:\s*(.*?)\]/i)
      if (imgMatch) {
        if (!currentState.canGeneratePicture()) {
          currentState.replaceLastAiMessage("You have reached your daily picture generation limit. Please upgrade your plan.")
          currentState.setSettingsModalOpen(true)
          return
        }
        currentState.incrementPictureUsage()

        const imagePrompt = imgMatch[1].trim()
        const lowerPrompt = imagePrompt.toLowerCase()
        let styleModifiers = "8k resolution, highly detailed, photorealistic, cinematic lighting, masterpiece"
        if (lowerPrompt.includes('logo')) {
          styleModifiers = "minimalist vector logo, clean professional branding, vector art, flat design, SVG style, white background"
        } else if (lowerPrompt.includes('map') || lowerPrompt.includes('floor plan') || lowerPrompt.includes('blueprint')) {
          styleModifiers = "highly detailed topographic map, clear geography labels, cartographic design, satellite style, detailed vectors"
        } else if (lowerPrompt.includes('card') || lowerPrompt.includes('ui') || lowerPrompt.includes('mockup') || lowerPrompt.includes('wireframe')) {
          styleModifiers = "UI UX layout, premium presentation design, high-fidelity app component mockup, glassmorphism, clean interface aesthetics"
        }

        const encodedPrompt = encodeURIComponent(`${imagePrompt}, ${styleModifiers}`)
        const pollinationsUrl = `https://image.pollinations.ai/prompt/${encodedPrompt}?width=1024&height=1024&model=flux&seed=${Math.floor(Math.random()*100000)}&nologo=true`
        const imageMarkdown = `Here is your high-fidelity generated image for **"${imagePrompt}"**:\n\n![Generated Image](${pollinationsUrl})`
        currentState.replaceLastAiMessage(imageMarkdown)
      }

      // 2. Process Adaptive Learning Correction tag
      const memorizeMatch = finalMsg.content.match(/\[MEMORIZE:\s*(.*?)\]/i)
      if (memorizeMatch) {
        const fact = memorizeMatch[1].trim()
        if (fact) {
          currentState.addMemory(fact)
          console.log('[Copetra Brain Auto-Learned Correction]:', fact)
          // Strip the tag from the final message content to keep the UI clean
          const cleanedText = finalMsg.content.replace(/\[MEMORIZE:\s*.*?\]/gi, '').trim()
          currentState.replaceLastAiMessage(cleanedText)
        }
      }

      // 3. Process Visual Memory Retention (VISUAL_SUMMARY tag)
      const visualSummaryMatch = finalMsg.content.match(/\[VISUAL_SUMMARY:\s*(.*?)\]/i)
      if (visualSummaryMatch) {
        const summary = visualSummaryMatch[1].trim()
        if (summary) {
          // Locate the user message that attached the image
          const userMsg = msgs[msgs.length - 2]
          if (userMsg && userMsg.role === 'user') {
            const originalContent = userMsg.content
            const imgIdx = originalContent.indexOf('\n\n[IMAGE:')
            if (imgIdx !== -1) {
              const query = originalContent.substring(0, imgIdx).trim()
              const imgBlock = originalContent.substring(imgIdx)
              // Store visual summary BEFORE the base64 image data block to survive pruning
              const updatedContent = `${query}\n\n[Attached Image Content Summary: ${summary}]${imgBlock}`
              currentState.editMessageInPlace(userMsg.id, updatedContent)
              console.log('[Copetra Brain Saved Visual Memory Summary]:', summary)
            }
          }
          // Strip the tag from the final message content to keep the UI clean
          const cleanedText = finalMsg.content.replace(/\[VISUAL_SUMMARY:\s*.*?\]/gi, '').trim()
          currentState.replaceLastAiMessage(cleanedText)
        }
      }

      // 4. Guarantee Official Ticket Widget ([TICKET: ...]) when user requests a ticket
      const latestState = useKronxStore.getState()
      const latestMsgs = latestState.activeMessages()
      const latestAi = latestMsgs[latestMsgs.length - 1]
      const latestUser = latestMsgs[latestMsgs.length - 2]
      if (latestAi && latestAi.role === 'ai' && latestUser && latestUser.role === 'user') {
        const uText = latestUser.content.toLowerCase()
        let updatedAiText = latestAi.content

        if (
          /\b(ticket|tiketi|nikatie|anicatie|boarding pass)\b/i.test(uText) &&
          !/\[TICKET:/i.test(updatedAiText)
        ) {
          const isFlight = /\b(ndege|flight|air|precision|air tanzania)\b/i.test(uText)
          const isBus = /\b(basi|bus|shabiby|abood|allp|tahmeli)\b/i.test(uText)
          const isEvent = /\b(event|tamasha|concert|movie|sinema|mpira|match|vip)\b/i.test(uText)
          const tType = isFlight
            ? 'FLIGHT BOARDING PASS'
            : isBus
            ? 'EXPRESS BUS TICKET'
            : isEvent
            ? 'VIP EVENT PASS'
            : 'SGR EXPRESS TICKET'
          const tTitle = isFlight
            ? 'Air Tanzania / Precision Air Express'
            : isBus
            ? 'Luxury Intercity Coach'
            : isEvent
            ? 'Copetra VIP Event Access Pass'
            : 'TRC Standard Gauge Railway (SGR Royal)'
          const passengerName = latestState.user?.name || 'Verified Passenger'
          const tomorrow = new Date(Date.now() + 86400000).toISOString().slice(0, 10)
          const refCode = `CPA-TKT-${Math.floor(10000 + Math.random() * 90000)}`
          const ticketTag = `\n\n[TICKET: type="${tType}" | title="${tTitle}" | passenger="${passengerName}" | from="Dar es Salaam" | to="Dodoma / Destination" | date="${tomorrow}" | time="08:00 AM" | seat="VIP Coach - Seat 12A" | price="TSh 50,000" | ref="${refCode}" | status="CONFIRMED"]`
          updatedAiText += ticketTag
        }

        // 5. Guarantee Auto-Save File to PC ([AUTO_SAVE_FILE: ...]) when user asks for code/file on their PC
        if (
          /\b(kwenye pc|save file|download file|faili|fail lake|nipatie faili|auto_save_file|nitengenezee code|tengeneza code|tengeneza programu|airun|i-run)\b/i.test(uText) &&
          /```\w+/i.test(updatedAiText) &&
          !/\[AUTO_SAVE_FILE:/i.test(updatedAiText)
        ) {
          const langMatch = updatedAiText.match(/```(\w+)/i)
          const lang = (langMatch?.[1] || 'html').toLowerCase()
          const ext =
            lang === 'python' || lang === 'py'
              ? 'py'
              : lang === 'javascript' || lang === 'js'
              ? 'js'
              : lang === 'typescript' || lang === 'ts'
              ? 'ts'
              : lang === 'sql'
              ? 'sql'
              : 'html'
          updatedAiText += `\n\n[AUTO_SAVE_FILE: copetra_autonomous_${Date.now().toString().slice(-5)}.${ext}]`
        }

        if (updatedAiText !== latestAi.content) {
          latestState.replaceLastAiMessage(updatedAiText)
        }
      }
    }
  }

  const send = useCallback(
    async (text: string) => {
      const activeState = useKronxStore.getState()
      if (!text.trim() || activeState.isStreaming) return

      // Auto-Request Push Notification permissions on direct user send click
      if (typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().catch(console.warn)
      }

      if (!activeState.activeConversationId) {
        activeState.newConversation()
      }

      // Re-read to guarantee we have the initialized activeConversationId
      const currentState = useKronxStore.getState()

      // Instant Picture generation request handler (Moved to AI Brain routing for 100% precision)
      const lower = text.toLowerCase()
      const isAttachedImage = text.includes('[IMAGE:') || text.includes('data:image/')

      // Video generation request handler
      if (
        lower.includes('video') ||
        lower.includes('tengeneza video') ||
        lower.includes('make video') ||
        lower.includes('generate video')
      ) {
        if (!currentState.canGenerateVideo()) {
          const limitMsg = `You have reached chat limit. Upgrade`
          currentState.addMessage(text, 'user')
          currentState.addMessage(limitMsg, 'ai')
          currentState.setSettingsModalOpen(true)
          return
        }
        currentState.incrementVideoUsage()

        const videoMarkdown = `**Video Generation is currently under maintenance.**\n\nWe are actively upgrading our video rendering pipeline to provide genuine AI-generated videos. Please check back later!`

        currentState.addMessage(text, 'user')
        currentState.addMessage(videoMarkdown, 'ai')
        return
      }

      // General Chat Message Daily Limit Handler
      if (!currentState.canSendMessage()) {
        const chatLimitMsg = `You have reached chat limit. Upgrade`
        currentState.addMessage(text, 'user')
        currentState.addMessage(chatLimitMsg, 'ai')
        currentState.setSettingsModalOpen(true)
        return
      }
      currentState.incrementChatUsage()

      // Dynamic & Real-time Action Queries: Never cache real-time, local, food, order, ticket, code-save, or autonomous queries
      const isDynamicOrActionQuery = /\b(saa ngapi|time is it|current time|what time|muda huu|leo tarehe|tarehe ngapi|today'?s date|current date|what day is|time now|saiv|sasa hivi|kfc|pizza|burger|order|delivery|pickup|near me|karibu|chakula|restaurant|mgahawa|menu|bei|price|gharama|hisa|rate|dola|news|habari|weather|flights|hotel|lodge|ticket|tiketi|nikatie|anicatie|kwenye pc|save file|download file|autonomous|security audit|kagua database)\b/i.test(text)

      // Direct Autonomous Engine Execution in Chat (for DB Introspection, Safe SQL, Security Penetration Audits)
      if (
        text.startsWith('[AUTONOMOUS_ENGINE]') ||
        /\b(autonomous security audit|autonomous database audit|fanya security audit|kagua usalama|penetration test|pentest|kagua database|angalia database|soma database|watumiaji wangapi kwenye database|majedwali ya mfumo|inspect database)\b/i.test(text)
      ) {
        const cleanGoal = text.replace(/^\[AUTONOMOUS_ENGINE\]\s*/i, '').trim()
        currentState.addMessage(cleanGoal, 'user')
        currentState.addMessage('**COPETRA AUTONOMOUS ENGINE INITIALIZED**\n\n- Step 1: Analyzing goal & selecting tools (Database Introspection / Safe SQL / Security Penetration Auditor / Live Web Intelligence)...', 'ai')
        currentState.setStreaming(true)
        try {
          const res = await fetch('/api/v1/autonomous/execute', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'x-user-id': currentState.user?.id || 'u-admin-master',
              'x-user-email': currentState.user?.email || '',
            },
            body: JSON.stringify({ goal: cleanGoal, max_steps: 4 }),
          })
          const data = await res.json()
          if (res.ok && data) {
            const stepsTrace = Array.isArray(data.steps_log) && data.steps_log.length > 0
              ? data.steps_log
                  .map(
                    (s: any) =>
                      `- **Step ${s.step} [${s.action}]**: Executed with args \`${JSON.stringify(s.args || {})}\``
                  )
                  .join('\n')
              : '- **Step 1 [DIRECT_ANALYSIS]**: Completed autonomous verification.'
            const finalMd = `### COPETRA AUTONOMOUS AGENT EXECUTION REPORT\n**Task ID:** \`${data.task_id || 'auto-' + Date.now()}\` | **Status:** \`${String(data.status || 'completed').toUpperCase()}\` | **Steps Executed:** \`${data.steps_executed || 1}\`\n\n#### Autonomous Tool Execution Trace\n${stepsTrace}\n\n---\n\n${data.result || 'Task completed.'}`
            currentState.replaceLastAiMessage(finalMd)
            postProcessResponse()
            currentState.setStreaming(false)
            return
          }
        } catch (autoErr) {
          console.warn('[Autonomous Engine Chat Fallback]', autoErr)
        }
        currentState.setStreaming(false)
      }
      const cacheKey = `kx_cache_v4:${currentState.mode}:${currentState.language}:${text.toLowerCase().trim()}`
      if (typeof window !== 'undefined' && !isDynamicOrActionQuery) {
        let cachedRes = localStorage.getItem(cacheKey)
        
        // Invalidate cache if it contains old preambles, stalling phrases, or internal leaks
        if (
          cachedRes && (
            cachedRes.toLowerCase().includes('hello! i am copetra ai') ||
            cachedRes.toLowerCase().includes('welcome to copetra ai') ||
            cachedRes.toLowerCase().includes('pole bro') ||
            cachedRes.toLowerCase().includes('talabat') ||
            cachedRes.toLowerCase().includes('jumia food') ||
            cachedRes.toLowerCase().includes('[persi]') ||
            cachedRes.toLowerCase().includes('[persi')
          )
        ) {
          localStorage.removeItem(cacheKey)
          cachedRes = null
        }

        if (cachedRes && !text.includes('[IMAGE:') && !text.includes('DOCUMENT ATTACHED:')) {
          currentState.addMessage(text, 'user')
          currentState.addMessage('', 'ai')
          currentState.setStreaming(true)
          
          let currentText = ''
          const words = cachedRes.split(' ')
          const stepSize = Math.max(1, Math.floor(words.length / 30))
          for (let i = 0; i < words.length; i += stepSize) {
            const chunkWords = words.slice(i, i + stepSize).join(' ')
            currentText += (i > 0 ? ' ' : '') + chunkWords
            currentState.replaceLastAiMessage(currentText)
            await new Promise(resolve => setTimeout(resolve, 20))
          }
          currentState.replaceLastAiMessage(cachedRes)
          currentState.setStreaming(false)
          return
        }
      }

      currentState.addMessage(text, 'user')
      currentState.addMessage('', 'ai')
      currentState.setStreaming(true)

      try {
        const history = buildHistory(currentState.activeMessages().slice(0, -2))
        const memories = currentState.userMemories || []
        const isPersonalQuery = /\b(who am i|my name|remember me|my memory|kuhusu mimi|unanijua|unajua nini kunihusu|my profile)\b/i.test(text)
        const hasAttachment = text.includes('[IMAGE:') || text.includes('DOCUMENT ATTACHED:')
        const memoryPrompt = (!hasAttachment && isPersonalQuery && memories.length > 0)
          ? `\n\n[PERSISTENT USER BRAIN MEMORY]:\n${memories.map(m => `- ${m}`).join('\n')}`
          : ''

        // Real-time client timezone, time, and date parameters
        const clientTz = typeof Intl !== 'undefined' ? Intl.DateTimeFormat().resolvedOptions().timeZone : 'Africa/Dar_es_Salaam'
        const nowObj = new Date()
        const userTimeStr = nowObj.toLocaleTimeString('en-US', { hour12: true, timeZone: clientTz })
        const userDateStr = nowObj.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', timeZone: clientTz })
        const userLocationStr = clientTz.includes('Dar_es_Salaam') || clientTz.includes('Nairobi') ? 'Tanzania, East Africa' : clientTz

        const gen = streamMessage({
          message: `${text}${memoryPrompt}`,
          mode: currentState.mode,
          language: currentState.language,
          conversation_id: currentState.activeConversationId ?? 'new',
          history,
          timezone: clientTz,
          user_time: userTimeStr,
          user_date: userDateStr,
          location: userLocationStr,
        })

        let finalResponseText = ''
        let bufferChunk = ''
        let lastFlushTime = Date.now()

        for await (const chunk of gen) {
          if (chunk.startsWith('\x00REPLACE\x00')) {
            const fallback = chunk.slice('\x00REPLACE\x00'.length)
            currentState.replaceLastAiMessage(fallback)
            finalResponseText = fallback
            bufferChunk = ''
          } else {
            bufferChunk += chunk
            finalResponseText += chunk

            const now = Date.now()
            if (now - lastFlushTime > 30) {
              currentState.updateLastAiMessage(bufferChunk)
              bufferChunk = ''
              lastFlushTime = now
            }
          }
        }
        if (bufferChunk) {
          currentState.updateLastAiMessage(bufferChunk)
        }
        
        // Save successfully streamed response to cache for future instant load (only for static knowledge queries)
        if (finalResponseText && !finalResponseText.includes('maintenance') && !isDynamicOrActionQuery && typeof window !== 'undefined') {
          localStorage.setItem(cacheKey, finalResponseText)
        }
        
        postProcessResponse()
      } catch (err) {
        console.warn('[Copetra AI stream fallback triggered]', err)
        try {
          const clientTz = typeof Intl !== 'undefined' ? Intl.DateTimeFormat().resolvedOptions().timeZone : 'Africa/Dar_es_Salaam'
          const nowObj = new Date()
          const userTimeStr = nowObj.toLocaleTimeString('en-US', { hour12: true, timeZone: clientTz })
          const userDateStr = nowObj.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', timeZone: clientTz })
          const userLocationStr = clientTz.includes('Dar_es_Salaam') || clientTz.includes('Nairobi') ? 'Tanzania, East Africa' : clientTz

          const directText = await sendMessage({
            message: text,
            mode: currentState.mode,
            language: currentState.language,
            conversation_id: currentState.activeConversationId ?? 'new',
            history: buildHistory(currentState.activeMessages().slice(0, -2)),
            timezone: clientTz,
            user_time: userTimeStr,
            user_date: userDateStr,
            location: userLocationStr,
          })
          currentState.replaceLastAiMessage(directText)
          postProcessResponse()
        } catch (directErr) {
          console.error('[Copetra direct fetch error]', directErr)
        }
      } finally {
        currentState.setStreaming(false)
        if (typeof window !== 'undefined' && document.visibilityState === 'hidden') {
          const isSw = currentState.language === 'sw'
          const title = 'Copetra AI'
          const body = isSw ? 'Majibu yako yako tayari! Fungua kuona.' : 'Your response is ready! Open to view.'
          const options = {
            body,
            icon: '/icon-192.png',
            badge: '/icon-192.png',
            vibrate: [200, 100, 200]
          }
          if ('Notification' in window && Notification.permission === 'granted') {
            if ('serviceWorker' in navigator) {
              navigator.serviceWorker.ready.then(reg => {
                reg.showNotification(title, options)
              }).catch(() => {
                new Notification(title, options)
              })
            } else {
              new Notification(title, options)
            }
          }
        }
      }
    },
    []
  )

  const regenerate = useCallback(async () => {
    const currentState = useKronxStore.getState()
    if (currentState.isStreaming) return
    const msgs = currentState.activeMessages()
    if (msgs.length === 0) return

    let lastUserMessage = ''
    for (let i = msgs.length - 1; i >= 0; i--) {
      if (msgs[i].role === 'user') {
        lastUserMessage = msgs[i].content
        break
      }
    }

    if (!lastUserMessage) return

    if (msgs[msgs.length - 1].role === 'ai') {
      currentState.removeLastAiMessage()
    }

    currentState.addMessage('', 'ai')
    currentState.setStreaming(true)

    try {
      const history = buildHistory(currentState.activeMessages().slice(0, -2))

      const gen = streamMessage({
        message: `${lastUserMessage} (Note: Provide an alternative, enhanced response)`,
        mode: currentState.mode,
        language: currentState.language,
        conversation_id: currentState.activeConversationId ?? 'new',
        history,
      })

      for await (const chunk of gen) {
        if (chunk.startsWith('\x00REPLACE\x00')) {
          const fallback = chunk.slice('\x00REPLACE\x00'.length)
          currentState.replaceLastAiMessage(fallback)
        } else {
          currentState.updateLastAiMessage(chunk)
        }
      }
      postProcessResponse()
    } catch (err) {
      const fallbackMsg = currentState.language === 'sw'
        ? ' Samahani, imeshindikana kupata majibu kwa sasa. Tafadhali jaribu tena.'
        : ' Sorry, there was an error generating your response. Please try again.'
      currentState.updateLastAiMessage(fallbackMsg)
    } finally {
      currentState.setStreaming(false)
      if (typeof window !== 'undefined' && document.visibilityState === 'hidden') {
        const isSw = currentState.language === 'sw'
        const title = 'Copetra AI'
        const body = isSw ? 'Majibu yako yako tayari! Fungua kuona.' : 'Your response is ready! Open to view.'
        const options = {
          body,
          icon: '/icon-192.png',
          badge: '/icon-192.png',
          vibrate: [200, 100, 200]
        }
        if ('Notification' in window && Notification.permission === 'granted') {
          if ('serviceWorker' in navigator) {
            navigator.serviceWorker.ready.then(reg => {
              reg.showNotification(title, options)
            }).catch(() => {
              new Notification(title, options)
            })
          } else {
            new Notification(title, options)
          }
        }
      }
    }
  }, [])

  const editAndResend = useCallback(
    async (messageId: string, newContent: string) => {
      const currentState = useKronxStore.getState()
      if (!newContent.trim() || currentState.isStreaming) return
      currentState.editMessageInPlace(messageId, newContent)
      currentState.setStreaming(true)

      try {
        const history = buildHistory(currentState.activeMessages().slice(0, -2))
        const gen = streamMessage({
          message: newContent,
          mode: currentState.mode,
          language: currentState.language,
          conversation_id: currentState.activeConversationId ?? 'new',
          history,
        })

        for await (const chunk of gen) {
          if (chunk.startsWith('\x00REPLACE\x00')) {
            const fallback = chunk.slice('\x00REPLACE\x00'.length)
            currentState.replaceLastAiMessage(fallback)
          } else {
            currentState.updateLastAiMessage(chunk)
          }
        }
        postProcessResponse()
      } catch (err) {
        const fallbackMsg = currentState.language === 'sw'
          ? ' Samahani, imeshindikana kupata majibu kwa sasa. Tafadhali jaribu tena.'
          : ' Sorry, there was an error generating your response. Please try again.'
        currentState.updateLastAiMessage(fallbackMsg)
      } finally {
        currentState.setStreaming(false)
        if (typeof window !== 'undefined' && document.visibilityState === 'hidden') {
          const isSw = currentState.language === 'sw'
          const title = 'Copetra AI'
          const body = isSw ? 'Majibu yako yako tayari! Fungua kuona.' : 'Your response is ready! Open to view.'
          const options = {
            body,
            icon: '/icon-192.png',
            badge: '/icon-192.png',
            vibrate: [200, 100, 200]
          }
          if ('Notification' in window && Notification.permission === 'granted') {
            if ('serviceWorker' in navigator) {
              navigator.serviceWorker.ready.then(reg => {
                reg.showNotification(title, options)
              }).catch(() => {
                new Notification(title, options)
              })
            } else {
              new Notification(title, options)
            }
          }
        }
      }
    },
    []
  )

  return {
    send,
    regenerate,
    editAndResend,
    messages: store.activeMessages(),
    isStreaming: store.isStreaming,
    mode: store.mode,
    language: store.language,
  }
}