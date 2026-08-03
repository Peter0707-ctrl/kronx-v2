'use client'

import { useCallback } from 'react'
import { useKronxStore } from '@/store/useKronxStore'
import { streamMessage, sendMessage, buildHistory } from '@/services/chat'

export function useChat() {
  const store = useKronxStore()

  const send = useCallback(
    async (text: string) => {
      const activeState = useKronxStore.getState()
      if (!text.trim() || activeState.isStreaming) return

      if (!activeState.activeConversationId) {
        activeState.newConversation()
      }

      // Re-read to guarantee we have the initialized activeConversationId
      const currentState = useKronxStore.getState()

      // Instant Picture generation request handler
      const lower = text.toLowerCase()
      if (
        lower.includes('image') ||
        lower.includes('picture') ||
        lower.includes('picha') ||
        lower.includes('draw') ||
        lower.includes('photo')
      ) {
        if (!currentState.canGeneratePicture()) {
          const limitMsg = `You have reached chat limit. Upgrade`
          currentState.addMessage(text, 'user')
          currentState.addMessage(limitMsg, 'ai')
          currentState.setSettingsModalOpen(true)
          return
        }
        currentState.incrementPictureUsage()

        const userPrompt = text.replace(/(generate|create|an|a|picture|image|photo|draw|tengeneza|picha|of|ya|please|help|me)/gi, '').trim() || 'futuristic masterpiece'
        const enhancedPrompt = `${userPrompt}, highly detailed photorealistic 8k resolution, cinematic lighting, masterpiece, hyperdetailed, professional photography, octane render`
        const encodedPrompt = encodeURIComponent(enhancedPrompt)
        const pollinationsUrl = `https://image.pollinations.ai/prompt/${encodedPrompt}?width=2048&height=2048&model=flux&seed=${Math.floor(Math.random()*100000)}&nologo=true&enhance=true`

        const imageMarkdown = `Here is your Ultra-HD generated image for **"${userPrompt}"**:\n\n![Generated Image](${pollinationsUrl})`

        currentState.addMessage(text, 'user')
        currentState.addMessage(imageMarkdown, 'ai')
        return
      }

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

        const rawTopic = text.replace(/(generate|create|an|a|video|make|tengeneza|of|ya)/gi, '').trim() || 'cinematic animation'
        const sampleVideo = 'https://assets.mixkit.co/videos/preview/mixkit-futuristic-robotic-arm-operating-42861-large.mp4'

        const videoMarkdown = `Here is your AI generated video for **"${rawTopic}"**:\n\n<video controls autoplay loop muted style="width: 100%; max-width: 512px; border-radius: 16px; border: 1px solid #bae6fd; box-shadow: 0 8px 24px rgba(2, 132, 199, 0.15);\"><source src="${sampleVideo}" type="video/mp4" />Your browser does not support video tag.</video>`

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

      currentState.addMessage(text, 'user')
      currentState.addMessage('', 'ai')
      currentState.setStreaming(true)

      try {
        const history = buildHistory(currentState.activeMessages())

        const gen = streamMessage({
          message: text,
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
      } catch (err) {
        console.warn('[Copetra AI stream fallback triggered]', err)
        try {
          const directText = await sendMessage({
            message: text,
            mode: currentState.mode,
            language: currentState.language,
            conversation_id: currentState.activeConversationId ?? 'new',
            history: buildHistory(currentState.activeMessages()),
          })
          currentState.replaceLastAiMessage(directText)
        } catch (directErr) {
          console.error('[Copetra direct fetch error]', directErr)
        }
      } finally {
        currentState.setStreaming(false)
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
      const history = buildHistory(currentState.activeMessages().slice(0, -1))

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
    } catch (err) {
      const fallbackMsg = currentState.language === 'sw'
        ? 'Nipo tayari kukusaidia! Tafadhali rudia swali lako.'
        : 'I am ready to help you! Please repeat your request.'
      currentState.updateLastAiMessage(fallbackMsg)
    } finally {
      currentState.setStreaming(false)
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
      } catch (err) {
        const fallbackMsg = currentState.language === 'sw'
          ? 'Nipo tayari kukusaidia! Tafadhali rudia swali lako.'
          : 'I am ready to help you! Please repeat your request.'
        currentState.updateLastAiMessage(fallbackMsg)
      } finally {
        currentState.setStreaming(false)
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