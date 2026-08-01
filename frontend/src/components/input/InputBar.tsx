'use client'

import { useRef, useState, KeyboardEvent } from 'react'
import { useKronxStore } from '@/store/useKronxStore'

interface Props {
  onSend: (text: string) => void
}

export default function InputBar({ onSend }: Props) {
  const { isStreaming } = useKronxStore()
  const [value, setValue] = useState('')
  const [isListening, setIsListening] = useState(false)
  const taRef = useRef<HTMLTextAreaElement>(null)
  const recognitionRef = useRef<any>(null)

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
    ta.style.height = Math.min(ta.scrollHeight, 120) + 'px'
  }

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop()
      setIsListening(false)
      return
    }

    const windowObj = typeof window !== 'undefined' ? (window as any) : {}
    const SpeechRecognition = windowObj.SpeechRecognition || windowObj.webkitSpeechRecognition

    if (!SpeechRecognition) {
      alert('Speech Recognition is not supported by your browser. Please use Chrome or Edge.')
      return
    }

    try {
      const rec = new SpeechRecognition()
      rec.lang = 'en-US'
      rec.continuous = false
      rec.interimResults = true

      rec.onstart = () => setIsListening(true)
      rec.onresult = (event: any) => {
        let transcript = ''
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript
        }
        if (transcript) {
          setValue(transcript)
        }
      }
      rec.onerror = (err: any) => {
        console.warn('[Speech recognition error]', err)
        setIsListening(false)
      }
      rec.onend = () => setIsListening(false)

      recognitionRef.current = rec
      rec.start()
    } catch (e) {
      console.error('[Speech recognition fail]', e)
      setIsListening(false)
    }
  }

  return (
    <div style={{ width: '100%', maxWidth: '760px', margin: '0 auto 28px auto', padding: '0 16px' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: '28px',
          padding: '8px 14px 8px 18px',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.04)',
          gap: '12px'
        }}
      >
        {/* Plus '+' icon button on left -> File Upload */}
        <input
          id="file-upload-input"
          type="file"
          style={{ display: 'none' }}
          onChange={e => {
            const file = e.target.files?.[0]
            if (file) {
              setValue(prev => (prev ? prev + ` [Attached file: ${file.name}]` : `Analyze file: ${file.name}`))
            }
          }}
        />
        <button
          onClick={() => document.getElementById('file-upload-input')?.click()}
          style={{
            background: 'none',
            border: 'none',
            color: '#64748b',
            cursor: 'pointer',
            padding: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          title="Upload document or file"
        >
          <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
        </button>

        {/* Ask anything text area */}
        <textarea
          ref={taRef}
          value={value}
          rows={1}
          placeholder={isStreaming ? "Kronx is generating response..." : "Ask anything"}
          onChange={e => setValue(e.target.value)}
          onInput={handleInput}
          onKeyDown={handleKey}
          style={{
            flex: 1,
            border: 'none',
            outline: 'none',
            resize: 'none',
            background: 'transparent',
            fontSize: '16px',
            color: '#0f172a',
            fontFamily: "Calibri, 'Calibri Light', sans-serif",
            padding: '6px 0',
            lineHeight: '1.4'
          }}
        />

        {/* Right Tools (Microphone & Voice Wave pill) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Microphone icon */}
          <button
            onClick={toggleListening}
            style={{
              background: 'none',
              border: 'none',
              color: isListening ? '#ef4444' : '#64748b',
              cursor: 'pointer',
              padding: '4px',
              display: 'flex',
              alignItems: 'center'
            }}
            title="Voice input"
          >
            <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 6 0V4a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8" />
            </svg>
          </button>

          {/* Voice Wave pill / Send button */}
          <button
            onClick={handleSend}
            disabled={!value.trim() && !isStreaming}
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              background: value.trim() ? '#0f172a' : '#000000',
              color: '#ffffff',
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: value.trim() ? 'pointer' : 'default'
            }}
          >
            {value.trim() ? (
              <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
                <line x1="12" y1="19" x2="12" y2="5" />
                <polyline points="5 12 12 5 19 12" />
              </svg>
            ) : (
              <svg width={16} height={16} viewBox="0 0 24 24" fill="currentColor">
                <rect x="5" y="6" width="2" height="12" rx="1" />
                <rect x="9" y="3" width="2" height="18" rx="1" />
                <rect x="13" y="8" width="2" height="8" rx="1" />
                <rect x="17" y="5" width="2" height="14" rx="1" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Powered by PJ COPETRANOVA attribution footer */}
      <div style={{ textAlign: 'center', marginTop: '10px', fontSize: '11px', fontWeight: '700', color: '#64748b', letterSpacing: '1px', fontFamily: "Calibri, 'Calibri Light', sans-serif" }}>
        POWERED BY <span style={{ color: '#0284c7', fontWeight: '800' }}>PJ COPETRANOVA</span>
      </div>
    </div>
  )
}