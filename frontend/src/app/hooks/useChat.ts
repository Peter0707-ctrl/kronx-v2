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
          store.updateLastAiMessage(chunk)
        }
      } catch (err) {
        const msg =
          store.language === 'sw'
            ? ' Hitilafu — tafadhali jaribu tena. (Connection error)'
            : ' Something went wrong — please try again.'
        store.updateLastAiMessage(msg)
        console.error('[Kronx chat error]', err)
      } finally {
        store.setStreaming(false)
      }
    },
    [store]
  )

  return {
    send,
    messages: store.activeMessages(),
    isStreaming: store.isStreaming,
    mode: store.mode,
    language: store.language,
  }
}