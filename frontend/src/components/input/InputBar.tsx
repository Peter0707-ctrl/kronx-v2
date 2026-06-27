'use client'

import { useRef, useState, KeyboardEvent } from 'react'
import { useKronxStore } from '@/store/useKronxStore'
import { PLACEHOLDER } from '@/lib/constants'

interface Props {
  onSend: (text: string) => void
}

export default function InputBar({ onSend }: Props) {
  const { language, setLanguage, isStreaming } = useKronxStore()
  const [value, setValue] = useState('')
  const taRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    const text = value.trim()
    if (!text || isStreaming) return
    setValue('')
    if (taRef.current) {
      taRef.current.style.height = 'auto'
    }
    onSend(text)
  }

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = () => {
    const ta = taRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 96) + 'px'
  }

  return (
    <div className="input-wrap">
      {/* Language toggle */}
      <div className="lang-row">
        <button
          className={`lang-pill ${language === 'sw' ? 'lang-on' : ''}`}
          onClick={() => setLanguage('sw')}
          aria-pressed={language === 'sw'}
        >
          🇹🇿 Kiswahili
        </button>
        <div className="lang-sep" aria-hidden="true" />
        <button
          className={`lang-pill ${language === 'en' ? 'lang-on' : ''}`}
          onClick={() => setLanguage('en')}
          aria-pressed={language === 'en'}
        >
          🇬🇧 English
        </button>
        <span className="input-hint" aria-hidden="true">
          Shift+Enter · mstari mpya / new line
        </span>
      </div>

      {/* Input row */}
      <div className={`input-row ${isStreaming ? 'input-row--busy' : ''}`}>
        <textarea
          ref={taRef}
          className="chat-ta"
          value={value}
          rows={1}
          placeholder={PLACEHOLDER[language]}
          onChange={e => setValue(e.target.value)}
          onInput={handleInput}
          onKeyDown={handleKey}
          disabled={isStreaming}
          aria-label="Andika ujumbe · Type your message"
        />
        <div className="input-tools">
          <button className="tool-btn" title="Faili · Attach file" aria-label="Attach file">
            <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
            </svg>
          </button>
          <button className="tool-btn" title="Sauti · Voice input" aria-label="Voice input">
            <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8" />
            </svg>
          </button>
          <button
            className="send-btn"
            onClick={handleSend}
            disabled={!value.trim() || isStreaming}
            title="Tuma · Send"
            aria-label="Send message"
          >
            {isStreaming ? (
              <span className="send-spinner" aria-hidden="true" />
            ) : (
              <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={2.2}>
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}