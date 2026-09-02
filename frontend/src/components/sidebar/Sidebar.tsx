import { useState } from 'react'
import { useKronxStore } from '@/store/useKronxStore'

export default function Sidebar() {
  const {
    sidebarOpen,
    conversations,
    activeConversationId,
    selectConversation,
    newConversation,
    deleteConversation,
    togglePinConversation,
    toggleArchiveConversation,
    clearAllConversations,
    setSettingsModalOpen,
    setActiveView,
    user,
    toggleSidebar,
    language
  } = useKronxStore()

  const [searchQuery, setSearchQuery] = useState('')
  const [showArchived, setShowArchived] = useState(false)
  const sw = language === 'sw'

  if (!sidebarOpen) return null

  const handleMobileClose = () => {
    if (typeof window !== 'undefined' && window.innerWidth <= 768) {
      toggleSidebar()
    }
  }

  const query = searchQuery.toLowerCase().trim()

  const activeConvs = conversations.filter(c => !c.isArchived && c.title.toLowerCase().includes(query))
  const pinnedConvs = activeConvs.filter(c => c.isPinned)
  const unpinnedConvs = activeConvs.filter(c => !c.isPinned)

  const archivedConvs = conversations.filter(c => c.isArchived && c.title.toLowerCase().includes(query))

  return (
    <>
      <div className="sidebar-overlay" onClick={toggleSidebar}></div>
      <aside className="sidebar" style={{ width: '280px', background: '#f8fafc', borderRight: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', flexShrink: 0, zIndex: 1000, fontFamily: "Calibri, 'Calibri Light', sans-serif" }}>
      {/* Top New Chat Action & Mobile Close */}
      <div style={{ padding: '16px 16px 8px 16px', display: 'flex', gap: '8px', alignItems: 'center' }}>
        <button
          onClick={() => {
            newConversation()
            handleMobileClose()
          }}
          style={{ flex: 1, padding: '10px 14px', borderRadius: '10px', background: '#ffffff', border: '1px solid #cbd5e1', color: '#0f172a', fontWeight: '700', fontSize: '13.5px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', boxShadow: '0 2px 6px rgba(0,0,0,0.04)' }}
        >
          <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
            <path d="M12 5v14M5 12h14" />
          </svg>
          {sw ? 'Mazungumzo Mapya' : 'New Chat'}
        </button>

        <button
          onClick={toggleSidebar}
          className="mobile-sidebar-close"
          style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'transparent', border: '1px solid #cbd5e1', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: '#64748b' }}
        >
          <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      {/* Search Input Bar */}
      <div style={{ padding: '0 16px 8px 16px' }}>
        <input
          type="text"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          placeholder={sw ? 'Tafuta historia...' : 'Search history...'}
          style={{ width: '100%', padding: '6px 10px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '12.5px', background: '#ffffff', color: '#0f172a', outline: 'none' }}
        />
      </div>

      {/* History List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 16px' }}>
        
        {/* Pinned Chats Section */}
        {pinnedConvs.length > 0 && (
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '11px', fontWeight: '800', color: '#0284c7', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span></span> {sw ? 'Yaliyobandikwa (Pinned)' : 'Pinned Chats'}
            </div>
            {pinnedConvs.map(conv => (
              <div
                key={conv.id}
                style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', borderRadius: '8px', background: conv.id === activeConversationId ? '#e2e8f0' : 'rgba(2, 132, 199, 0.06)', border: '1px solid rgba(2, 132, 199, 0.2)', marginBottom: '4px', cursor: 'pointer' }}
                onClick={() => {
                  selectConversation(conv.id)
                  handleMobileClose()
                }}
              >
                <span style={{ fontSize: '13px', fontWeight: '700', color: '#0f172a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flex: 1 }}>
                   {conv.title}
                </span>
                <button
                  onClick={e => {
                    e.stopPropagation()
                    togglePinConversation(conv.id)
                  }}
                  title="Unpin chat"
                  style={{ background: 'none', border: 'none', color: '#0284c7', fontSize: '12px', cursor: 'pointer', padding: '2px 4px' }}
                >
                  
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Active Recent Chats Section */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '11px', fontWeight: '800', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
            {sw ? 'Historia ya Chat' : 'Chat History'}
          </span>
          {conversations.length > 0 && (
            <button
              onClick={() => {
                if (confirm(sw ? 'Je, unataka kufuta historia yote?' : 'Clear all chat history?')) clearAllConversations()
              }}
              style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '11px', fontWeight: '600', cursor: 'pointer' }}
            >
              {sw ? 'Futa Zote' : 'Clear All'}
            </button>
          )}
        </div>

        {unpinnedConvs.length === 0 && pinnedConvs.length === 0 && (
          <p style={{ fontSize: '12.5px', color: '#94a3b8', fontStyle: 'italic', margin: '8px 0 0 0' }}>
            {searchQuery ? 'Hakuna chat zilizopatikana.' : 'Hakuna historia ya chat.'}
          </p>
        )}

        {unpinnedConvs.map(conv => (
          <div
            key={conv.id}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', borderRadius: '8px', background: conv.id === activeConversationId ? '#e2e8f0' : 'transparent', marginBottom: '4px', cursor: 'pointer' }}
            onClick={() => {
              selectConversation(conv.id)
              handleMobileClose()
            }}
          >
            <span style={{ fontSize: '13px', fontWeight: '600', color: conv.id === activeConversationId ? '#0f172a' : '#475569', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flex: 1 }}>
              {conv.title}
            </span>
            <div style={{ display: 'flex', gap: '4px' }}>
              <button
                onClick={e => {
                  e.stopPropagation()
                  toggleArchiveConversation(conv.id)
                }}
                title="Archive chat"
                style={{ background: 'none', border: 'none', color: '#64748b', fontSize: '11px', cursor: 'pointer', padding: '2px 4px' }}
              >
                
              </button>
              <button
                onClick={e => {
                  e.stopPropagation()
                  deleteConversation(conv.id)
                }}
                title="Delete chat"
                style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '12px', cursor: 'pointer', padding: '2px 4px' }}
              >
                
              </button>
            </div>
          </div>
        ))}

        {/* Archived Chats Accordion / Section */}
        {archivedConvs.length > 0 && (
          <div style={{ marginTop: '20px', paddingTop: '12px', borderTop: '1px solid #e2e8f0' }}>
            <button
              onClick={() => setShowArchived(!showArchived)}
              style={{ width: '100%', background: 'none', border: 'none', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px', fontWeight: '800', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.8px', cursor: 'pointer', padding: '4px 0' }}
            >
              <span> {sw ? `Kumbukumbu zilizohifadhiwa (${archivedConvs.length})` : `Archived Chats (${archivedConvs.length})`}</span>
              <span>{showArchived ? '' : ''}</span>
            </button>

            {showArchived && archivedConvs.map(conv => (
              <div
                key={conv.id}
                style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', borderRadius: '8px', background: '#f1f5f9', marginBottom: '4px', cursor: 'pointer', marginTop: '6px' }}
                onClick={() => {
                  selectConversation(conv.id)
                  handleMobileClose()
                }}
              >
                <span style={{ fontSize: '12.5px', color: '#64748b', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flex: 1 }}>
                  {conv.title}
                </span>
                <button
                  onClick={e => {
                    e.stopPropagation()
                    toggleArchiveConversation(conv.id)
                  }}
                  title="Unarchive chat"
                  style={{ background: 'none', border: 'none', color: '#0284c7', fontSize: '11px', fontWeight: '700', cursor: 'pointer' }}
                >
                  Unarchive
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Bottom Profile Account, Settings & Admin Console */}
      <div style={{ padding: '16px', borderTop: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {(user?.role === 'admin' || user?.email === 'pj0040280@gmail.com') && (
          <button
            onClick={() => setActiveView('admin')}
            title="AI Admin Dashboard"
            style={{ width: '42px', height: '42px', borderRadius: '12px', background: '#0f172a', border: 'none', color: '#ffffff', fontWeight: '900', fontSize: '18px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', boxShadow: '0 4px 14px rgba(15, 23, 42, 0.25)', margin: '0 auto' }}
          >
            
          </button>
        )}

        <button
          onClick={() => {
            setSettingsModalOpen(true)
            handleMobileClose()
          }}
          style={{ width: '100%', padding: '10px 12px', borderRadius: '12px', background: '#ffffff', border: '1px solid #cbd5e1', color: '#0f172a', fontWeight: '700', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}
        >
          <div style={{ width: '26px', height: '26px', borderRadius: '50%', background: '#0284c7', color: '#fff', fontWeight: '800', fontSize: '11px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            PE
          </div>
          <span>Settings & Account</span>
        </button>
      </div>
    </aside>
    </>
  )
}