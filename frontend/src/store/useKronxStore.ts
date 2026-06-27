import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { v4 as uuid } from 'uuid'
import { Conversation, KronxMode, Language, Message } from '@/types'

interface KronxStore {
  activeConversationId: string | null
  conversations: Conversation[]
  mode: KronxMode
  language: Language
  isStreaming: boolean

  newConversation: () => void
  selectConversation: (id: string) => void
  deleteConversation: (id: string) => void

  addMessage: (content: string, role: 'user' | 'ai') => Message
  updateLastAiMessage: (chunk: string) => void

  setMode: (mode: KronxMode) => void
  setLanguage: (lang: Language) => void
  setStreaming: (val: boolean) => void

  activeConversation: () => Conversation | null
  activeMessages: () => Message[]
}

export const useKronxStore = create<KronxStore>()(
  persist(
    (set, get) => ({
      activeConversationId: null,
      conversations: [],
      mode: 'Friend',
      language: 'sw',
      isStreaming: false,

      newConversation: () => {
        const conv: Conversation = {
          id: uuid(),
          title: 'Mazungumzo mapya · New conversation',
          messages: [],
          createdAt: new Date(),
          updatedAt: new Date(),
          mode: get().mode,
        }
        set(s => ({
          conversations: [conv, ...s.conversations],
          activeConversationId: conv.id,
        }))
      },

      selectConversation: (id) => set({ activeConversationId: id }),

      deleteConversation: (id) =>
        set(s => ({
          conversations: s.conversations.filter(c => c.id !== id),
          activeConversationId:
            s.activeConversationId === id ? null : s.activeConversationId,
        })),

      addMessage: (content, role) => {
        const msg: Message = {
          id: uuid(),
          role,
          content,
          timestamp: new Date(),
          mode: get().mode,
          lang: get().language,
        }
        set(s => {
          const convs = s.conversations.map(c => {
            if (c.id !== s.activeConversationId) return c
            const isFirst = c.messages.length === 0 && role === 'user'
            return {
              ...c,
              title: isFirst ? content.slice(0, 48) : c.title,
              messages: [...c.messages, msg],
              updatedAt: new Date(),
            }
          })
          return { conversations: convs }
        })
        return msg
      },

      updateLastAiMessage: (chunk) => {
        set(s => {
          const convs = s.conversations.map(c => {
            if (c.id !== s.activeConversationId) return c
            const msgs = [...c.messages]
            const last = msgs[msgs.length - 1]
            if (last?.role === 'ai') {
              msgs[msgs.length - 1] = { ...last, content: last.content + chunk }
            }
            return { ...c, messages: msgs }
          })
          return { conversations: convs }
        })
      },

      setMode: (mode) => set({ mode }),
      setLanguage: (language) => set({ language }),
      setStreaming: (val) => set({ isStreaming: val }),

      activeConversation: () => {
        const { conversations, activeConversationId } = get()
        return conversations.find(c => c.id === activeConversationId) ?? null
      },

      activeMessages: () => {
        return get().activeConversation()?.messages ?? []
      },
    }),
    {
      name: 'kronx-store',
      partialize: (s) => ({
        conversations: s.conversations,
        mode: s.mode,
        language: s.language,
        activeConversationId: s.activeConversationId,
      }),
    }
  )
)