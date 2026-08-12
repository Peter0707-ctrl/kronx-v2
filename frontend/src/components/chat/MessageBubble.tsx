'use client'

import { memo, useState } from 'react'
import { Message } from '@/types'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import JSZip from 'jszip'
import { useKronxStore } from '@/store/useKronxStore'

function getExtensionForLang(lang?: string): string {
  const l = (lang || '').toLowerCase()
  switch (l) {
    case 'html': case 'htm': return 'html'
    case 'css': return 'css'
    case 'javascript': case 'js': return 'js'
    case 'typescript': case 'ts': return 'ts'
    case 'jsx': return 'jsx'
    case 'tsx': return 'tsx'
    case 'python': case 'py': return 'py'
    case 'json': return 'json'
    case 'sql': return 'sql'
    case 'sh': case 'bash': return 'sh'
    case 'markdown': case 'md': return 'md'
    case 'svg': return 'svg'
    case 'xml': return 'xml'
    case 'java': return 'java'
    case 'c': return 'c'
    case 'cpp': case 'c++': return 'cpp'
    case 'go': return 'go'
    case 'rust': case 'rs': return 'rs'
    case 'php': return 'php'
    default: return 'txt'
  }
}

function downloadCodeFile(code: string, language: string, customFilename?: string) {
  const ext = getExtensionForLang(language)
  const name = customFilename || `copetra-code-${Date.now()}.${ext}`
  const blob = new Blob([code], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

async function downloadCodeAsZip(code: string, language: string, customFilename?: string) {
  const zip = new JSZip()
  const ext = getExtensionForLang(language)
  const fileName = customFilename || `index.${ext}`
  zip.file(fileName, code)
  zip.file('README.md', `# Exported from Copetra AI\n\nFile: ${fileName}\nLanguage: ${language}\nDate: ${new Date().toLocaleString()}\nPowered by PJ COPETRANOVA`)
  const zipBlob = await zip.generateAsync({ type: 'blob' })
  const url = URL.createObjectURL(zipBlob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${fileName.replace(/\.[^/.]+$/, '')}.zip`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

async function downloadAllCodeAsProjectZip(markdownContent: string, projectTitle: string = 'copetra-project') {
  const zip = new JSZip()
  const codeBlockRegex = /```(\w+)?(?:\s+([^\n]+))?\n([\s\S]*?)```/g
  let match
  let fileIndex = 1
  const usedNames = new Set<string>()

  while ((match = codeBlockRegex.exec(markdownContent)) !== null) {
    const rawLang = (match[1] || '').trim().toLowerCase()
    const headerInfo = (match[2] || '').trim()
    const codeContent = match[3] || ''

    let filename = ''
    if (headerInfo && headerInfo.includes('.')) {
      filename = headerInfo
    } else {
      const ext = getExtensionForLang(rawLang)
      if (ext === 'html' && !usedNames.has('index.html')) filename = 'index.html'
      else if (ext === 'css' && !usedNames.has('style.css')) filename = 'style.css'
      else if (ext === 'js' && !usedNames.has('app.js')) filename = 'app.js'
      else if (ext === 'py' && !usedNames.has('main.py')) filename = 'main.py'
      else filename = `code_${fileIndex}.${ext}`
    }

    if (usedNames.has(filename)) {
      filename = `file_${fileIndex}_${filename}`
    }
    usedNames.add(filename)
    zip.file(filename, codeContent)
    fileIndex++
  }

  if (!usedNames.has('README.md')) {
    zip.file('README.md', `# Copetra AI Project Export\n\nExported on: ${new Date().toLocaleString()}\nTotal Generated Files: ${fileIndex - 1}\n\nPowered by PJ COPETRANOVA`)
  }

  const zipBlob = await zip.generateAsync({ type: 'blob' })
  const url = URL.createObjectURL(zipBlob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${projectTitle.toLowerCase().replace(/[^a-z0-9]/g, '-')}.zip`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function CodeBlockRunner({ language, code, children, props }: any) {
  const [output, setOutput] = useState<string | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [activeTab, setActiveTab] = useState<'code' | 'preview'>('code')
  const [copied, setCopied] = useState(false)
  const [iframeKey, setIframeKey] = useState(0)

  const lang = (language || '').toLowerCase()
  const isHtmlPreviewable = ['html', 'htm', 'svg', 'xml'].includes(lang) || code.includes('<!DOCTYPE html>') || code.includes('<html') || code.includes('<svg')
  const isRunnable = ['javascript', 'js', 'python', 'py'].includes(lang)

  const handleCopy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleRun = () => {
    setIsRunning(true)
    setOutput(null)
    setTimeout(() => {
      try {
        if (lang === 'javascript' || lang === 'js') {
          const logs: string[] = []
          const originalLog = console.log
          console.log = (...args) => {
            logs.push(args.map(x => typeof x === 'object' ? JSON.stringify(x) : String(x)).join(' '))
          }
          
          const result = new Function(code)()
          console.log = originalLog
          
          let display = ''
          if (logs.length > 0) display += logs.join('\n')
          if (result !== undefined) display += (display ? '\nReturn: ' : '') + String(result)
          setOutput(display || 'Code executed successfully with no output.')
        } else {
          setOutput(`[Running ${language} code...]\nSuccess: Executed mock ${language} environment successfully!`)
        }
      } catch (err: any) {
        setOutput(`Error: ${err.message}`)
      } finally {
        setIsRunning(false)
      }
    }, 300)
  }

  const handlePopout = () => {
    const blob = new Blob([code], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
  }

  return (
    <div style={{ margin: '16px 0', border: '1px solid #1e293b', borderRadius: '14px', overflow: 'hidden', boxShadow: '0 4px 16px rgba(0,0,0,0.1)' }}>
      {/* Code Header Bar */}
      <div style={{ background: '#0f172a', padding: '8px 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #1e293b', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '11px', color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: '800', fontFamily: 'monospace' }}>
            {language || 'code'}
          </span>
          {isHtmlPreviewable && (
            <div style={{ display: 'inline-flex', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '8px', padding: '2px' }}>
              <button
                onClick={() => setActiveTab('code')}
                style={{
                  background: activeTab === 'code' ? '#0284c7' : 'transparent',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '3px 9px',
                  fontSize: '11px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  transition: 'all 0.15s'
                }}
              >
                &lt;/&gt; Code
              </button>
              <button
                onClick={() => setActiveTab('preview')}
                style={{
                  background: activeTab === 'preview' ? '#10b981' : 'transparent',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '3px 9px',
                  fontSize: '11px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  transition: 'all 0.15s'
                }}
              >
                👁️ Live Preview
              </button>
            </div>
          )}
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
          {isHtmlPreviewable && activeTab === 'preview' && (
            <>
              <button
                onClick={() => setIframeKey(k => k + 1)}
                title="Reload Preview"
                style={{ background: 'rgba(255, 255, 255, 0.1)', border: '1px solid rgba(255, 255, 255, 0.2)', color: '#ffffff', fontSize: '11px', fontWeight: '600', padding: '4px 8px', borderRadius: '6px', cursor: 'pointer' }}
              >
                🔄 Refresh
              </button>
              <button
                onClick={handlePopout}
                title="Open Preview in Fullscreen Tab"
                style={{ background: 'rgba(56, 189, 248, 0.2)', border: '1px solid rgba(56, 189, 248, 0.4)', color: '#38bdf8', fontSize: '11px', fontWeight: '700', padding: '4px 9px', borderRadius: '6px', cursor: 'pointer' }}
              >
                ⤢ Popout
              </button>
            </>
          )}

          {isRunnable && activeTab === 'code' && (
            <button
              onClick={handleRun}
              disabled={isRunning}
              style={{ background: '#7c6ef7', border: 'none', color: '#ffffff', fontSize: '11px', fontWeight: '700', padding: '4px 10px', borderRadius: '6px', cursor: 'pointer' }}
            >
              {isRunning ? 'Running...' : '▶ Run'}
            </button>
          )}

          <button
            onClick={() => downloadCodeFile(code, language)}
            title="Download Code File"
            style={{ background: 'rgba(255, 255, 255, 0.1)', border: '1px solid rgba(255, 255, 255, 0.2)', color: '#ffffff', fontSize: '11px', fontWeight: '600', padding: '4px 9px', borderRadius: '6px', cursor: 'pointer' }}
          >
            📥 Download
          </button>

          <button
            onClick={() => downloadCodeAsZip(code, language)}
            title="Download as ZIP Archive"
            style={{ background: 'rgba(16, 185, 129, 0.2)', border: '1px solid rgba(16, 185, 129, 0.4)', color: '#34d399', fontSize: '11px', fontWeight: '700', padding: '4px 9px', borderRadius: '6px', cursor: 'pointer' }}
          >
            📦 ZIP
          </button>

          <button
            onClick={handleCopy}
            style={{ background: copied ? '#10b981' : 'rgba(255, 255, 255, 0.1)', border: '1px solid rgba(255, 255, 255, 0.2)', color: '#ffffff', fontSize: '11px', fontWeight: '600', padding: '4px 9px', borderRadius: '6px', cursor: 'pointer' }}
          >
            {copied ? '✓ Copied' : 'Copy'}
          </button>
        </div>
      </div>

      {/* Code View vs Live Preview Content */}
      {isHtmlPreviewable && activeTab === 'preview' ? (
        <div style={{ background: '#ffffff', width: '100%', minHeight: '340px', position: 'relative' }}>
          <iframe
            key={iframeKey}
            srcDoc={code}
            title="Live HTML Sandbox Preview"
            sandbox="allow-scripts allow-modals allow-same-origin"
            style={{
              width: '100%',
              minHeight: '340px',
              height: '420px',
              border: 'none',
              display: 'block',
              background: '#ffffff'
            }}
          />
        </div>
      ) : (
        <pre style={{ background: '#090d16', padding: '16px', overflowX: 'auto', margin: '0', fontSize: '13px', fontFamily: 'Consolas, Monaco, monospace', color: '#f8fafc' }}>
          <code style={{ color: '#38bdf8' }} {...props}>{children}</code>
        </pre>
      )}

      {output && (
        <div style={{ background: '#0d1117', borderTop: '1px solid #1e293b', padding: '12px 16px', fontSize: '12px', fontFamily: 'monospace', color: '#34d399', whiteSpace: 'pre-wrap' }}>
          <strong style={{ color: '#94a3b8', display: 'block', marginBottom: '4px', fontSize: '11px', textTransform: 'uppercase' }}>Console Output:</strong>
          {output}
        </div>
      )}
    </div>
  )
}

interface Props {
  message: Message
  isStreaming?: boolean
  onRegenerate?: () => void
  onEditAndResend?: (messageId: string, newContent: string) => void
}

const MessageBubble = memo(function MessageBubble({ message, isStreaming, onRegenerate, onEditAndResend }: Props) {
  const isAi = message.role === 'ai'
  const [copied, setCopied] = useState(false)
  const [feedback, setFeedback] = useState<'good' | 'bad' | null>(null)
  const [moreMenuOpen, setMoreMenuOpen] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editText, setEditText] = useState(message.content)
  const [previewModalImg, setPreviewModalImg] = useState<string | null>(null)

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const markdownToHtml = (md: string): string => {
    if (!md) return ''
    return md
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/^\s*-\s+(.*$)/gim, '<ul><li>$1</li></ul>')
      .replace(/<\/ul>\s*<ul>/g, '')
      .replace(/```([\s\S]+?)```/g, '<pre>$1</pre>')
      .replace(/\|(.+?)\|/g, (match) => {
        if (/^\|[ :-|]+?\|$/.test(match)) return ''
        const cells = match.split('|').slice(1, -1).map(c => c.trim())
        return `<tr>${cells.map(c => `<td>${c}</td>`).join('')}</tr>`
      })
      .replace(/(<tr>[\s\S]+?<\/tr>)/g, '<table>$1</table>')
      .replace(/<\/table>\s*<table>/g, '')
      .replace(/\n/g, '<br/>')
  }

  const handleExportDocx = () => {
    const htmlContent = `
      <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
      <head>
        <title>Copetra AI Export</title>
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }
          h1, h2, h3 { color: #0284c7; margin-top: 18px; margin-bottom: 8px; }
          strong { color: #0f172a; }
          pre { background-color: #f1f5f9; padding: 12px; border-radius: 6px; font-family: Courier New, Courier, monospace; }
          table { border-collapse: collapse; width: 100%; margin: 15px 0; }
          th, td { border: 1px solid #cbd5e1; padding: 8px; text-align: left; }
          th { background-color: #f8fafc; font-weight: bold; }
        </style>
      </head>
      <body>
        <div style="border-bottom: 2px solid #0284c7; padding-bottom: 10px; margin-bottom: 20px;">
          <h2 style="margin: 0; color: #0284c7;">Copetra AI - Deep Research Report</h2>
          <p style="margin: 4px 0 0 0; color: #64748b; font-size: 12px;">Exported on ${new Date().toLocaleString()}</p>
        </div>
        ${markdownToHtml(message.content)}
      </body>
      </html>
    `
    const blob = new Blob(['\ufeff' + htmlContent], { type: 'application/msword' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `copetra_export_${Date.now()}.doc`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleExportPdf = () => {
    const printWindow = window.open('', '_blank')
    if (!printWindow) return
    printWindow.document.write(`
      <html>
      <head>
        <title>Copetra AI - Deep Research Export</title>
        <style>
          body { font-family: system-ui, -apple-system, sans-serif; padding: 40px; color: #0f172a; line-height: 1.6; }
          h1, h2, h3 { color: #0284c7; margin-top: 24px; }
          pre { background: #f1f5f9; padding: 14px; border-radius: 8px; font-family: monospace; overflow-x: auto; white-space: pre-wrap; }
          table { border-collapse: collapse; width: 100%; margin: 20px 0; }
          th, td { border: 1px solid #cbd5e1; padding: 10px; text-align: left; }
          th { background: #f8fafc; font-weight: bold; }
          ul, ol { padding-left: 20px; }
          li { margin-bottom: 6px; }
          @media print {
            body { padding: 0; }
            button { display: none; }
          }
        </style>
      </head>
      <body>
        <div style="margin-bottom: 24px; border-bottom: 2.5px solid #0284c7; padding-bottom: 12px; display: flex; justify-content: space-between; align-items: flex-end;">
          <div>
            <span style="font-weight: 900; color: #0284c7; font-size: 22px; letter-spacing: 0.5px;">PJ COPETRANOVA</span>
            <div style="color: #64748b; font-size: 12px; margin-top: 4px;">Copetra AI Deep Research Document</div>
          </div>
          <span style="color: #64748b; font-size: 12px;">Exported: ${new Date().toLocaleDateString()}</span>
        </div>
        ${markdownToHtml(message.content)}
      </body>
      </html>
    `)
    printWindow.document.close()
    printWindow.focus()
    setTimeout(() => {
      printWindow.print()
      printWindow.close()
    }, 600)
  }

  const handleExportExcel = () => {
    const tableRegex = /\|[\s\S]+?\|\r?\n\|[ :-|]+?\|\r?\n(\|[\s\S]+?\|\r?\n)*/g
    const tables = message.content.match(tableRegex)
    
    if (!tables || tables.length === 0) {
      alert('No tabular data found in this message to export to Excel.')
      return
    }

    const lines = tables[0].trim().split('\n')
    const csvRows = lines
      .map(line => {
        const cols = line.split('|').map(c => c.trim()).filter((_, idx, arr) => idx > 0 && idx < arr.length - 1)
        return cols.map(c => `"${c.replace(/"/g, '""')}"`).join(',')
      })
      .filter(row => !row.includes('---') && row.trim().length > 0)

    const csvContent = csvRows.join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `copetra_excel_export_${Date.now()}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const getCleanUserQuery = (content: string): string => {
    const docIdx = content.indexOf('\n\n[')
    if (docIdx !== -1) return content.substring(0, docIdx).trim()
    const imgIdx = content.indexOf('\n\n[IMAGE:')
    if (imgIdx !== -1) return content.substring(0, imgIdx).trim()
    return content.trim()
  }

  const handleGoodResponse = () => {
    const isLiking = feedback !== 'good'
    setFeedback(isLiking ? 'good' : null)
    if (isLiking) {
      const currentState = useKronxStore.getState()
      const msgs = currentState.activeMessages()
      const aiIdx = msgs.findIndex(m => m.id === message.id)
      if (aiIdx > 0 && msgs[aiIdx - 1].role === 'user') {
        const userQuery = getCleanUserQuery(msgs[aiIdx - 1].content)
        const goodSnippet = message.content.slice(0, 120).replace(/\n/g, ' ')
        const memoryItem = `User highly approved response to "${userQuery}". Preferred format starts like: "${goodSnippet}...". Prioritize this thorough and clear style of answer.`
        currentState.addMemory(memoryItem)
      }
    }
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
    const currentState = useKronxStore.getState()
    utterance.lang = currentState.language === 'sw' ? 'sw-TZ' : 'en-US'
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

  // Extract attached images & documents from user message
  const attachedImages: string[] = []
  const attachedDocs: string[] = []

  let displayContent = message.content.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
  
  if (!isAi) {
    const imageRegex = /\[IMAGE:\s*(data:image\/[a-zA-Z]+;base64,[^\]]+)\]/g
    let imgMatch
    while ((imgMatch = imageRegex.exec(message.content)) !== null) {
      attachedImages.push(imgMatch[1])
    }

    const docRegex = /\[(WORD|PDF|EXCEL|POWERPOINT|TEXT|CODE)\s+DOCUMENT ATTACHED:\s*([^\]]+)\]/gi
    let docMatch
    while ((docMatch = docRegex.exec(message.content)) !== null) {
      attachedDocs.push(`${docMatch[1]}: ${docMatch[2]}`)
    }

    displayContent = displayContent
      .replace(/\[IMAGE:\s*data:image\/[a-zA-Z]+;base64,[^\]]+\]/g, '')
      .replace(/\[(WORD|PDF|EXCEL|POWERPOINT|TEXT|CODE)\s+DOCUMENT ATTACHED:\s*([^\]]+)\][\s\S]*/gi, '')
      .trim()
  }

  // Check if AI response has multiple/any code blocks for project ZIP download
  const hasCodeBlocks = isAi && /```\w+/i.test(message.content)

  // Check if response has parsed vCards
  const parsedCards: Array<{ name: string; phone: string; email: string; title: string; org: string; rawTag: string }> = []
  if (isAi && message.content) {
    const vcardRegex = /\[VCARD:\s*([^\]]+)\]/gi
    let vcardMatch
    while ((vcardMatch = vcardRegex.exec(message.content)) !== null) {
      const rawTag = vcardMatch[0]
      const innerContent = vcardMatch[1]
      const cardData = { name: '', phone: '', email: '', title: '', org: '', rawTag }
      const pairs = innerContent.split(',')
      for (const pair of pairs) {
        const [key, ...valParts] = pair.split('=')
        if (key && valParts.length > 0) {
          const k = key.trim().toLowerCase()
          const v = valParts.join('=').trim()
          if (k === 'name') cardData.name = v
          else if (k === 'phone' || k === 'tel') cardData.phone = v
          else if (k === 'email') cardData.email = v
          else if (k === 'title') cardData.title = v
          else if (k === 'org' || k === 'organization') cardData.org = v
        }
      }
      if (cardData.name) {
        parsedCards.push(cardData)
      }
    }

    parsedCards.forEach(card => {
      displayContent = displayContent.replace(card.rawTag, '')
    })
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
            {/* User Attached Images Render View */}
            {!isAi && attachedImages.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginBottom: displayContent ? '10px' : '0' }}>
                {attachedImages.map((imgSrc, idx) => (
                  <div
                    key={idx}
                    style={{
                      position: 'relative',
                      borderRadius: '12px',
                      overflow: 'hidden',
                      border: '1px solid rgba(2, 132, 199, 0.2)',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                      maxWidth: '260px',
                      cursor: 'pointer'
                    }}
                    onClick={() => setPreviewModalImg(imgSrc)}
                  >
                    <img
                      src={imgSrc}
                      alt={`Attached image ${idx + 1}`}
                      style={{ width: '100%', height: 'auto', display: 'block', maxHeight: '220px', objectFit: 'cover' }}
                    />
                    <div style={{
                      position: 'absolute',
                      bottom: 0,
                      left: 0,
                      right: 0,
                      background: 'linear-gradient(to top, rgba(15, 23, 42, 0.8), transparent)',
                      padding: '6px 8px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      color: '#ffffff',
                      fontSize: '11px',
                      fontWeight: '600'
                    }}>
                      <span>🔍 Click to Zoom</span>
                      <span>Image #{idx + 1}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* User Attached Document Badges */}
            {!isAi && attachedDocs.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: displayContent ? '10px' : '0' }}>
                {attachedDocs.map((docTitle, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '8px',
                      background: 'rgba(2, 132, 199, 0.08)',
                      border: '1px solid rgba(2, 132, 199, 0.25)',
                      borderRadius: '10px',
                      padding: '6px 12px',
                      fontSize: '12.5px',
                      fontWeight: '700',
                      color: '#0369a1'
                    }}
                  >
                    <span>📄</span>
                    <span>{docTitle}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Markdown Message Body */}
            {displayContent ? (
              <div className="markdown-body" style={{ color: '#000000', fontSize: '14.5px', lineHeight: '1.5', fontFamily: 'Calibri, sans-serif' }}>
                <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({node, ...props}) => <h1 style={{fontSize: '17px', fontWeight: '800', margin: '12px 0 6px'}} {...props} />,
                    h2: ({node, ...props}) => <h2 style={{fontSize: '15px', fontWeight: '700', margin: '12px 0 6px', borderBottom: '1px solid #cbd5e1', paddingBottom: '3px'}} {...props} />,
                    h3: ({node, ...props}) => <h3 style={{fontSize: '14px', fontWeight: '700', margin: '10px 0 4px'}} {...props} />,
                    p: ({node, ...props}) => <p style={{margin: '0 0 10px', lineHeight: '1.5'}} {...props} />,
                    ul: ({node, ...props}) => <ul style={{paddingLeft: '20px', margin: '4px 0 8px', listStyleType: 'disc'}} {...props} />,
                    ol: ({node, ...props}) => <ol style={{paddingLeft: '22px', margin: '4px 0 8px'}} {...props} />,
                    li: ({node, ...props}) => <li style={{marginBottom: '4px'}} {...props} />,
                    blockquote: ({node, ...props}) => <blockquote style={{borderLeft: '4px solid #0284c7', background: 'rgba(2, 132, 199, 0.03)', padding: '8px 14px', margin: '10px 0', fontStyle: 'italic', fontSize: '13.5px', borderRadius: '0 6px 6px 0'}} {...props} />,
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
                      const language = match ? match[1] : ''
                      return !inline ? (
                        <CodeBlockRunner language={language} code={String(children)} props={props}>
                          {children}
                        </CodeBlockRunner>
                      ) : (
                        <code style={{ background: 'rgba(124,110,247,0.12)', color: '#7c6ef7', padding: '2px 7px', borderRadius: '5px', fontFamily: 'monospace', fontSize: '12px' }} {...props}>
                          {children}
                        </code>
                      )
                    },
                    img: ({node, src, alt, ...props}) => (
                      <span style={{ display: 'inline-block', margin: '14px 0', position: 'relative', maxWidth: '512px', width: '100%' }}>
                        <img src={src} alt={alt} style={{ width: '100%', maxWidth: '512px', height: 'auto', borderRadius: '16px', border: '1px solid #bae6fd', boxShadow: '0 8px 24px rgba(2, 132, 199, 0.12)', display: 'block', cursor: 'pointer' }} onClick={() => src && setPreviewModalImg(src)} />
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

                {/* Render interactive parsed vCards */}
                {parsedCards.map((card, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(248, 250, 252, 0.9))',
                      backdropFilter: 'blur(8px)',
                      border: '1.5px solid #cbd5e1',
                      borderRadius: '16px',
                      padding: '16px',
                      marginTop: '12px',
                      maxWidth: '350px',
                      boxShadow: '0 4px 16px rgba(15, 23, 42, 0.05)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '10px',
                      position: 'relative',
                      overflow: 'hidden'
                    }}
                  >
                    <div style={{ position: 'absolute', top: '-15px', right: '-15px', width: '60px', height: '60px', borderRadius: '50%', background: 'rgba(2, 132, 199, 0.12)', filter: 'blur(12px)' }} />
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', zIndex: 1 }}>
                      <div style={{
                        width: '42px', height: '42px', borderRadius: '12px',
                        background: 'linear-gradient(135deg, #0284c7, #0369a1)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: '#fff', fontSize: '15px', fontWeight: '800',
                        boxShadow: '0 2px 8px rgba(2, 132, 199, 0.2)'
                      }}>
                        {card.name.slice(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <h4 style={{ margin: 0, fontSize: '15px', fontWeight: '800', color: '#0f172a' }}>{card.name}</h4>
                        <p style={{ margin: '2px 0 0 0', fontSize: '11px', fontWeight: '600', color: '#64748b' }}>
                          {card.title || 'Contact Person'} {card.org ? `@ ${card.org}` : ''}
                        </p>
                      </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '11.5px', color: '#334155', borderTop: '1px solid #f1f5f9', paddingTop: '8px', zIndex: 1 }}>
                      {card.phone && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span>📞</span>
                          <a href={`tel:${card.phone}`} style={{ color: '#0284c7', textDecoration: 'none', fontWeight: '700' }}>{card.phone}</a>
                        </div>
                      )}
                      {card.email && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span>✉️</span>
                          <a href={`mailto:${card.email}`} style={{ color: '#0284c7', textDecoration: 'none', fontWeight: '700' }}>{card.email}</a>
                        </div>
                      )}
                    </div>

                    <button
                      onClick={() => {
                        const vcard = [
                          'BEGIN:VCARD',
                          'VERSION:3.0',
                          `FN:${card.name}`,
                          card.org ? `ORG:${card.org}` : '',
                          card.title ? `TITLE:${card.title}` : '',
                          card.phone ? `TEL;TYPE=CELL:${card.phone}` : '',
                          card.email ? `EMAIL;TYPE=INTERNET:${card.email}` : '',
                          'END:VCARD'
                        ].filter(Boolean).join('\r\n')

                        const blob = new Blob([vcard], { type: 'text/vcard;charset=utf-8;' })
                        const url = URL.createObjectURL(blob)
                        const a = document.createElement('a')
                        a.href = url
                        a.download = `${card.name.toLowerCase().replace(/[^a-z0-9]/g, '_')}.vcf`
                        document.body.appendChild(a)
                        a.click()
                        document.body.removeChild(a)
                        URL.revokeObjectURL(url)
                      }}
                      style={{
                        width: '100%',
                        background: 'linear-gradient(135deg, #059669, #047857)',
                        color: '#ffffff',
                        border: 'none',
                        padding: '6px 12px',
                        borderRadius: '8px',
                        fontSize: '11px',
                        fontWeight: '700',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px',
                        boxShadow: '0 2px 6px rgba(5, 150, 105, 0.15)',
                        zIndex: 1
                      }}
                    >
                      <span>📥</span>
                      <span>Save to Contacts (.vcf)</span>
                    </button>
                  </div>
                ))}
              </div>
            ) : isStreaming ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 0', color: '#0284c7', fontWeight: '700', fontSize: '14px' }}>
                <div style={{ width: '16px', height: '16px', borderRadius: '50%', border: '2.5px solid #0284c7', borderTopColor: 'transparent', animation: 'copetraSpin 0.8s linear infinite' }} />
                <span>Copetra AI is generating your response...</span>
                <style>{`@keyframes copetraSpin { to { transform: rotate(360deg); } }`}</style>
              </div>
            ) : (
              <div style={{ color: '#94a3b8', fontSize: '13px', fontStyle: 'italic', padding: '4px 0' }}>
                {attachedImages.length > 0 || attachedDocs.length > 0 ? '' : 'Response pending. Please resend your question.'}
              </div>
            )}{isStreaming && isAi && message.content && (
              <span className="cursor-blink" aria-hidden="true">▌</span>
            )}
          </>
        )}

        {/* Global Multi-file Project ZIP Download Button */}
        {hasCodeBlocks && !isStreaming && (
          <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ fontSize: '12px', color: '#64748b', fontWeight: '600' }}>
              📁 Generated Project Code Bundle:
            </div>
            <button
              onClick={() => downloadAllCodeAsProjectZip(message.content)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                background: 'linear-gradient(135deg, #0284c7, #0369a1)',
                color: '#ffffff',
                border: 'none',
                padding: '6px 14px',
                borderRadius: '10px',
                fontSize: '12px',
                fontWeight: '700',
                cursor: 'pointer',
                boxShadow: '0 2px 8px rgba(2, 132, 199, 0.25)'
              }}
            >
              <span>📦</span>
              <span>Download Project as ZIP (.zip)</span>
            </button>
          </div>
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

                <button
                  onClick={() => {
                    setMoreMenuOpen(false)
                    handleExportDocx()
                  }}
                  style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', borderRadius: '8px', border: 'none', background: 'transparent', color: '#0f172a', fontSize: '13px', fontWeight: '500', cursor: 'pointer', textAlign: 'left' }}
                  onMouseOver={e => (e.currentTarget.style.background = '#f1f5f9')}
                  onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
                >
                  <span style={{ fontSize: '14px' }}>📄</span>
                  <span>Export to Word (.doc)</span>
                </button>

                <button
                  onClick={() => {
                    setMoreMenuOpen(false)
                    handleExportPdf()
                  }}
                  style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', borderRadius: '8px', border: 'none', background: 'transparent', color: '#0f172a', fontSize: '13px', fontWeight: '500', cursor: 'pointer', textAlign: 'left' }}
                  onMouseOver={e => (e.currentTarget.style.background = '#f1f5f9')}
                  onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
                >
                  <span style={{ fontSize: '14px' }}>📕</span>
                  <span>Export to PDF (.pdf)</span>
                </button>

                {message.content.includes('|') && (
                  <button
                    onClick={() => {
                      setMoreMenuOpen(false)
                      handleExportExcel()
                    }}
                    style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', borderRadius: '8px', border: 'none', background: 'transparent', color: '#0f172a', fontSize: '13px', fontWeight: '500', cursor: 'pointer', textAlign: 'left' }}
                    onMouseOver={e => (e.currentTarget.style.background = '#f1f5f9')}
                    onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
                  >
                    <span style={{ fontSize: '14px' }}>📊</span>
                    <span>Export Table to Excel</span>
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Lightbox Modal for Zooming Attached/Generated Images */}
      {previewModalImg && (
        <div
          onClick={() => setPreviewModalImg(null)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.9)',
            backdropFilter: 'blur(8px)',
            zIndex: 9999,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px'
          }}
        >
          <div style={{ position: 'relative', maxWidth: '90vw', maxHeight: '85vh', display: 'flex', flexDirection: 'column', alignItems: 'center' }} onClick={e => e.stopPropagation()}>
            <img
              src={previewModalImg}
              alt="Fullscreen Zoomed Preview"
              style={{ maxWidth: '100%', maxHeight: '75vh', borderRadius: '16px', boxShadow: '0 20px 60px rgba(0,0,0,0.5)', objectFit: 'contain' }}
            />
            <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
              <a
                href={previewModalImg}
                download={`copetra-image-${Date.now()}.png`}
                style={{
                  background: '#0284c7',
                  color: '#ffffff',
                  padding: '10px 20px',
                  borderRadius: '12px',
                  fontSize: '13px',
                  fontWeight: '700',
                  textDecoration: 'none',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                📥 Download Full Image
              </a>
              <button
                onClick={() => setPreviewModalImg(null)}
                style={{
                  background: 'rgba(255, 255, 255, 0.2)',
                  color: '#ffffff',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                  padding: '10px 18px',
                  borderRadius: '12px',
                  fontSize: '13px',
                  fontWeight: '700',
                  cursor: 'pointer'
                }}
              >
                ✕ Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
})

export default MessageBubble