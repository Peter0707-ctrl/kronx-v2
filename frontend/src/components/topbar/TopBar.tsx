'use client'

import { useState, useEffect, useRef } from 'react'
import { useKronxStore } from '@/store/useKronxStore'

export default function TopBar() {
  const { toggleSidebar, sidebarOpen, setSettingsModalOpen, clearActiveConversationMessages, clearAllConversations, activeConversationId, deleteConversation, user, generateApiKey, setActiveView } = useKronxStore()
  const [menuOpen, setMenuOpen] = useState(false)
  const [brandMenuOpen, setBrandMenuOpen] = useState(false)
  const [pinned, setPinned] = useState(false)
  const [copiedKey, setCopiedKey] = useState(false)
  const [topToast, setTopToast] = useState<string | null>(null)
  const brandMenuRef = useRef<HTMLDivElement>(null)

  const showTopToast = (msg: string) => {
    setTopToast(msg)
    setTimeout(() => setTopToast(null), 3000)
  }

  const isPremium = user?.plan === 'premium' || user?.role === 'admin'
  const isAdmin = user?.role === 'admin'

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (brandMenuRef.current && !brandMenuRef.current.contains(event.target as Node)) {
        setBrandMenuOpen(false)
      }
    }
    if (brandMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [brandMenuOpen])

  const closeDropdowns = () => {
    if (brandMenuOpen) setBrandMenuOpen(false)
    if (menuOpen) setMenuOpen(false)
  }

  return (
    <header className="topbar" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 24px', background: 'transparent', position: 'relative' }}>
      {topToast && (
        <div style={{ position: 'absolute', top: '50px', left: '50%', transform: 'translateX(-50%)', background: '#0f172a', color: '#38bdf8', padding: '10px 18px', borderRadius: '12px', zIndex: 9999, boxShadow: '0 8px 24px rgba(0,0,0,0.2)', fontWeight: '700', fontSize: '13px', border: '1px solid #38bdf8' }}>
          ⚡ {topToast}
        </div>
      )}
      {/* Left Area: Sidebar Toggle & Admin Console Button */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <button
          onClick={toggleSidebar}
          title={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
          style={{
            background: '#ffffff',
            border: '1px solid #cbd5e1',
            borderRadius: '10px',
            width: '36px',
            height: '36px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            color: '#0f172a',
            boxShadow: '0 2px 6px rgba(0,0,0,0.04)'
          }}
        >
          <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
            <line x1="9" y1="3" x2="9" y2="21" />
          </svg>
        </button>

        {/* Dedicated Admin Console Button - Exclusively visible to logged in Admin */}
        {isAdmin && (
          <button
            onClick={() => {
              setBrandMenuOpen(false)
              setMenuOpen(false)
              setActiveView('admin')
            }}
            title="Open Master Admin Console"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: '#0f172a',
              color: '#ffffff',
              border: 'none',
              borderRadius: '10px',
              width: '36px',
              height: '36px',
              fontWeight: '900',
              fontSize: '16px',
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(15, 23, 42, 0.2)'
            }}
          >
            ⚙
          </button>
        )}
      </div>

      {/* Center KRON X Brand Header & Down Arrow Dropdown Trigger */}
      <div ref={brandMenuRef} style={{ position: 'absolute', left: '50%', transform: 'translateX(-50%)' }}>
        <div
          onClick={() => setBrandMenuOpen(!brandMenuOpen)}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', padding: '4px 10px', borderRadius: '12px', background: brandMenuOpen ? 'rgba(255,255,255,0.8)' : 'transparent' }}
        >
          <img
            src="/logo.jpg"
            alt="PJKRONX AI Logo"
            style={{ width: '28px', height: '28px', borderRadius: '8px', objectFit: 'cover', boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }}
          />
          <span style={{ fontSize: '20px', fontWeight: '900', color: '#000000', fontFamily: "Calibri, 'Calibri Light', sans-serif", letterSpacing: '-0.5px' }}>Copetra AI</span>
          <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="#000000" strokeWidth={3} style={{ transform: brandMenuOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s ease' }}>
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>

        {/* Invisible Click-Outside Backdrop to auto-close dropdowns */}
        {(brandMenuOpen || menuOpen) && (
          <div
            onClick={closeDropdowns}
            style={{ position: 'fixed', inset: 0, zIndex: 9990, background: 'transparent' }}
          />
        )}

        {/* Brand Down Arrow Dropdown Menu for API Key & Developer Suite */}
        {brandMenuOpen && (
          <div
            style={{
              position: 'absolute',
              top: '46px',
              left: '50%',
              transform: 'translateX(-50%)',
              width: '360px',
              background: '#ffffff',
              borderRadius: '24px',
              border: '1px solid #cbd5e1',
              boxShadow: '0 20px 50px rgba(0, 0, 0, 0.18)',
              padding: '22px',
              zIndex: 99999,
              fontFamily: "Calibri, 'Calibri Light', sans-serif",
              animation: 'fadeIn 0.2s ease-out'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', borderBottom: '1px solid #f1f5f9', paddingBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '16px', fontWeight: '800', color: '#0f172a' }}>🔑 Kronx Developer API Key</span>
              </div>
              <button
                onClick={() => setBrandMenuOpen(false)}
                style={{ width: '28px', height: '28px', borderRadius: '50%', border: 'none', background: '#f1f5f9', color: '#64748b', cursor: 'pointer', fontWeight: '700' }}
              >
                ✕
              </button>
            </div>

              {isPremium ? (
                <div>
                  {!user?.apiKey ? (
                    <div style={{ textAlign: 'center', padding: '6px 0' }}>
                      <p style={{ fontSize: '13.5px', color: '#475569', margin: '0 0 14px 0', lineHeight: '1.5' }}>
                        As a <strong>Kronx Plus Subscriber</strong>, you are eligible for developer API access. Click below to apply and generate your live key automatically:
                      </p>
                      <button
                        onClick={() => {
                          const newKey = generateApiKey()
                          showTopToast(`API Key Generated Successfully: ${newKey}`)
                        }}
                        style={{ width: '100%', padding: '12px 14px', borderRadius: '14px', background: '#0284c7', color: '#ffffff', border: 'none', fontWeight: '800', fontSize: '13.5px', cursor: 'pointer', boxShadow: '0 4px 12px rgba(2, 132, 199, 0.2)' }}
                      >
                        ⚡ Apply for Developer API Key
                      </button>
                    </div>
                  ) : (
                    <div>
                      <p style={{ fontSize: '13px', color: '#475569', margin: '0 0 10px 0', lineHeight: '1.4' }}>
                        Your active Premium API Key grants full access to Copetra LLM models and FLUX 8K image generation endpoints:
                      </p>
                      <div style={{ background: '#0f172a', borderRadius: '12px', padding: '12px 14px', color: '#38bdf8', fontFamily: 'monospace', fontSize: '13px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '230px' }}>
                          {user.apiKey}
                        </span>
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(user.apiKey!)
                            setCopiedKey(true)
                            setTimeout(() => setCopiedKey(false), 2000)
                          }}
                          style={{ background: '#0284c7', color: '#fff', border: 'none', borderRadius: '8px', padding: '6px 12px', fontSize: '11.5px', fontWeight: '800', cursor: 'pointer' }}
                        >
                          {copiedKey ? 'Copied!' : 'Copy'}
                        </button>
                      </div>
                      <button
                        onClick={() => {
                          const newKey = generateApiKey()
                          showTopToast(`New API Key Generated: ${newKey}`)
                        }}
                        style={{ width: '100%', padding: '10px', borderRadius: '12px', background: '#f1f5f9', border: '1px solid #cbd5e1', color: '#0f172a', fontWeight: '700', fontSize: '13px', cursor: 'pointer' }}
                      >
                        🔄 Regenerate API Key
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '8px 0' }}>
                  <p style={{ fontSize: '13.5px', color: '#64748b', margin: '0 0 16px 0', lineHeight: '1.5' }}>
                    🔒 API Keys are exclusively available to <strong>Kronx Plus Premium Subscribers</strong>. Upgrade your subscription to unlock API access!
                  </p>
                  <button
                    onClick={() => {
                      setBrandMenuOpen(false)
                      setSettingsModalOpen(true)
                    }}
                    style={{ width: '100%', padding: '12px', borderRadius: '14px', background: '#0f172a', color: '#ffffff', border: 'none', fontWeight: '800', fontSize: '13.5px', cursor: 'pointer' }}
                  >
                    ✦ Upgrade to Kronx Plus (15,000 TZS)
                  </button>
                </div>
              )}
          </div>
        )}
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
              onClick={() => {
                setMenuOpen(false)
                showTopToast('No media files uploaded in current session.')
              }}
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
                setPinned(!pinned)
              }}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '10px 12px', borderRadius: '10px', border: 'none', background: 'transparent', color: pinned ? '#0284c7' : '#0f172a', fontSize: '13.5px', fontWeight: '600', cursor: 'pointer', textAlign: 'left' }}
              onMouseOver={e => (e.currentTarget.style.background = '#f1f5f9')}
              onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
            >
              <svg width={16} height={16} viewBox="0 0 24 24" fill={pinned ? '#0284c7' : 'none'} stroke="currentColor" strokeWidth={2}>
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
              <span>{pinned ? 'Pinned' : 'Pin chat'}</span>
            </button>

            <button
              onClick={() => {
                setMenuOpen(false)
                if (activeConversationId) {
                  deleteConversation(activeConversationId)
                }
              }}
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
                if (confirm('Delete current chat session?')) {
                  clearActiveConversationMessages()
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