'use client'

import { useState } from 'react'
import { useKronxStore } from '@/store/useKronxStore'

export default function FloatingTools() {
  const { activeView, setActiveView, user, language } = useKronxStore()
  const [expanded, setExpanded] = useState(false)
  const sw = language === 'sw'

  if (activeView === 'landing') return null

  return (
    <div className="floating-tools-wrap">
      {expanded && (
        <div className="floating-menu">
          <button
            className="menu-item-btn"
            onClick={() => {
              setActiveView('chat')
              setExpanded(false)
            }}
          >
            <span className="btn-icon">💬</span>
            <span>{sw ? 'Mazungumzo (Chat)' : 'Chat View'}</span>
          </button>

          <button
            className="menu-item-btn"
            onClick={() => {
              setActiveView('dashboard')
              setExpanded(false)
            }}
          >
            <span className="btn-icon">📊</span>
            <span>{sw ? 'Mfumo & Takwimu' : 'Dashboard'}</span>
          </button>
        </div>

      )}

      {/* Main floating action button */}
      <button
        className={`fab-main-btn ${expanded ? 'fab-expanded' : ''}`}
        onClick={() => setExpanded(!expanded)}
        title={sw ? 'Zana za Haraka · Floating Tools' : 'Floating Tools'}
        aria-label="Floating Tools"
      >
        <span className="fab-aura" />
        <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={2}>
          {expanded ? (
            <path d="M18 6L6 18M6 6l12 12" />
          ) : (
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          )}
        </svg>
      </button>
    </div>
  )
}
