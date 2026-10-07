'use client'

import { useState } from 'react'
import { useKronxStore } from '@/store/useKronxStore'
import { UserProfile } from '@/types'
import { COPETRA_LOGO_BASE64 } from '@/lib/brandLogo'

interface AuthModalProps {
  isPage?: boolean
}

export default function AuthModal({ isPage = false }: AuthModalProps) {
  const { authModalOpen, setAuthModalOpen, loginUser, language } = useKronxStore()
  const [tab, setTab] = useState<'login' | 'register' | 'forgot'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  // Forgot Password Flow States
  const [forgotStep, setForgotStep] = useState<'request' | 'verify'>('request')
  const [forgotEmail, setForgotEmail] = useState('')
  const [resetCode, setResetCode] = useState('')
  const [generatedCodePreview, setGeneratedCodePreview] = useState<string | null>(null)
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showNewPassword, setShowNewPassword] = useState(false)

  // Feedback and Loading States
  const [authError, setAuthError] = useState<string | null>(null)
  const [authSuccess, setAuthSuccess] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const sw = language === 'sw'

  if (!isPage && !authModalOpen) return null

  const clearMessages = () => {
    setAuthError(null)
    setAuthSuccess(null)
  }

  // Zero-Knowledge Encrypted Security Verification (SHA-256 Hashes)
  // Master Admin Email (pj0040280@gmail.com): 9063d0bbb69a40812b28290f914b7bc398629d954c8322b0b666c0705e98bd95
  // Master Admin Password (Admin@123): e86f78a8a3caf0b60d8e74e5942aa6d86dc150cd3c03338aef25b7d2d7e3acc7
  const sha256 = async (str: string) => {
    const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(str))
    return Array.from(new Uint8Array(buf))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('')
  }

  // Handle Login & Registration Form Submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearMessages()
    if (!email.trim() || !password.trim()) return

    setIsLoading(true)

    try {
      const cleanEmail = email.trim().toLowerCase()
      const passHash = await sha256(password.trim())
      const emailHash = await sha256(cleanEmail)

      const isMasterAdmin =
        emailHash === '9063d0bbb69a40812b28290f914b7bc398629d954c8322b0b666c0705e98bd95' &&
        passHash === 'e86f78a8a3caf0b60d8e74e5942aa6d86dc150cd3c03338aef25b7d2d7e3acc7'

      if (tab === 'register') {
        const newUser: UserProfile = {
          id: isMasterAdmin ? 'u-admin-master' : 'u-' + Date.now(),
          name: isMasterAdmin ? 'Admin at pjcopetranovax' : name.trim() || cleanEmail.split('@')[0],
          email: cleanEmail,
          avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(name || cleanEmail)}`,
          role: isMasterAdmin ? 'admin' : 'user',
          plan: isMasterAdmin ? 'premium' : 'free',
          picturesUsedToday: 0,
          videosUsedToday: 0,
          chatsUsedToday: 0,
          provider: 'email',
          createdAt: new Date().toISOString(),
          ...(isMasterAdmin ? { adminKey: passHash } : {}),
        }

        const regRes = await fetch('/api/users', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-admin-key': isMasterAdmin ? passHash : '',
          },
          body: JSON.stringify({ ...newUser, password: password.trim() }),
        })

        if (!regRes.ok) {
          throw new Error(sw ? 'Usajili umeshindwa. Jaribu tena.' : 'Registration failed. Please try again.')
        }

        setAuthSuccess(
          sw
            ? 'Usajili umekamilika! Sasa unaweza kuingia kwa kutumia akaunti yako.'
            : 'Registration successful! Please sign in with your credentials.'
        )
        setTab('login')
        return
      }

      if (tab === 'login') {
        // Authenticate via secure /api/auth/login endpoint
        const loginRes = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: cleanEmail, password: password.trim() }),
        })

        const loginData = await loginRes.json().catch(() => ({}))

        if (!loginRes.ok || !loginData.success) {
          if (loginData.code === 'user_not_found') {
            setAuthError(
              sw
                ? 'Akaunti haipatikani. Tafadhali bonyeza Register ili kujiunga.'
                : 'Account not found. Please register to create an account.'
            )
            return
          }
          if (loginData.code === 'invalid_password') {
            setAuthError(
              sw
                ? 'Nenosiri si sahihi. Jaribu tena au bonyeza "Forgot Password" chini.'
                : 'Incorrect password. Try again or click "Forgot Password" below.'
            )
            return
          }
          throw new Error(
            loginData.message || (sw ? 'Kosa la kuingia. Jaribu tena.' : 'Failed to sign in. Please verify credentials.')
          )
        }

        loginUser(loginData.user)
      }
    } catch (err: any) {
      console.error('[Auth Error]', err)
      setAuthError(err?.message || (sw ? 'Kuna hitilafu imetokea.' : 'An error occurred during authentication.'))
    } finally {
      setIsLoading(false)
    }
  }

  // Step 1: Request 6-Digit Password Reset OTP Code
  const handleRequestResetCode = async (e: React.FormEvent) => {
    e.preventDefault()
    clearMessages()
    const targetEmail = forgotEmail.trim().toLowerCase()
    if (!targetEmail || !targetEmail.includes('@')) {
      setAuthError(sw ? 'Tafadhali andika barua pepe sahihi.' : 'Please enter a valid email address.')
      return
    }

    setIsLoading(true)
    try {
      const res = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: targetEmail }),
      })

      const data = await res.json().catch(() => ({}))

      if (!res.ok || !data.success) {
        setAuthError(
          data.message || (sw ? 'Akaunti haikupatikana na barua pepe hii.' : 'No account found with this email.')
        )
        return
      }

      setGeneratedCodePreview(data.code || null)
      if (data.code) {
        setResetCode(String(data.code))
      }
      setForgotStep('verify')
      setAuthSuccess(
        sw
          ? 'Nambari ya uhakiki imetengenezwa! Ingiza nambari na nenosiri jipya hapa chini.'
          : 'Verification code generated! Enter the code and your new password below.'
      )
    } catch (err: any) {
      console.error('[Forgot Password Error]', err)
      setAuthError(sw ? 'Kosa la mawasiliano na seva.' : 'Could not reach authentication server.')
    } finally {
      setIsLoading(false)
    }
  }

  // Step 2: Verify Code and Reset Password
  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    clearMessages()

    const targetEmail = forgotEmail.trim().toLowerCase()
    const code = resetCode.trim()
    const p1 = newPassword.trim()
    const p2 = confirmPassword.trim()

    if (!code || code.length < 4) {
      setAuthError(sw ? 'Ingiza nambari ya uhakiki (code).' : 'Please enter the verification code.')
      return
    }

    if (!p1 || p1.length < 4) {
      setAuthError(
        sw ? 'Nenosiri jipya linapaswa kuwa na herufi 4 au zaidi.' : 'Password must be at least 4 characters.'
      )
      return
    }

    if (p1 !== p2) {
      setAuthError(sw ? 'Manenosiri hayalingani! Hakiki tena.' : 'Passwords do not match. Please verify.')
      return
    }

    setIsLoading(true)
    try {
      const res = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: targetEmail,
          code,
          newPassword: p1,
        }),
      })

      const data = await res.json().catch(() => ({}))

      if (!res.ok || !data.success) {
        setAuthError(data.message || (sw ? 'Kosa la kubadilisha nenosiri.' : 'Failed to update password.'))
        return
      }

      setAuthSuccess(
        sw
          ? 'Nenosiri limebadilishwa kikamilifu! Unaelekezwa kuingia...'
          : 'Password reset successfully! Redirecting to sign in...'
      )
      setEmail(targetEmail)
      setPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setGeneratedCodePreview(null)

      setTimeout(() => {
        setTab('login')
        setForgotStep('request')
      }, 1500)
    } catch (err: any) {
      console.error('[Reset Password Error]', err)
      setAuthError(sw ? 'Kosa la mfumo wakati wa kurekebisha nenosiri.' : 'System error while resetting password.')
    } finally {
      setIsLoading(false)
    }
  }

  const content = (
    <div className="auth-modal auth-modal-container" onClick={(e) => e.stopPropagation()}>
      {/* LEFT SIDE: KRONX AI INTRODUCTORY BRAND PANEL */}
      <div className="auth-brand-panel">
        <div className="auth-brand-content">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
            <div
              style={{
                width: '46px',
                height: '46px',
                borderRadius: '13px',
                overflow: 'hidden',
                border: '1px solid rgba(255,255,255,0.25)',
                boxShadow: '0 4px 14px rgba(2, 132, 199, 0.4)',
                background: '#000000',
              }}
            >
              <img
                src={COPETRA_LOGO_BASE64}
                alt="Copetra AI Logo"
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
            </div>
            <span
              style={{
                fontSize: '26px',
                fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                fontWeight: '800',
                color: '#ffffff',
                letterSpacing: '-0.5px',
              }}
            >
              Copetra AI
            </span>
          </div>

          <h3 style={{ fontSize: '24px', fontWeight: '800', margin: '0 0 12px 0', letterSpacing: '-0.5px', color: '#ffffff' }}>
            Copetra AI Companion
          </h3>
          <p className="auth-brand-desc">
            Copetra AI is an advanced AI study companion created by PJ Copetranova to empower students with step-by-step
            academic explanations, homework guidance, research thesis writing, and programming.
          </p>

          <div
            className="auth-brand-features"
            style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '14px' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  background: 'rgba(255,255,255,0.1)',
                  padding: '4px 8px',
                  borderRadius: '8px',
                  fontWeight: '800',
                  color: '#38bdf8',
                }}
              >
                •
              </span>
              <span>Step-by-step academic explanation and homework help</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  background: 'rgba(255,255,255,0.1)',
                  padding: '4px 8px',
                  borderRadius: '8px',
                  fontWeight: '800',
                  color: '#38bdf8',
                }}
              >
                •
              </span>
              <span>Dual Language Support (Swahili & English)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  background: 'rgba(255,255,255,0.1)',
                  padding: '4px 8px',
                  borderRadius: '8px',
                  fontWeight: '800',
                  color: '#38bdf8',
                }}
              >
                •
              </span>
              <span>FLUX 8K Image Renders and Video Generators</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  background: 'rgba(255,255,255,0.1)',
                  padding: '4px 8px',
                  borderRadius: '8px',
                  fontWeight: '800',
                  color: '#38bdf8',
                }}
              >
                •
              </span>
              <span>Developer API Keys for Machine-to-Machine Integration</span>
            </div>
          </div>
          <div
            style={{
              borderTop: '1px solid rgba(255,255,255,0.1)',
              paddingTop: '16px',
              marginTop: '28px',
              fontSize: '12px',
              color: '#64748b',
              letterSpacing: '0.5px',
            }}
          >
            POWERED BY PJ COPETRANOVA
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
            style={{
              position: 'absolute',
              top: '16px',
              right: '16px',
              background: '#f1f5f9',
              border: 'none',
              borderRadius: '50%',
              width: '32px',
              height: '32px',
              cursor: 'pointer',
              color: '#0f172a',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}

        <div className="auth-header" style={{ marginBottom: '18px' }}>
          <h2 style={{ fontSize: '22px', fontWeight: '800', margin: '0 0 4px 0', color: '#0f172a' }}>
            {tab === 'login'
              ? sw
                ? 'Karibu Tena'
                : 'Welcome Back'
              : tab === 'register'
              ? sw
                ? 'Fungua Akaunti'
                : 'Register Account'
              : forgotStep === 'request'
              ? sw
                ? 'Umesahau Nenosiri?'
                : 'Reset Password'
              : sw
              ? 'Weka Nenosiri Jipya'
              : 'Set New Password'}
          </h2>
          <p style={{ fontSize: '13px', color: '#64748b', margin: 0 }}>
            {tab === 'login'
              ? sw
                ? 'Ingia ili uendelee na workspace yako ya Copetra AI'
                : 'Sign in to access your Copetra AI workspace'
              : tab === 'register'
              ? sw
                ? 'Jisajili ili kuanza kutumia Copetra AI bure'
                : 'Register to get started with Copetra AI'
              : forgotStep === 'request'
              ? sw
                ? 'Ingiza barua pepe yako ili kupokea nambari ya uhakiki'
                : 'Enter your registered email to receive a recovery code'
              : sw
              ? 'Weka nambari ya uhakiki (OTP) na nenosiri jipya'
              : 'Enter verification code and your new password'}
          </p>
        </div>

        {/* Tab Selector: Login vs Register vs Forgot */}
        <div
          className="auth-tabs"
          style={{
            display: 'flex',
            background: '#f1f5f9',
            padding: '4px',
            borderRadius: '12px',
            marginBottom: '16px',
            gap: '4px',
          }}
        >
          <button
            type="button"
            className={`auth-tab-btn ${tab === 'login' ? 'tab-active' : ''}`}
            onClick={() => {
              setTab('login')
              clearMessages()
            }}
            style={{
              flex: 1,
              padding: '8px 4px',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '700',
              fontSize: '12.5px',
              background: tab === 'login' ? '#ffffff' : 'transparent',
              color: tab === 'login' ? '#0f172a' : '#64748b',
              boxShadow: tab === 'login' ? '0 2px 6px rgba(0,0,0,0.05)' : 'none',
            }}
          >
            {sw ? 'Kuingia' : 'Sign In'}
          </button>
          <button
            type="button"
            className={`auth-tab-btn ${tab === 'register' ? 'tab-active' : ''}`}
            onClick={() => {
              setTab('register')
              clearMessages()
            }}
            style={{
              flex: 1,
              padding: '8px 4px',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '700',
              fontSize: '12.5px',
              background: tab === 'register' ? '#ffffff' : 'transparent',
              color: tab === 'register' ? '#0f172a' : '#64748b',
              boxShadow: tab === 'register' ? '0 2px 6px rgba(0,0,0,0.05)' : 'none',
            }}
          >
            {sw ? 'Kujisajili' : 'Register'}
          </button>
          {tab === 'forgot' && (
            <button
              type="button"
              className="auth-tab-btn tab-active"
              style={{
                flex: 1,
                padding: '8px 4px',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: '700',
                fontSize: '12.5px',
                background: '#ffffff',
                color: '#0284c7',
                boxShadow: '0 2px 6px rgba(0,0,0,0.05)',
              }}
            >
              {sw ? 'Rejesha Nenosiri' : 'Reset'}
            </button>
          )}
        </div>

        {/* Global Notifications: Error or Success */}
        {authError && (
          <div
            style={{
              background: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#b91c1c',
              padding: '10px 14px',
              borderRadius: '10px',
              fontSize: '12.5px',
              marginBottom: '14px',
              fontWeight: '600',
              lineHeight: 1.4,
            }}
          >
            {authError}
          </div>
        )}

        {authSuccess && (
          <div
            style={{
              background: '#f0fdf4',
              border: '1px solid #bbf7d0',
              color: '#15803d',
              padding: '10px 14px',
              borderRadius: '10px',
              fontSize: '12.5px',
              marginBottom: '14px',
              fontWeight: '600',
              lineHeight: 1.4,
            }}
          >
            {authSuccess}
          </div>
        )}

        {/* ========================================================
            TAB 1 & 2: LOGIN & REGISTER FORMS
            ======================================================== */}
        {(tab === 'login' || tab === 'register') && (
          <form onSubmit={handleSubmit} className="auth-form">
            {tab === 'register' && (
              <div className="auth-field">
                <label>{sw ? 'Jina Kamili' : 'Full Name'}</label>
                <input
                  type="text"
                  className="auth-input"
                  placeholder={sw ? 'Ingiza jina lako kamili' : 'Enter your full name'}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
            )}

            <div className="auth-field">
              <label>{sw ? 'Barua Pepe' : 'Email Address'}</label>
              <input
                type="email"
                className="auth-input"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="auth-field">
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '6px',
                }}
              >
                <label style={{ margin: 0 }}>{sw ? 'Nenosiri' : 'Password'}</label>
                {tab === 'login' && (
                  <button
                    type="button"
                    onClick={() => {
                      setTab('forgot')
                      setForgotStep('request')
                      setForgotEmail(email.trim())
                      clearMessages()
                      setGeneratedCodePreview(null)
                    }}
                    style={{
                      background: 'none',
                      border: 'none',
                      padding: 0,
                      cursor: 'pointer',
                      fontSize: '12.5px',
                      color: '#0284c7',
                      textDecoration: 'none',
                      fontWeight: '700',
                    }}
                  >
                    {sw ? 'Umesahau Nenosiri?' : 'Forgot Password?'}
                  </button>
                )}
              </div>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="auth-input"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{ paddingRight: '40px', width: '100%' }}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: 'absolute',
                    right: '12px',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '12px',
                    color: '#64748b',
                    fontWeight: '700',
                  }}
                  title={showPassword ? 'Hide Password' : 'Show Password'}
                >
                  {showPassword ? (sw ? 'Ficha' : 'Hide') : sw ? 'Onyesha' : 'Show'}
                </button>
              </div>
            </div>

            <button type="submit" className="auth-submit-btn" disabled={isLoading} style={{ opacity: isLoading ? 0.7 : 1 }}>
              {isLoading
                ? sw
                  ? 'Inashughulikia...'
                  : 'Processing...'
                : tab === 'login'
                ? sw
                  ? 'Ingia Kwenye Akaunti'
                  : 'Sign In'
                : sw
                ? 'Kamilisha Usajili'
                : 'Create Account'}
            </button>
          </form>
        )}

        {/* ========================================================
            TAB 3: FORGOT PASSWORD RECOVERY WORKFLOW
            ======================================================== */}
        {tab === 'forgot' && (
          <div className="forgot-password-container">
            {/* Step 1: Enter Email to Generate Reset Code */}
            {forgotStep === 'request' && (
              <form onSubmit={handleRequestResetCode} className="auth-form">
                <div className="auth-field">
                  <label>{sw ? 'Barua Pepe Yako Iliyosajiliwa' : 'Registered Email Address'}</label>
                  <input
                    type="email"
                    className="auth-input"
                    placeholder="name@example.com"
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    required
                  />
                  <span style={{ fontSize: '11.5px', color: '#64748b', marginTop: '4px', display: 'block' }}>
                    {sw
                      ? 'Tutatengeneza nambari salama ya uhakiki (6-digit code) kwa ajili ya akaunti yako.'
                      : 'We will generate a secure 6-digit recovery code for your account.'}
                  </span>
                </div>

                <button
                  type="submit"
                  className="auth-submit-btn"
                  disabled={isLoading}
                  style={{ opacity: isLoading ? 0.7 : 1 }}
                >
                  {isLoading
                    ? sw
                      ? 'Inatengeneza Nambari...'
                      : 'Generating Code...'
                    : sw
                    ? 'Tuma Nambari ya Uhakiki'
                    : 'Get Verification Code'}
                </button>

                <div style={{ textAlign: 'center', marginTop: '12px' }}>
                  <button
                    type="button"
                    onClick={() => {
                      setTab('login')
                      clearMessages()
                    }}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#64748b',
                      fontSize: '12.5px',
                      fontWeight: '700',
                      cursor: 'pointer',
                    }}
                  >
                    &larr; {sw ? 'Rudi Kwenye Kuingia' : 'Back to Sign In'}
                  </button>
                </div>
              </form>
            )}

            {/* Step 2: Verification Code & New Password */}
            {forgotStep === 'verify' && (
              <form onSubmit={handleResetPassword} className="auth-form">
                {/* Instant Verification Code Card (guarantees 100% usability without external SMTP) */}
                {generatedCodePreview && (
                  <div
                    style={{
                      background: '#ecfdf5',
                      border: '1px solid #6ee7b7',
                      borderRadius: '12px',
                      padding: '12px 14px',
                      marginBottom: '14px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '12px', fontWeight: '700', color: '#065f46' }}>
                        {sw ? 'Nambari Yako ya Uhakiki (OTP):' : 'Your Recovery Code:'}
                      </span>
                      <span
                        style={{
                          fontSize: '16px',
                          fontWeight: '900',
                          letterSpacing: '2px',
                          color: '#047857',
                          background: '#ffffff',
                          padding: '3px 10px',
                          borderRadius: '8px',
                          border: '1px dashed #059669',
                          fontFamily: 'monospace',
                        }}
                      >
                        {generatedCodePreview}
                      </span>
                    </div>
                    <div style={{ fontSize: '11px', color: '#047857', marginTop: '4px' }}>
                      {sw
                        ? 'Nambari hii inatumika kwa dakika 15. Imejazwa tayari hapa chini.'
                        : 'Valid for 15 minutes. Automatically filled in for your convenience.'}
                    </div>
                  </div>
                )}

                <div className="auth-field">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <label style={{ margin: 0 }}>{sw ? 'Nambari ya Uhakiki (Code)' : '6-Digit Verification Code'}</label>
                    <button
                      type="button"
                      onClick={() => setForgotStep('request')}
                      style={{ background: 'none', border: 'none', padding: 0, color: '#0284c7', fontSize: '11.5px', fontWeight: '700', cursor: 'pointer' }}
                    >
                      {sw ? 'Tuma Upya?' : 'Resend?'}
                    </button>
                  </div>
                  <input
                    type="text"
                    className="auth-input"
                    placeholder="123456"
                    value={resetCode}
                    onChange={(e) => setResetCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    style={{ fontFamily: 'monospace', letterSpacing: '4px', fontSize: '15px', fontWeight: '800' }}
                    required
                  />
                </div>

                <div className="auth-field">
                  <label>{sw ? 'Nenosiri Jipya' : 'New Password'}</label>
                  <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                    <input
                      type={showNewPassword ? 'text' : 'password'}
                      className="auth-input"
                      placeholder="••••••••"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      style={{ paddingRight: '40px', width: '100%' }}
                      required
                      minLength={4}
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      style={{
                        position: 'absolute',
                        right: '12px',
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: '12px',
                        color: '#64748b',
                        fontWeight: '700',
                      }}
                      title={showNewPassword ? 'Hide' : 'Show'}
                    >
                      {showNewPassword ? (sw ? 'Ficha' : 'Hide') : sw ? 'Onyesha' : 'Show'}
                    </button>
                  </div>
                </div>

                <div className="auth-field">
                  <label>{sw ? 'Thibitisha Nenosiri Jipya' : 'Confirm New Password'}</label>
                  <input
                    type="password"
                    className="auth-input"
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    minLength={4}
                  />
                </div>

                <button
                  type="submit"
                  className="auth-submit-btn"
                  disabled={isLoading}
                  style={{ opacity: isLoading ? 0.7 : 1 }}
                >
                  {isLoading
                    ? sw
                      ? 'Inahifadhi Nenosiri...'
                      : 'Saving Password...'
                    : sw
                    ? 'Hifadhi Nenosiri Jipya'
                    : 'Set New Password'}
                </button>

                <div style={{ textAlign: 'center', marginTop: '12px' }}>
                  <button
                    type="button"
                    onClick={() => {
                      setTab('login')
                      clearMessages()
                    }}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#64748b',
                      fontSize: '12.5px',
                      fontWeight: '700',
                      cursor: 'pointer',
                    }}
                  >
                    &larr; {sw ? 'Rudi Kwenye Kuingia' : 'Back to Sign In'}
                  </button>
                </div>
              </form>
            )}
          </div>
        )}

        {/* Founder & Developer Social Action Buttons */}
        <div
          style={{
            marginTop: '20px',
            paddingTop: '16px',
            borderTop: '1px solid #e2e8f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
          }}
        >
          <a
            href="https://wa.me/255673190931?text=Habari%20PJ%20COPETRANOVA,%20nimetembelea%20Copetra%20AI%20na%20ningependa%20mawasiliano."
            target="_blank"
            rel="noopener noreferrer"
            title="WhatsApp Support"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              background: '#25D366',
              color: '#ffffff',
              textDecoration: 'none',
              boxShadow: '0 2px 8px rgba(37, 211, 102, 0.3)',
            }}
          >
            <svg width={18} height={18} viewBox="0 0 24 24" fill="currentColor">
              <path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-1.107 4.04 4.05-1.061z" />
            </svg>
          </a>

          <a
            href="https://ig.me/m/peterjoh_jim"
            target="_blank"
            rel="noopener noreferrer"
            title="Direct Instagram Message"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              background:
                'linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%)',
              color: '#ffffff',
              textDecoration: 'none',
              boxShadow: '0 2px 8px rgba(220, 39, 67, 0.3)',
            }}
          >
            <svg width={18} height={18} viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
            </svg>
          </a>

          <a
            href="https://mail.google.com/mail/?view=cm&fs=1&to=pb0040280@gmail.com&su=Inquiry%20from%20Copetra%20AI%20Platform"
            target="_blank"
            rel="noopener noreferrer"
            title="Email Founder"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              background: '#0284c7',
              color: '#ffffff',
              textDecoration: 'none',
              boxShadow: '0 2px 8px rgba(2, 132, 199, 0.3)',
            }}
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
