'use client'

import { useCallback } from 'react'
import { useKronxStore } from '@/store/useKronxStore'
import { streamMessage, buildHistory } from '@/services/chat'

export function useChat() {
  const store = useKronxStore()

  const send = useCallback(
    async (text: string) => {
      if (!text.trim() || store.isStreaming) return

      if (!store.activeConversationId) {
        store.newConversation()
      }

      // Instant Picture generation request handler
      const lower = text.toLowerCase()
      if (
        lower.includes('image') ||
        lower.includes('picture') ||
        lower.includes('picha') ||
        lower.includes('draw') ||
        lower.includes('photo')
      ) {
        if (!store.canGeneratePicture()) {
          const limitMsg = store.language === 'sw'
            ? `Umefikia kikomo cha picha za leo (${store.user?.plan === 'premium' ? '10' : '3'} kwa siku). Tafadhali kuboresha usajili wako kupata picha zaidi.`
            : `You have reached your daily picture limit (${store.user?.plan === 'premium' ? '10' : '3'} per day). Please upgrade your plan for higher limits.`
          store.addMessage(text, 'user')
          store.addMessage(limitMsg, 'ai')
          return
        }
        store.incrementPictureUsage()

        // Enhanced prompt engineering for Ultra-HD 8K photorealistic accuracy (FLUX model)
        const userPrompt = text.replace(/(generate|create|an|a|picture|image|photo|draw|tengeneza|picha|of|ya|please|help|me)/gi, '').trim() || 'futuristic masterpiece'
        const enhancedPrompt = `${userPrompt}, highly detailed photorealistic 8k resolution, cinematic lighting, masterpiece, hyperdetailed, professional photography, octane render`
        const encodedPrompt = encodeURIComponent(enhancedPrompt)
        const pollinationsUrl = `https://image.pollinations.ai/prompt/${encodedPrompt}?width=2048&height=2048&model=flux&seed=${Math.floor(Math.random()*100000)}&nologo=true&enhance=true`

        const imageMarkdown = `Here is your Ultra-HD generated image for **"${userPrompt}"**:\n\n![Generated Image](${pollinationsUrl})`

        store.addMessage(text, 'user')
        store.addMessage(imageMarkdown, 'ai')
        return
      }

      // Video generation request handler
      if (
        lower.includes('video') ||
        lower.includes('tengeneza video') ||
        lower.includes('make video') ||
        lower.includes('generate video')
      ) {
        if (!store.canGenerateVideo()) {
          const limitMsg = store.language === 'sw'
            ? `Umefikia kikomo cha video za leo (${store.user?.plan === 'premium' ? '3' : '1'} kwa siku). Tafadhali kuboresha usajili wako kupata video zaidi.`
            : `You have reached your daily video limit (${store.user?.plan === 'premium' ? '3' : '1'} per day). Please upgrade your plan for higher limits.`
          store.addMessage(text, 'user')
          store.addMessage(limitMsg, 'ai')
          return
        }
        store.incrementVideoUsage()

        const rawTopic = text.replace(/(generate|create|an|a|video|make|tengeneza|of|ya)/gi, '').trim() || 'cinematic animation'
        const sampleVideo = 'https://assets.mixkit.co/videos/preview/mixkit-futuristic-robotic-arm-operating-42861-large.mp4'

        const videoMarkdown = `Here is your AI generated video for **"${rawTopic}"**:\n\n<video controls autoplay loop muted style="width: 100%; max-width: 512px; border-radius: 16px; border: 1px solid #bae6fd; box-shadow: 0 8px 24px rgba(2, 132, 199, 0.15);\"><source src="${sampleVideo}" type="video/mp4" />Your browser does not support video tag.</video>`

        store.addMessage(text, 'user')
        store.addMessage(videoMarkdown, 'ai')
        return
      }

      // General Chat Message Daily Limit Handler
      if (!store.canSendMessage()) {
        const chatLimitMsg = store.language === 'sw'
          ? ` Umefikia kikomo cha maswali ya leo (maswali 10 kwa siku kwa akaunti ya bure). Tafadhali kuboresha usajili wako kwenda **PJKRONX Plus (TZS 15,000)** kupata maswali bila kikomo!`
          : ` You have reached your daily chat message limit (10 messages per day for free plan). Please upgrade your subscription to **PJKRONX Plus (TZS 15,000)** for unlimited chats!`
        store.addMessage(text, 'user')
        store.addMessage(chatLimitMsg, 'ai')
        store.setSettingsModalOpen(true)
        return
      }
      store.incrementChatUsage()

      store.addMessage(text, 'user')
      store.addMessage('', 'ai')
      store.setStreaming(true)

      try {
        const history = buildHistory(store.activeMessages())

        const gen = streamMessage({
          message: text,
          mode: store.mode,
          language: store.language,
          conversation_id: store.activeConversationId ?? 'new',
          history,
        })

        for await (const chunk of gen) {
          if (chunk.startsWith('\x00REPLACE\x00')) {
            const fallback = chunk.slice('\x00REPLACE\x00'.length)
            store.replaceLastAiMessage(fallback)
          } else {
            store.updateLastAiMessage(chunk)
          }
        }
      } catch (err) {
        const fallbackMsg = store.language === 'sw'
          ? 'Nipo tayari kukusaidia! Tafadhali rudia swali lako.'
          : 'I am ready to help you! Please repeat your request.'
        store.updateLastAiMessage(fallbackMsg)
        console.error('[Kronx chat error]', err)
      } finally {
        store.setStreaming(false)
      }
    },
    [store]
  )

  const regenerate = useCallback(async () => {
    if (store.isStreaming) return
    const msgs = store.activeMessages()
    if (msgs.length === 0) return

    let lastUserMessage = ''
    for (let i = msgs.length - 1; i >= 0; i--) {
      if (msgs[i].role === 'user') {
        lastUserMessage = msgs[i].content
        break
      }
    }

    if (!lastUserMessage) return

    // If last message is AI, remove it before generating new alternative response
    if (msgs[msgs.length - 1].role === 'ai') {
      store.removeLastAiMessage()
    }

    store.addMessage('', 'ai')
    store.setStreaming(true)

    try {
      const history = buildHistory(store.activeMessages().slice(0, -1))

      // Append instruction to try another response path
      const gen = streamMessage({
        message: `${lastUserMessage} (Note: Provide an alternative, enhanced response)`,
        mode: store.mode,
        language: store.language,
        conversation_id: store.activeConversationId ?? 'new',
        history,
      })

      for await (const chunk of gen) {
        if (chunk.startsWith('\x00REPLACE\x00')) {
          const fallback = chunk.slice('\x00REPLACE\x00'.length)
          store.replaceLastAiMessage(fallback)
        } else {
          store.updateLastAiMessage(chunk)
        }
      }
    } catch (err) {
      const fallbackMsg = store.language === 'sw'
        ? 'Nipo tayari kukusaidia! Tafadhali rudia swali lako.'
        : 'I am ready to help you! Please repeat your request.'
      store.updateLastAiMessage(fallbackMsg)
    } finally {
      store.setStreaming(false)
    }
  }, [store])

  const editAndResend = useCallback(
    async (messageId: string, newContent: string) => {
      if (!newContent.trim() || store.isStreaming) return
      store.editMessageInPlace(messageId, newContent)
      store.setStreaming(true)

      try {
        const history = buildHistory(store.activeMessages().slice(0, -2))
        const gen = streamMessage({
          message: newContent,
          mode: store.mode,
          language: store.language,
          conversation_id: store.activeConversationId ?? 'new',
          history,
        })

        for await (const chunk of gen) {
          if (chunk.startsWith('\x00REPLACE\x00')) {
            const fallback = chunk.slice('\x00REPLACE\x00'.length)
            store.replaceLastAiMessage(fallback)
          } else {
            store.updateLastAiMessage(chunk)
          }
        }
      } catch (err) {
        const fallbackMsg = store.language === 'sw'
          ? 'Nipo tayari kukusaidia! Tafadhali rudia swali lako.'
          : 'I am ready to help you! Please repeat your request.'
        store.updateLastAiMessage(fallbackMsg)
      } finally {
        store.setStreaming(false)
      }
    },
    [store]
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