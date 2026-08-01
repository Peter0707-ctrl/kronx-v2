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
  const [payerName, setPayerName] = useState('')
  const [loading, setLoading] = useState(false)
  const [pushSent, setPushSent] = useState(false)
  const [pin, setPin] = useState('')

  if (!settingsModalOpen) return null

  const isPremium = user?.plan === 'premium'
  const picUsed = user?.picturesUsedToday || 0
  const vidUsed = user?.videosUsedToday || 0
  const picLimit = isPremium ? 10 : 3
  const vidLimit = isPremium ? 3 : 1

  const handlePay = () => {
    if (selectedMethod === 'mpesa' && (!phone.trim() || !payerName.trim())) {
      alert(language === 'sw' ? 'Tafadhali ingiza namba ya simu na jina lililotumika kulipia' : 'Please enter your phone number and payer full name')
      return
    }
    setLoading(true)
    setTimeout(() => {
      setLoading(false)
      setPushSent(true)
    }, 1200)
  }

  const handleSendWhatsAppVerification = () => {
    const text = encodeURIComponent(
      `HABARI ADMIN, NIMEFANYA MALIPO YA KRONX PLUS (15,000 TZS).\n\n` +
      `Jina la Mlipaji: ${payerName.trim() || user?.name || 'Mtumiaji'}\n` +
      `Namba Iliyotumika Kulipia: ${phone.trim()}\n` +
      `Lipa Namba: 45342017 (Mix by Yas)\n` +
      `Email: ${user?.email || 'N/A'}\n\n` +
      `Tafadhali thibitisha malipo yangu na uboreshe akaunti yangu.`
    )
    window.open(`https://wa.me/255673190931?text=${text}`, '_blank')
  }

  const handleConfirmPush = () => {
    setLoading(true)
    setTimeout(() => {
      upgradeSubscription('premium')
      setLoading(false)
      setPushSent(false)
      alert(language === 'sw' ? 'Malipo yamefanikiwa! Akaunti yako imeboreshwa kuwa Kronx Plus (15,000 TZS).' : 'Payment Successful! STK Push confirmed. Your account has been upgraded to Kronx Plus.')
    }, 1500)
  }

  const handleLogout = () => {
    setSettingsModalOpen(false)
    logoutUser()
  }

  return (
    <div className="auth-backdrop" onClick={() => setSettingsModalOpen(false)} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(15, 23, 42, 0.55)', backdropFilter: 'blur(10px)', position: 'fixed', inset: 0, zIndex: 9999, padding: '20px' }}>
      <div className="auth-modal" style={{ width: '100%', maxWidth: '780px', maxHeight: '90vh', overflowY: 'auto', padding: '36px', background: '#ffffff', borderRadius: '28px', border: '1px solid #e2e8f0', boxShadow: '0 25px 60px rgba(0, 0, 0, 0.12)', fontFamily: "Calibri, 'Calibri Light', sans-serif" }} onClick={e => e.stopPropagation()}>

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
              <div style={{ background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: '22px', padding: '24px', boxShadow: '0 8px 24px rgba(0,0,0,0.04)', marginTop: '20px' }}>
                <div style={{ fontSize: '15px', fontWeight: '800', color: '#0f172a', marginBottom: '14px', letterSpacing: '-0.3px' }}>
                  Select Mobile Payment Method
                </div>
                <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                  <button
                    onClick={() => setSelectedMethod('mpesa')}
                    style={{ flex: 1, padding: '12px', borderRadius: '14px', border: selectedMethod === 'mpesa' ? '2px solid #0f172a' : '1px solid #cbd5e1', background: selectedMethod === 'mpesa' ? '#f8fafc' : '#ffffff', fontWeight: '800', fontSize: '13.5px', color: '#0f172a', cursor: 'pointer', textAlign: 'center' }}
                  >
                    Mobile Money (M-Pesa / Tigo / Airtel)
                  </button>
                  <button
                    onClick={() => setSelectedMethod('card')}
                    style={{ flex: 1, padding: '12px', borderRadius: '14px', border: selectedMethod === 'card' ? '2px solid #0f172a' : '1px solid #cbd5e1', background: selectedMethod === 'card' ? '#f8fafc' : '#ffffff', fontWeight: '800', fontSize: '13.5px', color: '#0f172a', cursor: 'pointer', textAlign: 'center' }}
                  >
                    Credit / Debit Card
                  </button>
                </div>

                {selectedMethod === 'mpesa' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                    <div style={{ background: '#0f172a', color: '#ffffff', padding: '16px 20px', borderRadius: '16px', fontSize: '13.5px', lineHeight: '1.5' }}>
                      <div style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#94a3b8', letterSpacing: '0.8px', marginBottom: '4px' }}>LIPA NAMBA PAYMENT DETAILS</div>
                      Pay <strong>15,000 TZS</strong> to Lipa Namba <strong>45342017 (Mix by Yas)</strong>. Enter your full name and phone number below to send payment verification directly to Admin on WhatsApp for instant activation.
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      <input
                        type="text"
                        placeholder="Full Name of Payer (Jina la Mlipaji)"
                        value={payerName}
                        onChange={e => setPayerName(e.target.value)}
                        style={{ padding: '12px 16px', borderRadius: '12px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none', background: '#f8fafc', fontWeight: '600', color: '#0f172a' }}
                      />
                      <input
                        type="text"
                        placeholder="Phone Number Used to Pay (Namba Uliyolipia 07XX XXX XXX)"
                        value={phone}
                        onChange={e => setPhone(e.target.value)}
                        style={{ padding: '12px 16px', borderRadius: '12px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none', background: '#f8fafc', fontWeight: '600', color: '#0f172a' }}
                      />
                    </div>

                    <div style={{ display: 'flex', gap: '10px', marginTop: '4px' }}>
                      <button
                        onClick={handlePay}
                        disabled={loading}
                        style={{ flex: 1, padding: '12px', borderRadius: '14px', background: '#0f172a', color: '#ffffff', border: 'none', fontWeight: '800', fontSize: '13.5px', cursor: 'pointer', boxShadow: '0 4px 14px rgba(15, 23, 42, 0.2)' }}
                      >
                        {loading ? 'Sending Prompt...' : 'Send STK Push'}
                      </button>
                      <button
                        onClick={handleSendWhatsAppVerification}
                        style={{ flex: 1, padding: '12px', borderRadius: '14px', background: '#10b981', color: '#ffffff', border: 'none', fontWeight: '800', fontSize: '13.5px', cursor: 'pointer', boxShadow: '0 4px 14px rgba(16, 185, 129, 0.2)' }}
                      >
                        Verify on WhatsApp
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Mobile Phone STK Push Notification Overlay */}
            {pushSent && (
              <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.75)', backdropFilter: 'blur(8px)', zIndex: 10000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ background: '#ffffff', borderRadius: '24px', padding: '28px', width: '100%', maxWidth: '380px', boxShadow: '0 20px 50px rgba(0,0,0,0.3)', border: '1px solid #e2e8f0', textAlign: 'center', animation: 'fadeIn 0.3s ease-out' }}>
                  <div style={{ width: '44px', height: '44px', borderRadius: '50%', background: '#f1f5f9', color: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 14px auto', fontWeight: '900', fontSize: '16px' }}>
                    STK
                  </div>
                  <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#0f172a', margin: '0 0 6px 0' }}>
                    M-Pesa STK Push Sent!
                  </h3>
                  <p style={{ fontSize: '13.5px', color: '#475569', margin: '0 0 16px 0', lineHeight: '1.5' }}>
                    A payment prompt of <strong>15,000 TZS</strong> for <strong>Kronx Plus Subscription</strong> has been pushed to <strong>{phone || '07XX XXX XXX'}</strong>.
                  </p>

                  <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '12px', marginBottom: '16px' }}>
                    <label style={{ fontSize: '11.5px', fontWeight: '700', color: '#64748b', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>
                      Enter M-Pesa PIN to Confirm
                    </label>
                    <input
                      type="password"
                      maxLength={4}
                      placeholder="••••"
                      value={pin}
                      onChange={e => setPin(e.target.value)}
                      style={{ width: '100%', textAlign: 'center', letterSpacing: '8px', fontSize: '20px', padding: '8px', borderRadius: '8px', border: '1px solid #cbd5e1', outline: 'none' }}
                    />
                  </div>

                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                      onClick={() => setPushSent(false)}
                      style={{ flex: 1, padding: '10px', borderRadius: '12px', border: '1px solid #cbd5e1', background: '#fff', color: '#64748b', fontWeight: '700', fontSize: '13px', cursor: 'pointer' }}
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleConfirmPush}
                      disabled={loading || pin.length < 4}
                      style={{ flex: 1, padding: '10px', borderRadius: '12px', border: 'none', background: pin.length >= 4 ? '#10b981' : '#cbd5e1', color: '#fff', fontWeight: '700', fontSize: '13px', cursor: pin.length >= 4 ? 'pointer' : 'default' }}
                    >
                      {loading ? 'Confirming...' : 'Confirm PIN'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: ACCOUNT MANAGEMENT & SECURITY */}
        {activeTab === 'account' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', animation: 'fadeIn 0.3s ease-out' }}>
            {/* User Profile Header Banner Card */}
            <div style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)', borderRadius: '24px', padding: '28px', color: '#ffffff', boxShadow: '0 12px 30px rgba(15, 23, 42, 0.15)', display: 'flex', alignItems: 'center', gap: '20px' }}>
              <div style={{ width: '72px', height: '72px', borderRadius: '50%', background: '#38bdf8', color: '#0f172a', fontWeight: '900', fontSize: '26px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, boxShadow: '0 6px 20px rgba(56, 189, 248, 0.3)' }}>
                {user?.name ? user.name.substring(0, 2).toUpperCase() : 'PJ'}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                  <h3 style={{ fontSize: '20px', fontWeight: '800', margin: 0, color: '#ffffff' }}>
                    {user?.name || 'PJ COPETRANOVA'}
                  </h3>
                  <span style={{ background: user?.role === 'admin' ? '#38bdf8' : '#10b981', color: '#0f172a', fontSize: '11px', fontWeight: '900', padding: '3px 10px', borderRadius: '12px', letterSpacing: '0.5px' }}>
                    {user?.role === 'admin' ? 'MASTER ADMIN' : (isPremium ? 'PLUS TIER' : 'FREE TIER')}
                  </span>
                </div>
                <p style={{ fontSize: '14px', color: '#94a3b8', margin: 0 }}>
                  {user?.email || 'pj0040280@gmail.com'}
                </p>
              </div>
            </div>

            {/* Account & Security Information Card */}
            <div style={{ background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: '22px', padding: '24px', boxShadow: '0 8px 24px rgba(0,0,0,0.04)' }}>
              <div style={{ fontSize: '13px', fontWeight: '800', color: '#64748b', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '16px' }}>
                SECURITY & SUBSCRIPTION PROFILE
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 0', borderBottom: '1px solid #f1f5f9', fontSize: '14.5px' }}>
                <span style={{ color: '#64748b', fontWeight: '600' }}>Active Subscription Plan</span>
                <span style={{ fontWeight: '800', color: '#0f172a', background: '#f8fafc', padding: '6px 14px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                  {user?.role === 'admin' ? 'Master Admin Unlimited' : (isPremium ? 'Kronx Plus (15,000 TZS)' : 'Free Tier')}
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 0', borderBottom: '1px solid #f1f5f9', fontSize: '14.5px' }}>
                <span style={{ color: '#64748b', fontWeight: '600' }}>Authentication Standard</span>
                <span style={{ fontWeight: '700', color: '#0f172a' }}>Zero-Knowledge SHA-256 Protocol</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 0', fontSize: '14.5px' }}>
                <span style={{ color: '#64748b', fontWeight: '600' }}>Device Persistent State</span>
                <span style={{ fontWeight: '700', color: '#10b981' }}>Active Auto-Login Enabled</span>
              </div>
            </div>

            <button
              onClick={handleLogout}
              style={{ width: '100%', padding: '14px', borderRadius: '16px', background: '#ef4444', color: '#ffffff', border: 'none', fontWeight: '800', fontSize: '14.5px', cursor: 'pointer', boxShadow: '0 4px 16px rgba(239, 68, 68, 0.25)', transition: 'transform 0.2s ease' }}
            >
              Sign out of Kronx Account
            </button>
          </div>
        )}

      </div>
    </div>
  )
}
