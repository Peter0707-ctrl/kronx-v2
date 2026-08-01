'use client'

import { useCallback, useEffect, useState } from 'react'

import Sidebar from '@/components/sidebar/Sidebar'
import TopBar from '@/components/topbar/TopBar'
import ChatArea from '@/components/chat/ChatArea'
import InputBar from '@/components/input/InputBar'
import AdminDashboard from '@/components/admin/AdminDashboard'
import LandingPage from '@/components/landing/LandingPage'
import AuthModal from '@/components/auth/AuthModal'
import SettingsModal from '@/components/settings/SettingsModal'
import { useChat } from '@/hooks/useChat'
import { useKronxStore } from '@/store/useKronxStore'

export default function Home() {
  const { send, regenerate, editAndResend } = useChat()
  const { newConversation, activeConversationId, activeView, user, systemDisabled } = useKronxStore()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleSend = useCallback(
    async (text: string) => {
      if (!activeConversationId) newConversation()
      await send(text)
    },
    [send, activeConversationId, newConversation]
  )

  if (!mounted) {
    return (
      <main className="shell" role="main">
        <div style={{ flex: 1, background: '#f8fafc' }} />
      </main>
    )
  }

  // Emergency System Kill Switch Enforcement: Regular users are blocked if system is shut down
  const isAdmin = user?.role === 'admin' || user?.email === 'pj0040280@gmail.com'

  if (systemDisabled && !isAdmin) {
    return (
      <main
        className="shell"
        role="main"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          width: '100vw',
          padding: '24px',
          background: '#0f172a',
          color: '#ffffff',
          textAlign: 'center',
          fontFamily: "Calibri, 'Calibri Light', sans-serif"
        }}
      >
        <div style={{ maxWidth: '460px', background: '#1e293b', padding: '36px', borderRadius: '24px', border: '1px solid #334155', boxShadow: '0 20px 50px rgba(0,0,0,0.4)' }}>
          <div style={{ fontSize: '12px', fontWeight: '800', color: '#ef4444', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px' }}>
            SYSTEM OFFLINE / MAINTENANCE
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: '800', margin: '0 0 12px 0', color: '#ffffff' }}>
            Kronx AI System Currently Unavailable
          </h2>
          <p style={{ fontSize: '14px', color: '#94a3b8', lineHeight: '1.6', margin: 0 }}>
            The administrator has temporarily shut down Kronx AI services for scheduled system updates and maintenance. Please try again later.
          </p>
        </div>
      </main>
    )
  }

  // Front Page Authentication: If not logged in, show Login & Register screen directly!
  if (!user) {
    return (
      <main
        className="shell"
        role="main"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          width: '100vw',
          padding: '20px',
        }}
      >
        <AuthModal isPage={true} />
      </main>
    )
  }


  return (
    <main className="shell" role="main">
      <Sidebar />
      <div className="main-panel">
        <TopBar />
        {activeView === 'admin' ? (
          <AdminDashboard />
        ) : (
          <>
            <ChatArea onSend={handleSend} onRegenerate={regenerate} onEditAndResend={editAndResend} />
            <InputBar onSend={handleSend} />
          </>
        )}
      </div>
      <AuthModal />
      <SettingsModal />
    </main>
  )
}