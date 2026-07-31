'use client'

import { useMemo } from 'react'
import { useKronxStore } from '@/store/useKronxStore'
import { KronxMode, Language } from '@/types'

interface Props {
  onSend: (text: string) => void
}

/** Context-aware follow-up suggestions based on last exchange */
export default function SuggestionChips({ onSend }: Props) {
  const { activeMessages, isStreaming, mode, language } = useKronxStore()
  const messages = activeMessages()

  const suggestions = useMemo(() => {
    if (messages.length < 2) return []

    const lastUser = [...messages].reverse().find(m => m.role === 'user')
    const lastAi = [...messages].reverse().find(m => m.role === 'ai')

    if (!lastUser || !lastAi || !lastAi.content) return []

    return generateSuggestions(
      lastUser.content,
      lastAi.content,
      mode,
      language
    )
  }, [messages, mode, language])

  // Don't show while streaming or if no suggestions
  if (isStreaming || suggestions.length === 0) return null

  // Only show after an AI message is the last message
  const lastMsg = messages[messages.length - 1]
  if (!lastMsg || lastMsg.role !== 'ai' || !lastMsg.content) return null

  return (
    <div className="suggestion-chips-container">
      <div className="suggestion-chips-label">
        {language === 'sw' ? 'Endelea na...' : 'Continue with...'}
      </div>
      <div className="suggestion-chips-row">
        {suggestions.map((sug, idx) => (
          <button
            key={idx}
            className="suggestion-chip"
            onClick={() => onSend(sug)}
            style={{ animationDelay: `${idx * 80}ms` }}
          >
            <span className="suggestion-chip-icon">→</span>
            <span className="suggestion-chip-text">{sug}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

function generateSuggestions(
  userMsg: string,
  aiResponse: string,
  mode: KronxMode,
  lang: Language
): string[] {
  const combined = `${userMsg} ${aiResponse}`.toLowerCase()
  const suggestions: string[] = []

  // ─── Swahili suggestions ───
  if (lang === 'sw') {
    // Business / money topics
    if (hasAny(combined, ['biashara', 'pesa', 'faida', 'mtaji', 'uwekezaji', 'mapato', 'bajeti', 'm-pesa', 'tzs', 'shilingi'])) {
      suggestions.push('Eleza zaidi kuhusu hatua za kuanza')
      suggestions.push('Nipe mfano halisi wa mahesabu')
      suggestions.push('Je, kuna changamoto gani za kutarajia?')
    }
    // Education / learning
    else if (hasAny(combined, ['jifunze', 'somo', 'elimu', 'darasa', 'mwalimu', 'mtihani', 'lugha'])) {
      suggestions.push('Nipe mazoezi ya kufanya')
      suggestions.push('Eleza kwa undani zaidi')
      suggestions.push('Nipe mfano mwingine')
    }
    // Health
    else if (hasAny(combined, ['afya', 'mwili', 'dawa', 'hospitali', 'ugonjwa', 'lishe', 'mazoezi'])) {
      suggestions.push('Nipe ushauri zaidi kuhusu hili')
      suggestions.push('Je, kuna hatua za kuchukua?')
      suggestions.push('Eleza kuhusu kinga')
    }
    // Technology
    else if (hasAny(combined, ['programu', 'simu', 'kompyuta', 'app', 'teknolojia', 'code', 'software'])) {
      suggestions.push('Nipe hatua za utekelezaji')
      suggestions.push('Eleza kwa undani zaidi')
      suggestions.push('Je, kuna zana gani muhimu?')
    }
    // Generic Swahili follow-ups
    else {
      suggestions.push('Eleza zaidi kuhusu hili')
      suggestions.push('Nipe mfano halisi')
      suggestions.push('Fanya muhtasari mfupi')
    }

    // Mode-specific additions
    if (mode === 'Teacher' && suggestions.length < 4) {
      suggestions.push('Nipe mtihani mfupi')
    }
    if (mode === 'Business' && suggestions.length < 4) {
      suggestions.push('Tengeneza mpango wa biashara')
    }
  }
  // ─── English suggestions ───
  else {
    // Business / finance
    if (hasAny(combined, ['business', 'money', 'profit', 'invest', 'budget', 'revenue', 'startup', 'market', 'sales'])) {
      suggestions.push('Break down the financial projections')
      suggestions.push('What are the key risks to watch for?')
      suggestions.push('Give me a step-by-step action plan')
    }
    // Education / learning
    else if (hasAny(combined, ['learn', 'study', 'course', 'teach', 'explain', 'education', 'lesson'])) {
      suggestions.push('Give me practice exercises')
      suggestions.push('Explain this in more detail')
      suggestions.push('Show me another example')
    }
    // Coding / tech
    else if (hasAny(combined, ['code', 'programming', 'javascript', 'python', 'react', 'api', 'database', 'software', 'app'])) {
      suggestions.push('Show me the implementation steps')
      suggestions.push('Explain the architecture')
      suggestions.push('Give me a code example')
    }
    // Health / wellness
    else if (hasAny(combined, ['health', 'exercise', 'diet', 'wellness', 'mental', 'fitness', 'nutrition'])) {
      suggestions.push('Give me more detailed advice')
      suggestions.push('Create a weekly plan')
      suggestions.push('What are common mistakes to avoid?')
    }
    // Generic fallbacks
    else {
      suggestions.push('Tell me more about this')
      suggestions.push('Give me a real-world example')
      suggestions.push('Summarize the key points')
    }

    // Mode-specific additions
    if (mode === 'Teacher' && suggestions.length < 4) {
      suggestions.push('Quiz me on this topic')
    }
    if (mode === 'Research' && suggestions.length < 4) {
      suggestions.push('What does the data show?')
    }
    if (mode === 'Business' && suggestions.length < 4) {
      suggestions.push('How can I monetize this?')
    }
  }

  return suggestions.slice(0, 3)
}

function hasAny(text: string, keywords: string[]): boolean {
  return keywords.some(kw => text.includes(kw))
}
