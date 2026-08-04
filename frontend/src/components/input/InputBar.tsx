'use client'

import { useRef, useState, KeyboardEvent } from 'react'
import { useKronxStore } from '@/store/useKronxStore'

interface Props {
  onSend: (text: string) => void
}

interface AttachedFile {
  name: string
  type: string
  preview?: string
  content: string
}

export default function InputBar({ onSend }: Props) {
  const { isStreaming } = useKronxStore()
  const [value, setValue] = useState('')
  const [attachedFile, setAttachedFile] = useState<AttachedFile | null>(null)
  const [isListening, setIsListening] = useState(false)
  const taRef = useRef<HTMLTextAreaElement>(null)
  const recognitionRef = useRef<any>(null)

  const handleSend = () => {
    let text = value.trim()
    if (attachedFile) {
      if (attachedFile.type.startsWith('image/')) {
        text = `${text}\n\n[IMAGE: ${attachedFile.content}]`.trim()
      } else {
        text = `${text}\n\n[FILE ATTACHED: ${attachedFile.name}]\n\`\`\`\n${attachedFile.content}\n\`\`\``.trim()
      }
    }

    if (!text || isStreaming) return
    setValue('')
    setAttachedFile(null)
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

  const handleFileUpload = (file: File) => {
    const reader = new FileReader()

    if (file.type.startsWith('image/')) {
      reader.onload = (e) => {
        const result = e.target?.result as string
        setAttachedFile({
          name: file.name,
          type: file.type,
          preview: result,
          content: result,
        })
      }
      reader.readAsDataURL(file)
    } else {
      reader.onload = (e) => {
        let textResult = e.target?.result as string || ''
        // If binary file content, sanitize or provide summary
        if (typeof textResult !== 'string' || textResult.includes('\0')) {
          textResult = `[Binary Document '${file.name}' - ${Math.round(file.size / 1024)} KB]`
        } else {
          textResult = textResult.slice(0, 12000)
        }
        setAttachedFile({
          name: file.name,
          type: file.type || 'text/plain',
          content: textResult,
        })
      }
      reader.readAsText(file)
    }
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
      {/* Attached File Preview Badge */}
      {attachedFile && (
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(37, 99, 235, 0.08)',
            border: '1px solid rgba(37, 99, 235, 0.2)',
            borderRadius: '16px',
            padding: '6px 12px',
            marginBottom: '8px',
            fontSize: '13px',
            color: '#1e40af',
            fontWeight: 500,
          }}
        >
          {attachedFile.preview ? (
            <img
              src={attachedFile.preview}
              alt="Uploaded file preview"
              style={{ width: '24px', height: '24px', borderRadius: '4px', objectFit: 'cover' }}
            />
          ) : (
            <span>📄</span>
          )}
          <span style={{ maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {attachedFile.name}
          </span>
          <button
            onClick={() => setAttachedFile(null)}
            style={{
              background: 'none',
              border: 'none',
              color: '#1e40af',
              cursor: 'pointer',
              fontWeight: 'bold',
              padding: '0 4px',
              fontSize: '14px',
            }}
            title="Remove attachment"
          >
            ✕
          </button>
        </div>
      )}

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: '28px',
          padding: '8px 14px 8px 18px',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.04)',
          gap: '12px',
        }}
      >
        {/* Plus '+' icon button on left -> File Upload */}
        <input
          id="file-upload-input"
          type="file"
          style={{ display: 'none' }}
          accept=".pdf,.docx,.xlsx,.pptx,.png,.jpg,.jpeg,.webp,.gif,.txt,.md,.json,.csv,.js,.py,.java,.cpp,.html,.css,.sql"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleFileUpload(file)
            e.target.value = ''
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
            justifyContent: 'center',
          }}
          title="Upload Image, Document or Code File for AI Analysis"
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
          placeholder={isStreaming ? "Copetra AI is analyzing & generating..." : "Ask anything or attach files/images..."}
          onChange={(e) => setValue(e.target.value)}
          onInput={handleInput}
          onKeyDown={handleKey}
          onFocus={() => window.dispatchEvent(new Event('hide-suggestions'))}
          onClick={() => window.dispatchEvent(new Event('hide-suggestions'))}
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
            lineHeight: '1.4',
          }}
        />

        {/* Right Tools (Microphone & Voice Wave pill) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Microphone icon */}
          <button
            onClick={toggleListening}
            style={{
              background: isListening ? '#ef4444' : 'none',
              border: 'none',
              color: isListening ? '#ffffff' : '#64748b',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s ease',
            }}
            title={isListening ? "Listening... Click to stop" : "Voice Dictation"}
          >
            <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="23" />
              <line x1="8" y1="23" x2="16" y2="23" />
            </svg>
          </button>

          {/* Send Button */}
          <button
            onClick={handleSend}
            disabled={(!value.trim() && !attachedFile) || isStreaming}
            style={{
              background: (!value.trim() && !attachedFile) || isStreaming ? '#cbd5e1' : '#2563eb',
              color: '#ffffff',
              border: 'none',
              borderRadius: '50%',
              width: '34px',
              height: '34px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: (!value.trim() && !attachedFile) || isStreaming ? 'not-allowed' : 'pointer',
              transition: 'background 0.2s ease',
            }}
            title="Send to Copetra AI"
          >
            <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}