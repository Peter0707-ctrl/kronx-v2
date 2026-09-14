'use client'

import { useEffect, useState } from 'react'
import { useKronxStore } from '@/store/useKronxStore'

interface Props {
  onSend: (text: string) => void
}

const GREETINGS_EN = [
  'What project or exam are we tackling today?',
  'Ready when you are.',
  'What can I help you build, solve or research today?',
  'Where shall we start today?',
  'How can I assist your studies, business or code today?',
  'Need help with database schema, Python or thesis writing?',
  'Ask me anything from TRA tax calculations to medical analysis.'
]

const GREETINGS_SW = [
  'Je, tukuze au tutatue nini leo?',
  'Nipo tayari kukusaidia leo.',
  'Tuanzie wapi katika masomo, kodi au biashara yako?',
  'Nikusaidie nini katika utafiti, kodi za TRA au mifumo ya programu?',
  'Karibu Copetra AI, tuko tayari kuanza!',
  'Unahitaji msaada wa maswali ya mitihani au uchambuzi wa data?',
  'Uliza swali lolote la kitaaluma, kisheria au kibiashara.'
]

export default function WelcomeScreen({ onSend }: Props) {
  const { language } = useKronxStore()
  const [displayText, setDisplayText] = useState('')

  useEffect(() => {
    const list = language === 'sw' ? GREETINGS_SW : GREETINGS_EN
    let currentIdx = Math.floor(Math.random() * list.length)
    let charIdx = 0
    let isDeleting = false
    let timeoutId: NodeJS.Timeout

    const typeLoop = () => {
      const fullText = list[currentIdx % list.length]
      if (!isDeleting) {
        setDisplayText(fullText.substring(0, charIdx + 1))
        charIdx++
        if (charIdx >= fullText.length) {
          isDeleting = true
          timeoutId = setTimeout(typeLoop, 5000)
          return
        }
        timeoutId = setTimeout(typeLoop, 45)
      } else {
        setDisplayText(fullText.substring(0, charIdx - 1))
        charIdx--
        if (charIdx <= 0) {
          isDeleting = false
          currentIdx = (currentIdx + 1) % list.length
          timeoutId = setTimeout(typeLoop, 600)
          return
        }
        timeoutId = setTimeout(typeLoop, 20)
      }
    }

    typeLoop()

    return () => clearTimeout(timeoutId)
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
        padding: '20px',
        width: '100%',
        height: '100%',
        margin: '0 auto',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        textAlign: 'center',
        position: 'relative'
      }}
    >
      <style>{`
        @keyframes waterWavePulse {
          0% {
            transform: translate(-50%, -50%) scale(0.15);
            opacity: 0.85;
          }
          45% {
            opacity: 0.5;
          }
          85% {
            opacity: 0.12;
          }
          100% {
            transform: translate(-50%, -50%) scale(1.6);
            opacity: 0;
          }
        }

        @keyframes corePulse {
          0%, 100% {
            transform: translate(-50%, -50%) scale(0.85);
            opacity: 0.5;
          }
          50% {
            transform: translate(-50%, -50%) scale(1.15);
            opacity: 0.85;
          }
        }

        @keyframes cursorBlink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }

        .water-ripple-container {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: min(75vw, 560px);
          height: min(75vw, 560px);
          pointer-events: none;
          z-index: 0;
          -webkit-mask-image: radial-gradient(circle, rgba(0,0,0,1) 25%, rgba(0,0,0,0) 70%);
          mask-image: radial-gradient(circle, rgba(0,0,0,1) 25%, rgba(0,0,0,0) 70%);
        }

        .center-core-glow {
          position: absolute;
          top: 50%;
          left: 50%;
          width: 180px;
          height: 180px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(14, 165, 233, 0.45) 0%, rgba(56, 189, 248, 0.22) 45%, transparent 70%);
          filter: blur(20px);
          animation: corePulse 4s ease-in-out infinite;
        }

        .ripple-wave {
          position: absolute;
          top: 50%;
          left: 50%;
          width: 320px;
          height: 320px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(14, 165, 233, 0.4) 0%, rgba(56, 189, 248, 0.25) 30%, rgba(2, 132, 199, 0.08) 55%, transparent 70%);
          filter: blur(18px);
          pointer-events: none;
        }

        .wave-1 {
          animation: waterWavePulse 6s cubic-bezier(0.15, 0.85, 0.35, 1) infinite;
        }

        .wave-2 {
          animation: waterWavePulse 6s cubic-bezier(0.15, 0.85, 0.35, 1) infinite;
          animation-delay: 1.5s;
        }

        .wave-3 {
          animation: waterWavePulse 6s cubic-bezier(0.15, 0.85, 0.35, 1) infinite;
          animation-delay: 3s;
        }

        .wave-4 {
          animation: waterWavePulse 6s cubic-bezier(0.15, 0.85, 0.35, 1) infinite;
          animation-delay: 4.5s;
        }

        .typed-cursor {
          display: inline-block;
          width: 3px;
          height: 1em;
          background: #0284c7;
          margin-left: 4px;
          vertical-align: -0.1em;
          border-radius: 2px;
          box-shadow: 0 0 8px #38bdf8;
          animation: cursorBlink 0.9s infinite;
        }
      `}</style>

      {/* Seamless Masked 360-Degree Water Ripple Waves (Guaranteed 0 Frame Edges & 0 Box Clipping) */}
      <div className="water-ripple-container">
        <div className="center-core-glow" />
        <div className="ripple-wave wave-1" />
        <div className="ripple-wave wave-2" />
        <div className="ripple-wave wave-3" />
        <div className="ripple-wave wave-4" />
      </div>

      {/* Content Layer */}
      <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', maxWidth: '780px', padding: '0 20px' }}>
        {/* Main Greeting with Dynamic Typewriter Effect & Inline Cursor */}
        <h1
          style={{
            fontSize: '32px',
            fontWeight: '800',
            color: '#0f172a',
            marginBottom: '14px',
            letterSpacing: '-0.6px',
            lineHeight: '1.3',
            minHeight: '84px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            maxWidth: '720px'
          }}
        >
          <span style={{ display: 'inline' }}>
            {displayText}
            <span className="typed-cursor" />
          </span>
        </h1>

        {/* Subtitle / Capabilities hint */}
        <p
          style={{
            fontSize: '15px',
            color: '#64748b',
            maxWidth: '540px',
            lineHeight: '1.6',
            margin: '0 auto',
            fontWeight: '500'
          }}
        >
          {isSw
            ? 'Uliza swali lolote kuhusu mitihani, masomo, programu za kompyuta, kodi za TRA, uchambuzi wa data au tafsiri.'
            : 'Ask anything about academic research, programming, business, exams, data analysis, or writing.'}
        </p>
      </div>
    </div>
  )
}