'use client'

import { useState } from 'react'
import { Message } from '@/types'
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

  const handleGoodResponse = () => {
    setFeedback(feedback === 'good' ? null : 'good')
  }

  const handleBadResponse = () => {
    setFeedback('bad')
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
      onEditAndResend(message.id, editText.trim())
    }
  }

  return (
    <div className={`msg-row ${isAi ? 'msg-ai' : 'msg-user'}`}>
      <div className={`bubble ${isAi ? 'bubble-ai' : 'bubble-user'}`} style={{ position: 'relative' }}>
        {!isAi && !isEditing && (
          <button
            onClick={() => {
              setEditText(message.content)
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
              <MarkdownRenderer content={message.content} isAi={isAi} />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 0', color: '#0284c7', fontWeight: '700', fontSize: '14px' }}>
                <div style={{ width: '16px', height: '16px', borderRadius: '50%', border: '2.5px solid #0284c7', borderTopColor: 'transparent', animation: 'copetraSpin 0.8s linear infinite' }} />
                <span>Copetra AI is generating your response...</span>
                <style>{`@keyframes copetraSpin { to { transform: rotate(360deg); } }`}</style>
              </div>
            )}{isStreaming && isAi && message.content && (
              <span className="cursor-blink" aria-hidden="true">▌</span>
            )}
          </>
        )}

        {/* 4 Action Buttons Bar on AI responses */}
        {isAi && message.content && !isStreaming && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '12px', position: 'relative' }}>
            {/* Button 1: Copy */}
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

            {/* Button 2: Good Response (Thumbs up) */}
            <button
              onClick={handleGoodResponse}
              title="Good response"
              style={{ background: 'none', border: 'none', color: feedback === 'good' ? '#0284c7' : '#64748b', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center' }}
            >
              <svg width={16} height={16} viewBox="0 0 24 24" fill={feedback === 'good' ? '#0284c7' : 'none'} stroke="currentColor" strokeWidth={2}>
                <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
              </svg>
            </button>

            {/* Button 3: Bad Response (Thumbs down -> triggers alternative response) */}
            <button
              onClick={handleBadResponse}
              title="Bad response (Generate alternative)"
              style={{ background: 'none', border: 'none', color: feedback === 'bad' ? '#ef4444' : '#64748b', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center' }}
            >
              <svg width={16} height={16} viewBox="0 0 24 24" fill={feedback === 'bad' ? '#ef4444' : 'none'} stroke="currentColor" strokeWidth={2}>
                <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3" />
              </svg>
            </button>

            {/* Button 4: Share / Export */}
            <button
              title="Share response"
              onClick={() => handleCopy()}
              style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center' }}
            >
              <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <circle cx="18" cy="5" r="3" />
                <circle cx="6" cy="12" r="3" />
                <circle cx="18" cy="19" r="3" />
                <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
                <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
              </svg>
            </button>

            {/* Button 5: Regenerate / Retry */}
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

            {/* Button 6: Three dots (...) for Read aloud */}
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

            {/* Read aloud popup modal matching screenshot */}
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


function cleanContent(content: string): string {
  return content
    .replace(/^#+\s*$/gm, '')
    .replace(/^code\s*$/gm, '')
    .replace(/^`{3}(\w*)\n/gm, '\n```$1\n')
    .replace(/```(\w+)/g, '\n```$1\n')
    .replace(/(?<!\w)```(?!\w)/g, '\n```\n')
    .replace(/##\s/g, '\n## ')
    .replace(/###\s/g, '\n### ')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/\[?(Error|Notice|System|Gemini|API key|Quota|Model|gemini-[\w.-]+)\]?/gi, '')
    .replace(/\(Note:[^)]*\)/gi, '')
    .trim()
}

function MarkdownRenderer({ content, isAi }: { content: string; isAi: boolean }) {
  const cleaned = cleanContent(content)
  const lines = cleaned.split('\n')
  const elements: React.ReactNode[] = []
  let i = 0

  while (i < lines.length) {
    const line = lines[i]

    // ── Code block ──
    if (line.trimStart().startsWith('```')) {
      const lang = line.trim().slice(3).trim() || 'code'
      const codeLines: string[] = []
      i++
      while (i < lines.length && !lines[i].trimStart().startsWith('```')) {
        codeLines.push(lines[i])
        i++
      }
      const rawCode = codeLines.join('\n')
      elements.push(
        <div key={`code-${i}`} style={{ margin: '14px 0', border: '1px solid #1e293b', borderRadius: '12px', overflow: 'hidden' }}>
          <div style={{
            background: '#0f172a',
            padding: '8px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #1e293b',
          }}>
            <span style={{
              fontSize: '11px',
              color: '#38bdf8',
              textTransform: 'uppercase',
              letterSpacing: '1px',
              fontWeight: '700',
              fontFamily: 'monospace'
            }}>{lang}</span>
            <button
              onClick={() => navigator.clipboard.writeText(rawCode)}
              style={{
                background: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                color: '#ffffff',
                fontSize: '11px',
                fontWeight: '600',
                padding: '4px 10px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontFamily: "Calibri, 'Calibri Light', sans-serif"
              }}
            >
              Copy code
            </button>
          </div>
          <pre style={{
            background: '#090d16',
            padding: '16px',
            overflowX: 'auto',
            margin: '0',
            fontSize: '13px',
            fontFamily: 'Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace',
            lineHeight: '1.7',
            color: '#f8fafc',
            whiteSpace: 'pre',
            userSelect: 'text'
          }}>
            <code style={{ fontFamily: 'Consolas, Monaco, monospace', color: '#38bdf8' }}>{rawCode}</code>
          </pre>
        </div>
      )
      i++
      continue
    }

    // ── H1 ──
    if (line.startsWith('# ') && !line.startsWith('## ')) {
      elements.push(
        <h1 key={`h1-${i}`} style={{
          fontSize: '18px',
          fontWeight: '800',
          margin: '16px 0 8px',
          color: '#000000',
          lineHeight: '1.4'
        }}>
          {renderInline(line.slice(2))}
        </h1>
      )
      i++
      continue
    }

    // ── H2 ──
    if (line.startsWith('## ') && !line.startsWith('### ')) {
      elements.push(
        <h2 key={`h2-${i}`} style={{
          fontSize: '16px',
          fontWeight: '700',
          margin: '16px 0 8px',
          color: '#000000',
          lineHeight: '1.4',
          paddingBottom: '4px',
          borderBottom: '1px solid #cbd5e1'
        }}>
          {renderInline(line.slice(3))}
        </h2>
      )
      i++
      continue
    }

    // ── H3 ──
    if (line.startsWith('### ')) {
      elements.push(
        <h3 key={`h3-${i}`} style={{
          fontSize: '14.5px',
          fontWeight: '700',
          margin: '12px 0 6px',
          color: '#000000'
        }}>
          {renderInline(line.slice(4))}
        </h3>
      )
      i++
      continue
    }

    // ── Bullet list ──
    if (
      line.startsWith('• ') ||
      line.startsWith('- ') ||
      line.startsWith('* ')
    ) {
      const listItems: string[] = []
      while (
        i < lines.length &&
        (lines[i].startsWith('• ') ||
          lines[i].startsWith('- ') ||
          lines[i].startsWith('* '))
      ) {
        listItems.push(lines[i].slice(2))
        i++
      }
      elements.push(
        <ul key={`ul-${i}`} style={{
          paddingLeft: '20px',
          margin: '6px 0 10px',
          listStyleType: 'disc'
        }}>
          {listItems.map((item, idx) => (
            <li key={idx} style={{
              marginBottom: '5px',
              fontSize: '14.5px',
              lineHeight: '1.65',
              color: '#000000'
            }}>
              {renderInline(item)}
            </li>
          ))}
        </ul>
      )
      continue
    }

    // ── Numbered list ──
    if (/^\d+\.\s/.test(line)) {
      const listItems: string[] = []
      while (i < lines.length && /^\d+\.\s/.test(lines[i])) {
        listItems.push(lines[i].replace(/^\d+\.\s/, ''))
        i++
      }
      elements.push(
        <ol key={`ol-${i}`} style={{
          paddingLeft: '22px',
          margin: '6px 0 10px'
        }}>
          {listItems.map((item, idx) => (
            <li key={idx} style={{
              marginBottom: '5px',
              fontSize: '14.5px',
              lineHeight: '1.65',
              color: '#000000'
            }}>
              {renderInline(item)}
            </li>
          ))}
        </ol>
      )
      continue
    }

    // ── Blockquote ──
    if (line.startsWith('> ')) {
      elements.push(
        <blockquote key={`bq-${i}`} style={{
          borderLeft: '3px solid #0284c7',
          paddingLeft: '12px',
          margin: '8px 0',
          color: '#000000',
          fontStyle: 'italic',
          fontSize: '14px'
        }}>
          {renderInline(line.slice(2))}
        </blockquote>
      )
      i++
      continue
    }

    // ── HR ──
    if (line.trim() === '---' || line.trim() === '***') {
      elements.push(
        <hr key={`hr-${i}`} style={{
          border: 'none',
          borderTop: '1px solid #cbd5e1',
          margin: '12px 0'
        }} />
      )
      i++
      continue
    }

    // ── Empty line ──
    if (line.trim() === '') {
      elements.push(
        <div key={`sp-${i}`} style={{ height: '6px' }} />
      )
      i++
      continue
    }

    // ── Normal paragraph ──
    elements.push(
      <p key={`p-${i}`} style={{
        marginBottom: '6px',
        lineHeight: '1.75',
        fontSize: '14.5px',
        color: '#000000'
      }}>
        {renderInline(line)}
      </p>
    )
    i++
  }

  return <div style={{ width: '100%' }}>{elements}</div>
}

function renderInline(text: string): React.ReactNode[] {
  const parts = text.split(/(!\[[^\]]*\]\([^)]+\)|\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*|~~[^~]+~~)/)
  return parts.map((part, i) => {
    if (part.startsWith('![') && part.includes('](') && part.endsWith(')')) {
      const altMatch = part.match(/^!\[([^\]]*)\]/)
      const urlMatch = part.match(/\(([^)]+)\)$/)
      const alt = altMatch ? altMatch[1] : 'Image'
      const url = urlMatch ? urlMatch[1] : ''
      return (
        <span key={i} style={{ display: 'inline-block', margin: '14px 0', position: 'relative', maxWidth: '512px', width: '100%' }}>
          <img
            src={url}
            alt={alt}
            style={{ width: '100%', maxWidth: '512px', height: 'auto', borderRadius: '16px', border: '1px solid #bae6fd', boxShadow: '0 8px 24px rgba(2, 132, 199, 0.12)', display: 'block' }}
          />
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            download="kronx_ai_image.png"
            style={{
              position: 'absolute',
              bottom: '12px',
              right: '12px',
              background: 'rgba(15, 23, 42, 0.85)',
              color: '#ffffff',
              padding: '6px 14px',
              borderRadius: '20px',
              fontSize: '12px',
              fontWeight: '700',
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backdropFilter: 'blur(8px)',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)',
              fontFamily: "Calibri, 'Calibri Light', sans-serif"
            }}
          >
            <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            <span>Download High Quality</span>
          </a>
        </span>
      )
    }
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} style={{ fontWeight: '600' }}>
          {part.slice(2, -2)}
        </strong>
      )
    }
    if (part.startsWith('~~') && part.endsWith('~~')) {
      return <del key={i}>{part.slice(2, -2)}</del>
    }
    if (
      part.startsWith('*') &&
      part.endsWith('*') &&
      part.length > 2
    ) {
      return <em key={i}>{part.slice(1, -1)}</em>
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code key={i} style={{
          background: 'rgba(124,110,247,0.12)',
          color: '#7c6ef7',
          padding: '2px 7px',
          borderRadius: '5px',
          fontFamily: 'monospace',
          fontSize: '12px'
        }}>
          {part.slice(1, -1)}
        </code>
      )
    }
    return <span key={i}>{part}</span>
  })
}

function TypingDots() {
  return (
    <span className="typing-dots" aria-label="Kronx anaandika">
      <span /><span /><span />
    </span>
  )
}

function TranslatingIndicator() {
  return (
    <span className="translating-indicator" aria-label="Inatafsiri">
      <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="#6366f1" strokeWidth={2} className="translating-globe">
        <circle cx="12" cy="12" r="10" />
        <line x1="2" y1="12" x2="22" y2="12" />
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
      </svg>
      <span className="translating-text">Inatafsiri...</span>
      <span /><span /><span />
    </span>
  )
}