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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !password.trim()) return

    const user: UserProfile = {
      id: 'u-' + Date.now(),
      name: name.trim() || email.split('@')[0],
      email: email.trim(),
      avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(name || email)}`,
      role: 'user',
      plan: 'free',
      picturesUsedToday: 0,
      videosUsedToday: 0,
      provider: 'email',
      createdAt: new Date().toISOString(),
    }
    loginUser(user)
  }

  const content = (
    <div className="auth-modal" onClick={e => e.stopPropagation()}>
      {!isPage && (
        <button
          className="auth-close-btn"
          onClick={() => setAuthModalOpen(false)}
          title="Funga · Close"
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

      <div className="auth-header">
        <div style={{ width: '64px', height: '64px', borderRadius: '18px', overflow: 'hidden', margin: '0 auto 12px auto', border: '1px solid #bae6fd', boxShadow: '0 6px 20px rgba(2, 132, 199, 0.15)' }}>
          <img src="/kronx_logo.jpg" alt="Kron-X Logo" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </div>
        <h2>Kronx AI</h2>
        <p>{sw ? 'Ingia au Jisajili kuanza kutumia Kronx' : 'Sign in or register to get started with Kronx'}</p>
      </div>


        {/* Auth Tabs */}
        <div className="auth-tabs">
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
            <input
              type="password"
              className="auth-input"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="auth-submit-btn">
            {tab === 'login'
              ? (sw ? 'Ingia Sasa' : 'Sign In')
              : (sw ? 'Tengeneza Akaunti' : 'Create Account')}
          </button>
        </form>
      </div>
  )

  if (isPage) return content

  return (
    <div className="auth-backdrop" onClick={() => setAuthModalOpen(false)}>
      {content}
    </div>
  )
}

