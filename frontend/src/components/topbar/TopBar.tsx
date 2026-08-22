'use client'

import { useState, useEffect, useRef } from 'react'
import { useKronxStore } from '@/store/useKronxStore'

export default function TopBar() {
  const {
    toggleSidebar,
    sidebarOpen,
    setSettingsModalOpen,
    clearActiveConversationMessages,
    clearAllConversations,
    activeConversationId,
    deleteConversation,
    togglePinConversation,
    toggleArchiveConversation,
    conversations,
    activeMessages,
    user,
    setActiveView,
    language
  } = useKronxStore()

  const [menuOpen, setMenuOpen] = useState(false)
  const [brandMenuOpen, setBrandMenuOpen] = useState(false)
  const [topToast, setTopToast] = useState<string | null>(null)
  const [viewFilesModalOpen, setViewFilesModalOpen] = useState(false)
  const brandMenuRef = useRef<HTMLDivElement>(null)
  const sw = language === 'sw'

  const activeConv = conversations.find(c => c.id === activeConversationId)
  const isPinned = activeConv?.isPinned ?? false
  const isArchived = activeConv?.isArchived ?? false

  const showTopToast = (msg: string) => {
    setTopToast(msg)
    setTimeout(() => setTopToast(null), 3000)
  }

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

  // Extract images and code files from active messages
  const msgs = activeMessages()
  const extractedFiles: { type: 'image' | 'code'; content: string; name: string }[] = []
  msgs.forEach((m) => {
    if (m.content) {
      // Find Markdown images ![alt](url) or HTML <img src="...">
      const imgRegex = /!\[.*?\]\((.*?)\)|<img.*?src=["'](.*?)["']/g
      let match
      while ((match = imgRegex.exec(m.content)) !== null) {
        const url = match[1] || match[2]
        if (url) {
          extractedFiles.push({ type: 'image', content: url, name: `Image ${extractedFiles.length + 1}` })
        }
      }
      // Find code blocks ```lang ... ```
      const codeRegex = /```(\w+)?\n([\s\S]*?)```/g
      let codeMatch
      while ((codeMatch = codeRegex.exec(m.content)) !== null) {
        const lang = codeMatch[1] || 'code'
        extractedFiles.push({ type: 'code', content: codeMatch[2], name: `Snippet ${extractedFiles.length + 1} (.${lang})` })
      }
    }
  })

  return (
    <header className="topbar" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 24px', background: 'transparent', position: 'relative' }}>
      {topToast && (
        <div style={{ position: 'absolute', top: '50px', left: '50%', transform: 'translateX(-50%)', background: '#0f172a', color: '#38bdf8', padding: '10px 18px', borderRadius: '12px', zIndex: 9999, boxShadow: '0 8px 24px rgba(0,0,0,0.2)', fontWeight: '700', fontSize: '13px', border: '1px solid #38bdf8' }}>
          ⚡ {topToast}
        </div>
      )}

      {/* Modal for Viewing Files in Chat */}
      {viewFilesModalOpen && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.8)', backdropFilter: 'blur(8px)', zIndex: 99999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
          <div style={{ background: '#ffffff', borderRadius: '24px', width: '100%', maxWidth: '600px', maxHeight: '80vh', display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.3)' }}>
            <div style={{ padding: '20px 24px', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ fontSize: '16px', fontWeight: '800', color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>📁</span>
                <span>{sw ? 'Faili na Picha Katika Chat' : 'Files & Media in Current Chat'}</span>
              </div>
              <button
                onClick={() => setViewFilesModalOpen(false)}
                style={{ background: '#f1f5f9', border: 'none', borderRadius: '50%', width: '28px', height: '28px', cursor: 'pointer', fontWeight: '700' }}
              >
                ✕
              </button>
            </div>
            
            <div style={{ padding: '20px 24px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {extractedFiles.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 20px', color: '#94a3b8' }}>
                  <div style={{ fontSize: '32px', marginBottom: '8px' }}>🖼️</div>
                  <div style={{ fontSize: '14px', fontWeight: '600' }}>
                    {sw ? 'Hakuna picha au faili zilizo zalishwa katika mazungumzo haya bado.' : 'No images or code files generated in this conversation yet.'}
                  </div>
                </div>
              ) : (
                extractedFiles.map((f, i) => (
                  <div key={i} style={{ border: '1px solid #cbd5e1', borderRadius: '14px', padding: '12px', background: '#f8fafc' }}>
                    <div style={{ fontSize: '12.5px', fontWeight: '700', color: '#0284c7', marginBottom: '8px' }}>{f.name}</div>
                    {f.type === 'image' ? (
                      <img src={f.content} alt="Chat media" style={{ maxWidth: '100%', maxHeight: '250px', borderRadius: '8px', objectFit: 'contain' }} />
                    ) : (
                      <pre style={{ background: '#0f172a', color: '#f8fafc', padding: '12px', borderRadius: '8px', fontSize: '12px', overflowX: 'auto', margin: 0 }}>
                        <code>{f.content}</code>
                      </pre>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Left Area: Sidebar Toggle & Admin Console Button */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <button
          onClick={toggleSidebar}
          aria-label="Toggle Navigation Menu"
          style={{
            background: '#ffffff',
            border: '1px solid #cbd5e1',
            borderRadius: '12px',
            width: '40px',
            height: '40px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
            color: '#0f172a'
          }}
        >
          <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>

        {/* Master AI Admin Console Access Icon Button (Only for Master Admin) */}
        {(isAdmin || user?.email === 'pj0040280@gmail.com') && (
          <button
            onClick={() => setActiveView('admin')}
            title="Master AI Admin Dashboard"
            style={{
              background: '#0f172a',
              border: 'none',
              color: '#ffffff',
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

      {/* Center Copetra AI Brand Header & Down Arrow Dropdown Trigger (Instagram Font Style) */}
      <div ref={brandMenuRef} style={{ position: 'absolute', left: '50%', transform: 'translateX(-50%)' }}>
        <div
          onClick={() => setBrandMenuOpen(!brandMenuOpen)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            cursor: 'pointer',
            padding: '2px 10px',
            borderRadius: '12px',
            background: brandMenuOpen ? 'rgba(0,0,0,0.06)' : 'transparent',
            transition: 'background-color 0.2s ease',
            userSelect: 'none'
          }}
        >
          <span
            className="copetra-brand-instagram instagram-font copetra-script-font"
            style={{
              fontSize: '34px',
              fontWeight: '400',
              color: '#000000',
              fontFamily: "'Grand Hotel', 'Pacifico', 'Dancing Script', 'Satisfy', 'Cookie', cursive",
              letterSpacing: '0.5px',
              lineHeight: 1.1,
              paddingTop: '2px',
              display: 'inline-block'
            }}
          >
            Copetra AI
          </span>
          <svg
            width={14}
            height={14}
            viewBox="0 0 24 24"
            fill="none"
            stroke="#000000"
            strokeWidth={2.5}
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{
              transform: brandMenuOpen ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s ease',
              marginTop: '4px'
            }}
          >
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
              boxShadow: '0 20px 50px rgba(0,0,0,0.2)',
              padding: '20px',
              zIndex: 9999,
              animation: 'fadeIn 0.2s ease-out',
              fontFamily: "Calibri, 'Calibri Light', sans-serif"
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: '#0284c7', color: '#fff', fontWeight: '900', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px' }}>
                ⚡
              </div>
              <div>
                <div style={{ fontSize: '15px', fontWeight: '800', color: '#0f172a' }}>Copetra Developer API</div>
                <div style={{ fontSize: '11.5px', color: '#64748b' }}>Project keys · Gateway · Docs</div>
              </div>
            </div>

            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '12px', marginBottom: '14px' }}>
              <div style={{ fontSize: '11px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>
                Base URL
              </div>
              <code style={{ fontSize: '11px', color: '#0f172a', wordBreak: 'break-all' }}>
                {process.env.NEXT_PUBLIC_SITE_URL || 'https://miraculous-forgiveness-production-10d4.up.railway.app'}
              </code>
            </div>

            <div style={{ fontSize: '12px', color: '#475569', display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '16px', background: '#f0f9ff', padding: '10px 12px', borderRadius: '12px', border: '1px solid #bae6fd' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Endpoint:</span>
                <span style={{ fontWeight: '700', fontFamily: 'monospace' }}>POST /api/gateway</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Access:</span>
                <span style={{ fontWeight: '700', color: user?.isDeveloper || user?.role === 'admin' ? '#10b981' : '#f59e0b' }}>
                  {user?.isDeveloper || user?.role === 'admin' ? 'Granted ✓' : 'Ask admin to grant'}
                </span>
              </div>
            </div>

            <button
              onClick={() => {
                setBrandMenuOpen(false)
                setSettingsModalOpen(true)
              }}
              style={{ width: '100%', padding: '10px', borderRadius: '10px', background: '#0284c7', color: '#fff', border: 'none', fontWeight: 700, fontSize: 13, cursor: 'pointer', marginBottom: 8 }}
            >
              Open Developer Settings & Docs
            </button>
          </div>
        )}
      </div>

      {/* Right Area: Top Action Three-Dot Menu Trigger */}
      <div style={{ position: 'relative' }}>
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="More Options Menu"
          style={{
            background: '#ffffff',
            border: '1px solid #cbd5e1',
            borderRadius: '12px',
            width: '40px',
            height: '40px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
            color: '#0f172a'
          }}
        >
          <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
            <circle cx="12" cy="5" r="1.5" />
            <circle cx="12" cy="12" r="1.5" />
            <circle cx="12" cy="19" r="1.5" />
          </svg>
        </button>

        {/* Top Actions Dropdown Menu */}
        {menuOpen && (
          <div
            style={{
              position: 'absolute',
              right: 0,
              top: '48px',
              width: '220px',
              background: '#ffffff',
              borderRadius: '16px',
              border: '1px solid #e2e8f0',
              boxShadow: '0 10px 30px rgba(0,0,0,0.15)',
              padding: '8px',
              zIndex: 999,
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
              fontFamily: "Calibri, 'Calibri Light', sans-serif"
            }}
          >
            {/* 1. View files in chat */}
            <button
              onClick={() => {
                setMenuOpen(false)
                setViewFilesModalOpen(true)
              }}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '10px 12px', borderRadius: '10px', border: 'none', background: 'transparent', color: '#0f172a', fontSize: '13.5px', fontWeight: '600', cursor: 'pointer', textAlign: 'left' }}
              onMouseOver={e => (e.currentTarget.style.background = '#f1f5f9')}
              onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
            >
              <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <line x1="9" y1="3" x2="9" y2="21" />
              </svg>
              <span>{sw ? 'Tazama faili katika chat' : 'View files in chat'}</span>
            </button>

            {/* 2. Pin chat */}
            <button
              onClick={() => {
                setMenuOpen(false)
                if (activeConversationId) {
                  togglePinConversation(activeConversationId)
                  showTopToast(!isPinned ? 'Chat Pinned to Top 📌' : 'Chat Unpinned')
                } else {
                  showTopToast('No active conversation to pin.')
                }
              }}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '10px 12px', borderRadius: '10px', border: 'none', background: 'transparent', color: isPinned ? '#0284c7' : '#0f172a', fontSize: '13.5px', fontWeight: '600', cursor: 'pointer', textAlign: 'left' }}
              onMouseOver={e => (e.currentTarget.style.background = '#f1f5f9')}
              onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
            >
              <svg width={16} height={16} viewBox="0 0 24 24" fill={isPinned ? '#0284c7' : 'none'} stroke="currentColor" strokeWidth={2}>
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
              <span>{isPinned ? (sw ? 'Yaliyobandikwa (Pinned ✓)' : 'Pinned ✓') : (sw ? 'Bandika chat (Pin chat)' : 'Pin chat')}</span>
            </button>

            {/* 3. Archive chat */}
            <button
              onClick={() => {
                setMenuOpen(false)
                if (activeConversationId) {
                  toggleArchiveConversation(activeConversationId)
                  showTopToast(!isArchived ? 'Chat Archived 📦' : 'Chat Unarchived')
                } else {
                  showTopToast('No active conversation to archive.')
                }
              }}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%', padding: '10px 12px', borderRadius: '10px', border: 'none', background: 'transparent', color: isArchived ? '#0284c7' : '#0f172a', fontSize: '13.5px', fontWeight: '600', cursor: 'pointer', textAlign: 'left' }}
              onMouseOver={e => (e.currentTarget.style.background = '#f1f5f9')}
              onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
            >
              <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <polyline points="21 8 21 21 3 21 3 8" />
                <rect x="1" y="3" width="22" height="5" />
                <line x1="10" y1="12" x2="14" y2="12" />
              </svg>
              <span>{isArchived ? (sw ? 'Ondoa Kwenye Archive' : 'Unarchive') : (sw ? 'Hifadhi kwenye Archive' : 'Archive')}</span>
            </button>

            {/* 4. Delete chat */}
            <button
              onClick={() => {
                setMenuOpen(false)
                if (confirm(sw ? 'Futa mazungumzo haya ya sasa?' : 'Delete current chat session?')) {
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
              <span>{sw ? 'Futa Chat' : 'Delete'}</span>
            </button>
          </div>
        )}
      </div>
    </header>
  )
}