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
  category: 'image' | 'pdf' | 'word' | 'excel' | 'powerpoint' | 'text' | 'code'
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
      if (attachedFile.category === 'image') {
        text = `${text}\n\n[IMAGE: ${attachedFile.content}]`.trim()
      } else {
        const catName = attachedFile.category.toUpperCase()
        text = `${text}\n\n[${catName} DOCUMENT ATTACHED: ${attachedFile.name}]\n\`\`\`\n${attachedFile.content}\n\`\`\``.trim()
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
    const fileName = file.name.toLowerCase()
    const reader = new FileReader()

    // 1. IMAGE FILES (PNG, JPG, JPEG, WEBP, GIF)
    if (file.type.startsWith('image/')) {
      reader.onload = (e) => {
        const result = e.target?.result as string
        setAttachedFile({
          name: file.name,
          type: file.type,
          preview: result,
          content: result,
          category: 'image',
        })
      }
      reader.readAsDataURL(file)
      return
    }

    // 2. WORD DOCUMENTS (.docx, .doc)
    if (fileName.endsWith('.docx') || fileName.endsWith('.doc')) {
      reader.onload = (e) => {
        const buffer = e.target?.result as ArrayBuffer
        let textResult = ''
        try {
          const utf8Decoder = new TextDecoder('utf-8', { fatal: false })
          const latin1Decoder = new TextDecoder('latin1')
          const decodedUtf8 = utf8Decoder.decode(buffer)
          const decodedLatin1 = latin1Decoder.decode(buffer)

          // Extract text nodes from Word XML <w:t> tags
          const xmlMatches = decodedUtf8.match(/<w:t[^>]*>(.*?)<\/w:t>/g) || decodedLatin1.match(/<w:t[^>]*>(.*?)<\/w:t>/g)
          if (xmlMatches && xmlMatches.length > 0) {
            textResult = xmlMatches.map(m => m.replace(/<[^>]+>/g, '').trim()).filter(Boolean).join(' ')
          }

          if (!textResult || textResult.length < 20) {
            // Fallback: extract all printable ASCII word words
            const words = decodedLatin1.match(/[A-Za-z0-9.,?!'"()$%:\-]{2,}/g)
            if (words) {
              textResult = words.join(' ')
            }
          }
        } catch (err) {
          console.warn('[Word Document Extraction Fallback]', err)
        }

        setAttachedFile({
          name: file.name,
          type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
          content: textResult.slice(0, 6000) || `[Word Document '${file.name}' - ${Math.round(file.size / 1024)} KB attached]`,
          category: 'word',
        })
      }
      reader.readAsArrayBuffer(file)
      return
    }

    // 3. EXCEL SPREADSHEETS (.xlsx, .xls, .csv)
    if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls') || fileName.endsWith('.csv')) {
      if (fileName.endsWith('.csv')) {
        reader.onload = (e) => {
          const csvText = e.target?.result as string || ''
          setAttachedFile({
            name: file.name,
            type: 'text/csv',
            content: csvText.slice(0, 6000),
            category: 'excel',
          })
        }
        reader.readAsText(file)
        return
      }

      reader.onload = (e) => {
        const buffer = e.target?.result as ArrayBuffer
        let textResult = ''
        try {
          const latin1Decoder = new TextDecoder('latin1')
          const decoded = latin1Decoder.decode(buffer)
          const cellMatches = decoded.match(/<(?:v|t)[^>]*>(.*?)<\/(?:v|t)>/g)
          if (cellMatches && cellMatches.length > 0) {
            textResult = cellMatches.map(m => m.replace(/<[^>]+>/g, '').trim()).filter(Boolean).join(' | ')
          } else {
            const words = decoded.match(/[A-Za-z0-9.,?!'"()$%:\-]{2,}/g)
            if (words) textResult = words.join(' ')
          }
        } catch { }

        setAttachedFile({
          name: file.name,
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          content: textResult.slice(0, 6000) || `[Excel Spreadsheet '${file.name}' - ${Math.round(file.size / 1024)} KB attached]`,
          category: 'excel',
        })
      }
      reader.readAsArrayBuffer(file)
      return
    }

    // 4. POWERPOINT PRESENTATIONS (.pptx, .ppt)
    if (fileName.endsWith('.pptx') || fileName.endsWith('.ppt')) {
      reader.onload = (e) => {
        const buffer = e.target?.result as ArrayBuffer
        let textResult = ''
        try {
          const utf8Decoder = new TextDecoder('utf-8', { fatal: false })
          const latin1Decoder = new TextDecoder('latin1')
          const decoded = utf8Decoder.decode(buffer) || latin1Decoder.decode(buffer)
          const slideMatches = decoded.match(/<a:t[^>]*>(.*?)<\/a:t>/g)
          if (slideMatches) {
            textResult = slideMatches.map(m => m.replace(/<[^>]+>/g, '').trim()).filter(Boolean).join('\n')
          }
        } catch { }

        setAttachedFile({
          name: file.name,
          type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
          content: textResult.slice(0, 6000) || `[PowerPoint Presentation '${file.name}' - ${Math.round(file.size / 1024)} KB attached]`,
          category: 'powerpoint',
        })
      }
      reader.readAsArrayBuffer(file)
      return
    }

    // 5. PDF DOCUMENTS (.pdf)
    if (fileName.endsWith('.pdf')) {
      reader.onload = (e) => {
        const buffer = e.target?.result as ArrayBuffer
        let textResult = ''
        try {
          const latin1Decoder = new TextDecoder('latin1')
          const decoded = latin1Decoder.decode(buffer)
          // Extract text inside PDF parenthesis stream objects ( ... )
          const parenMatches = decoded.match(/\(([^()]{2,})\)/g)
          if (parenMatches && parenMatches.length > 0) {
            textResult = parenMatches
              .map(m => m.slice(1, -1).trim())
              .filter(t => t.length > 1 && !/^[0-9\/\\_]+$/.test(t))
              .join(' ')
          }

          if (!textResult || textResult.length < 30) {
            const words = decoded.match(/[A-Za-z0-9.,?!'"()$%:\-]{3,}/g)
            if (words) {
              textResult = words.filter(w => !w.startsWith('/') && !w.startsWith('obj') && !w.startsWith('endobj')).join(' ')
            }
          }
        } catch { }

        setAttachedFile({
          name: file.name,
          type: 'application/pdf',
          content: textResult.slice(0, 6000) || `[PDF Document '${file.name}' - ${Math.round(file.size / 1024)} KB attached]`,
          category: 'pdf',
        })
      }
      reader.readAsArrayBuffer(file)
      return
    }

    // 6. TEXT & CODE FILES (.txt, .md, .py, .js, .json, .html, .css, .sql)
    reader.onload = (e) => {
      let textResult = e.target?.result as string || ''
      if (typeof textResult !== 'string' || textResult.includes('\0')) {
        textResult = `[Attached File '${file.name}' - ${Math.round(file.size / 1024)} KB]`
      } else {
        textResult = textResult.slice(0, 18000)
      }

      const isCode = /\.(py|js|ts|tsx|jsx|html|css|json|sql|java|cpp|c|cs|go|rs|sh)$/i.test(fileName)

      setAttachedFile({
        name: file.name,
        type: file.type || 'text/plain',
        content: textResult,
        category: isCode ? 'code' : 'text',
      })
    }
    reader.readAsText(file)
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

  const getCategoryIcon = (cat: string) => {
    switch (cat) {
      case 'image': return '🖼️'
      case 'word': return '📄'
      case 'pdf': return '📕'
      case 'excel': return '📊'
      case 'powerpoint': return '📙'
      case 'code': return '💻'
      default: return '📝'
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
            <span>{getCategoryIcon(attachedFile.category)}</span>
          )}
          <span style={{ maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {attachedFile.name} ({attachedFile.category.toUpperCase()})
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
          accept=".pdf,.docx,.doc,.xlsx,.xls,.csv,.pptx,.ppt,.png,.jpg,.jpeg,.webp,.gif,.txt,.md,.json,.js,.py,.java,.cpp,.html,.css,.sql"
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
          title="Upload Image, Word, PDF, Excel or Code File for AI Analysis"
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
          placeholder={isStreaming ? "Copetra AI is analyzing document & generating..." : "Ask anything or attach Image, Word, PDF, Excel..."}
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