'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useKronxStore } from '@/store/useKronxStore'

export default function ChatRoute() {
  const router = useRouter()
  const setActiveView = useKronxStore(s => s.setActiveView)

  useEffect(() => {
    setActiveView('chat')
    router.replace('/')
  }, [router, setActiveView])

  return null
}
