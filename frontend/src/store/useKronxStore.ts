import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { v4 as uuid } from 'uuid'
import { ActiveView, Conversation, KronxMode, Language, Message, UserGoal, UserProfile, UserRole } from '@/types'


interface KronxStore {
  activeConversationId: string | null
  conversations: Conversation[]
  mode: KronxMode
  language: Language
  isStreaming: boolean
  activeView: ActiveView
  goals: UserGoal[]
  user: UserProfile | null
  authModalOpen: boolean
  settingsModalOpen: boolean
  sidebarOpen: boolean

  toggleSidebar: () => void

  newConversation: () => void
  selectConversation: (id: string) => void
  deleteConversation: (id: string) => void
  clearAllConversations: () => void
  clearActiveConversationMessages: () => void

  setUser: (user: UserProfile | null) => void
  setAuthModalOpen: (open: boolean) => void
  setSettingsModalOpen: (open: boolean) => void
  loginUser: (user: UserProfile) => void
  logoutUser: () => void
  updateUserRole: (role: UserRole) => void
  upgradeSubscription: (plan: 'free' | 'premium') => void
  generateApiKey: () => string
  canGeneratePicture: () => boolean
  canGenerateVideo: () => boolean
  canSendMessage: () => boolean
  incrementPictureUsage: () => void
  incrementVideoUsage: () => void
  incrementChatUsage: () => void
  systemDisabled: boolean
  toggleSystemKillSwitch: (disabled: boolean) => void


  addMessage: (content: string, role: 'user' | 'ai') => Message
  updateLastAiMessage: (chunk: string) => void
  replaceLastAiMessage: (content: string) => void
  removeLastAiMessage: () => void
  editUserMessage: (messageId: string, newContent: string) => void
  editMessageInPlace: (messageId: string, newContent: string) => void

  setMode: (mode: KronxMode) => void
  setLanguage: (lang: Language) => void
  setStreaming: (val: boolean) => void
  setActiveView: (view: ActiveView) => void

  addGoal: (title: string, category: UserGoal['category']) => void
  toggleGoal: (id: string) => void
  deleteGoal: (id: string) => void

  activeConversation: () => Conversation | null
  activeMessages: () => Message[]
}

const DEFAULT_GOALS: UserGoal[] = [
  { id: 'g-1', title: 'Plan M-Pesa kiosk business budget (TZS 1.5M)', category: 'business', completed: false, createdAt: new Date().toISOString() },
  { id: 'g-2', title: 'Learn Swahili business vocabulary & greetings', category: 'education', completed: true, createdAt: new Date().toISOString() },
  { id: 'g-3', title: 'Build modern Next.js AI companion app', category: 'personal', completed: true, createdAt: new Date().toISOString() },
]

const DEFAULT_USER: UserProfile = {
  id: 'u-1',
  name: 'User',
  email: 'user@kronx.ai',
  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=John',
  role: 'user',
  plan: 'free',
  picturesUsedToday: 0,
  videosUsedToday: 0,
  chatsUsedToday: 0,
  provider: 'email',
  createdAt: new Date().toISOString(),
}

export const useKronxStore = create<KronxStore>()(
  persist(
    (set, get) => ({
      activeConversationId: null,
      conversations: [],
      mode: 'Friend',
      language: 'en',
      isStreaming: false,
      activeView: 'chat',
      goals: DEFAULT_GOALS,
      user: DEFAULT_USER,
      authModalOpen: false,
      settingsModalOpen: false,
      sidebarOpen: true,
      setSettingsModalOpen: (settingsModalOpen: boolean) => set({ settingsModalOpen }),
      toggleSidebar: () => set(s => ({ sidebarOpen: !s.sidebarOpen })),


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
          activeView: 'chat',
        }))
      },

      selectConversation: (id) => set({ activeConversationId: id, activeView: 'chat' }),

      deleteConversation: (id) =>
        set(s => ({
          conversations: s.conversations.filter(c => c.id !== id),
          activeConversationId:
            s.activeConversationId === id ? null : s.activeConversationId,
        })),

      clearAllConversations: () =>
        set({ conversations: [], activeConversationId: null }),

      clearActiveConversationMessages: () =>
        set(s => ({
          conversations: s.conversations.map(c =>
            c.id === s.activeConversationId ? { ...c, messages: [] } : c
          ),
        })),


      setUser: (user) => set({ user }),
      setAuthModalOpen: (authModalOpen) => set({ authModalOpen }),
      loginUser: (user) => set({ user, activeView: 'chat', authModalOpen: false }),
      logoutUser: () => set({ user: null, activeView: 'landing' }),
      updateUserRole: (role) =>
        set(s => ({
          user: s.user ? { ...s.user, role } : null,
        })),
      upgradeSubscription: (plan) =>
        set(s => {
          if (!s.user) return { user: null }
          const apiKey = plan === 'premium' ? (s.user.apiKey || 'kx-live-' + Math.random().toString(36).substring(2, 10) + Math.random().toString(36).substring(2, 10)) : undefined
          return { user: { ...s.user, plan, apiKey } }
        }),
      generateApiKey: () => {
        const key = 'kx-live-' + Math.random().toString(36).substring(2, 10) + Math.random().toString(36).substring(2, 10)
        set(s => ({
          user: s.user ? { ...s.user, apiKey: key } : null
        }))
        return key
      },
      systemDisabled: false,
      toggleSystemKillSwitch: (disabled) => set({ systemDisabled: disabled }),
      canGeneratePicture: () => {
        const u = get().user
        if (!u) return false
        if (u.plan === 'premium') return true
        const now = Date.now()
        const lastReset = u.lastResetTimestamp ? new Date(u.lastResetTimestamp).getTime() : 0
        const sixHoursMs = 6 * 60 * 60 * 1000
        if (now - lastReset > sixHoursMs) {
          // Reset 6-hour window
          set(s => ({ user: s.user ? { ...s.user, picturesUsedToday: 0, videosUsedToday: 0, chatsUsedToday: 0, lastResetTimestamp: new Date().toISOString() } : null }))
          return true
        }
        return (u.picturesUsedToday || 0) < 3 && (u.chatsUsedToday || 0) < 10
      },
      canGenerateVideo: () => {
        const u = get().user
        if (!u) return false
        if (u.plan === 'premium') return true
        const now = Date.now()
        const lastReset = u.lastResetTimestamp ? new Date(u.lastResetTimestamp).getTime() : 0
        const sixHoursMs = 6 * 60 * 60 * 1000
        if (now - lastReset > sixHoursMs) {
          set(s => ({ user: s.user ? { ...s.user, picturesUsedToday: 0, videosUsedToday: 0, chatsUsedToday: 0, lastResetTimestamp: new Date().toISOString() } : null }))
          return true
        }
        return (u.videosUsedToday || 0) < 1 && (u.chatsUsedToday || 0) < 10
      },
      canSendMessage: () => {
        const u = get().user
        if (!u) return true
        if (u.plan === 'premium') return true
        const now = Date.now()
        const lastReset = u.lastResetTimestamp ? new Date(u.lastResetTimestamp).getTime() : 0
        const sixHoursMs = 6 * 60 * 60 * 1000
        if (now - lastReset > sixHoursMs) {
          // Reset 6-hour window
          set(s => ({ user: s.user ? { ...s.user, picturesUsedToday: 0, videosUsedToday: 0, chatsUsedToday: 0, lastResetTimestamp: new Date().toISOString() } : null }))
          return true
        }
        return (u.chatsUsedToday || 0) < 10
      },
      incrementPictureUsage: () =>
        set(s => ({
          user: s.user ? { ...s.user, picturesUsedToday: (s.user.picturesUsedToday || 0) + 1 } : null,
        })),
      incrementVideoUsage: () =>
        set(s => ({
          user: s.user ? { ...s.user, videosUsedToday: (s.user.videosUsedToday || 0) + 1 } : null,
        })),
      incrementChatUsage: () =>
        set(s => ({
          user: s.user ? { ...s.user, chatsUsedToday: (s.user.chatsUsedToday || 0) + 1 } : null,
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
            const updatedMsgs = [...c.messages, msg].slice(-50)
            return {
              ...c,
              title: isFirst ? content.slice(0, 48) : c.title,
              messages: updatedMsgs,
              updatedAt: new Date(),
            }
          })
          return { conversations: convs.slice(0, 25) }
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

      replaceLastAiMessage: (content) =>
        set(s => ({
          conversations: s.conversations.map(c => {
            if (c.id !== s.activeConversationId) return c
            const msgs = [...c.messages]
            if (msgs.length > 0 && msgs[msgs.length - 1].role === 'ai') {
              msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], content }
            }
            return { ...c, messages: msgs }
          }),
        })),

      removeLastAiMessage: () =>
        set(s => ({
          conversations: s.conversations.map(c => {
            if (c.id !== s.activeConversationId) return c
            const msgs = [...c.messages]
            if (msgs.length > 0 && msgs[msgs.length - 1].role === 'ai') {
              msgs.pop()
            }
            return { ...c, messages: msgs }
          }),
        })),

      editUserMessage: (messageId, newContent) =>
        set(s => ({
          conversations: s.conversations.map(c => {
            if (c.id !== s.activeConversationId) return c
            const msgs = c.messages.map(m =>
              m.id === messageId ? { ...m, content: newContent } : m
            )
            return { ...c, messages: msgs }
          }),
        })),

      editMessageInPlace: (messageId, newContent) =>
        set(s => ({
          conversations: s.conversations.map(c => {
            if (c.id !== s.activeConversationId) return c
            const targetIdx = c.messages.findIndex(m => m.id === messageId)
            if (targetIdx === -1) return c
            const truncated = c.messages.slice(0, targetIdx)
            const editedUserMsg: Message = {
              id: messageId,
              role: 'user',
              content: newContent,
              timestamp: new Date(),
              mode: s.mode,
              lang: s.language,
            }
            const aiMsg: Message = {
              id: 'msg-' + Date.now(),
              role: 'ai',
              content: '',
              timestamp: new Date(),
              mode: s.mode,
              lang: s.language,
            }
            return { ...c, messages: [...truncated, editedUserMsg, aiMsg] }
          }),
        })),

      setMode: (mode) => set({ mode }),
      setLanguage: (language) => set({ language }),
      setStreaming: (val) => set({ isStreaming: val }),
      setActiveView: (activeView) => set({ activeView }),

      addGoal: (title, category) => {
        const goal: UserGoal = {
          id: uuid(),
          title,
          category,
          completed: false,
          createdAt: new Date().toISOString(),
        }
        set(s => ({ goals: [goal, ...s.goals] }))
      },

      toggleGoal: (id) =>
        set(s => ({
          goals: s.goals.map(g => (g.id === id ? { ...g, completed: !g.completed } : g)),
        })),

      deleteGoal: (id) => set(s => ({ goals: s.goals.filter(g => g.id !== id) })),

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
        conversations: s.conversations.slice(0, 20),
        mode: s.mode,
        language: s.language,
        activeConversationId: s.activeConversationId,
        goals: s.goals,
        activeView: s.activeView,
        user: s.user,
        systemDisabled: s.systemDisabled,
      }),
    }
  )
)

