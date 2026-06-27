export type KronxMode = 'Friend' | 'Teacher' | 'Business' | 'Research' | 'Quick'

export type Language = 'sw' | 'en'

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