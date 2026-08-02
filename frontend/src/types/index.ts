export type KronxMode = 'Friend' | 'Teacher' | 'Business' | 'Research' | 'Quick'

export type Language = 'sw' | 'en'

export type ActiveView = 'landing' | 'chat' | 'dashboard' | 'admin'

export type UserRole = 'user' | 'admin'

export type SubscriptionPlan = 'free' | 'premium'

export interface UserProfile {
  id: string
  name: string
  email: string
  avatar: string
  role: UserRole
  plan: SubscriptionPlan
  apiKey?: string
  picturesUsedToday: number
  videosUsedToday: number
  chatsUsedToday: number
  lastResetTimestamp?: string
  provider: 'google' | 'email'
  createdAt: string
}

export interface Message {
  id: string
  role: 'user' | 'ai'
  content: string
  timestamp: Date
  mode: KronxMode
  lang: Language
}

export interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
  updatedAt: Date
  mode: KronxMode
}

export interface ModeConfig {
  key: KronxMode
  labelSw: string
  labelEn: string
  color: string
  pip: string
}

export interface SuggestionCard {
  mode: KronxMode
  labelSw: string
  labelEn: string
  textSw: string
  textEn: string
  prompt: string
}

export interface UserGoal {
  id: string
  title: string
  category: 'business' | 'education' | 'personal' | 'finance'
  completed: boolean
  createdAt: string
  targetDate?: string
}

export interface MemoryFact {
  id: string
  content: string
  type: string
  importance: number
  created_at: string
}

export interface SystemTelemetry {
  status: string
  active_model: string
  ollama_url: string
  ram_optimization: string
  total_memories: number
  active_conversations_in_store: number
  diagnostics?: any[]
}

export interface AdminUserRecord {
  id: string
  name: string
  email: string
  role: UserRole
  avatar: string
  lastActive: string
  conversationCount: number
}
