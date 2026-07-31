'use client'

import { useState } from 'react'
import { useKronxStore } from '@/store/useKronxStore'

export default function TopBar() {
  const { setSettingsModalOpen, clearActiveConversationMessages, clearAllConversations } = useKronxStore()
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 24px', background: 'transparent', position: 'relative' }}>
      {/* Left empty container or toggle icon placeholder */}
      <div style={{ width: '40px' }} />

      {/* Center KRON X Brand Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', position: 'absolute', left: '50%', transform: 'translateX(-50%)' }}>
        <span style={{ fontSize: '22px', fontWeight: '900', color: '#000000', fontFamily: "Calibri, 'Calibri Light', sans-serif", letterSpacing: '-0.5px' }}>KRON X</span>
        <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="#000000" strokeWidth={3}>
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </div>

      {/* Right Actions: Upgrade & Three Dots Menu */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', position: 'relative' }}>
        <button
          onClick={() => setSettingsModalOpen(true)}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'transparent', border: 'none', color: '#2563eb', fontWeight: '600', fontSize: '14px', cursor: 'pointer', fontFamily: "Calibri, 'Calibri Light', sans-serif" }}
        >
          <span style={{ fontSize: '14px' }}>✦</span>
          <span>Upgrade</span>
        </button>

        {/* Three Dots Menu Button */}
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          title="More options"
          style={{ background: 'transparent', border: 'none', color: '#0f172a', padding: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', borderRadius: '8px' }}
        >
          <svg width={20} height={20} viewBox="0 0 24 24" fill="currentColor">
            <circle cx="5" cy="12" r="2" />
            <circle cx="12" cy="12" r="2" />
            <circle cx="19" cy="12" r="2" />
          </svg>
        </button>

        {/* Dropdown Menu Modal matching ChatGPT Screenshot */}
        {menuOpen && (
          <div
            style={{
              position: 'absolute',
              top: '42px',
              right: '0',
              width: '200px',
              background: '#ffffff',
              borderRadius: '16px',
              border: '1px solid #e2e8f0',
              boxShadow: '0 10px 30px rgba(0, 0, 0, 0.1)',
              padding: '8px',
              zIndex: 999,
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
              fontFamily: "Calibri, 'Calibri Light', sans-serif"
            }}
          >
            <button
              onClick={() => setMenuOpen(false)}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '10px 12px', borderRadius: '10px', border: 'none', background: 'transparent', color: '#0f172a', fontSize: '13.5px', fontWeight: '600', cursor: 'pointer', textAlign: 'left' }}
              onMouseOver={e => (e.currentTarget.style.background = '#f1f5f9')}
              onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
            >
              <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <line x1="9" y1="3" x2="9" y2="21" />
              </svg>
              <span>View files in chat</span>
            </button>

            <button
              onClick={() => {
                setMenuOpen(false)
                clearActiveConversationMessages()
              }}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '10px 12px', borderRadius: '10px', border: 'none', background: 'transparent', color: '#0f172a', fontSize: '13.5px', fontWeight: '600', cursor: 'pointer', textAlign: 'left' }}
              onMouseOver={e => (e.currentTarget.style.background = '#f1f5f9')}
              onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
            >
              <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
              <span>Pin chat</span>
            </button>

            <button
              onClick={() => setMenuOpen(false)}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '10px 12px', borderRadius: '10px', border: 'none', background: 'transparent', color: '#0f172a', fontSize: '13.5px', fontWeight: '600', cursor: 'pointer', textAlign: 'left' }}
              onMouseOver={e => (e.currentTarget.style.background = '#f1f5f9')}
              onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
            >
              <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <polyline points="21 8 21 21 3 21 3 8" />
                <rect x="1" y="3" width="22" height="5" />
                <line x1="10" y1="12" x2="14" y2="12" />
              </svg>
              <span>Archive</span>
            </button>

            <button
              onClick={() => {
                setMenuOpen(false)
                if (confirm('Delete chat session history?')) {
                  clearAllConversations()
                }
              }}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '10px 12px', borderRadius: '10px', border: 'none', background: 'transparent', color: '#ef4444', fontSize: '13.5px', fontWeight: '600', cursor: 'pointer', textAlign: 'left' }}
              onMouseOver={e => (e.currentTarget.style.background = '#fef2f2')}
              onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
            >
              <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
              <span>Delete</span>
            </button>
          </div>
        )}
      </div>
    </header>
  )
}