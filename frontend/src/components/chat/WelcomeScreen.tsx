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
        padding: '40px 20px',
        width: '100%',
        maxWidth: '780px',
        margin: '0 auto',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      <style>{`
        @keyframes waterWaveUpward1 {
          0% {
            transform: translate(-50%, -40%) scale(0.3);
            opacity: 0;
          }
          15% {
            opacity: 0.9;
          }
          55% {
            opacity: 0.6;
          }
          100% {
            transform: translate(-50%, -140%) scale(2.6);
            opacity: 0;
          }
        }

        @keyframes waterWaveUpward2 {
          0% {
            transform: translate(-50%, -40%) scale(0.45);
            opacity: 0;
          }
          20% {
            opacity: 0.8;
          }
          60% {
            opacity: 0.45;
          }
          100% {
            transform: translate(-50%, -150%) scale(2.8);
            opacity: 0;
          }
        }

        @keyframes waterWaveUpward3 {
          0% {
            transform: translate(-50%, -40%) scale(0.6);
            opacity: 0;
          }
          25% {
            opacity: 0.7;
          }
          65% {
            opacity: 0.35;
          }
          100% {
            transform: translate(-50%, -160%) scale(3.1);
            opacity: 0;
          }
        }

        @keyframes verticalAuraBeam {
          0% {
            transform: translateX(-50%) scaleY(0.5);
            opacity: 0.35;
          }
          50% {
            transform: translateX(-50%) scaleY(1.3);
            opacity: 0.85;
          }
          100% {
            transform: translateX(-50%) scaleY(0.5);
            opacity: 0.35;
          }
        }

        @keyframes cursorBlink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }

        .ambient-wave {
          position: absolute;
          left: 50%;
          top: 45%;
          border-radius: 50%;
          pointer-events: none;
          z-index: 0;
          filter: blur(32px);
        }

        .wave-layer-1 {
          width: 380px;
          height: 380px;
          background: radial-gradient(circle, rgba(14, 165, 233, 0.75) 0%, rgba(2, 132, 199, 0.45) 40%, rgba(3, 105, 161, 0.1) 70%, transparent 85%);
          animation: waterWaveUpward1 5.5s cubic-bezier(0.2, 0.9, 0.4, 1) infinite;
        }

        .wave-layer-2 {
          width: 440px;
          height: 440px;
          background: radial-gradient(circle, rgba(56, 189, 248, 0.65) 0%, rgba(14, 165, 233, 0.4) 45%, rgba(2, 132, 199, 0.08) 75%, transparent 90%);
          animation: waterWaveUpward2 5.5s cubic-bezier(0.2, 0.9, 0.4, 1) infinite;
          animation-delay: 1.8s;
        }

        .wave-layer-3 {
          width: 500px;
          height: 500px;
          background: radial-gradient(circle, rgba(125, 211, 252, 0.55) 0%, rgba(56, 189, 248, 0.3) 50%, rgba(14, 165, 233, 0.05) 80%, transparent 95%);
          animation: waterWaveUpward3 5.5s cubic-bezier(0.2, 0.9, 0.4, 1) infinite;
          animation-delay: 3.6s;
        }

        .aura-beam {
          position: absolute;
          bottom: 40%;
          left: 50%;
          width: 320px;
          height: 420px;
          background: linear-gradient(to top, rgba(2, 132, 199, 0.5) 0%, rgba(56, 189, 248, 0.35) 45%, rgba(186, 230, 253, 0.15) 75%, transparent 100%);
          transform-origin: bottom center;
          filter: blur(42px);
          pointer-events: none;
          z-index: 0;
          animation: verticalAuraBeam 4s ease-in-out infinite;
        }

        .typed-cursor {
          display: inline-block;
          width: 3px;
          height: 32px;
          background: #0284c7;
          margin-left: 6px;
          vertical-align: middle;
          border-radius: 2px;
          box-shadow: 0 0 10px #38bdf8;
          animation: cursorBlink 0.9s infinite;
        }
      `}</style>

      {/* Vibrant Electric Blue Water Waves Light Effect */}
      <div className="ambient-wave wave-layer-1" />
      <div className="ambient-wave wave-layer-2" />
      <div className="ambient-wave wave-layer-3" />
      <div className="aura-beam" />

      {/* Content Container */}
      <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
        {/* Main Greeting with Dynamic Typewriter Effect */}
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
            flexWrap: 'wrap',
            maxWidth: '680px'
          }}
        >
          <span>{displayText}</span>
          <span className="typed-cursor" />
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