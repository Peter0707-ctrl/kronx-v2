'use client'

import { useEffect, useState } from 'react'
import { useKronxStore } from '@/store/useKronxStore'

export default function PwaInstallPrompt() {
  const { user, language } = useKronxStore()
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null)
  const [isStandalone, setIsStandalone] = useState(false)
  const [showPrompt, setShowPrompt] = useState(false)
  const [isIos, setIsIos] = useState(false)
  const sw = language === 'sw'

  useEffect(() => {
    // 1. Check if running in standalone mode (already installed)
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
    // Show install prompt whenever user is logged in AND app is NOT running as installed PWA
    if (user && !isStandalone) {
      // Delay slightly to let the UI load smoothly
      const timer = setTimeout(() => {
        setShowPrompt(true)
      }, 1000)
      return () => clearTimeout(timer)
    } else {
      setShowPrompt(false)
    }
  }, [user, isStandalone])

  const handleInstallClick = async () => {
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
        right: '24px',
        left: '24px',
        maxWidth: '440px',
        margin: '0 auto',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        color: '#ffffff',
        borderRadius: '20px',
        padding: '20px 22px',
        boxShadow: '0 12px 36px rgba(0,0,0,0.35)',
        zIndex: 99999,
        border: '1px solid #38bdf8',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        animation: 'message-pop 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              overflow: 'hidden',
              background: '#0284c7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '1px solid rgba(255,255,255,0.2)',
            }}
          >
            <img src="/kronx_logo.jpg" alt="Copetra Logo" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          </div>
          <div>
            <div style={{ fontSize: '15px', fontWeight: '800', color: '#ffffff', letterSpacing: '-0.2px' }}>
              {sw ? 'Sakinisha Programu ya Copetra AI' : 'Install Copetra AI App'}
            </div>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
              {sw ? 'Pata uwezo kamili bila kutumia browser' : 'Download for faster access & instant AI responses'}
            </div>
          </div>
        </div>

        <button
          onClick={() => setShowPrompt(false)}
          style={{
            background: 'rgba(255,255,255,0.1)',
            border: 'none',
            color: '#94a3b8',
            borderRadius: '50%',
            width: '28px',
            height: '28px',
            cursor: 'pointer',
            fontWeight: '700',
            fontSize: '14px',
          }}
          title="Close"
        >
          ✕
        </button>
      </div>

      <div style={{ display: 'flex', gap: '10px' }}>
        <button
          onClick={handleInstallClick}
          style={{
            flex: 1,
            padding: '11px 16px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #0284c7, #0369a1)',
            color: '#ffffff',
            border: 'none',
            fontWeight: '800',
            fontSize: '13.5px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            boxShadow: '0 4px 14px rgba(2, 132, 199, 0.4)',
          }}
        >
          <span>📱</span>
          <span>{sw ? 'SAKINISHA APP SASA' : 'INSTALL APP NOW'}</span>
        </button>
        <button
          onClick={() => setShowPrompt(false)}
          style={{
            padding: '11px 14px',
            borderRadius: '12px',
            background: 'transparent',
            color: '#94a3b8',
            border: '1px solid rgba(255,255,255,0.15)',
            fontWeight: '600',
            fontSize: '12.5px',
            cursor: 'pointer',
          }}
        >
          {sw ? 'Baadaye' : 'Later'}
        </button>
      </div>
    </div>
  )
}
