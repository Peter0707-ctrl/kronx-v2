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
  const { newConversation, activeConversationId, activeView, user } = useKronxStore()
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