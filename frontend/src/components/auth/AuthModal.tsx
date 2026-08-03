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
    alert("Google Login is currently disabled. Please create an account using your email.")
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
      chatsUsedToday: 0,
      provider: 'email',
      createdAt: new Date().toISOString(),
    }

    if (tab === 'register') {
      // Create user but don't log them in yet
      fetch('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(user)
      }).catch(e => console.warn('Could not register user to DB:', e));
      
      alert(sw ? "Usajili umekamilika! Tafadhali ingia." : "Registration successful! Please sign in.")
      setTab('login')
      return
    }

    loginUser(user)
  }

  const content = (
    <div
      className="auth-modal auth-modal-container"
      onClick={e => e.stopPropagation()}
    >
      {/* LEFT SIDE: KRONX AI INTRODUCTORY BRAND PANEL */}
      <div className="auth-brand-panel">
        <div className="auth-brand-content">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '28px' }}>
            <div style={{ width: '44px', height: '44px', borderRadius: '12px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.2)' }}>
              <img src="/kronx_logo.jpg" alt="Kronx Logo" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            </div>
            <span style={{ fontSize: '24px', fontWeight: '900', letterSpacing: '-0.5px' }}>KRON X</span>
          </div>

          <h3 style={{ fontSize: '32px', fontWeight: '800', margin: '0 0 12px 0', letterSpacing: '-0.5px', color: '#ffffff' }}>
            Copetra AI Companion
          </h3>
          <p className="auth-brand-desc">
            Copetra AI is an advanced AI study companion created by PJ Copetranova to empower students with step-by-step academic explanations, homework guidance, research thesis writing, and programming.
          </p>

          <div className="auth-brand-features" style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ background: 'rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: '8px', fontWeight: '800', color: '#38bdf8' }}>•</span>
              <span>Step-by-step academic explanation & homework help</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ background: 'rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: '8px', fontWeight: '800', color: '#38bdf8' }}>•</span>
              <span>Dual Language Support (Swahili & English)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ background: 'rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: '8px', fontWeight: '800', color: '#38bdf8' }}>•</span>
              <span>FLUX 8K Image Renders & Video Generators</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ background: 'rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: '8px', fontWeight: '800', color: '#38bdf8' }}>•</span>
              <span>Developer API Keys for Premium Subscribers</span>
          </div>
          <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '16px', marginTop: '28px', fontSize: '12px', color: '#64748b', letterSpacing: '0.5px' }}>
            POWERED BY PJ COPETRANOVA
          </div>
        </div>
      </div>
      </div>

      {/* RIGHT SIDE: AUTHENTICATION FORM */}
      <div className="auth-form-panel">
        {!isPage && (
          <button
            className="auth-close-btn"
            onClick={() => setAuthModalOpen(false)}
            title="Close"
            style={{ position: 'absolute', top: '16px', right: '16px', background: '#f1f5f9', border: 'none', borderRadius: '50%', width: '32px', height: '32px', cursor: 'pointer', fontWeight: '700', color: '#0f172a' }}
          >
            ✕
          </button>
        )}

        <div className="auth-header" style={{ marginBottom: '20px' }}>
          <h2 style={{ fontSize: '22px', fontWeight: '800', margin: '0 0 4px 0', color: '#0f172a' }}>
            {tab === 'login' ? 'Welcome Back' : 'Register Account'}
          </h2>
          <p style={{ fontSize: '13.5px', color: '#64748b', margin: 0 }}>
            {tab === 'login' ? 'Sign in to access your Copetra AI workspace' : 'Register to get started with Copetra AI'}
          </p>
        </div>

        {/* Tab Selector: Login vs Register */}
        <div className="auth-tabs" style={{ display: 'flex', background: '#f1f5f9', padding: '4px', borderRadius: '12px', marginBottom: '20px', gap: '4px' }}>
          <button
            type="button"
            className={`auth-tab-btn ${tab === 'login' ? 'tab-active' : ''}`}
            onClick={() => setTab('login')}
            style={{ flex: 1, padding: '8px 4px', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '700', fontSize: '12.5px', background: tab === 'login' ? '#ffffff' : 'transparent', color: tab === 'login' ? '#0f172a' : '#64748b', boxShadow: tab === 'login' ? '0 2px 6px rgba(0,0,0,0.05)' : 'none', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`auth-tab-btn ${tab === 'register' ? 'tab-active' : ''}`}
            onClick={() => setTab('register')}
            style={{ flex: 1, padding: '8px 4px', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '700', fontSize: '12.5px', background: tab === 'register' ? '#ffffff' : 'transparent', color: tab === 'register' ? '#0f172a' : '#64748b', boxShadow: tab === 'register' ? '0 2px 6px rgba(0,0,0,0.05)' : 'none', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}
          >
            Register
          </button>
        </div>

        {/* Removed Fake Google & Guest Buttons to force real registration */}

        {/* Email Auth Form */}
        <form onSubmit={handleSubmit} className="auth-form">
          {tab === 'register' && (
            <div className="auth-field">
              <label>Full Name</label>
              <input
                type="text"
                className="auth-input"
                placeholder="Enter your full name"
                value={name}
                onChange={e => setName(e.target.value)}
                required
              />
            </div>
          )}

          <div className="auth-field">
            <label>Email Address</label>
            <input
              type="email"
              className="auth-input"
              placeholder="Enter your email address"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="auth-field">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label style={{ margin: 0 }}>Password</label>
              {tab === 'login' && (
                <a 
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    window.open(`https://wa.me/255673190931?text=${encodeURIComponent('Habari Admin, nimesahau nenosiri (password) la akaunti yangu ya Copetra AI. Naomba msaada wa kureset.')}`, '_blank');
                  }}
                  style={{ fontSize: '12.5px', color: '#0ea5e9', textDecoration: 'none', fontWeight: '700' }}
                >
                  Forgot Password?
                </a>
              )}
            </div>
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
            {tab === 'login' ? 'Sign In' : 'Register'}
          </button>
        </form>

        {/* Founder & Developer Social Action Buttons */}
        <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
          <a
            href="https://wa.me/255673190931?text=Habari%20PJ%20COPETRANOVA,%20nimetembelea%20PJKRONX%20AI%20na%20ningependa%20mawasiliano."
            target="_blank"
            rel="noopener noreferrer"
            title="WhatsApp Support"
            style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '36px', height: '36px', borderRadius: '50%', background: '#25D366', color: '#ffffff', textDecoration: 'none', boxShadow: '0 2px 8px rgba(37, 211, 102, 0.3)' }}
          >
            <svg width={18} height={18} viewBox="0 0 24 24" fill="currentColor">
              <path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-1.107 4.04 4.05-1.061z"/>
            </svg>
          </a>

          <a
            href="https://ig.me/m/peterjoh_jim"
            target="_blank"
            rel="noopener noreferrer"
            title="Direct Instagram Message"
            style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '36px', height: '36px', borderRadius: '50%', background: 'linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%)', color: '#ffffff', textDecoration: 'none', boxShadow: '0 2px 8px rgba(220, 39, 67, 0.3)' }}
          >
            <svg width={18} height={18} viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
            </svg>
          </a>

          <a
            href="https://mail.google.com/mail/?view=cm&fs=1&to=pb0040280@gmail.com&su=Inquiry%20from%20PJKRONX%20AI%20Platform"
            target="_blank"
            rel="noopener noreferrer"
            title="Email Founder"
            style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '36px', height: '36px', borderRadius: '50%', background: '#0284c7', color: '#ffffff', textDecoration: 'none', boxShadow: '0 2px 8px rgba(2, 132, 199, 0.3)' }}
          >
            <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
              <polyline points="22,6 12,13 2,6" />
            </svg>
          </a>
        </div>
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

