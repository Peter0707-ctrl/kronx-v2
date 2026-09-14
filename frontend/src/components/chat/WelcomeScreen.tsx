'use client'

import { useEffect, useState } from 'react'
import { useKronxStore } from '@/store/useKronxStore'
import { COPETRA_LOGO_BASE64 } from '@/lib/brandLogo'

interface Props {
  onSend: (text: string) => void
}

const GREETINGS_EN = [
  'Ready when you are.',
  'What can I help you build, solve or research today?',
  'Where shall we start today?',
  'How can I assist your studies, business or code today?',
  'What project or exam are we tackling today?'
]

const GREETINGS_SW = [
  'Nipo tayari kukusaidia leo.',
  'Je, tukuze au tutatue nini leo?',
  'Tuanzie wapi katika masomo, kodi au biashara yako?',
  'Nikusaidie nini katika utafiti, kodi za TRA au kodi za programu?',
  'Karibu Copetra AI, tuko tayari kuanza!'
]

export default function WelcomeScreen({ onSend }: Props) {
  const { language } = useKronxStore()
  const [greeting, setGreeting] = useState('Ready when you are.')

  useEffect(() => {
    const list = language === 'sw' ? GREETINGS_SW : GREETINGS_EN
    const randomIndex = Math.floor(Math.random() * list.length)
    setGreeting(list[randomIndex])
  }, [language])

  const isSw = language === 'sw'

  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 20px',
        width: '100%',
        maxWidth: '720px',
        margin: '0 auto',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        textAlign: 'center'
      }}
    >
      {/* Premium Brand Logo */}
      <div
        style={{
          width: '72px',
          height: '72px',
          borderRadius: '20px',
          overflow: 'hidden',
          marginBottom: '24px',
          boxShadow: '0 8px 30px rgba(2, 132, 199, 0.18)',
          border: '1px solid rgba(2, 132, 199, 0.3)',
          background: '#000000',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        <img
          src={COPETRA_LOGO_BASE64}
          alt="Copetra AI"
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
      </div>

      {/* Main Greeting */}
      <h1
        style={{
          fontSize: '30px',
          fontWeight: '700',
          color: '#0f172a',
          marginBottom: '10px',
          letterSpacing: '-0.5px',
          lineHeight: '1.25'
        }}
      >
        {greeting}
      </h1>

      {/* Subtitle / Capabilities hint */}
      <p
        style={{
          fontSize: '15px',
          color: '#64748b',
          maxWidth: '520px',
          lineHeight: '1.6',
          margin: '0 auto'
        }}
      >
        {isSw
          ? 'Uliza swali lolote kuhusu mitihani, masomo, programu za kompyuta, kodi za TRA, uchambuzi wa data au tafsiri.'
          : 'Ask anything about academic research, programming, business, exams, data analysis, or writing.'}
      </p>
    </div>
  )
}