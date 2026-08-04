'use client'

import { useEffect, useState, useRef } from 'react'
import { useKronxStore } from '@/store/useKronxStore'

export default function PwaInstallPrompt() {
  const { user, language } = useKronxStore()
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null)
  const [isStandalone, setIsStandalone] = useState(false)
  const [showPrompt, setShowPrompt] = useState(false)
  const [isIos, setIsIos] = useState(false)
  const [showIosGuide, setShowIosGuide] = useState(false)
  const autoCloseTimerRef = useRef<NodeJS.Timeout | null>(null)
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
    const hasBeenShown = typeof window !== 'undefined' && sessionStorage.getItem('copetra_pwa_shown') === 'true'

    if (user && !isStandalone && !hasBeenShown) {
      sessionStorage.setItem('copetra_pwa_shown', 'true')
      setShowPrompt(true)
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
      setShowIosGuide(true)
    } else {
      alert(
        sw
          ? 'Ili kupakua Programu:\n1. Fungua menyu ya kivinjari chako (⋮).\n2. Chagua "Sakinisha Programu (Install App)" au "Pakua".'
          : 'To download the App:\n1. Open your browser menu (⋮).\n2. Tap "Install App" or "Download".'
      )
    }
  }

  if (isStandalone) return null

  return (
    <>
      {/* 1. Sleek PWA Banner Prompt (Permanent until dismissed/installed) */}
      {showPrompt && (
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
            boxShadow: '0 12px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(56, 189, 248, 0.3)',
            zIndex: 99999,
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            overflow: 'hidden',
            animation: 'message-pop 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards',
          }}
        >
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
                <span style={{ fontSize: '18px' }}>📥</span>
              </div>
              <div>
                <div style={{ fontSize: '14px', fontWeight: '800', color: '#ffffff', letterSpacing: '-0.2px' }}>
                  {sw ? 'Pakua Programu ya Copetra AI' : 'Download Copetra AI App'}
                </div>
                <div style={{ fontSize: '11.5px', color: '#94a3b8' }}>
                  {isIos
                    ? (sw ? 'Bofya kuweka kwenye iPhone' : 'Tap to add to iPhone Home Screen')
                    : (sw ? 'Pakua app ya simu haraka' : 'Download direct app to your phone')}
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
              <span>📥</span>
              <span>{sw ? 'PAKUA APP SASA' : 'DOWNLOAD APP NOW'}</span>
            </button>
            <button
              onClick={() => setShowPrompt(false)}
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
      )}

      {/* 2. Modern iPhone 2-Step Visual PWA Installation Modal */}
      {showIosGuide && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.85)',
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)',
            zIndex: 100000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
            animation: 'message-pop 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards',
          }}
        >
          <div
            style={{
              background: '#ffffff',
              borderRadius: '24px',
              padding: '24px',
              maxWidth: '380px',
              width: '100%',
              color: '#0f172a',
              boxShadow: '0 20px 40px rgba(0,0,0,0.3)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '36px', marginBottom: '8px' }}>📱</div>
            <h3 style={{ fontSize: '18px', fontWeight: 800, margin: '0 0 6px 0', color: '#0f172a' }}>
              {sw ? 'Sakinisha Copetra AI kwenye iPhone' : 'Install Copetra AI on iPhone'}
            </h3>
            <p style={{ fontSize: '13px', color: '#64748b', margin: '0 0 20px 0', lineHeight: 1.5 }}>
              {sw
                ? 'Mifumo ya Apple haikuruhusu kupakua kwa 1-Click. Fuata hatua 2 rahisi zifuatazo:'
                : 'Apple iOS requires 2 simple steps to add Copetra AI to your iPhone Home Screen:'}
            </p>

            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
                textAlign: 'left',
                marginBottom: '24px',
              }}
            >
              {/* Step 1 */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '16px',
                  padding: '12px 14px',
                }}
              >
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    background: '#2563eb',
                    color: '#ffffff',
                    fontWeight: 800,
                    fontSize: '14px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  1
                </div>
                <div style={{ fontSize: '13px', color: '#1e293b', lineHeight: 1.4 }}>
                  {sw ? (
                    <>
                      Gusa kitufe cha <strong>Shiriki (Share 📤)</strong> chini au juu ya Safari.
                    </>
                  ) : (
                    <>
                      Tap the <strong>Share button (📤 / ⎋)</strong> at the bottom of Safari.
                    </>
                  )}
                </div>
              </div>

              {/* Step 2 */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '16px',
                  padding: '12px 14px',
                }}
              >
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    background: '#16a34a',
                    color: '#ffffff',
                    fontWeight: 800,
                    fontSize: '14px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  2
                </div>
                <div style={{ fontSize: '13px', color: '#1e293b', lineHeight: 1.4 }}>
                  {sw ? (
                    <>
                      Tembea chini kisha uchague <strong>&quot;Ongeza kwenye Skrini ya Nyumbani&quot; (➕ Add to Home Screen)</strong>.
                    </>
                  ) : (
                    <>
                      Scroll down and tap <strong>&quot;Add to Home Screen&quot; (➕)</strong>.
                    </>
                  )}
                </div>
              </div>
            </div>

            <button
              onClick={() => {
                setShowIosGuide(false)
                setShowPrompt(false)
              }}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '14px',
                background: '#2563eb',
                color: '#ffffff',
                border: 'none',
                fontWeight: 700,
                fontSize: '14px',
                cursor: 'pointer',
                boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)',
              }}
            >
              {sw ? 'Nimeelewa (Got It)' : 'Got It!'}
            </button>
          </div>
        </div>
      )}
    </>
  )
}
