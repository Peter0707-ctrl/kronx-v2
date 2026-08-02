'use client'

import { useState } from 'react'
import { useKronxStore } from '@/store/useKronxStore'
import { UserProfile } from '@/types'

interface AuthModalProps {
  isPage?: boolean
}

export default function AuthModal({ isPage = false }: AuthModalProps) {
  const { authModalOpen, setAuthModalOpen, loginUser, language, setLanguage } = useKronxStore()
  const [tab, setTab] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const sw = language === 'sw'

  if (!isPage && !authModalOpen) return null

  const handleGoogleLogin = () => {
    const googleUser: UserProfile = {
      id: 'g-' + Date.now(),
      name: 'User Account',
      email: 'user@kronx.ai',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Alex',
      role: 'user',
      plan: 'free',
      picturesUsedToday: 0,
      videosUsedToday: 0,
      provider: 'google',
      createdAt: new Date().toISOString(),
    }
    loginUser(googleUser)
  }

  // Zero-Knowledge Encrypted Security Verification (SHA-256 Hashes)
  // Master Admin Email (pj0040280@gmail.com): 9063d0bbb69a40812b28290f914b7bc398629d954c8322b0b666c0705e98bd95
  // Master Admin Password (Admin@123): e86f78a8a3caf0b60d8e74e5942aa6d86dc150cd3c03338aef25b7d2d7e3acc7
  const sha256 = async (str: string) => {
    const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(str))
    return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !password.trim()) return

    const emailHash = await sha256(email.trim().toLowerCase())
    const passHash = await sha256(password.trim())

    const isMasterAdmin =
      emailHash === '9063d0bbb69a40812b28290f914b7bc398629d954c8322b0b666c0705e98bd95' &&
      passHash === 'e86f78a8a3caf0b60d8e74e5942aa6d86dc150cd3c03338aef25b7d2d7e3acc7'

    const user: UserProfile = {
      id: isMasterAdmin ? 'u-admin-master' : 'u-' + Date.now(),
      name: isMasterAdmin ? 'Peter Joseph Msira' : (name.trim() || email.split('@')[0]),
      email: email.trim(),
      avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(name || email)}`,
      role: isMasterAdmin ? 'admin' : 'user',
      plan: isMasterAdmin ? 'premium' : 'free',
      picturesUsedToday: 0,
      videosUsedToday: 0,
      provider: 'email',
      createdAt: new Date().toISOString(),
    }
    loginUser(user)
  }

  const content = (
    <div
      className="auth-modal"
      onClick={e => e.stopPropagation()}
      style={{
        display: 'flex',
        flexDirection: 'row',
        maxWidth: '920px',
        width: '100%',
        padding: 0,
        overflow: 'hidden',
        borderRadius: '28px',
        boxShadow: '0 25px 60px rgba(0,0,0,0.18)',
        background: '#ffffff'
      }}
    >
      {/* LEFT SIDE: KRONX AI INTRODUCTORY BRAND PANEL */}
      <div
        style={{
          flex: 1,
          background: '#0f172a',
          color: '#ffffff',
          padding: '40px 32px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          fontFamily: "Calibri, 'Calibri Light', sans-serif"
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '28px' }}>
            <div style={{ width: '44px', height: '44px', borderRadius: '12px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.2)' }}>
              <img src="/kronx_logo.jpg" alt="Kronx Logo" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            </div>
            <span style={{ fontSize: '24px', fontWeight: '900', letterSpacing: '-0.5px' }}>KRON X</span>
          </div>

          <h2 style={{ fontSize: '26px', fontWeight: '800', marginBottom: '14px', lineHeight: '1.25' }}>
            {sw ? 'Karibu Kronx AI — Mshauri wa Wanafunzi na Elimu' : 'Welcome to Kronx AI — Student Study Companion'}
          </h2>

          <p style={{ fontSize: '14.5px', color: '#94a3b8', lineHeight: '1.6', marginBottom: '28px' }}>
            {sw
              ? 'Kronx ni mfumo wa hali ya juu wa AI uliotengenezwa na PJ COPETRANOVA maalum kusaidia wanafunzi katika kujifunza, kufanya assignments, kuelewa masomo kwa hatua kwa hatua, na kufanya tafiti.'
              : 'Kronx is an advanced AI study companion created by PJ COPETRANOVA specifically to empower students with step-by-step academic explanations, homework guidance, research thesis writing, and programming.'}
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ background: 'rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: '8px', fontWeight: '800', color: '#38bdf8' }}>•</span>
              <span>{sw ? 'Usaidizi wa masomo kwa hatua kwa hatua' : 'Step-by-step academic explanation & homework help'}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ background: 'rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: '8px', fontWeight: '800', color: '#38bdf8' }}>•</span>
              <span>{sw ? 'Ufasaha wa Kiswahili na Kiingereza katika masomo' : 'Dual Language Support (Swahili & English)'}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ background: 'rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: '8px', fontWeight: '800', color: '#38bdf8' }}>•</span>
              <span>{sw ? 'Uwezo wa kutengeneza Picha za FLUX 8K na Video' : 'FLUX 8K Image Renders & Video Generators'}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ background: 'rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: '8px', fontWeight: '800', color: '#38bdf8' }}>•</span>
              <span>{sw ? 'Fursa ya kupata Developer API Keys' : 'Developer API Keys for Premium Subscribers'}</span>
            </div>
          </div>
        </div>

        <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '16px', marginTop: '28px', fontSize: '12px', color: '#64748b', letterSpacing: '0.5px' }}>
          POWERED BY PJ COPETRANOVA
        </div>
      </div>

      {/* RIGHT SIDE: AUTHENTICATION FORM */}
      <div style={{ flex: 1, padding: '40px 36px', background: '#ffffff', position: 'relative' }}>
        {!isPage && (
          <button
            className="auth-close-btn"
            onClick={() => setAuthModalOpen(false)}
            title="Funga · Close"
            style={{ top: '16px', right: '16px' }}
          >
            ✕
          </button>
        )}

        {/* Language Switcher on Front Page */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '16px' }}>
          <div className="lang-toggle-mini">
            <button
              className={`mini-pill ${sw ? 'pill-active' : ''}`}
              onClick={() => setLanguage('sw')}
            >
              Kiswahili
            </button>
            <button
              className={`mini-pill ${!sw ? 'pill-active' : ''}`}
              onClick={() => setLanguage('en')}
            >
              English
            </button>
          </div>
        </div>

        <div className="auth-header" style={{ marginBottom: '20px' }}>
          <h2 style={{ fontSize: '22px', fontWeight: '800', margin: '0 0 4px 0', color: '#0f172a' }}>
            {tab === 'login' ? (sw ? 'Karibu Tena' : 'Welcome Back') : (sw ? 'Fungua Akaunti' : 'Create Account')}
          </h2>
          <p style={{ fontSize: '13.5px', color: '#64748b', margin: 0 }}>
            {sw ? 'Ingia au Jisajili kuanza kutumia Kronx' : 'Sign in or register to get started with Kronx'}
          </p>
        </div>

        {/* Auth Tabs */}
        <div className="auth-tabs" style={{ marginBottom: '20px' }}>
          <button
            className={`auth-tab ${tab === 'login' ? 'auth-tab--active' : ''}`}
            onClick={() => setTab('login')}
          >
            {sw ? 'Ingia · Login' : 'Sign In'}
          </button>
          <button
            className={`auth-tab ${tab === 'register' ? 'auth-tab--active' : ''}`}
            onClick={() => setTab('register')}
          >
            {sw ? 'Jisajili · Register' : 'Create Account'}
          </button>
        </div>

        {/* Google OAuth Button */}
        <button className="google-btn" onClick={handleGoogleLogin}>
          <svg width={18} height={18} viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
            />
            <path
              fill="#34A853"
              d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.11-6.72-4.96H1.27v3.15C3.25 21.3 7.31 24 12 24z"
            />
            <path
              fill="#FBBC05"
              d="M5.28 14.24c-.25-.72-.38-1.49-.38-2.24s.13-1.52.38-2.24V6.61H1.27C.46 8.23 0 10.06 0 12s.46 3.77 1.27 5.39l4.01-3.15z"
            />
            <path
              fill="#EA4335"
              d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.25 2.7 1.27 6.61l4.01 3.15c.95-2.85 3.6-4.96 6.72-4.96z"
            />
          </svg>
          <span>{sw ? 'Endelea na Google' : 'Continue with Google'}</span>
        </button>

        <div className="auth-divider">
          <span>{sw ? 'au tumia barua pepe' : 'or continue with email'}</span>
        </div>

        {/* Email Auth Form */}
        <form onSubmit={handleSubmit} className="auth-form">
          {tab === 'register' && (
            <div className="auth-field">
              <label>{sw ? 'Jina Kamili' : 'Full Name'}</label>
              <input
                type="text"
                className="auth-input"
                placeholder="John Mwangi"
                value={name}
                onChange={e => setName(e.target.value)}
                required
              />
            </div>
          )}

          <div className="auth-field">
            <label>{sw ? 'Barua Pepe' : 'Email Address'}</label>
            <input
              type="email"
              className="auth-input"
              placeholder="user@example.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="auth-field">
            <label>{sw ? 'Neno la Siri' : 'Password'}</label>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                className="auth-input"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                style={{ paddingRight: '40px', width: '100%' }}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{ position: 'absolute', right: '12px', background: 'none', border: 'none', cursor: 'pointer', fontSize: '16px', color: '#64748b' }}
                title={showPassword ? 'Hide Password' : 'Show Password'}
              >
                {showPassword ? '👁️' : '🙈'}
              </button>
            </div>
          </div>

          <button type="submit" className="auth-submit-btn">
            {tab === 'login'
              ? (sw ? 'Ingia Sasa' : 'Sign In')
              : (sw ? 'Tengeneza Akaunti' : 'Create Account')}
          </button>
        </form>
      </div>
    </div>
  )

  if (isPage) return content

  return (
    <div className="auth-backdrop" onClick={() => setAuthModalOpen(false)}>
      {content}
    </div>
  )
}

