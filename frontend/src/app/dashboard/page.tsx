'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useKronxStore } from '@/store/useKronxStore'

export default function DashboardRoute() {
  const router = useRouter()
  const setActiveView = useKronxStore(s => s.setActiveView)

  useEffect(() => {
    setActiveView('dashboard')
    router.replace('/')
  }, [router, setActiveView])

  return null
}
