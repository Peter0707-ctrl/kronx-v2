'use client'

import { useKronxStore } from '@/store/useKronxStore'

export default function Sidebar() {
  const {
    sidebarOpen,
    conversations,
    activeConversationId,
    selectConversation,
    newConversation,
    deleteConversation,
    clearAllConversations,
    setSettingsModalOpen
  } = useKronxStore()

  if (!sidebarOpen) return null

  return (
    <aside style={{ width: '240px', background: '#f8fafc', borderRight: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', flexShrink: 0, zIndex: 10, height: '100vh', fontFamily: "Calibri, 'Calibri Light', sans-serif" }}>
      {/* Top New Chat Action */}
      <div style={{ padding: '16px 16px 8px 16px' }}>
        <button
          onClick={newConversation}
          style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', background: '#ffffff', border: '1px solid #cbd5e1', color: '#0f172a', fontWeight: '700', fontSize: '13.5px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', boxShadow: '0 2px 6px rgba(0,0,0,0.04)' }}
        >
          <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
            <path d="M12 5v14M5 12h14" />
          </svg>
          New Chat
        </button>
      </div>

      {/* History List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '11px', fontWeight: '800', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
            Chat History
          </span>
          {conversations.length > 0 && (
            <button
              onClick={() => {
                if (confirm('Clear all chat history?')) clearAllConversations()
              }}
              style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '11px', fontWeight: '600', cursor: 'pointer' }}
            >
              Clear
            </button>
          )}
        </div>

        {conversations.filter(c => c.id !== activeConversationId && c.messages.length > 0).length === 0 && (
          <p style={{ fontSize: '12.5px', color: '#94a3b8', fontStyle: 'italic', margin: '8px 0 0 0' }}>
            No closed chat history.
          </p>
        )}

        {conversations.filter(c => c.id !== activeConversationId && c.messages.length > 0).map(conv => (
          <div
            key={conv.id}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', borderRadius: '8px', background: conv.id === activeConversationId ? '#e2e8f0' : 'transparent', marginBottom: '4px', cursor: 'pointer' }}
            onClick={() => selectConversation(conv.id)}
          >
            <span style={{ fontSize: '13px', fontWeight: '600', color: conv.id === activeConversationId ? '#0f172a' : '#475569', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flex: 1 }}>
              {conv.title}
            </span>
            <button
              onClick={e => {
                e.stopPropagation()
                deleteConversation(conv.id)
              }}
              style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '12px', cursor: 'pointer', padding: '2px 4px' }}
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      {/* Bottom Profile Account & Settings */}
      <div style={{ padding: '16px', borderTop: '1px solid #e2e8f0' }}>
        <button
          onClick={() => setSettingsModalOpen(true)}
          style={{ width: '100%', padding: '10px 12px', borderRadius: '12px', background: '#ffffff', border: '1px solid #cbd5e1', color: '#0f172a', fontWeight: '700', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}
        >
          <div style={{ width: '26px', height: '26px', borderRadius: '50%', background: '#0284c7', color: '#fff', fontWeight: '800', fontSize: '11px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            PE
          </div>
          <span>Settings & Account</span>
        </button>
      </div>
    </aside>
  )
}