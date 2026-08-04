'use client'

import { useEffect, useState, useRef } from 'react'
import { useKronxStore } from '@/store/useKronxStore'

export default function PwaInstallPrompt() {
  const { user, language } = useKronxStore()
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null)
  const [isStandalone, setIsStandalone] = useState(false)
  const [showPrompt, setShowPrompt] = useState(false)
  const [isIos, setIsIos] = useState(false)
  const autoCloseTimerRef = useRef<NodeJS.Timeout | null>(null)
  const sw = language === 'sw'

  useEffect(() => {
    // 1. Check if running in standalone mode (already installed & downloaded)
    const checkStandalone = () => {
      const isStandaloneMode =
        window.matchMedia('(display-mode: standalone)').matches ||
        (window.navigator as any).standalone ||
        document.referrer.includes('android-app://')
      setIsStandalone(isStandaloneMode)
    }

    checkStandalone()

    // 2. Detect iOS
    const ua = window.navigator.userAgent
    const isIosDevice = /iPad|iPhone|iPod/.test(ua) && !(window as any).MSStream
    setIsIos(isIosDevice)

    // 3. Listen for browser PWA install prompt
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    }
  }, [])

  useEffect(() => {
    // Show install prompt ONLY whenever user is logged in AND app is NOT installed
    if (user && !isStandalone) {
      setShowPrompt(true)

      // Auto-disappear within 2.5 seconds automatically
      autoCloseTimerRef.current = setTimeout(() => {
        setShowPrompt(false)
      }, 2500)

      return () => {
        if (autoCloseTimerRef.current) clearTimeout(autoCloseTimerRef.current)
      }
    } else {
      setShowPrompt(false)
    }
  }, [user, isStandalone])

  const handleInstallClick = async () => {
    if (autoCloseTimerRef.current) clearTimeout(autoCloseTimerRef.current)

    if (deferredPrompt) {
      deferredPrompt.prompt()
      const { outcome } = await deferredPrompt.userChoice
      if (outcome === 'accepted') {
        setShowPrompt(false)
      }
      setDeferredPrompt(null)
    } else if (isIos) {
      alert(
        sw
          ? 'Ili kusakinisha Programu kwenye iPhone/iPad:\n1. Gusa kitufe cha Shiriki (Share ⎋) chini ya Safari.\n2. Chagua "Ongeza kwenye Skrini ya Nyumbani (Add to Home Screen ➕)".'
          : 'To install on iPhone/iPad:\n1. Tap the Share button (⎋) at the bottom of Safari.\n2. Scroll down and tap "Add to Home Screen (➕)".'
      )
    } else {
      alert(
        sw
          ? 'Ili kusakinisha Programu:\n1. Fungua menyu ya kivinjari chako (⋮).\n2. Chagua "Sakinisha Programu (Install App)" au "Ongeza kwenye Skrini ya Nyumbani".'
          : 'To install the App:\n1. Open your browser menu (⋮).\n2. Tap "Install App" or "Add to Home Screen".'
      )
    }
  }

  if (!showPrompt || isStandalone) return null

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '20px',
        left: '20px',
        maxWidth: '400px',
        margin: '0 auto',
        background: 'rgba(15, 23, 42, 0.94)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        color: '#ffffff',
        borderRadius: '18px',
        padding: '16px 18px',
        boxShadow: '0 12px 32px rgba(0,0,0,0.4), 0 0 0 1px rgba(56, 189, 248, 0.25)',
        zIndex: 99999,
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        overflow: 'hidden',
        animation: 'message-pop 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      }}
    >
      {/* Sleek 2-second Auto-Cancel Timer Progress Line */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          height: '3px',
          background: 'linear-gradient(90deg, #38bdf8, #0284c7)',
          width: '100%',
          animation: 'pwa-timer-shrink 2.5s linear forwards',
        }}
      />

      <style jsx>{`
        @keyframes pwa-timer-shrink {
          from {
            width: 100%;
          }
          to {
            width: 0%;
          }
        }
      `}</style>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              overflow: 'hidden',
              background: '#0284c7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 8px rgba(2, 132, 199, 0.4)',
            }}
          >
            <img src="/kronx_logo.jpg" alt="Copetra Logo" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          </div>
          <div>
            <div style={{ fontSize: '14px', fontWeight: '800', color: '#ffffff', letterSpacing: '-0.2px' }}>
              {sw ? 'Sakinisha Programu ya Copetra AI' : 'Install Copetra AI App'}
            </div>
            <div style={{ fontSize: '11.5px', color: '#94a3b8' }}>
              {sw ? 'Pakua app bila kutumia browser' : 'Get fast access without browser bar'}
            </div>
          </div>
        </div>

        <button
          onClick={() => {
            if (autoCloseTimerRef.current) clearTimeout(autoCloseTimerRef.current)
            setShowPrompt(false)
          }}
          style={{
            background: 'rgba(255,255,255,0.1)',
            border: 'none',
            color: '#94a3b8',
            borderRadius: '50%',
            width: '26px',
            height: '26px',
            cursor: 'pointer',
            fontWeight: '700',
            fontSize: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
          title="Close"
        >
          ✕
        </button>
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={handleInstallClick}
          style={{
            flex: 1,
            padding: '9px 14px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #0284c7, #0369a1)',
            color: '#ffffff',
            border: 'none',
            fontWeight: '800',
            fontSize: '12.5px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            boxShadow: '0 4px 12px rgba(2, 132, 199, 0.35)',
          }}
        >
          <span>📱</span>
          <span>{sw ? 'SAKINISHA SASA' : 'INSTALL NOW'}</span>
        </button>
        <button
          onClick={() => {
            if (autoCloseTimerRef.current) clearTimeout(autoCloseTimerRef.current)
            setShowPrompt(false)
          }}
          style={{
            padding: '9px 12px',
            borderRadius: '10px',
            background: 'transparent',
            color: '#94a3b8',
            border: '1px solid rgba(255,255,255,0.15)',
            fontWeight: '600',
            fontSize: '12px',
            cursor: 'pointer',
          }}
        >
          {sw ? 'Acha' : 'Cancel'}
        </button>
      </div>
    </div>
  )
}
