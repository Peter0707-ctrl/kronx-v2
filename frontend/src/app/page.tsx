'use client'

import { useCallback, useEffect, useState } from 'react'
import Sidebar from '@/components/sidebar/Sidebar'
import TopBar from '@/components/topbar/TopBar'
import ChatArea from '@/components/chat/ChatArea'
import InputBar from '@/components/input/InputBar'
import { useChat } from '@/hooks/useChat'
import { useKronxStore } from '@/store/useKronxStore'

export default function Home() {
  const { send } = useChat()
  const { newConversation, activeConversationId } = useKronxStore()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleSend = useCallback(
    async (text: string) => {
      if (!activeConversationId) newConversation()
      await send(text)
    },
    [send, activeConversationId, newConversation]
  )

  if (!mounted) return null

  return (
    <main className="shell" role="main">
      <Sidebar />
      <div className="main-panel">
        <TopBar />
        <ChatArea onSend={handleSend} />
        <InputBar onSend={handleSend} />
      </div>
    </main>
  )
}