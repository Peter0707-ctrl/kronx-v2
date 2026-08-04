'use client'

import { useEffect, useRef } from 'react'
import { useKronxStore } from '@/store/useKronxStore'
import MessageBubble from './MessageBubble'
import WelcomeScreen from './WelcomeScreen'

interface Props {
  onSend: (text: string) => void
  onRegenerate: () => void
  onEditAndResend: (messageId: string, newContent: string) => void
}

export default function ChatArea({ onSend, onRegenerate, onEditAndResend }: Props) {
  const { activeMessages, isStreaming } = useKronxStore()
  const messages = activeMessages()
  const bottomRef = useRef<HTMLDivElement>(null)

  // Automatic scroll to bottom: use 'auto' (instant) during active streaming to prevent animation thread choke
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({
        behavior: isStreaming ? 'auto' : 'smooth'
      })
    }
  }, [messages.length, messages[messages.length - 1]?.content, isStreaming])

  return (
    <div className="chat-area" role="log" aria-live="polite" aria-label="Conversation stream" style={{ flex: 1, overflowY: 'auto' }}>
      {messages.length === 0 ? (
        <WelcomeScreen onSend={onSend} />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', width: '100%', maxWidth: '760px', margin: '0 auto', padding: '20px 16px 40px 16px' }}>
          {messages.map((msg, idx) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              isStreaming={isStreaming && idx === messages.length - 1}
              onRegenerate={onRegenerate}
              onEditAndResend={onEditAndResend}
            />
          ))}
          <div ref={bottomRef} style={{ height: '1px' }} />
        </div>
      )}
    </div>
  )
}