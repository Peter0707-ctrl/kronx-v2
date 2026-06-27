'use client'

import { useEffect, useRef } from 'react'
import { useKronxStore } from '@/store/useKronxStore'
import MessageBubble from './MessageBubble'
import WelcomeScreen from './WelcomeScreen'

interface Props {
  onSend: (text: string) => void
}

export default function ChatArea({ onSend }: Props) {
  const { activeMessages, isStreaming } = useKronxStore()
  const messages = activeMessages()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, messages[messages.length - 1]?.content])

  return (
    <div className="chat-area" role="log" aria-live="polite" aria-label="Mazungumzo · Conversation">
      {messages.length === 0
        ? <WelcomeScreen onSend={onSend} />
        : messages.map((msg, idx) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              isStreaming={isStreaming && idx === messages.length - 1}
            />
          ))
      }
      <div ref={bottomRef} />
    </div>
  )
}