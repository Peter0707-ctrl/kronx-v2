'use client'

import { Message } from '@/types'

interface Props {
  message: Message
  isStreaming?: boolean
}

export default function MessageBubble({ message, isStreaming }: Props) {
  const isAi = message.role === 'ai'

  return (
    <div className={`msg-row ${isAi ? 'msg-ai' : 'msg-user'}`}>
      <div className="msg-meta">
        {isAi ? (
          <>
            <div className="msg-av av-ai">K</div>
            <span className="msg-who">Kronx</span>
          </>
        ) : (
          <>
            <span className="msg-who">Wewe · You</span>
            <div className="msg-av av-user">U</div>
          </>
        )}
      </div>

      <div className={`bubble ${isAi ? 'bubble-ai' : 'bubble-user'}`}>
        {message.content ? (
          <MarkdownRenderer content={message.content} isAi={isAi} />
        ) : isStreaming && isAi ? (
          <TypingDots />
        ) : null}
        {isStreaming && isAi && message.content && (
          <span className="cursor-blink" aria-hidden="true">▌</span>
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
      elements.push(
        <div key={`code-${i}`} style={{ margin: '12px 0' }}>
          <div style={{
            background: '#0d0d14',
            borderRadius: '10px 10px 0 0',
            padding: '6px 14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '0.5px solid #252530',
          }}>
            <span style={{
              fontSize: '10px',
              color: '#7c6ef7',
              textTransform: 'uppercase',
              letterSpacing: '1px',
              fontFamily: 'monospace'
            }}>{lang}</span>
          </div>
          <pre style={{
            background: '#0d0d14',
            borderRadius: '0 0 10px 10px',
            padding: '14px 16px',
            overflowX: 'auto',
            margin: '0',
            fontSize: '12.5px',
            fontFamily: 'JetBrains Mono, Fira Mono, Consolas, monospace',
            lineHeight: '1.7',
            color: '#e8e4ff',
            whiteSpace: 'pre',
          }}>
            <code>{codeLines.join('\n')}</code>
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
          fontSize: '17px',
          fontWeight: '700',
          margin: '16px 0 8px',
          color: isAi ? '#1a1a2e' : '#fff',
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
          fontSize: '15px',
          fontWeight: '600',
          margin: '16px 0 8px',
          color: isAi ? '#1a1a2e' : '#fff',
          lineHeight: '1.4',
          paddingBottom: '4px',
          borderBottom: isAi
            ? '0.5px solid #e4e4ec'
            : '0.5px solid rgba(255,255,255,0.1)'
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
          fontSize: '13.5px',
          fontWeight: '600',
          margin: '12px 0 6px',
          color: isAi ? '#1a1a2e' : '#e8e4ff'
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
              fontSize: '13.5px',
              lineHeight: '1.65',
              color: isAi ? '#1a1a2e' : '#e8e4ff'
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
              fontSize: '13.5px',
              lineHeight: '1.65',
              color: isAi ? '#1a1a2e' : '#e8e4ff'
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
          borderLeft: '3px solid #7c6ef7',
          paddingLeft: '12px',
          margin: '8px 0',
          color: isAi ? '#7a7a96' : '#c5bcff',
          fontStyle: 'italic',
          fontSize: '13px'
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
          borderTop: isAi
            ? '0.5px solid #e4e4ec'
            : '0.5px solid rgba(255,255,255,0.1)',
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
        fontSize: '13.5px',
        color: isAi ? '#1a1a2e' : '#e8e4ff'
      }}>
        {renderInline(line)}
      </p>
    )
    i++
  }

  return <div style={{ width: '100%' }}>{elements}</div>
}

function renderInline(text: string): React.ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*|~~[^~]+~~)/)
  return parts.map((part, i) => {
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