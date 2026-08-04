'use client'

import { useState, useRef, useEffect } from 'react'
import { useKronxStore } from '@/store/useKronxStore'

// Payment provider logos (SVG inline for zero dependency)
const MpesaLogo = () => (
  <svg width="52" height="28" viewBox="0 0 120 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="120" height="48" rx="8" fill="#009B3A"/>
    <text x="60" y="31" textAnchor="middle" fill="white" fontSize="16" fontWeight="800" fontFamily="Arial">M-PESA</text>
  </svg>
)

const TigoLogo = () => (
  <svg width="52" height="28" viewBox="0 0 120 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="120" height="48" rx="8" fill="#0050FF"/>
    <text x="60" y="31" textAnchor="middle" fill="white" fontSize="17" fontWeight="800" fontFamily="Arial">TIGO</text>
  </svg>
)

const AirtelLogo = () => (
  <svg width="52" height="28" viewBox="0 0 120 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="120" height="48" rx="8" fill="#ED1C24"/>
    <text x="60" y="31" textAnchor="middle" fill="white" fontSize="14" fontWeight="800" fontFamily="Arial">AIRTEL</text>
  </svg>
)

const HalotelLogo = () => (
  <svg width="52" height="28" viewBox="0 0 120 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="120" height="48" rx="8" fill="#F7941D"/>
    <text x="60" y="31" textAnchor="middle" fill="white" fontSize="13" fontWeight="800" fontFamily="Arial">HALOTEL</text>
  </svg>
)

const VisaLogo = () => (
  <svg width="52" height="28" viewBox="0 0 120 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="120" height="48" rx="8" fill="#1A1F71"/>
    <text x="60" y="31" textAnchor="middle" fill="#F7B600" fontSize="18" fontWeight="900" fontFamily="Arial Narrow, Arial">VISA</text>
  </svg>
)

const MastercardLogo = () => (
  <svg width="52" height="28" viewBox="0 0 120 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect width="120" height="48" rx="8" fill="#252525"/>
    <circle cx="44" cy="24" r="16" fill="#EB001B"/>
    <circle cx="76" cy="24" r="16" fill="#F79E1B"/>
    <path d="M60 13.8a16 16 0 0 1 0 20.4A16 16 0 0 1 60 13.8z" fill="#FF5F00"/>
  </svg>
)

const WhatsAppIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="white" xmlns="http://www.w3.org/2000/svg">
    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>
    <path d="M12 0C5.373 0 0 5.373 0 12c0 2.126.555 4.121 1.527 5.854L0 24l6.338-1.501A11.934 11.934 0 0 0 12 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.818a9.793 9.793 0 0 1-5.028-1.385l-.36-.214-3.761.891.951-3.665-.235-.376A9.818 9.818 0 0 1 2.182 12C2.182 6.57 6.57 2.182 12 2.182S21.818 6.57 21.818 12 17.43 21.818 12 21.818z"/>
  </svg>
)

const CheckIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
)

export default function SettingsModal() {
  const {
    settingsModalOpen,
    setSettingsModalOpen,
    user,
    logoutUser,
    language,
    updateUserAvatar,
  } = useKronxStore()

  const fileInputRef = useRef<HTMLInputElement>(null)
  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onloadend = () => {
        if (typeof reader.result === 'string') {
          updateUserAvatar(reader.result)
        }
      }
      reader.readAsDataURL(file)
    }
  }

  const [activeTab, setActiveTab] = useState<'menu'|'upgrade'|'account'|'support'|'developer'>('menu')
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly')
  const [selectedPlan, setSelectedPlan] = useState<'plus' | 'pro'>('plus')

  const [notificationStatus, setNotificationStatus] = useState<string>('default')

  useEffect(() => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      setNotificationStatus(Notification.permission)
    }
  }, [])

  const handleRequestNotificationPermission = async () => {
    if (typeof window === 'undefined') return
    if (!('Notification' in window)) {
      alert(language === 'sw' ? 'Kifaa chako hakiauni arifa.' : 'Notifications are not supported on this device.')
      return
    }
    try {
      const permission = await Notification.requestPermission()
      setNotificationStatus(permission)
      if (permission === 'granted') {
        alert(language === 'sw' ? 'Arifa zimeamilishwa kikamilifu! 🎉' : 'Notifications enabled successfully! 🎉')
      } else {
        alert(language === 'sw' ? 'Ruhusa ya arifa imekataliwa. Tafadhali ruhusu kwenye mipangilio ya kivinjari chako.' : 'Notification permission was denied. Please allow notifications in browser settings.')
      }
    } catch (err) {
      console.error(err)
    }
  }
  const [contactSent, setContactSent] = useState(false)
  const [feedbackType, setFeedbackType] = useState<'bug' | 'feature' | 'other'>('feature')
  const [feedbackText, setFeedbackText] = useState('')

  if (!settingsModalOpen) return null

  const isPremium = user?.plan === 'premium'
  const picUsed = user?.picturesUsedToday || 0
  const vidUsed = user?.videosUsedToday || 0
  const sw = language === 'sw'

  const plans = {
    plus: {
      name: 'Copetra Plus',
      monthly: 15000,
      yearly: 12000,
      features: [
        sw ? 'Kipaumbele cha jibu la AI' : 'Priority AI response speed',
        sw ? 'Picha 10 kwa siku' : '10 AI images per day',
        sw ? 'Video 3 kwa siku' : '3 AI videos per day',
        sw ? 'Msaada wa haraka' : 'Priority customer support',
        sw ? 'Kumbukumbu ya mazungumzo' : 'Extended conversation memory',
      ]
    },
    pro: {
      name: 'Copetra Pro',
      monthly: 35000,
      yearly: 28000,
      features: [
        sw ? 'Kila kitu cha Plus' : 'Everything in Plus',
        sw ? 'Picha Zisizo na Kikomo' : 'Unlimited AI images',
        sw ? 'Video Zisizo na Kikomo' : 'Unlimited AI videos',
        sw ? 'Upatikanaji wa API' : 'API access & integration',
        sw ? 'Kipaumbele cha Kwanza cha Msaada' : 'Priority 1 support (WhatsApp)',
        sw ? 'Uchambuzi wa Kina wa Biashara' : 'Advanced business analytics',
      ]
    }
  }

  const activePlan = plans[selectedPlan]
  const price = billingCycle === 'monthly' ? activePlan.monthly : activePlan.yearly

  const handleContactAdmin = () => {
    const planLabel = selectedPlan === 'plus' ? 'Copetra Plus (15,000 TZS/month)' : 'Copetra Pro (35,000 TZS/month)'
    const text = encodeURIComponent(
      `Habari Admin! Nataka kujiandikisha kwenye:\n\n` +
      `MPANGO: ${planLabel}\n` +
      `BILI: ${billingCycle === 'monthly' ? 'Kila Mwezi' : 'Kila Mwaka'}\n` +
      `JINA: ${user?.name || 'Mtumiaji'}\n` +
      `EMAIL: ${user?.email || 'N/A'}\n\n` +
      `Tafadhali nielekeze jinsi ya kulipa na kuamilisha akaunti yangu.`
    )
    window.open(`https://wa.me/255673190931?text=${text}`, '_blank')
    setContactSent(true)
    setTimeout(() => setContactSent(false), 5000)
  }

  const handleSendFeedback = () => {
    if (!feedbackText.trim()) return
    const text = encodeURIComponent(
      `*PJKRONX Feedback / Support*\n` +
      `TYPE: ${feedbackType.toUpperCase()}\n` +
      `FROM: ${user?.name || 'User'} (${user?.email || 'N/A'})\n\n` +
      `MESSAGE:\n${feedbackText}`
    )
    window.open(`https://wa.me/255673190931?text=${text}`, '_blank')
    setFeedbackText('')
  }

  const handleLogout = () => {
    setSettingsModalOpen(false)
    logoutUser()
  }

  return (
    <div
      className="settings-modal-backdrop"
      onClick={() => setSettingsModalOpen(false)}
    >
      <div
        className="settings-modal-container"
        onClick={e => e.stopPropagation()}
      >
        <div className="settings-header">
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '12px' }}>
            {activeTab !== 'menu' && (
              <button
                onClick={() => setActiveTab('menu')}
                style={{
                  background: 'rgba(255,255,255,0.1)', border: 'none', color: '#fff',
                  width: '36px', height: '36px', borderRadius: '10px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  cursor: 'pointer', fontSize: '18px'
                }}
              >
                ←
              </button>
            )}
            <div>
              <h2 className="settings-title">
                {activeTab === 'menu' ? (sw ? 'Mipangilio' : 'Settings') :
                 activeTab === 'upgrade' ? (sw ? 'Mipango na Bei' : 'Plans & Pricing') :
                 activeTab === 'account' ? (sw ? 'Akaunti Yangu' : 'My Account') :
                 activeTab === 'support' ? (sw ? 'Andika Maoni (Review)' : 'Write a Review') :
                 activeTab === 'developer' ? 'Developer & API' : ''}
              </h2>
              <p className="settings-subtitle">
                {sw ? 'Dhibiti akaunti yako na mapendeleo' : 'Manage your account and preferences'}
              </p>
            </div>
          </div>
          <button
            className="settings-close-btn"
            onClick={() => setSettingsModalOpen(false)}
            style={{
              width: '40px', height: '40px', borderRadius: '12px',
              border: '1px solid rgba(255,255,255,0.2)',
              background: 'rgba(255,255,255,0.1)',
              color: '#ffffff', cursor: 'pointer',
              fontSize: '18px', display: 'flex', alignItems: 'center', justifyContent: 'center',
              position: 'relative', zIndex: 1
            }}
          >✕</button>
        </div>

        <div className="settings-content">
          {activeTab === 'menu' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <button
                onClick={() => setActiveTab('upgrade')}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  background: '#f8fafc', padding: '16px 20px', borderRadius: '16px',
                  border: '1px solid #e2e8f0', cursor: 'pointer', textAlign: 'left',
                  transition: 'background 0.2s', width: '100%'
                }}
                onMouseEnter={e => (e.currentTarget.style.background = '#f1f5f9')}
                onMouseLeave={e => (e.currentTarget.style.background = '#f8fafc')}
              >
                <div>
                  <div style={{ fontSize: '16px', fontWeight: '800', color: '#0f172a', marginBottom: '4px' }}>
                    {sw ? 'Mipango & Usajili' : 'Subscription Plans'}
                  </div>
                  <div style={{ fontSize: '13px', color: '#64748b' }}>
                    {sw ? 'Tazama na ununue vifurushi vya Copetra' : 'View and purchase Copetra plans'}
                  </div>
                </div>
                <div style={{ color: '#0ea5e9' }}>➔</div>
              </button>

              <button
                onClick={() => setActiveTab('account')}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  background: '#f8fafc', padding: '16px 20px', borderRadius: '16px',
                  border: '1px solid #e2e8f0', cursor: 'pointer', textAlign: 'left',
                  transition: 'background 0.2s', width: '100%'
                }}
                onMouseEnter={e => (e.currentTarget.style.background = '#f1f5f9')}
                onMouseLeave={e => (e.currentTarget.style.background = '#f8fafc')}
              >
                <div>
                  <div style={{ fontSize: '16px', fontWeight: '800', color: '#0f172a', marginBottom: '4px' }}>
                    {sw ? 'Akaunti Yangu' : 'My Account'}
                  </div>
                  <div style={{ fontSize: '13px', color: '#64748b' }}>
                    {sw ? 'Badili picha ya wasifu, toka kwenye akaunti' : 'Change profile picture, sign out'}
                  </div>
                </div>
                <div style={{ color: '#0ea5e9' }}>➔</div>
              </button>

              <button
                onClick={() => setActiveTab('support')}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  background: '#f8fafc', padding: '16px 20px', borderRadius: '16px',
                  border: '1px solid #e2e8f0', cursor: 'pointer', textAlign: 'left',
                  transition: 'background 0.2s', width: '100%'
                }}
                onMouseEnter={e => (e.currentTarget.style.background = '#f1f5f9')}
                onMouseLeave={e => (e.currentTarget.style.background = '#f8fafc')}
              >
                <div>
                  <div style={{ fontSize: '16px', fontWeight: '800', color: '#0f172a', marginBottom: '4px' }}>
                    {sw ? 'Andika Maoni (Review)' : 'Write a Review'}
                  </div>
                  <div style={{ fontSize: '13px', color: '#64748b' }}>
                    {sw ? 'Tuambie nini kiboreshwe na mapendekezo yako' : 'Tell us what should be updated or improved'}
                  </div>
                </div>
                <div style={{ color: '#0ea5e9' }}>➔</div>
              </button>

              <button
                onClick={handleRequestNotificationPermission}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  background: '#f8fafc', padding: '16px 20px', borderRadius: '16px',
                  border: '1px solid #e2e8f0', cursor: 'pointer', textAlign: 'left',
                  transition: 'background 0.2s', width: '100%'
                }}
                onMouseEnter={e => (e.currentTarget.style.background = '#f1f5f9')}
                onMouseLeave={e => (e.currentTarget.style.background = '#f8fafc')}
              >
                <div>
                  <div style={{ fontSize: '16px', fontWeight: '800', color: '#0f172a', marginBottom: '4px' }}>
                    {sw ? 'Arifa za PWA (Push)' : 'PWA Push Notifications'}
                  </div>
                  <div style={{ fontSize: '13px', color: '#64748b' }}>
                    {notificationStatus === 'granted' ? 
                      (sw ? 'Hali: Zimeamilishwa kikamilifu' : 'Status: Fully Activated') : 
                      (sw ? 'Gusa kuwasha arifa za ujumbe' : 'Tap to enable chat response notifications')}
                  </div>
                </div>
                <div style={{
                  color: notificationStatus === 'granted' ? '#22c55e' : '#0ea5e9',
                  fontWeight: 'bold', fontSize: '14px'
                }}>
                  {notificationStatus === 'granted' ? 'ON ✓' : 'OFF ➔'}
                </div>
              </button>

              {user?.isDeveloper && (
                <button
                  onClick={() => setActiveTab('developer')}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    background: '#f8fafc', padding: '16px 20px', borderRadius: '16px',
                    border: '1px solid #e2e8f0', cursor: 'pointer', textAlign: 'left',
                    transition: 'background 0.2s', width: '100%'
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = '#f1f5f9')}
                  onMouseLeave={e => (e.currentTarget.style.background = '#f8fafc')}
                >
                  <div>
                    <div style={{ fontSize: '16px', fontWeight: '800', color: '#0f172a', marginBottom: '4px' }}>
                      Developer API & Integrations
                    </div>
                    <div style={{ fontSize: '13px', color: '#64748b' }}>
                      {sw ? 'Dhibiti API key na Webhooks' : 'Manage your API keys and Webhooks'}
                    </div>
                  </div>
                  <div style={{ color: '#0ea5e9' }}>➔</div>
                </button>
              )}
            </div>
          )}

          {/* ═══════════════════════════════════════════
              TAB 1: PLANS & PRICING
          ═══════════════════════════════════════════ */}
          {activeTab === 'upgrade' && (
            <div>
              {/* Already Premium Banner */}
              {isPremium && (
                <div style={{
                  background: 'linear-gradient(135deg, #064e3b, #065f46)',
                  borderRadius: '16px', padding: '16px 20px',
                  display: 'flex', alignItems: 'center', gap: '12px',
                  marginBottom: '24px',
                }}>
                  <div style={{ fontSize: '24px' }}>✓</div>
                  <div>
                    <div style={{ color: '#6ee7b7', fontWeight: '800', fontSize: '15px' }}>
                      {sw ? 'Umeshainuliwa!' : 'You are already subscribed!'}
                    </div>
                    <div style={{ color: '#a7f3d0', fontSize: '13px', marginTop: '2px' }}>
                      {sw ? 'Mpango wako wa Copetra Plus unaendelea. Asante!' : 'Your Copetra Plus plan is active. Thank you!'}
                    </div>
                  </div>
                </div>
              )}

              {/* Billing cycle toggle */}
              {!isPremium && (
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '24px' }}>
                  <div style={{
                    display: 'inline-flex', background: '#f1f5f9',
                    borderRadius: '24px', padding: '4px', gap: '4px'
                  }}>
                    {(['monthly', 'yearly'] as const).map(cycle => (
                      <button
                        key={cycle}
                        onClick={() => setBillingCycle(cycle)}
                        style={{
                          padding: '8px 20px', borderRadius: '20px', border: 'none',
                          background: billingCycle === cycle ? '#0f172a' : 'transparent',
                          color: billingCycle === cycle ? '#ffffff' : '#64748b',
                          fontSize: '13px', fontWeight: '700', cursor: 'pointer',
                          transition: 'all 0.2s',
                          display: 'flex', alignItems: 'center', gap: '6px',
                        }}
                      >
                        {cycle === 'monthly' ? (sw ? 'Kila Mwezi' : 'Monthly') : (sw ? 'Kila Mwaka' : 'Yearly')}
                        {cycle === 'yearly' && (
                          <span style={{ background: '#10b981', color: '#fff', borderRadius: '8px', padding: '1px 6px', fontSize: '10px' }}>
                            -20%
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Plan Cards */}
              {!isPremium && (
                <div className="plans-grid">

                  {/* Free Card */}
                  <div className="plan-card free">
                    <div style={{ fontSize: '13px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '8px' }}>Free</div>
                    <div className="plan-price-badge">0 TZS</div>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '20px' }}>{sw ? 'Daima bila malipo' : 'Always free'}</div>
                    <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
                      <div className="plan-feature-item">
                        <span style={{ color: '#10b981', marginTop: '1px' }}><CheckIcon /></span>
                        <span>{sw ? 'Picha 3 kwa siku' : '3 images/day'} ({picUsed}/3 used)</span>
                      </div>
                      <div className="plan-feature-item">
                        <span style={{ color: '#10b981', marginTop: '1px' }}><CheckIcon /></span>
                        <span>{sw ? 'Video 1 kwa siku' : '1 video/day'} ({vidUsed}/1 used)</span>
                      </div>
                      <div className="plan-feature-item">
                        <span style={{ color: '#10b981', marginTop: '1px' }}><CheckIcon /></span>
                        <span>{sw ? 'Jibu la kawaida la AI' : 'Standard AI answers'}</span>
                      </div>
                    </div>
                    <button disabled style={{
                      marginTop: '20px', width: '100%', padding: '11px',
                      borderRadius: '14px', background: '#e2e8f0',
                      color: '#94a3b8', border: 'none', fontWeight: '700', fontSize: '13px'
                    }}>
                      {sw ? 'Mpango wa Sasa' : 'Current Plan'}
                    </button>
                  </div>

                  {/* Plus Card */}
                  <div
                    onClick={() => setSelectedPlan('plus')}
                    className="plan-card plus"
                    style={{
                      border: selectedPlan === 'plus' ? '2px solid #0ea5e9' : '1px solid #cbd5e1',
                      boxShadow: selectedPlan === 'plus' ? '0 12px 32px rgba(14, 165, 233, 0.12)' : 'none',
                    }}
                  >
                    <div style={{
                      position: 'absolute', top: '-11px', left: '50%', transform: 'translateX(-50%)',
                      background: '#0ea5e9', color: '#fff', fontSize: '10px', fontWeight: '800',
                      padding: '4px 14px', borderRadius: '12px', letterSpacing: '1px', whiteSpace: 'nowrap',
                    }}>
                      POPULAR
                    </div>
                    <div style={{ fontSize: '13px', fontWeight: '700', color: '#0ea5e9', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '8px' }}>Plus</div>
                    <div className="plan-price-badge">
                      {billingCycle === 'monthly' ? '15,000' : '12,000'} <span style={{ fontSize: '13px', fontWeight: '500', color: '#64748b' }}>TZS</span>
                    </div>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '20px' }}>
                      {sw ? 'kwa mwezi' : 'per month'}
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
                      {plans.plus.features.map((f, i) => (
                        <div key={i} className="plan-feature-item">
                          <span style={{ color: '#0ea5e9', marginTop: '1px' }}><CheckIcon /></span>
                          <span>{f}</span>
                        </div>
                      ))}
                    </div>
                    <div style={{
                      marginTop: '16px', padding: '10px',
                      borderRadius: '12px', textAlign: 'center',
                      background: selectedPlan === 'plus' ? '#0ea5e9' : '#f1f5f9',
                      color: selectedPlan === 'plus' ? '#fff' : '#64748b',
                      fontSize: '13px', fontWeight: '700', transition: 'all 0.2s'
                    }}>
                      {selectedPlan === 'plus' ? (sw ? 'Umechagua' : 'Selected') : (sw ? 'Chagua' : 'Select')}
                    </div>
                  </div>

                  {/* Pro Card */}
                  <div
                    onClick={() => setSelectedPlan('pro')}
                    className="plan-card pro"
                    style={{
                      border: selectedPlan === 'pro' ? '2px solid #8b5cf6' : '1px solid #cbd5e1',
                      boxShadow: selectedPlan === 'pro' ? '0 12px 32px rgba(139, 92, 246, 0.12)' : 'none',
                    }}
                  >
                    <div style={{ fontSize: '13px', fontWeight: '700', color: '#8b5cf6', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '8px' }}>Pro</div>
                    <div className="plan-price-badge">
                      {billingCycle === 'monthly' ? '35,000' : '28,000'} <span style={{ fontSize: '13px', fontWeight: '500', color: '#64748b' }}>TZS</span>
                    </div>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '20px' }}>
                      {sw ? 'kwa mwezi' : 'per month'}
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
                      {plans.pro.features.map((f, i) => (
                        <div key={i} className="plan-feature-item">
                          <span style={{ color: '#8b5cf6', marginTop: '1px' }}><CheckIcon /></span>
                          <span>{f}</span>
                        </div>
                      ))}
                    </div>
                    <div style={{
                      marginTop: '16px', padding: '10px',
                      borderRadius: '12px', textAlign: 'center',
                      background: selectedPlan === 'pro' ? '#8b5cf6' : '#f1f5f9',
                      color: selectedPlan === 'pro' ? '#fff' : '#64748b',
                      fontSize: '13px', fontWeight: '700', transition: 'all 0.2s'
                    }}>
                      {selectedPlan === 'pro' ? (sw ? 'Umechagua' : 'Selected') : (sw ? 'Chagua' : 'Select')}
                    </div>
                  </div>
                </div>
              )}

              {/* Payment Instructions + Contact Admin Box */}
              {!isPremium && (
                <div style={{
                  background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)',
                  border: '1.5px solid #bae6fd',
                  borderRadius: '20px', padding: '24px',
                  marginBottom: '24px',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                    <div style={{
                      width: '40px', height: '40px', borderRadius: '12px',
                      background: 'linear-gradient(135deg, #0284c7, #0ea5e9)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '20px', color: '#fff',
                    }}>ℹ</div>
                    <div>
                      <div style={{ fontSize: '15px', fontWeight: '800', color: '#0c4a6e' }}>
                        {sw ? 'Jinsi ya Kulipa na Kuamilisha Akaunti' : 'How to Pay & Activate Your Account'}
                      </div>
                      <div style={{ fontSize: '12.5px', color: '#0369a1', marginTop: '2px' }}>
                        {sw ? 'Mchakato rahisi wa hatua 2' : '2-step simple process'}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px' }}>
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                      <div style={{
                        width: '28px', height: '28px', borderRadius: '50%',
                        background: '#0284c7', color: '#fff',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '13px', fontWeight: '800', flexShrink: 0,
                      }}>1</div>
                      <div style={{ fontSize: '13.5px', color: '#0c4a6e', lineHeight: '1.5' }}>
                        <strong>{sw ? 'Lipa Kwa Simu:' : 'Pay via Mobile Money:'}</strong>{' '}
                        {sw
                          ? `Tuma TZS ${price.toLocaleString()} kwenye Lipa Namba 45342017 (Mix by Yas) — M-Pesa, Tigo Pesa, Airtel Money, au Halotel`
                          : `Send TZS ${price.toLocaleString()} to Lipa Namba 45342017 (Mix by Yas) — via M-Pesa, Tigo Pesa, Airtel Money, or Halotel`}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                      <div style={{
                        width: '28px', height: '28px', borderRadius: '50%',
                        background: '#10b981', color: '#fff',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '13px', fontWeight: '800', flexShrink: 0,
                      }}>2</div>
                      <div style={{ fontSize: '13.5px', color: '#0c4a6e', lineHeight: '1.5' }}>
                        <strong>{sw ? 'Wasiliana na Admin:' : 'Contact Admin:'}</strong>{' '}
                        {sw
                          ? 'Bonyeza kitufe cha WhatsApp hapa chini kumtumia Admin uthibitisho wa malipo yako. Ataongeza subscription yako kwa dakika!'
                          : 'Click the WhatsApp button below to send Admin your payment confirmation. They will activate your subscription within minutes!'}
                      </div>
                    </div>
                  </div>

                  {/* Payment Logo Strip */}
                  <div style={{ marginBottom: '20px' }}>
                    <div style={{ fontSize: '11px', fontWeight: '700', color: '#0369a1', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '10px' }}>
                      {sw ? 'Njia Zinazokubaliwa za Malipo' : 'Accepted Payment Methods'}
                    </div>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                      <MpesaLogo />
                      <TigoLogo />
                      <AirtelLogo />
                      <HalotelLogo />
                      <div style={{ width: '1px', height: '28px', background: '#cbd5e1', margin: '0 4px' }} />
                      <VisaLogo />
                      <MastercardLogo />
                    </div>
                  </div>

                  {/* Lipa Namba Highlight */}
                  <div style={{
                    background: '#0f172a', borderRadius: '14px',
                    padding: '14px 18px', marginBottom: '16px',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  }}>
                    <div>
                      <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
                        {sw ? 'Lipa Namba (M-Pesa/Tigo/Airtel/Halotel)' : 'Lipa Namba (M-Pesa/Tigo/Airtel/Halotel)'}
                      </div>
                      <div style={{ fontSize: '22px', fontWeight: '900', color: '#38bdf8', letterSpacing: '2px', marginTop: '2px' }}>
                        45342017
                      </div>
                      <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>Mix by Yas</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: '700', textTransform: 'uppercase' }}>
                        {sw ? 'Kiasi' : 'Amount'}
                      </div>
                      <div style={{ fontSize: '20px', fontWeight: '900', color: '#4ade80' }}>
                        {price.toLocaleString()} TZS
                      </div>
                      <div style={{ fontSize: '11px', color: '#64748b' }}>
                        {activePlan.name}
                      </div>
                    </div>
                  </div>

                  {/* WhatsApp Contact Admin Button */}
                  {contactSent ? (
                    <div style={{
                      width: '100%', padding: '14px',
                      borderRadius: '16px', background: '#10b981',
                      color: '#fff', textAlign: 'center',
                      fontWeight: '800', fontSize: '14px',
                    }}>
                      {sw ? '✓ Ujumbe Umetumwa! Admin atajibu hivi karibuni.' : '✓ Message Sent! Admin will respond shortly.'}
                    </div>
                  ) : (
                    <button
                      onClick={handleContactAdmin}
                      style={{
                        width: '100%', padding: '14px',
                        borderRadius: '16px',
                        background: 'linear-gradient(135deg, #25D366, #128C7E)',
                        color: '#ffffff', border: 'none',
                        fontWeight: '800', fontSize: '14.5px',
                        cursor: 'pointer',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
                        boxShadow: '0 6px 20px rgba(37, 211, 102, 0.35)',
                        transition: 'transform 0.15s ease',
                      }}
                      onMouseEnter={e => (e.currentTarget.style.transform = 'translateY(-1px)')}
                      onMouseLeave={e => (e.currentTarget.style.transform = 'translateY(0)')}
                    >
                      <WhatsAppIcon />
                      {sw
                        ? `Jiunge kupitia WhatsApp`
                        : `Subscribe via WhatsApp`}
                    </button>
                  )}

                  <p style={{ fontSize: '12px', color: '#64748b', textAlign: 'center', marginTop: '12px', lineHeight: '1.5' }}>
                    {sw
                      ? 'Admin atakuongezea subscription mara tu baada ya kuthibitisha malipo yako.'
                      : 'Admin will manually activate your subscription immediately after verifying your payment.'}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* ═══════════════════════════════════════════
              TAB 2: ACCOUNT & SECURITY
          ═══════════════════════════════════════════ */}
          {activeTab === 'account' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

              {/* Profile Banner */}
              <div style={{
                background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
                borderRadius: '20px', padding: '24px',
                display: 'flex', alignItems: 'center', gap: '18px',
                boxShadow: '0 8px 24px rgba(15,23,42,0.15)',
              }}>
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  style={{
                    width: '64px', height: '64px', borderRadius: '50%',
                    background: 'linear-gradient(135deg, #38bdf8, #0ea5e9)',
                    color: '#0f172a', fontWeight: '900', fontSize: '22px',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0, boxShadow: '0 4px 16px rgba(56,189,248,0.3)',
                    cursor: 'pointer', overflow: 'hidden', position: 'relative'
                  }}
                  title={sw ? "Badilisha picha ya wasifu" : "Change profile picture"}
                >
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    style={{ display: 'none' }} 
                    accept="image/*" 
                    onChange={handleAvatarChange} 
                  />
                  {user?.avatar ? (
                    <img src={user.avatar} alt="Avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  ) : (
                    user?.name ? user.name.substring(0, 2).toUpperCase() : 'PJ'
                  )}
                  
                  {/* Hover overlay for 'Edit' */}
                  <div style={{
                    position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.4)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    opacity: 0, transition: 'opacity 0.2s'
                  }}
                  onMouseEnter={e => e.currentTarget.style.opacity = '1'}
                  onMouseLeave={e => e.currentTarget.style.opacity = '0'}
                  >
                    <span style={{ color: '#fff', fontSize: '10px', fontWeight: 'bold', letterSpacing: '1px' }}>
                      {sw ? 'BADILI' : 'EDIT'}
                    </span>
                  </div>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                    <h3 style={{ fontSize: '18px', fontWeight: '800', margin: 0, color: '#ffffff' }}>
                      {user?.name || 'Copetra User'}
                    </h3>
                    <span style={{
                      background: user?.role === 'admin' ? '#38bdf8' : (isPremium ? '#10b981' : '#475569'),
                      color: '#fff',
                      fontSize: '10px', fontWeight: '900',
                      padding: '3px 10px', borderRadius: '10px', letterSpacing: '0.5px'
                    }}>
                      {user?.role === 'admin' ? 'MASTER ADMIN' : (isPremium ? 'PLUS' : 'FREE')}
                    </span>
                  </div>
                  <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0 }}>
                    {user?.email || 'user@kronx.ai'}
                  </p>
                </div>
              </div>

              {/* Subscription Info */}
              <div style={{
                background: '#ffffff', border: '1px solid #e2e8f0',
                borderRadius: '18px', padding: '20px',
                boxShadow: '0 4px 16px rgba(0,0,0,0.04)',
              }}>
                <div style={{ fontSize: '11px', fontWeight: '800', color: '#64748b', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '14px' }}>
                  {sw ? 'Maelezo ya Akaunti' : 'Account Details'}
                </div>
                {[
                  {
                    label: sw ? 'Mpango wa Sasa' : 'Current Plan',
                    value: user?.role === 'admin' ? 'Master Admin Unlimited' : (isPremium ? 'Copetra Plus ✓' : 'Free Tier'),
                    valueColor: user?.role === 'admin' ? '#0284c7' : (isPremium ? '#10b981' : '#64748b'),
                  },
                  {
                    label: sw ? 'Picha Zilizotumika Leo' : 'Images Used Today',
                    value: `${picUsed} / ${isPremium ? 10 : 3}`,
                    valueColor: '#0f172a',
                  },
                  {
                    label: sw ? 'Video Zilizotumika Leo' : 'Videos Used Today',
                    value: `${vidUsed} / ${isPremium ? 3 : 1}`,
                    valueColor: '#0f172a',
                  },
                  {
                    label: sw ? 'Usalama wa Akaunti' : 'Account Security',
                    value: 'SHA-256 Encrypted',
                    valueColor: '#10b981',
                  },
                ].map((row, i, arr) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '13px 0',
                    borderBottom: i < arr.length - 1 ? '1px solid #f1f5f9' : 'none',
                    fontSize: '13.5px',
                  }}>
                    <span style={{ color: '#64748b', fontWeight: '600' }}>{row.label}</span>
                    <span style={{ fontWeight: '800', color: row.valueColor }}>{row.value}</span>
                  </div>
                ))}
              </div>

              {/* Upgrade CTA if free */}
              {!isPremium && user?.role !== 'admin' && (
                <button
                  onClick={() => setActiveTab('upgrade')}
                  style={{
                    width: '100%', padding: '14px',
                    borderRadius: '16px',
                    background: 'linear-gradient(135deg, #0f172a, #1e3a5f)',
                    color: '#ffffff', border: 'none',
                    fontWeight: '800', fontSize: '14px', cursor: 'pointer',
                    boxShadow: '0 6px 20px rgba(15,23,42,0.2)',
                  }}
                >
                  {sw ? 'Nunua Subscription — Angalia Mipango' : 'Get Subscription — View Plans'}
                </button>
              )}

              {/* Logout */}
              <button
                onClick={handleLogout}
                style={{
                  width: '100%', padding: '13px',
                  borderRadius: '16px', background: '#fef2f2',
                  color: '#dc2626', border: '1px solid #fecaca',
                  fontWeight: '800', fontSize: '14px', cursor: 'pointer',
                  transition: 'background 0.2s',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = '#fee2e2')}
                onMouseLeave={e => (e.currentTarget.style.background = '#fef2f2')}
              >
                {sw ? 'Toka Nje' : 'Sign Out'}
              </button>
            </div>
          )}

          {/* ═══════════════════════════════════════════
              TAB 3: SUPPORT & FEEDBACK
          ═══════════════════════════════════════════ */}
          {activeTab === 'support' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{
                background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)',
                borderRadius: '20px', padding: '24px',
                border: '1px solid #bae6fd'
              }}>
                <h3 style={{ margin: '0 0 8px 0', color: '#0c4a6e', fontSize: '18px', fontWeight: '800' }}>
                  {sw ? 'Tusaidie Kuboresha Copetra AI' : 'Help Us Improve Copetra AI'}
                </h3>
                <p style={{ margin: 0, color: '#0369a1', fontSize: '13px', lineHeight: '1.6' }}>
                  {sw 
                    ? 'Una wazo la kipengele kipya? Umekutana na tatizo? Tunataka kusikia kutoka kwako moja kwa moja! Ujumbe wako utatumwa kwa Admin kwa ajili ya kufanyiwa kazi haraka.'
                    : 'Have an idea for a new feature? Found a bug? We want to hear from you directly! Your message will be securely sent to Admin for immediate review.'}
                </p>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: '#0f172a', marginBottom: '8px' }}>
                    {sw ? 'Aina ya Ujumbe' : 'Message Type'}
                  </label>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    {(['feature', 'bug', 'other'] as const).map(type => (
                      <button
                        key={type}
                        onClick={() => setFeedbackType(type)}
                        style={{
                          flex: 1, padding: '10px',
                          borderRadius: '12px', border: '1px solid',
                          borderColor: feedbackType === type ? '#0ea5e9' : '#cbd5e1',
                          background: feedbackType === type ? '#f0f9ff' : '#ffffff',
                          color: feedbackType === type ? '#0284c7' : '#64748b',
                          fontWeight: '700', fontSize: '13px', cursor: 'pointer',
                          transition: 'all 0.2s',
                        }}
                      >
                        {type === 'feature' ? (sw ? 'Wazo Kipya' : 'New Feature') : 
                         type === 'bug' ? (sw ? 'Tatizo/Bug' : 'Report Bug') : 
                         (sw ? 'Mengineyo' : 'Other')}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: '#0f172a', marginBottom: '8px' }}>
                    {sw ? 'Ujumbe Wako' : 'Your Message'}
                  </label>
                  <textarea
                    value={feedbackText}
                    onChange={(e) => setFeedbackText(e.target.value)}
                    placeholder={sw 
                      ? 'Eleza wazo lako au tatizo unalokumbana nalo hapa...' 
                      : 'Describe your feature request, idea, or issue here...'}
                    style={{
                      width: '100%', height: '140px', padding: '16px',
                      borderRadius: '16px', border: '1px solid #cbd5e1',
                      background: '#f8fafc', fontSize: '14px',
                      color: '#0f172a', resize: 'none', outline: 'none',
                      fontFamily: 'inherit'
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = '#0ea5e9'
                      e.target.style.background = '#ffffff'
                      e.target.style.boxShadow = '0 0 0 3px rgba(14, 165, 233, 0.1)'
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = '#cbd5e1'
                      e.target.style.background = '#f8fafc'
                      e.target.style.boxShadow = 'none'
                    }}
                  />
                </div>

                <button
                  onClick={handleSendFeedback}
                  disabled={!feedbackText.trim()}
                  style={{
                    width: '100%', padding: '14px',
                    borderRadius: '16px',
                    background: feedbackText.trim() ? 'linear-gradient(135deg, #0f172a, #1e3a5f)' : '#e2e8f0',
                    color: feedbackText.trim() ? '#ffffff' : '#94a3b8', 
                    border: 'none',
                    fontWeight: '800', fontSize: '14px', 
                    cursor: feedbackText.trim() ? 'pointer' : 'not-allowed',
                    boxShadow: feedbackText.trim() ? '0 6px 20px rgba(15,23,42,0.2)' : 'none',
                    transition: 'all 0.2s',
                  }}
                >
                  {sw ? 'Tuma Ujumbe kwa Admin' : 'Send Message to Admin'}
                </button>
              </div>
            </div>
          )}

          {/* ═══════════════════════════════════════════
              TAB 4: DEVELOPER & API INTEGRATION
          ═══════════════════════════════════════════ */}
          {activeTab === 'developer' && user?.isDeveloper && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{
                background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)',
                borderRadius: '20px', padding: '24px',
                border: '1px solid #bae6fd'
              }}>
                <h3 style={{ margin: '0 0 8px 0', color: '#0c4a6e', fontSize: '18px', fontWeight: '800' }}>
                  {sw ? 'PJKRONX Developer Gateway' : 'PJKRONX Developer Gateway'}
                </h3>
                <p style={{ margin: 0, color: '#0369a1', fontSize: '13px', lineHeight: '1.6' }}>
                  {sw 
                    ? 'Tumia API zetu kuziunganisha na mifumo yako mingine. Tunatumia Bearer Token authentication na asynchronous webhooks.'
                    : 'Integrate PJKRONX into your own systems using our Developer API. We use Bearer Token authentication and asynchronous webhooks.'}
                </p>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: '#0f172a', marginBottom: '8px' }}>
                  {sw ? 'Ufunguo wa API (API Key)' : 'Your API Key'}
                </label>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <input
                    type="text"
                    readOnly
                    value={user?.apiKey || '••••••••••••••••••••••••••••'}
                    style={{
                      flex: 1, padding: '14px', borderRadius: '12px',
                      border: '1px solid #cbd5e1', background: '#f8fafc',
                      color: '#475569', fontSize: '14px', fontFamily: 'monospace'
                    }}
                  />
                  <button
                    onClick={async () => {
                      const { generateApiKey } = useKronxStore.getState()
                      const key = generateApiKey()
                      const updatedUser = { ...user, apiKey: key }
                      await fetch('/api/users', { method: 'POST', body: JSON.stringify(updatedUser) })
                    }}
                    style={{
                      padding: '0 20px', borderRadius: '12px',
                      background: '#0ea5e9', color: '#fff', border: 'none',
                      fontWeight: '700', cursor: 'pointer', transition: '0.2s'
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = '#0284c7'}
                    onMouseLeave={e => e.currentTarget.style.background = '#0ea5e9'}
                  >
                    {sw ? 'Tengeneza Mpya' : 'Generate'}
                  </button>
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: '700', color: '#0f172a', marginBottom: '8px' }}>
                  {sw ? 'URL ya Kurudisha Majibu (Callback URL)' : 'Callback URL (Webhook)'}
                </label>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <input
                    type="url"
                    placeholder="https://your-system.com/api/webhook"
                    value={user?.callbackUrl || ''}
                    onChange={(e) => useKronxStore.getState().updateCallbackUrl(e.target.value)}
                    style={{
                      flex: 1, padding: '14px', borderRadius: '12px',
                      border: '1px solid #cbd5e1', background: '#fff',
                      color: '#0f172a', fontSize: '14px'
                    }}
                  />
                  <button
                    onClick={async () => {
                      const updatedUser = { ...user }
                      await fetch('/api/users', { method: 'POST', body: JSON.stringify(updatedUser) })
                      alert(sw ? 'Callback URL imehifadhiwa!' : 'Callback URL saved!')
                    }}
                    style={{
                      padding: '0 20px', borderRadius: '12px',
                      background: '#10b981', color: '#fff', border: 'none',
                      fontWeight: '700', cursor: 'pointer', transition: '0.2s'
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = '#059669'}
                    onMouseLeave={e => e.currentTarget.style.background = '#10b981'}
                  >
                    {sw ? 'Hifadhi' : 'Save'}
                  </button>
                </div>
                <p style={{ fontSize: '12px', color: '#64748b', marginTop: '8px' }}>
                  {sw 
                    ? 'Tutatumia URL hii kurudisha majibu ya AI yako (POST request).'
                    : 'We will POST asynchronous AI responses to this URL.'}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
