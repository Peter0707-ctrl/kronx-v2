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

  useEffect(() => {
    const randomIndex = Math.floor(Math.random() * GREETINGS.length)
    setGreeting(GREETINGS[randomIndex])
  }, [])

  const suggestions = [
    {
      icon: (
        <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <polyline points="21 15 16 10 5 21" />
        </svg>
      ),
      text: 'Create an image',
      prompt: 'Create a high quality image'
    },
    {
      icon: (
        <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <path d="M12 20h9" />
          <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
        </svg>
      ),
      text: 'Write or edit',
      prompt: 'Help me write or edit code'
    },
    {
      icon: (
        <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <circle cx="12" cy="12" r="10" />
          <line x1="2" y1="12" x2="22" y2="12" />
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
        </svg>
      ),
      text: 'Search the web',
      prompt: 'Search the web for news'
    }
  ]

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '65vh', width: '100%', fontFamily: "Calibri, 'Calibri Light', sans-serif" }}>
      {/* Title */}
      <h1 style={{ fontSize: '32px', fontWeight: '500', color: '#0f172a', marginBottom: '32px', letterSpacing: '-0.3px', textAlign: 'center' }}>
        {greeting}
      </h1>

      {/* Suggested Actions List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%', maxWidth: '420px', marginTop: '20px' }}>
        {suggestions.map((s, idx) => (
          <button
            key={idx}
            onClick={() => onSend(s.prompt)}
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
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'background 0.15s ease'
            }}
            onMouseOver={e => (e.currentTarget.style.background = '#f1f5f9')}
            onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
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