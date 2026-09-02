'use client'

import { useKronxStore } from '@/store/useKronxStore'

interface Props {
  onSend: (text: string) => void
}

export default function DashboardView({ onSend }: Props) {
  const { language, setActiveView, conversations, goals, user } = useKronxStore()
  const sw = language === 'sw'

  return (
    <div className="dash-container" style={{ flex: 1, overflowY: 'auto', padding: '32px 40px', background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)', fontFamily: "Calibri, 'Calibri Light', sans-serif" }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px' }}>
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'rgba(2, 132, 199, 0.08)', border: '1px solid rgba(2, 132, 199, 0.2)', padding: '6px 14px', borderRadius: '20px', fontSize: '12px', fontWeight: '700', color: '#0284c7', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px' }}>
            <span style={{ width: '8px', height: '8px', background: '#0284c7', borderRadius: '50%', boxShadow: '0 0 8px #0284c7' }} />
            {sw ? 'Mfumo wa Antigravity Ice' : 'Antigravity Ice Telemetry'}
          </div>
          <h1 style={{ fontSize: '24px', fontWeight: '800', margin: '4px 0', color: '#0f172a', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span className="copetra-script-font" style={{ fontFamily: "'Grand Hotel', 'Pacifico', cursive", fontSize: '34px', color: '#0f172a' }}>Copetra AI</span>
            <span>{sw ? 'Dashboard' : 'Telemetry & Analytics'}</span>
          </h1>
          <p style={{ fontSize: '14px', color: '#64748b', marginTop: '4px' }}>
            {sw ? 'Tathmini utendaji wa Mfumo, Malengo ya Biashara, na Kumbukumbu.' : 'Real-time system telemetry, active user goals, and cloud memory vault status.'}
          </p>
        </div>

        <button
          className="hero-primary-btn"
          onClick={() => setActiveView('chat')}
          style={{ background: 'linear-gradient(135deg, #0284c7, #0369a1)', padding: '12px 24px', borderRadius: '12px', boxShadow: '0 6px 20px rgba(2, 132, 199, 0.25)' }}
        >
           {sw ? 'Rudi Kwenye Mazungumzo' : 'Return to Chat'}
        </button>
      </div>

      {/* Analytics Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '32px' }}>
        <div style={{ background: 'rgba(255, 255, 255, 0.95)', border: '1px solid #bae6fd', borderRadius: '18px', padding: '20px', boxShadow: '0 4px 15px rgba(2, 132, 199, 0.05)' }}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#0284c7', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '8px' }}>
            {sw ? 'Hali ya Injini' : 'AI Engine Status'}
          </div>
          <div style={{ fontSize: '24px', fontWeight: '800', color: '#0f172a' }}>PJ COPETRANOVA</div>
          <div style={{ fontSize: '12px', color: '#10b981', fontWeight: '600', marginTop: '4px' }}> 0% Local RAM (Ultra-Fast)</div>
        </div>

        <div style={{ background: 'rgba(255, 255, 255, 0.95)', border: '1px solid #bae6fd', borderRadius: '18px', padding: '20px', boxShadow: '0 4px 15px rgba(2, 132, 199, 0.05)' }}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#0284c7', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '8px' }}>
            {sw ? 'Mazungumzo Yaliyohifadhiwa' : 'Recent Chats'}
          </div>
          <div style={{ fontSize: '24px', fontWeight: '800', color: '#0f172a' }}>{conversations.length}</div>
          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>{sw ? 'Mazungumzo amilifu' : 'Active sessions'}</div>
        </div>

        <div style={{ background: 'rgba(255, 255, 255, 0.95)', border: '1px solid #bae6fd', borderRadius: '18px', padding: '20px', boxShadow: '0 4px 15px rgba(2, 132, 199, 0.05)' }}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#0284c7', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '8px' }}>
            {sw ? 'Malengo na Bajeti' : 'User Goals & Targets'}
          </div>
          <div style={{ fontSize: '24px', fontWeight: '800', color: '#0f172a' }}>{goals.length}</div>
          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>{goals.filter(g => g.completed).length} {sw ? 'yamekamilika' : 'completed'}</div>
        </div>

        <div style={{ background: 'rgba(255, 255, 255, 0.95)', border: '1px solid #bae6fd', borderRadius: '18px', padding: '20px', boxShadow: '0 4px 15px rgba(2, 132, 199, 0.05)' }}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#0284c7', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '8px' }}>
            {sw ? 'Akaunti' : 'Active User'}
          </div>
          <div style={{ fontSize: '20px', fontWeight: '800', color: '#0f172a' }}>{user?.name || 'Guest User'}</div>
          <div style={{ fontSize: '12px', color: '#0284c7', fontWeight: '600', marginTop: '4px' }}>{user?.role === 'admin' ? 'Admin Role' : 'User Account'}</div>
        </div>
      </div>

      {/* Active Goals Section */}
      <div style={{ background: 'rgba(255, 255, 255, 0.95)', border: '1px solid #bae6fd', borderRadius: '20px', padding: '28px', boxShadow: '0 6px 25px rgba(2, 132, 199, 0.06)' }}>
        <h2 style={{ fontSize: '18px', fontWeight: '800', color: '#0f172a', marginBottom: '16px' }}>
           {sw ? 'Malengo Yangu' : 'Active Personal & Business Goals'}
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {goals.map(g => (
            <div key={g.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', background: '#f0f9ff', border: '1px solid #e0f2fe', borderRadius: '12px' }}>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#0f172a' }}>{g.title}</span>
              <span style={{ padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '700', background: g.completed ? 'rgba(16, 185, 129, 0.12)' : 'rgba(2, 132, 199, 0.12)', color: g.completed ? '#10b981' : '#0284c7' }}>
                {g.completed ? (sw ? 'Kamilifu' : 'Done') : (sw ? 'Inaendelea' : 'In Progress')}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
