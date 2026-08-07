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

const CURRENT_APP_VERSION = 'v2026.08.06.1510'

export default function Home() {
  const { send, regenerate, editAndResend } = useChat()
  const { newConversation, activeConversationId, activeView, user, setUser, systemDisabled } = useKronxStore()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)

    // PWA Force-Sync Engine: Guarantees mobile PWAs and browsers immediately purge stale assets and load new Railway deployments
    if (typeof window !== 'undefined') {
      try {
        const lastVersion = localStorage.getItem('kx_version_stamp')
        if (lastVersion !== CURRENT_APP_VERSION) {
          console.log('[PWA Sync]: New deployment detected! Purging old phone caches and stuck memory...')
          
          // Clear all local query caches and stuck memory items
          const keysToRemove: string[] = []
          for (let i = 0; i < localStorage.length; i++) {
            const k = localStorage.key(i)
            if (k && (k.startsWith('kx_cache') || k.includes('memory') || k.includes('memories'))) {
              keysToRemove.push(k)
            }
          }
          keysToRemove.forEach(k => localStorage.removeItem(k))

          // Clear Service Worker CacheStorage
          if ('caches' in window) {
            caches.keys().then(names => {
              names.forEach(name => caches.delete(name))
            })
          }

          // Unregister old Service Workers to force fresh fetch
          if ('serviceWorker' in navigator) {
            navigator.serviceWorker.getRegistrations().then(registrations => {
              for (let reg of registrations) {
                reg.unregister()
              }
            })
          }

          localStorage.setItem('kx_version_stamp', CURRENT_APP_VERSION)
          window.location.reload()
          return
        }
      } catch (err) {
        console.warn('[PWA Sync Error]:', err)
      }
    }

    // Global keyboard shortcuts helper
    const handleKeyDown = (e: KeyboardEvent) => {
      const store = useKronxStore.getState()
      
      // Ctrl + Alt + N: New conversation
      if ((e.ctrlKey || e.metaKey) && e.altKey && e.key.toLowerCase() === 'n') {
        e.preventDefault()
        store.newConversation()
        console.log('[Keyboard Shortcut]: Started new conversation')
      }
      // Ctrl + Alt + S: Toggle sidebar
      if ((e.ctrlKey || e.metaKey) && e.altKey && e.key.toLowerCase() === 's') {
        e.preventDefault()
        store.toggleSidebar()
        console.log('[Keyboard Shortcut]: Toggled sidebar')
      }
      // Ctrl + Alt + L: Toggle language
      if ((e.ctrlKey || e.metaKey) && e.altKey && e.key.toLowerCase() === 'l') {
        e.preventDefault()
        const newLang = store.language === 'sw' ? 'en' : 'sw'
        store.setLanguage(newLang)
        console.log('[Keyboard Shortcut]: Toggled language to:', newLang)
      }
    }

    window.addEventListener('keydown', handleKeyDown)

    // Force PWA Service Worker to check for live updates and force reload instantly on activation
    if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then(registration => {
        registration.update()
      }).catch(err => console.warn('[PWA Update Check Error]', err))

      let refreshing = false
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (!refreshing) {
          refreshing = true
          window.location.reload()
        }
      })
    }

    // Start a new clean conversation on load if the current active conversation has messages
    const store = useKronxStore.getState()
    const activeMessages = store.activeMessages()
    if (activeMessages && activeMessages.length > 0) {
      store.newConversation()
    }

    // Purge old cached PWA bundles once so Chrome loads latest build
    if (typeof window !== 'undefined' && 'caches' in window) {
      caches.keys().then(names => {
        for (const name of names) {
          if (name.includes('workbox-precache') || name.includes('kronx') || name.includes('copetra') || name.includes('next-pwa')) {
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

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
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
          {activeView === 'admin' && isAdmin ? (
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