'use client'

import { useKronxStore } from '@/store/useKronxStore'
import { MODES } from '@/lib/constants'
import { KronxMode } from '@/types'

export default function Sidebar() {
  const {
    mode, setMode,
    conversations, activeConversationId,
    selectConversation, newConversation,
  } = useKronxStore()

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="logo">
        <div className="logo-row">
          <div className="logo-gem">
            <svg viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={2}>
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <div>
            <div className="logo-name">Kronx</div>
            <div className="logo-sub">AI Companion</div>
          </div>
        </div>
      </div>

      {/* New chat */}
      <button className="new-chat-btn" onClick={newConversation}>
        <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <path d="M12 5v14M5 12h14" />
        </svg>
        Mazungumzo mapya · New chat
      </button>

      {/* Mode selector */}
      <nav className="modes">
        <div className="section-label">Hali · Mode</div>
        {MODES.map(m => (
          <button
            key={m.key}
            className={`mode-btn ${mode === m.key ? 'active' : ''}`}
            onClick={() => setMode(m.key as KronxMode)}
          >
            <span className="mode-pip" style={{ background: m.pip }} />
            <span>{m.labelSw}</span>
            <span className="mode-en">{m.labelEn}</span>
          </button>
        ))}
      </nav>

      {/* Conversation history */}
      <div className="history">
        <div className="section-label">Historia · Recent</div>
        {conversations.length === 0 && (
          <p className="hist-empty">
            Hakuna mazungumzo bado.<br />No conversations yet.
          </p>
        )}
        {conversations.map(conv => (
          <button
            key={conv.id}
            className={`hist-item ${conv.id === activeConversationId ? 'hist-active' : ''}`}
            onClick={() => selectConversation(conv.id)}
          >
            <div className="hist-title">{conv.title}</div>
            <div className="hist-meta">{formatTime(conv.updatedAt)}</div>
          </button>
        ))}
      </div>

      {/* User footer */}
      <div className="sidebar-footer">
        <div className="user-pill">
          <div className="avatar">JM</div>
          <div>
            <div className="user-name">John Mwangi</div>
            <div className="user-plan">Foundation · Msingi</div>
          </div>
        </div>
      </div>
    </aside>
  )
}

function formatTime(date: Date): string {
  const d = new Date(date)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000)
  if (diffDays === 0) return `Leo ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
  if (diffDays === 1) return 'Jana · Yesterday'
  if (diffDays === 2) return 'Juzi · 2 days ago'
  return d.toLocaleDateString('sw-TZ', { day: 'numeric', month: 'short' })
}