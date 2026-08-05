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

      // Auto-Request Push Notification permissions on direct user send click
      if (typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().catch(console.warn)
      }

      if (!activeState.activeConversationId) {
        activeState.newConversation()
      }

      // Re-read to guarantee we have the initialized activeConversationId
      const currentState = useKronxStore.getState()

      // Instant Picture generation request handler (Skip if user is uploading/analyzing an image)
      const lower = text.toLowerCase()
      const isAttachedImage = text.includes('[IMAGE:') || text.includes('data:image/')

      if (
        !isAttachedImage &&
        (
          lower.startsWith('generate image') ||
          lower.startsWith('create image') ||
          lower.startsWith('draw') ||
          lower.startsWith('generate picture') ||
          lower.startsWith('make image') ||
          lower.startsWith('tengeneza picha') ||
          lower.includes('draw a ') ||
          lower.includes('generate an image') ||
          lower.includes('create an image')
        )
      ) {
        if (!currentState.canGeneratePicture()) {
          const limitMsg = `You have reached chat limit. Upgrade`
          currentState.addMessage(text, 'user')
          currentState.addMessage(limitMsg, 'ai')
          currentState.setSettingsModalOpen(true)
          return
        }
        currentState.incrementPictureUsage()

        let subjectPrompt = text
          .replace(/^(generate|create|draw|make|show)\s+(me\s+)?(an?\s+)?(image|picture|photo|illustration|art)\s+(of\s+)?/i, '')
          .replace(/^(tengeneza|chora)\s+(picha)\s+(ya\s+)?/i, '')
          .trim()
        if (!subjectPrompt) subjectPrompt = text.trim()

        const enhancedPrompt = `${subjectPrompt}, 8k resolution, highly detailed, photorealistic, cinematic lighting, masterpiece`
        const encodedPrompt = encodeURIComponent(enhancedPrompt)
        const pollinationsUrl = `https://image.pollinations.ai/prompt/${encodedPrompt}?width=1024&height=1024&model=flux&seed=${Math.floor(Math.random()*100000)}&nologo=true`

        const imageMarkdown = `Here is your high-fidelity generated image for **"${subjectPrompt}"**:\n\n![Generated Image](${pollinationsUrl})`

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

      currentState.addMessage(text, 'user')
      currentState.addMessage('', 'ai')
      currentState.setStreaming(true)

      try {
        const history = buildHistory(currentState.activeMessages())
        const memories = currentState.userMemories || []
        const memoryPrompt = memories.length > 0 ? `\n\n[PERSISTENT USER BRAIN MEMORY]:\n${memories.map(m => `- ${m}`).join('\n')}` : ''

        const gen = streamMessage({
          message: `${text}${memoryPrompt}`,
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
        if (typeof window !== 'undefined' && document.visibilityState === 'hidden') {
          const isSw = currentState.language === 'sw'
          const title = '📚 Copetra AI'
          const body = isSw ? 'Majibu yako yako tayari! Fungua kuona.' : 'Your response is ready! Open to view.'
          const options = {
            body,
            icon: '/kronx_logo.jpg',
            badge: '/kronx_logo.jpg',
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
        ? '⚠️ Samahani, imeshindikana kupata majibu kwa sasa. Tafadhali jaribu tena.'
        : '⚠️ Sorry, there was an error generating your response. Please try again.'
      currentState.updateLastAiMessage(fallbackMsg)
    } finally {
      currentState.setStreaming(false)
      if (typeof window !== 'undefined' && document.visibilityState === 'hidden') {
        const isSw = currentState.language === 'sw'
        const title = '📚 Copetra AI'
        const body = isSw ? 'Majibu yako yako tayari! Fungua kuona.' : 'Your response is ready! Open to view.'
        const options = {
          body,
          icon: '/kronx_logo.jpg',
          badge: '/kronx_logo.jpg',
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
      } catch (err) {
        const fallbackMsg = currentState.language === 'sw'
          ? '⚠️ Samahani, imeshindikana kupata majibu kwa sasa. Tafadhali jaribu tena.'
          : '⚠️ Sorry, there was an error generating your response. Please try again.'
        currentState.updateLastAiMessage(fallbackMsg)
      } finally {
        currentState.setStreaming(false)
        if (typeof window !== 'undefined' && document.visibilityState === 'hidden') {
          const isSw = currentState.language === 'sw'
          const title = '📚 Copetra AI'
          const body = isSw ? 'Majibu yako yako tayari! Fungua kuona.' : 'Your response is ready! Open to view.'
          const options = {
            body,
            icon: '/kronx_logo.jpg',
            badge: '/kronx_logo.jpg',
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