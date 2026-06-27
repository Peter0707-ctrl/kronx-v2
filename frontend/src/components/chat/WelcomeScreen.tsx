'use client'

import { useKronxStore } from '@/store/useKronxStore'
import { SUGGESTION_CARDS, QUICK_CHIPS, MODES } from '@/lib/constants'

interface Props {
  onSend: (text: string) => void
}

export default function WelcomeScreen({ onSend }: Props) {
  const { language } = useKronxStore()
  const sw = language === 'sw'

  return (
    <div className="welcome-screen">
      {/* Gem logo */}
      <div className="w-gem">
        <svg viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={1.5} width={28} height={28}>
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
      </div>

      <h1 className="w-greeting">
        {sw ? 'Habari, rafiki. 👋' : 'Hello, friend. 👋'}
      </h1>

      <p className="w-sub">
        {sw ? (
          <>Mimi ni <strong>Kronx</strong> — mshauri wako wa akili bandia.<br />Niko hapa kukusaidia kujifunza, kukua, na kufanikisha.</>
        ) : (
          <>I&apos;m <strong>Kronx</strong> — your intelligent AI companion.<br />Here to help you learn, grow, and succeed.</>
        )}
      </p>

      {/* Quick chips */}
      <div className="chips-row">
        {QUICK_CHIPS.map((c, i) => (
          <button key={i} className="quick-chip" onClick={() => onSend(c.prompt)}>
            {sw ? c.sw : `${c.sw.split(' ')[0]} ${c.en}`}
          </button>
        ))}
      </div>

      {/* Suggestion grid */}
      <div className="sug-grid">
        {SUGGESTION_CARDS.map((card, i) => {
          const modeConf = MODES.find(m => m.key === card.mode)!
          return (
            <button key={i} className="sug-card" onClick={() => onSend(card.prompt)}>
              <div className="sug-mode-label" style={{ color: modeConf.color }}>
                {card.labelSw} · {card.labelEn}
              </div>
              <div className="sug-main">{sw ? card.textSw : card.textEn}</div>
              <div className="sug-alt">{sw ? card.textEn : card.textSw}</div>
            </button>
          )
        })}
      </div>
    </div>
  )
}