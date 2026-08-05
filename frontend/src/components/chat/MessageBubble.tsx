'use client'

import { useState } from 'react'
import { Message } from '@/types'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useKronxStore } from '@/store/useKronxStore'

interface Props {
  message: Message
  isStreaming?: boolean
  onRegenerate?: () => void
  onEditAndResend?: (messageId: string, newContent: string) => void
}

export default function MessageBubble({ message, isStreaming, onRegenerate, onEditAndResend }: Props) {
  const isAi = message.role === 'ai'
  const [copied, setCopied] = useState(false)
  const [feedback, setFeedback] = useState<'good' | 'bad' | null>(null)
  const [moreMenuOpen, setMoreMenuOpen] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editText, setEditText] = useState(message.content)

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const getCleanUserQuery = (content: string): string => {
    const docIdx = content.indexOf('\n\n[')
    if (docIdx !== -1) return content.substring(0, docIdx).trim()
    const imgIdx = content.indexOf('\n\n[IMAGE:')
    if (imgIdx !== -1) return content.substring(0, imgIdx).trim()
    return content.trim()
  }

  const handleGoodResponse = () => {
    setFeedback(feedback === 'good' ? null : 'good')
  }

  const handleBadResponse = () => {
    setFeedback('bad')
    const currentState = useKronxStore.getState()
    const msgs = currentState.activeMessages()
    const aiIdx = msgs.findIndex(m => m.id === message.id)
    if (aiIdx > 0 && msgs[aiIdx - 1].role === 'user') {
      const userQuery = getCleanUserQuery(msgs[aiIdx - 1].content)
      const badSnippet = message.content.slice(0, 120).replace(/\n/g, ' ')
      const memoryItem = `User disliked response to "${userQuery}". Avoid answering like: "${badSnippet}...". Be more detailed, thorough, follow all instructions, and explain clearly.`
      currentState.addMemory(memoryItem)
      console.log('[Copetra Brain Saved Reinforcement Memory]:', memoryItem)
    }
    if (onRegenerate) {
      onRegenerate()
    }
  }

  const handleSpeak = () => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return

    if (isSpeaking) {
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
      return
    }

    window.speechSynthesis.cancel()
    const textToSpeak = message.content.replace(/[*_#`~>]/g, '')
    const utterance = new SpeechSynthesisUtterance(textToSpeak)
    utterance.lang = 'en-US'
    utterance.rate = 1.0

    utterance.onstart = () => setIsSpeaking(true)
    utterance.onend = () => setIsSpeaking(false)
    utterance.onerror = () => setIsSpeaking(false)

    window.speechSynthesis.speak(utterance)
  }

  const handleSaveEdit = () => {
    if (!editText.trim()) return
    setIsEditing(false)
    if (onEditAndResend) {
      let finalContent = editText.trim()
      const docIdx = message.content.indexOf('\n\n[')
      if (docIdx !== -1) {
        finalContent = `${finalContent}\n\n${message.content.substring(docIdx).trim()}`
      } else {
        const imgIdx = message.content.indexOf('\n\n[IMAGE:')
        if (imgIdx !== -1) {
          finalContent = `${finalContent}\n\n${message.content.substring(imgIdx).trim()}`
        }
      }
      onEditAndResend(message.id, finalContent)
    }
  }

  // Format user messages cleanly: hide raw Base64 images & raw document text dumps behind sleek badges
  let displayContent = message.content.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
  if (!isAi) {
    displayContent = displayContent
      .replace(/\[IMAGE: data:image\/[a-zA-Z]+;base64,.*?\]/g, '🖼️ [Attached Image]')
      .replace(/\[(WORD|PDF|EXCEL|POWERPOINT|TEXT|CODE) DOCUMENT ATTACHED:\s*([^\]]+)\][\s\S]*/gi, '📄 [Attached Document: $2]')
  }

  return (
    <div className={`msg-row ${isAi ? 'msg-ai' : 'msg-user'}`}>
      <div className={`bubble ${isAi ? 'bubble-ai' : 'bubble-user'}`} style={{ position: 'relative' }}>
        {!isAi && !isEditing && (
          <button
            onClick={() => {
              setEditText(getCleanUserQuery(message.content))
              setIsEditing(true)
            }}
            title="Edit prompt"
            style={{
              position: 'absolute',
              top: '-24px',
              right: '4px',
              background: '#ffffff',
              border: '1px solid #cbd5e1',
              borderRadius: '50%',
              width: '24px',
              height: '24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              color: '#64748b',
              boxShadow: '0 2px 6px rgba(0,0,0,0.06)'
            }}
          >
            <svg width={12} height={12} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M12 20h9" />
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
            </svg>
          </button>
        )}

        {isEditing ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', width: '100%', minWidth: '300px' }}>
            <textarea
              value={editText}
              onChange={e => setEditText(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '12px',
                border: '1px solid #0284c7',
                fontSize: '15px',
                color: '#000000',
                outline: 'none',
                fontFamily: "Calibri, 'Calibri Light', sans-serif",
                resize: 'none'
              }}
              rows={3}
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button
                onClick={() => setIsEditing(false)}
                style={{ padding: '6px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', background: '#fff', color: '#64748b', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                style={{ padding: '6px 14px', borderRadius: '8px', border: 'none', background: '#0284c7', color: '#fff', fontSize: '13px', fontWeight: '700', cursor: 'pointer' }}
              >
                Save & Submit
              </button>
            </div>
          </div>
        ) : (
          <>
            {message.content ? (
              <div className="markdown-body" style={{ color: '#000000', fontSize: '14.5px', lineHeight: '1.8', whiteSpace: 'pre-wrap', fontFamily: 'Calibri, sans-serif' }}>
                <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({node, ...props}) => <h1 style={{fontSize: '18px', fontWeight: '800', margin: '16px 0 8px'}} {...props} />,
                    h2: ({node, ...props}) => <h2 style={{fontSize: '16px', fontWeight: '700', margin: '16px 0 8px', borderBottom: '1px solid #cbd5e1', paddingBottom: '4px'}} {...props} />,
                    h3: ({node, ...props}) => <h3 style={{fontSize: '14.5px', fontWeight: '700', margin: '12px 0 6px'}} {...props} />,
                    p: ({node, ...props}) => <p style={{marginBottom: '10px', whiteSpace: 'pre-wrap', lineHeight: '1.8'}} {...props} />,
                    ul: ({node, ...props}) => <ul style={{paddingLeft: '20px', margin: '6px 0 10px', listStyleType: 'disc'}} {...props} />,
                    ol: ({node, ...props}) => <ol style={{paddingLeft: '22px', margin: '6px 0 10px'}} {...props} />,
                    li: ({node, ...props}) => <li style={{marginBottom: '6px'}} {...props} />,
                    blockquote: ({node, ...props}) => <blockquote style={{borderLeft: '4px solid #0284c7', background: 'rgba(2, 132, 199, 0.03)', padding: '10px 16px', margin: '12px 0', fontStyle: 'italic', fontSize: '14px', borderRadius: '0 8px 8px 0'}} {...props} />,
                    table: ({node, ...props}) => (
                      <div style={{ overflowX: 'auto', margin: '16px 0', width: '100%', borderRadius: '8px', border: '1px solid #cbd5e1', boxShadow: '0 2px 8px rgba(0,0,0,0.02)' }}>
                        <table style={{ borderCollapse: 'collapse', width: '100%', minWidth: '500px', fontSize: '13px', color: '#0f172a' }} {...props} />
                      </div>
                    ),
                    thead: ({node, ...props}) => <thead style={{ background: '#f8fafc', borderBottom: '2px solid #cbd5e1' }} {...props} />,
                    th: ({node, ...props}) => <th style={{ padding: '8px 12px', fontWeight: '700', textAlign: 'left', borderRight: '1px solid #cbd5e1' }} {...props} />,
                    tr: ({node, ...props}) => <tr style={{ borderBottom: '1px solid #cbd5e1', background: '#ffffff' }} {...props} />,
                    td: ({node, ...props}) => <td style={{ padding: '8px 12px', borderRight: '1px solid #cbd5e1' }} {...props} />,
                    code: ({node, inline, className, children, ...props}: any) => {
                      const match = /language-(\w+)/.exec(className || '')
                      return !inline ? (
                        <div style={{ margin: '14px 0', border: '1px solid #1e293b', borderRadius: '12px', overflow: 'hidden' }}>
                          <div style={{ background: '#0f172a', padding: '8px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #1e293b' }}>
                            <span style={{ fontSize: '11px', color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: '700', fontFamily: 'monospace' }}>{match ? match[1] : 'code'}</span>
                            <button onClick={() => navigator.clipboard.writeText(String(children))} style={{ background: 'rgba(255, 255, 255, 0.1)', border: '1px solid rgba(255, 255, 255, 0.2)', color: '#ffffff', fontSize: '11px', fontWeight: '600', padding: '4px 10px', borderRadius: '6px', cursor: 'pointer' }}>Copy code</button>
                          </div>
                          <pre style={{ background: '#090d16', padding: '16px', overflowX: 'auto', margin: '0', fontSize: '13px', fontFamily: 'Consolas, Monaco, monospace', color: '#f8fafc' }}>
                            <code style={{ color: '#38bdf8' }} {...props}>{children}</code>
                          </pre>
                        </div>
                      ) : (
                        <code style={{ background: 'rgba(124,110,247,0.12)', color: '#7c6ef7', padding: '2px 7px', borderRadius: '5px', fontFamily: 'monospace', fontSize: '12px' }} {...props}>
                          {children}
                        </code>
                      )
                    },
                    img: ({node, src, alt, ...props}) => (
                      <span style={{ display: 'inline-block', margin: '14px 0', position: 'relative', maxWidth: '512px', width: '100%' }}>
                        <img src={src} alt={alt} style={{ width: '100%', maxWidth: '512px', height: 'auto', borderRadius: '16px', border: '1px solid #bae6fd', boxShadow: '0 8px 24px rgba(2, 132, 199, 0.12)', display: 'block' }} />
                        <a href={src} target="_blank" rel="noopener noreferrer" style={{ position: 'absolute', bottom: '12px', right: '12px', background: 'rgba(15, 23, 42, 0.85)', color: '#ffffff', padding: '6px 14px', borderRadius: '20px', fontSize: '12px', fontWeight: '700', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '6px', backdropFilter: 'blur(8px)', boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)', transition: 'all 0.2s ease-in-out' }} onMouseOver={e => e.currentTarget.style.background = '#0f172a'} onMouseOut={e => e.currentTarget.style.background = 'rgba(15, 23, 42, 0.85)'}>
                          <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                            <polyline points="7 10 12 15 17 10" />
                            <line x1="12" y1="15" x2="12" y2="3" />
                          </svg>
                          <span>Download Image</span>
                        </a>
                      </span>
                    )
                  }}
                >
                  {displayContent}
                </ReactMarkdown>
              </div>
            ) : isStreaming ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 0', color: '#0284c7', fontWeight: '700', fontSize: '14px' }}>
                <div style={{ width: '16px', height: '16px', borderRadius: '50%', border: '2.5px solid #0284c7', borderTopColor: 'transparent', animation: 'copetraSpin 0.8s linear infinite' }} />
                <span>Copetra AI is generating your response...</span>
                <style>{`@keyframes copetraSpin { to { transform: rotate(360deg); } }`}</style>
              </div>
            ) : (
              <div style={{ color: '#94a3b8', fontSize: '13px', fontStyle: 'italic', padding: '4px 0' }}>
                Response pending. Please resend your question.
              </div>
            )}{isStreaming && isAi && message.content && (
              <span className="cursor-blink" aria-hidden="true">▌</span>
            )}
          </>
        )}

        {/* 4 Action Buttons Bar on AI responses */}
        {isAi && message.content && !isStreaming && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '12px', position: 'relative' }}>
            <button
              onClick={handleCopy}
              title={copied ? 'Copied!' : 'Copy response'}
              style={{ background: 'none', border: 'none', color: copied ? '#10b981' : '#64748b', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center' }}
            >
              {copied ? (
                <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              ) : (
                <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                </svg>
              )}
            </button>

            <button
              onClick={handleGoodResponse}
              title="Good response"
              style={{ background: 'none', border: 'none', color: feedback === 'good' ? '#0284c7' : '#64748b', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center' }}
            >
              <svg width={16} height={16} viewBox="0 0 24 24" fill={feedback === 'good' ? '#0284c7' : 'none'} stroke="currentColor" strokeWidth={2}>
                <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
              </svg>
            </button>

            <button
              onClick={handleBadResponse}
              title="Bad response (Generate alternative)"
              style={{ background: 'none', border: 'none', color: feedback === 'bad' ? '#ef4444' : '#64748b', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center' }}
            >
              <svg width={16} height={16} viewBox="0 0 24 24" fill={feedback === 'bad' ? '#ef4444' : 'none'} stroke="currentColor" strokeWidth={2}>
                <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3" />
              </svg>
            </button>

            <button
              onClick={onRegenerate}
              title="Regenerate response"
              style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center' }}
            >
              <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <polyline points="23 4 23 10 17 10" />
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
              </svg>
            </button>

            <button
              onClick={() => setMoreMenuOpen(!moreMenuOpen)}
              title="More actions"
              style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center' }}
            >
              <svg width={16} height={16} viewBox="0 0 24 24" fill="currentColor">
                <circle cx="5" cy="12" r="2" />
                <circle cx="12" cy="12" r="2" />
                <circle cx="19" cy="12" r="2" />
              </svg>
            </button>

            {moreMenuOpen && (
              <div
                style={{
                  position: 'absolute',
                  bottom: '30px',
                  left: '120px',
                  background: '#ffffff',
                  borderRadius: '12px',
                  border: '1px solid #e2e8f0',
                  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.1)',
                  padding: '6px',
                  zIndex: 100,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                  minWidth: '160px'
                }}
              >
                <button
                  onClick={() => {
                    setMoreMenuOpen(false)
                    handleSpeak()
                  }}
                  style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', borderRadius: '8px', border: 'none', background: 'transparent', color: '#0f172a', fontSize: '13px', fontWeight: '500', cursor: 'pointer', textAlign: 'left' }}
                  onMouseOver={e => (e.currentTarget.style.background = '#f1f5f9')}
                  onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
                >
                  <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                    <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
                  </svg>
                  <span>{isSpeaking ? 'Stop reading' : 'Read aloud'}</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}