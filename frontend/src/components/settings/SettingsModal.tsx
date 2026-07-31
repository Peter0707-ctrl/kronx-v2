'use client'

import { useState } from 'react'
import { useKronxStore } from '@/store/useKronxStore'

export default function SettingsModal() {
  const {
    settingsModalOpen,
    setSettingsModalOpen,
    user,
    logoutUser,
    upgradeSubscription,
    language
  } = useKronxStore()

  const [activeTab, setActiveTab] = useState<'upgrade' | 'account'>('upgrade')
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly')
  const [selectedMethod, setSelectedMethod] = useState<'mpesa' | 'card'>('mpesa')
  const [phone, setPhone] = useState('')
  const [loading, setLoading] = useState(false)

  if (!settingsModalOpen) return null

  const isPremium = user?.plan === 'premium'
  const picUsed = user?.picturesUsedToday || 0
  const vidUsed = user?.videosUsedToday || 0
  const picLimit = isPremium ? 10 : 3
  const vidLimit = isPremium ? 3 : 1

  const handlePay = () => {
    setLoading(true)
    setTimeout(() => {
      upgradeSubscription('premium')
      setLoading(false)
      alert(language === 'sw' ? 'Hongera! Akaunti yako imeboreshwa kuwa Kronx Premium.' : 'Success! Your account has been upgraded to Kronx Plus.')
    }, 1500)
  }

  const handleLogout = () => {
    setSettingsModalOpen(false)
    logoutUser()
  }

  return (
    <div className="auth-backdrop" onClick={() => setSettingsModalOpen(false)} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(15, 23, 42, 0.55)', backdropFilter: 'blur(10px)', position: 'fixed', inset: 0, zIndex: 9999 }}>
      <div className="auth-modal" style={{ width: '100%', maxWidth: '780px', padding: '36px', background: '#ffffff', borderRadius: '28px', border: '1px solid #e2e8f0', boxShadow: '0 25px 60px rgba(0, 0, 0, 0.12)', fontFamily: "Calibri, 'Calibri Light', sans-serif" }} onClick={e => e.stopPropagation()}>

        {/* Modal Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
          <div>
            <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#0f172a', margin: 0, letterSpacing: '-0.4px' }}>
              {language === 'sw' ? 'Upgrade mpango wako' : 'Upgrade your plan'}
            </h2>
            <p style={{ fontSize: '14px', color: '#64748b', margin: '4px 0 0 0' }}>
              {language === 'sw' ? 'Pata fursa ya kutengeneza picha na video zaidi kila siku' : 'Get higher picture & video generation limits and priority response speed'}
            </p>
          </div>

          <button
            onClick={() => setSettingsModalOpen(false)}
            style={{ width: '32px', height: '32px', borderRadius: '50%', border: 'none', background: '#f1f5f9', color: '#64748b', cursor: 'pointer', fontWeight: '700', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          >
            ✕
          </button>
        </div>

        {/* Top Segment Control (Upgrade vs Account) */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px', borderBottom: '1px solid #e2e8f0', paddingBottom: '12px' }}>
          <div style={{ display: 'flex', gap: '20px' }}>
            <button
              onClick={() => setActiveTab('upgrade')}
              style={{ background: 'none', border: 'none', padding: '6px 0', fontSize: '15px', fontWeight: '700', color: activeTab === 'upgrade' ? '#0f172a' : '#94a3b8', borderBottom: activeTab === 'upgrade' ? '2.5px solid #0f172a' : 'none', cursor: 'pointer' }}
            >
              Plans & Pricing
            </button>
            <button
              onClick={() => setActiveTab('account')}
              style={{ background: 'none', border: 'none', padding: '6px 0', fontSize: '15px', fontWeight: '700', color: activeTab === 'account' ? '#0f172a' : '#94a3b8', borderBottom: activeTab === 'account' ? '2.5px solid #0f172a' : 'none', cursor: 'pointer' }}
            >
              Account & Security
            </button>
          </div>

          {activeTab === 'upgrade' && (
            /* Monthly / Yearly Toggle Switch */
            <div style={{ display: 'flex', background: '#f1f5f9', padding: '3px', borderRadius: '20px' }}>
              <button
                onClick={() => setBillingCycle('monthly')}
                style={{ padding: '4px 14px', borderRadius: '16px', border: 'none', background: billingCycle === 'monthly' ? '#ffffff' : 'transparent', color: billingCycle === 'monthly' ? '#0f172a' : '#64748b', fontSize: '12.5px', fontWeight: '700', cursor: 'pointer', boxShadow: billingCycle === 'monthly' ? '0 2px 6px rgba(0,0,0,0.06)' : 'none' }}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingCycle('yearly')}
                style={{ padding: '4px 14px', borderRadius: '16px', border: 'none', background: billingCycle === 'yearly' ? '#ffffff' : 'transparent', color: billingCycle === 'yearly' ? '#0f172a' : '#64748b', fontSize: '12.5px', fontWeight: '700', cursor: 'pointer', boxShadow: billingCycle === 'yearly' ? '0 2px 6px rgba(0,0,0,0.06)' : 'none' }}
              >
                Yearly <span style={{ color: '#10b981', fontSize: '11px' }}>(Save 20%)</span>
              </button>
            </div>
          )}
        </div>

        {/* TAB 1: MODERN INTERNATIONAL AI PRICING CARDS */}
        {activeTab === 'upgrade' && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '28px' }}>

              {/* Free Tier Card */}
              <div style={{ border: '1px solid #e2e8f0', borderRadius: '20px', padding: '24px', background: '#ffffff', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontSize: '18px', fontWeight: '700', color: '#0f172a', marginBottom: '4px' }}>Free</div>
                  <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '16px' }}>For exploring AI capabilities</div>
                  <div style={{ fontSize: '28px', fontWeight: '800', color: '#0f172a', marginBottom: '20px' }}>0 TZS <span style={{ fontSize: '13px', color: '#64748b', fontWeight: '500' }}>/ month</span></div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13.5px', color: '#334155' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: '#10b981', fontWeight: '800' }}>✓</span> Standard AI response speed
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: '#10b981', fontWeight: '800' }}>✓</span> Max 3 Pictures per day ({picUsed}/3 used)
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: '#10b981', fontWeight: '800' }}>✓</span> Max 1 Video per day ({vidUsed}/1 used)
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: '24px' }}>
                  <button
                    disabled
                    style={{ width: '100%', padding: '12px', borderRadius: '20px', background: '#f1f5f9', color: '#94a3b8', border: 'none', fontWeight: '700', fontSize: '14px' }}
                  >
                    Current Plan
                  </button>
                </div>
              </div>

              {/* Premium Plus Tier Card */}
              <div style={{ border: '2px solid #0f172a', borderRadius: '20px', padding: '24px', background: '#ffffff', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', position: 'relative', boxShadow: '0 10px 30px rgba(0, 0, 0, 0.06)' }}>
                <span style={{ position: 'absolute', top: '-12px', right: '20px', background: '#0f172a', color: '#ffffff', fontSize: '11px', fontWeight: '700', padding: '3px 12px', borderRadius: '12px', letterSpacing: '0.5px' }}>
                  MOST POPULAR
                </span>
                <div>
                  <div style={{ fontSize: '18px', fontWeight: '700', color: '#0f172a', marginBottom: '4px' }}>Plus</div>
                  <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '16px' }}>For power users seeking maximum limits</div>
                  <div style={{ fontSize: '28px', fontWeight: '800', color: '#0f172a', marginBottom: '20px' }}>
                    {billingCycle === 'monthly' ? '15,000 TZS' : '12,000 TZS'} <span style={{ fontSize: '13px', color: '#64748b', fontWeight: '500' }}>/ month</span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13.5px', color: '#0f172a', fontWeight: '600' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: '#10b981', fontWeight: '800' }}>✓</span> High Priority response speed
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: '#10b981', fontWeight: '800' }}>✓</span> Max 10 Pictures per day
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: '#10b981', fontWeight: '800' }}>✓</span> Max 3 Videos per day
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: '#10b981', fontWeight: '800' }}>✓</span> Priority customer support
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: '24px' }}>
                  {!isPremium ? (
                    <button
                      onClick={handlePay}
                      disabled={loading}
                      style={{ width: '100%', padding: '12px', borderRadius: '20px', background: '#0f172a', color: '#ffffff', border: 'none', fontWeight: '700', fontSize: '14px', cursor: 'pointer', boxShadow: '0 4px 14px rgba(15, 23, 42, 0.2)' }}
                    >
                      {loading ? 'Processing...' : 'Upgrade to Plus'}
                    </button>
                  ) : (
                    <button
                      disabled
                      style={{ width: '100%', padding: '12px', borderRadius: '20px', background: '#10b981', color: '#ffffff', border: 'none', fontWeight: '700', fontSize: '14px' }}
                    >
                      ✓ Plus Active
                    </button>
                  )}
                </div>
              </div>

            </div>

            {/* Payment Method Selector */}
            {!isPremium && (
              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '18px', padding: '18px 22px' }}>
                <div style={{ fontSize: '13px', fontWeight: '700', color: '#475569', marginBottom: '10px' }}>Select Payment Method</div>
                <div style={{ display: 'flex', gap: '12px', marginBottom: '12px' }}>
                  <button
                    onClick={() => setSelectedMethod('mpesa')}
                    style={{ flex: 1, padding: '10px', borderRadius: '12px', border: selectedMethod === 'mpesa' ? '2px solid #0f172a' : '1px solid #cbd5e1', background: selectedMethod === 'mpesa' ? '#ffffff' : 'transparent', fontWeight: '700', fontSize: '13px', color: '#0f172a', cursor: 'pointer' }}
                  >
                    📲 M-Pesa / TigoPesa / Airtel
                  </button>
                  <button
                    onClick={() => setSelectedMethod('card')}
                    style={{ flex: 1, padding: '10px', borderRadius: '12px', border: selectedMethod === 'card' ? '2px solid #0f172a' : '1px solid #cbd5e1', background: selectedMethod === 'card' ? '#ffffff' : 'transparent', fontWeight: '700', fontSize: '13px', color: '#0f172a', cursor: 'pointer' }}
                  >
                    💳 Card Payment
                  </button>
                </div>

                {selectedMethod === 'mpesa' && (
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <input
                      type="text"
                      placeholder="Enter mobile phone number (07XX XXX XXX)"
                      value={phone}
                      onChange={e => setPhone(e.target.value)}
                      style={{ flex: 1, padding: '10px 14px', borderRadius: '10px', border: '1px solid #cbd5e1', fontSize: '13.5px', outline: 'none' }}
                    />
                    <button
                      onClick={handlePay}
                      disabled={loading}
                      style={{ padding: '10px 20px', borderRadius: '10px', background: '#0284c7', color: '#fff', border: 'none', fontWeight: '700', fontSize: '13.5px', cursor: 'pointer' }}
                    >
                      Pay 15,000 TZS
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: ACCOUNT MANAGEMENT & LOGOUT */}
        {activeTab === 'account' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '20px', padding: '24px', textAlign: 'center' }}>
              <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: '#0284c7', color: '#ffffff', fontWeight: '800', fontSize: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px auto' }}>
                PE
              </div>
              <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#0f172a', margin: '0 0 4px 0' }}>
                User Account
              </h3>
              <p style={{ fontSize: '14px', color: '#64748b', margin: 0 }}>
                user@kronx.ai
              </p>
            </div>

            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '20px', padding: '20px' }}>
              <div style={{ fontSize: '13px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '12px' }}>
                Account Information
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid #f1f5f9', fontSize: '14px' }}>
                <span style={{ color: '#64748b' }}>Current Plan</span>
                <span style={{ fontWeight: '700', color: '#0f172a' }}>{isPremium ? 'Plus (15,000 TZS)' : 'Free Tier'}</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0', fontSize: '14px' }}>
                <span style={{ color: '#64748b' }}>Authentication</span>
                <span style={{ fontWeight: '700', color: '#0f172a' }}>Email & Security Pass</span>
              </div>
            </div>

            <button
              onClick={handleLogout}
              style={{ width: '100%', padding: '14px', borderRadius: '16px', background: '#ef4444', color: '#ffffff', border: 'none', fontWeight: '700', fontSize: '14.5px', cursor: 'pointer', boxShadow: '0 4px 16px rgba(239, 68, 68, 0.2)' }}
            >
              Log out
            </button>
          </div>
        )}

      </div>
    </div>
  )
}
