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
import PwaInstallPrompt from '@/components/pwa/PwaInstallPrompt'
import ErrorBoundary from '@/components/ErrorBoundary'
import { useChat } from '@/hooks/useChat'
import { useKronxStore } from '@/store/useKronxStore'

export default function Home() {
  const { send, regenerate, editAndResend } = useChat()
  const { newConversation, activeConversationId, activeView, user, setUser, systemDisabled } = useKronxStore()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)

    // Force PWA Service Worker to check for live updates from Railway on launch
    if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then(registration => {
        registration.update()
      }).catch(err => console.warn('[PWA Update Check Error]', err))
    }

    // Purge old cached PWA bundles once so Chrome loads latest build
    if (typeof window !== 'undefined' && 'caches' in window) {
      caches.keys().then(names => {
        for (const name of names) {
          if (name.includes('workbox-precache') || name.includes('kronx') || name.includes('copetra')) {
            caches.delete(name)
          }
        }
      })
    }

    // Sync logged-in user profile & plan directly from PostgreSQL DB (assigned by Admin)
    if (user?.email) {
      fetch('/api/users')
        .then(res => res.json())
        .then(users => {
          if (Array.isArray(users)) {
            const dbUser = users.find((u: any) => u.email?.toLowerCase() === user.email.toLowerCase())
            if (dbUser) {
              if (dbUser.plan !== user.plan || dbUser.role !== user.role || dbUser.isDeveloper !== user.isDeveloper) {
                setUser({
                  ...user,
                  plan: dbUser.plan || user.plan,
                  role: dbUser.role || user.role,
                  isDeveloper: dbUser.isDeveloper !== undefined ? dbUser.isDeveloper : user.isDeveloper
                })
              }
            }
          }
        })
        .catch(err => console.warn('[User DB Plan Sync Error]', err))
    }
  }, [user?.email])

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
            Copetra AI System Currently Unavailable
          </h2>
          <p style={{ fontSize: '14px', color: '#94a3b8', lineHeight: '1.6', margin: 0 }}>
            The administrator has temporarily shut down Copetra AI services for scheduled system updates and maintenance. Please try again later.
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
    <ErrorBoundary>
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
        <PwaInstallPrompt />
      </main>
    </ErrorBoundary>
  )
}