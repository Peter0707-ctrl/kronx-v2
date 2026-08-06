'use client'

import { useEffect, useState } from 'react'

interface Props {
  onSend: (text: string) => void
}

const GREETINGS = [
  'Ready when you are.',
  'What can I help with today?',
  'What would you like to build or explore?',
  'Where shall we start today?',
  'What is on your mind today?',
  'How can I assist your workflow today?',
  'What project are we working on today?'
]

export default function WelcomeScreen({ onSend }: Props) {
  const [greeting, setGreeting] = useState('Ready when you are.')
  const [showSuggestions, setShowSuggestions] = useState(true)

  useEffect(() => {
    const randomIndex = Math.floor(Math.random() * GREETINGS.length)
    setGreeting(GREETINGS[randomIndex])

    const timer = setTimeout(() => {
      setShowSuggestions(false)
    }, 3000)

    const hideHandler = () => setShowSuggestions(false)
    window.addEventListener('hide-suggestions', hideHandler)

    return () => {
      clearTimeout(timer)
      window.removeEventListener('hide-suggestions', hideHandler)
    }
  }, [])

  const suggestions = [
    {
      icon: (
        <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="#0284c7" strokeWidth={2}>
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
        </svg>
      ),
      text: 'Academic Research & Thesis Writing',
      prompt: 'Help me outline a university research thesis methodology with academic citations.'
    },
    {
      icon: (
        <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth={2}>
          <polyline points="16 18 22 12 16 6" />
          <polyline points="8 6 2 12 8 18" />
        </svg>
      ),
      text: 'Software Engineering & Code Generator',
      prompt: 'Write a high-performance Python data processing script with error handling.'
    },
    {
      icon: (
        <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" strokeWidth={2}>
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <polyline points="21 15 16 10 5 21" />
        </svg>
      ),
      text: 'FLUX 8K Photorealistic Image Generator',
      prompt: 'Generate an ultra-HD picture of a futuristic quantum research laboratory'
    },
    {
      icon: (
        <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth={2}>
          <circle cx="12" cy="12" r="10" />
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
        </svg>
      ),
      text: 'Mathematics & Complex Problem Solving',
      prompt: 'Explain the principles of Partial Differential Equations with step-by-step examples.'
    }
  ]

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '32px 16px', width: '100%', fontFamily: "Calibri, 'Calibri Light', sans-serif" }}>
      {/* Title */}
      <h1 style={{ fontSize: '32px', fontWeight: '500', color: '#0f172a', marginBottom: '32px', letterSpacing: '-0.3px', textAlign: 'center' }}>
        {greeting}
      </h1>

      {/* Suggested Actions List */}
      <div style={{ 
        display: 'flex', flexDirection: 'column', gap: '12px', width: '100%', maxWidth: '420px', marginTop: '20px',
        opacity: showSuggestions ? 1 : 0,
        pointerEvents: showSuggestions ? 'auto' : 'none',
        transition: 'opacity 0.5s ease',
      }}>
        {suggestions.map((s, idx) => (
          <button
            key={idx}
            onClick={() => {
              if (!showSuggestions) return
              onSend(s.prompt)
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '14px',
              padding: '14px 18px',
              borderRadius: '16px',
              border: 'none',
              background: 'transparent',
              color: '#475569',
              fontSize: '15px',
              fontWeight: '500',
              cursor: showSuggestions ? 'pointer' : 'default',
              textAlign: 'left',
              transition: 'background 0.15s ease'
            }}
            onMouseOver={e => showSuggestions && (e.currentTarget.style.background = '#f1f5f9')}
            onMouseOut={e => showSuggestions && (e.currentTarget.style.background = 'transparent')}
          >
            <span style={{ color: '#64748b', display: 'flex', alignItems: 'center' }}>
              {s.icon}
            </span>
            <span>{s.text}</span>
          </button>
        ))}
      </div>
    </div>
  )
}