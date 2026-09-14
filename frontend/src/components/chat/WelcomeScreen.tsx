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
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      <style>{`
        @keyframes waterWaveUpward1 {
          0% {
            transform: translate(-50%, -50%) scale(0.3);
            opacity: 0;
          }
          20% {
            opacity: 0.65;
          }
          60% {
            opacity: 0.4;
          }
          100% {
            transform: translate(-50%, -120%) scale(2.2);
            opacity: 0;
          }
        }

        @keyframes waterWaveUpward2 {
          0% {
            transform: translate(-50%, -50%) scale(0.4);
            opacity: 0;
          }
          25% {
            opacity: 0.55;
          }
          65% {
            opacity: 0.3;
          }
          100% {
            transform: translate(-50%, -130%) scale(2.4);
            opacity: 0;
          }
        }

        @keyframes waterWaveUpward3 {
          0% {
            transform: translate(-50%, -50%) scale(0.5);
            opacity: 0;
          }
          30% {
            opacity: 0.45;
          }
          70% {
            opacity: 0.2;
          }
          100% {
            transform: translate(-50%, -140%) scale(2.6);
            opacity: 0;
          }
        }

        @keyframes verticalAuraBeam {
          0% {
            transform: translateX(-50%) scaleY(0.4);
            opacity: 0.15;
          }
          50% {
            transform: translateX(-50%) scaleY(1.1);
            opacity: 0.55;
          }
          100% {
            transform: translateX(-50%) scaleY(0.4);
            opacity: 0.15;
          }
        }

        @keyframes centerPulseGlow {
          0%, 100% {
            box-shadow: 0 0 35px rgba(2, 132, 199, 0.25), 0 0 70px rgba(56, 189, 248, 0.15);
            transform: scale(1);
          }
          50% {
            box-shadow: 0 0 55px rgba(2, 132, 199, 0.45), 0 0 100px rgba(56, 189, 248, 0.25);
            transform: scale(1.02);
          }
        }

        .ambient-wave {
          position: absolute;
          left: 50%;
          top: 40%;
          border-radius: 50%;
          pointer-events: none;
          z-index: 0;
          filter: blur(28px);
        }

        .wave-layer-1 {
          width: 320px;
          height: 320px;
          background: radial-gradient(circle, rgba(56, 189, 248, 0.45) 0%, rgba(2, 132, 199, 0.2) 45%, rgba(2, 132, 199, 0) 70%);
          animation: waterWaveUpward1 6s cubic-bezier(0.25, 1, 0.5, 1) infinite;
        }

        .wave-layer-2 {
          width: 360px;
          height: 360px;
          background: radial-gradient(circle, rgba(14, 165, 233, 0.4) 0%, rgba(56, 189, 248, 0.18) 50%, rgba(2, 132, 199, 0) 75%);
          animation: waterWaveUpward2 6s cubic-bezier(0.25, 1, 0.5, 1) infinite;
          animation-delay: 2s;
        }

        .wave-layer-3 {
          width: 400px;
          height: 400px;
          background: radial-gradient(circle, rgba(186, 230, 253, 0.35) 0%, rgba(14, 165, 233, 0.15) 55%, rgba(2, 132, 199, 0) 80%);
          animation: waterWaveUpward3 6s cubic-bezier(0.25, 1, 0.5, 1) infinite;
          animation-delay: 4s;
        }

        .aura-beam {
          position: absolute;
          bottom: 45%;
          left: 50%;
          width: 240px;
          height: 340px;
          background: linear-gradient(to top, rgba(2, 132, 199, 0.28) 0%, rgba(56, 189, 248, 0.15) 50%, rgba(240, 249, 255, 0) 100%);
          transform-origin: bottom center;
          filter: blur(36px);
          pointer-events: none;
          z-index: 0;
          animation: verticalAuraBeam 4.5s ease-in-out infinite;
        }
      `}</style>

      {/* Ambient Blue Water Waves Light Effect */}
      <div className="ambient-wave wave-layer-1" />
      <div className="ambient-wave wave-layer-2" />
      <div className="ambient-wave wave-layer-3" />
      <div className="aura-beam" />

      {/* Content Container (Layered on top of ambient waves) */}
      <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        {/* Premium Brand Logo with Center Pulse Glow */}
        <div
          style={{
            width: '74px',
            height: '74px',
            borderRadius: '22px',
            overflow: 'hidden',
            marginBottom: '24px',
            border: '1.5px solid rgba(56, 189, 248, 0.4)',
            background: '#000000',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            animation: 'centerPulseGlow 4s ease-in-out infinite'
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
            fontWeight: '800',
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
    </div>
  )
}