'use client'

import { useKronxStore } from '@/store/useKronxStore'

interface Props {
  onStart: () => void
}

export default function LandingPage({ onStart }: Props) {
  const { setAuthModalOpen } = useKronxStore()

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
          <span className="landing-logo-title">PJKRONX AI</span>
        </div>

        <div className="landing-nav-right" style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button
            className="landing-sign-btn"
            onClick={() => setAuthModalOpen(true)}
            style={{
              padding: '10px 22px',
              borderRadius: '20px',
              background: '#0f172a',
              color: '#ffffff',
              border: '1px solid #334155',
              fontWeight: '800',
              fontSize: '14px',
              cursor: 'pointer',
              boxShadow: '0 4px 14px rgba(15, 23, 42, 0.3)',
              transition: 'transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), background-color 0.2s'
            }}
          >
            Sign In / Register
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="landing-hero">
        <div className="hero-badge">
          <span className="badge-glow" />
          <span>Next-Gen Academic AI Companion</span>
        </div>

        <h1 className="hero-title">
          Your Intelligent AI Companion<br />
          <span className="text-gradient">Fast, Empathetic & Academic-First</span>
        </h1>

        <p className="hero-sub">
          PJKRONX AI empowers your education, daily assignments, research thesis, and creative image rendering with real-time intelligence — engineered by PJ COPETRANOVA.
        </p>

        {/* Hero Image Showcase */}
        <div style={{ margin: '24px 0', width: '100%', maxWidth: '840px', borderRadius: '24px', overflow: 'hidden', border: '1px solid #334155', boxShadow: '0 20px 50px rgba(0, 0, 0, 0.3)' }}>
          <img
            src="/hero_banner.jpg"
            alt="PJKRONX AI Companion Interface Showcase"
            style={{ width: '100%', height: 'auto', display: 'block', objectFit: 'cover' }}
          />
        </div>

        <div className="hero-actions" style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', justifyContent: 'center' }}>
          <button
            className="hero-primary-btn"
            onClick={onStart}
            style={{
              padding: '14px 32px',
              borderRadius: '24px',
              background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
              color: '#ffffff',
              fontWeight: '800',
              fontSize: '15px',
              border: 'none',
              cursor: 'pointer',
              boxShadow: '0 8px 24px rgba(37, 99, 235, 0.4)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '10px',
              transition: 'transform 0.2s cubic-bezier(0.16, 1, 0.3, 1)'
            }}
          >
            <span>Launch PJKRONX AI Now</span>
            <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>

          <button
            className="hero-secondary-btn"
            onClick={() => setAuthModalOpen(true)}
            style={{
              padding: '14px 28px',
              borderRadius: '24px',
              background: '#ffffff',
              color: '#0f172a',
              fontWeight: '800',
              fontSize: '15px',
              border: '1px solid #e2e8f0',
              cursor: 'pointer',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.08)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '10px',
              transition: 'transform 0.2s cubic-bezier(0.16, 1, 0.3, 1)'
            }}
          >
            <svg width={18} height={18} viewBox="0 0 24 24">
              <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z" />
              <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.11-6.72-4.96H1.27v3.15C3.25 21.3 7.31 24 12 24z" />
              <path fill="#FBBC05" d="M5.28 14.24c-.25-.72-.38-1.49-.38-2.24s.13-1.52.38-2.24V6.61H1.27C.46 8.23 0 10.06 0 12s.46 3.77 1.27 5.39l4.01-3.15z" />
              <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.25 2.7 1.27 6.61l4.01 3.15c.95-2.85 3.6-4.96 6.72-4.96z" />
            </svg>
            <span>Sign in to Account</span>
          </button>
        </div>
      </section>

      {/* Feature Showcase Grid */}
      <section className="landing-features">
        <h2 className="section-heading">
          Why Choose PJKRONX AI?
        </h2>

        <div className="features-grid">
          <div className="feat-card">
            <div className="feat-icon-box">⚡</div>
            <h3>Low-RAM Optimization</h3>
            <p>Runs seamlessly on 350MB-500MB RAM using single-model auto-detection for maximum speed.</p>
          </div>

          <div className="feat-card">
            <div className="feat-icon-box">🎙️</div>
            <h3>Speech Recognition & Playback</h3>
            <p>Full Speech-to-Text listening & Text-to-Speech playback in Kiswahili and English.</p>
          </div>

          <div className="feat-card">
            <div className="feat-icon-box">🧠</div>
            <h3>Personal Memory Vault</h3>
            <p>Intelligent vector memory vault stores personal facts and past business context.</p>
          </div>

          <div className="feat-card">
            <div className="feat-icon-box">📊</div>
            <h3>Glassmorphic Analytics Dashboard</h3>
            <p>Sleek dark obsidian dashboard tracking system telemetry, goals, and facts.</p>
          </div>
        </div>
      </section>

      {/* Developer & Founder Social Links - Secure SVG Action Buttons */}
      <section style={{ textAlign: 'center', padding: '32px 16px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '24px', margin: '36px auto 0 auto', maxWidth: '680px', border: '1px solid #334155' }}>
        <div style={{ fontSize: '13px', color: '#94a3b8', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '12px' }}>
          Engineered by PJ COPETRANOVA
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '16px', flexWrap: 'wrap' }}>
          {/* WhatsApp Direct Action Button */}
          <a
            href="https://wa.me/255673190931?text=Habari%20PJ%20COPETRANOVA,%20nimetembelea%20PJKRONX%20AI%20na%20ningependa%20mawasiliano."
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 20px',
              borderRadius: '20px',
              background: '#25D366',
              color: '#ffffff',
              fontWeight: '700',
              fontSize: '14px',
              textDecoration: 'none',
              boxShadow: '0 4px 14px rgba(37, 211, 102, 0.3)',
              transition: 'transform 0.2s ease'
            }}
          >
            <svg width={20} height={20} viewBox="0 0 24 24" fill="currentColor">
              <path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-1.107 4.04 4.05-1.061z"/>
            </svg>
            <span>WhatsApp Support</span>
          </a>

          {/* Instagram Direct Messaging Action Button */}
          <a
            href="https://ig.me/m/peterjoh_jim"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 20px',
              borderRadius: '20px',
              background: 'linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%)',
              color: '#ffffff',
              fontWeight: '700',
              fontSize: '14px',
              textDecoration: 'none',
              boxShadow: '0 4px 14px rgba(220, 39, 67, 0.3)',
              transition: 'transform 0.2s ease'
            }}
          >
            <svg width={20} height={20} viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
            </svg>
            <span>Direct Instagram Message</span>
          </a>

          {/* Email Founder Direct Action Button (Gmail Webmail & Native Mail) */}
          <a
            href="https://mail.google.com/mail/?view=cm&fs=1&to=pb0040280@gmail.com&su=Inquiry%20from%20PJKRONX%20AI%20Platform"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 20px',
              borderRadius: '20px',
              background: '#0284c7',
              color: '#ffffff',
              fontWeight: '700',
              fontSize: '14px',
              textDecoration: 'none',
              boxShadow: '0 4px 14px rgba(2, 132, 199, 0.3)',
              transition: 'transform 0.2s ease'
            }}
          >
            <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
              <polyline points="22,6 12,13 2,6" />
            </svg>
            <span>Email Founder</span>
          </a>
        </div>
      </section>

      {/* Landing Footer */}
      <footer className="landing-footer">
        <p>© 2026 PJKRONX AI Companion by PJ COPETRANOVA. All rights reserved.</p>
      </footer>
    </div>
  )
}
