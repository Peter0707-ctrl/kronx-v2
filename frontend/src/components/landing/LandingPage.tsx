'use client'

import { useKronxStore } from '@/store/useKronxStore'

interface Props {
  onStart: () => void
}

export default function LandingPage({ onStart }: Props) {
  const { language, setLanguage, setAuthModalOpen } = useKronxStore()
  const sw = language === 'sw'

  return (
    <div className="landing-container">
      {/* Landing Navbar */}
      <header className="landing-nav">
        <div className="landing-logo">
          <div className="landing-logo-gem">
            <svg viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={2} width={22} height={22}>
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <span className="landing-logo-title">Kronx AI</span>
        </div>

        <div className="landing-nav-right">
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

          <button className="landing-sign-btn" onClick={() => setAuthModalOpen(true)}>
            {sw ? 'Ingia / Jisajili' : 'Sign In / Register'}
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="landing-hero">
        <div className="hero-badge">
          <span className="badge-glow" />
          <span>{sw ? 'Akili Bandia ya Kizazi Kipya' : 'Next-Gen AI Companion for East Africa'}</span>
        </div>

        <h1 className="hero-title">
          {sw ? (
            <>Mshauri Wako wa Akili Bandia<br /><span className="text-gradient">Yenye Haraka & Kinga ya RAM</span></>
          ) : (
            <>Your Intelligent AI Companion<br /><span className="text-gradient">Fast, Empathetic & RAM-Optimized</span></>
          )}
        </h1>

        <p className="hero-sub">
          {sw
            ? 'Kronx anakusaidia kujifunza, kukuza biashara yako, na kuweka akiba kwa lugha ya Kiswahili na Kiingereza — bila kumaliza RAM ya kompyuta yako.'
            : 'Kronx empowers your business, education, and daily life with real-time Swahili and English intelligence — running on zero memory overhead.'}
        </p>

        <div className="hero-actions">
          <button className="hero-primary-btn" onClick={onStart}>
            <span>{sw ? 'Anza Kutumia Kronx Libre' : 'Launch Kron-X Now'}</span>
            <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>

          <button className="hero-secondary-btn" onClick={() => setAuthModalOpen(true)}>
            <svg width={18} height={18} viewBox="0 0 24 24">
              <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z" />
              <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.11-6.72-4.96H1.27v3.15C3.25 21.3 7.31 24 12 24z" />
              <path fill="#FBBC05" d="M5.28 14.24c-.25-.72-.38-1.49-.38-2.24s.13-1.52.38-2.24V6.61H1.27C.46 8.23 0 10.06 0 12s.46 3.77 1.27 5.39l4.01-3.15z" />
              <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.25 2.7 1.27 6.61l4.01 3.15c.95-2.85 3.6-4.96 6.72-4.96z" />
            </svg>
            <span>{sw ? 'Ingia na Google' : 'Sign in with Google'}</span>
          </button>
        </div>
      </section>

      {/* Feature Showcase Grid */}
      <section className="landing-features">
        <h2 className="section-heading">
          {sw ? 'Kwanini Kronx ni Tofauti?' : 'Why Choose Kronx AI?'}
        </h2>

        <div className="features-grid">
          <div className="feat-card">
            <div className="feat-icon-box">⚡</div>
            <h3>{sw ? 'Matumizi Madogo ya RAM' : 'Low-RAM Optimization'}</h3>
            <p>{sw ? 'Mfumo umewekewa vikwazo safi vya memory (350MB-500MB RAM pekee) ili kompyuta yako ibaki na kasi.' : 'Runs seamlessly on 350MB-500MB RAM using single-model auto-detection.'}</p>
          </div>

          <div className="feat-card">
            <div className="feat-icon-box">🎙️</div>
            <h3>{sw ? 'Sauti kwa Kiswahili & Kiingereza' : 'Speech Recognition & Playback'}</h3>
            <p>{sw ? 'Sikiliza majibu kwa sauti na tumia mic kuongea kwa Kiswahili (sw-TZ) au Kiingereza (en-US).' : 'Full Speech-to-Text listening & Text-to-Speech playback in Kiswahili and English.'}</p>
          </div>

          <div className="feat-card">
            <div className="feat-icon-box">🧠</div>
            <h3>{sw ? 'Kumbukumbu ya Kipekee (Memory Vault)' : 'Personal Memory Vault'}</h3>
            <p>{sw ? 'Kronx anakumbuka maelezo yako ya biashara, malengo, na bajeti zako za zamani ili kutoa ushauri bora.' : 'Intelligent vector memory vault stores personal facts and past business context.'}</p>
          </div>

          <div className="feat-card">
            <div className="feat-icon-box">📊</div>
            <h3>{sw ? 'Dashboard ya Glassmorphic' : 'Glassmorphic Analytics Dashboard'}</h3>
            <p>{sw ? 'Tathmini utendaji wa mfumo, malengo yako ya biashara, na takwimu za kumbukumbu kwa urahisi.' : 'Sleek dark obsidian dashboard tracking system telemetry, goals, and facts.'}</p>
          </div>
        </div>
      </section>

      {/* Landing Footer */}
      <footer className="landing-footer">
        <p>© 2026 Kron-X AI Companion. Crafted for Tanzania & East Africa.</p>
      </footer>
    </div>
  )
}
