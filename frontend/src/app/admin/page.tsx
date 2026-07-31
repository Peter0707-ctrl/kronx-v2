'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useKronxStore } from '@/store/useKronxStore'

export default function AdminRoute() {
  const router = useRouter()
  const setActiveView = useKronxStore(s => s.setActiveView)

  useEffect(() => {
    setActiveView('admin')
    router.replace('/')
  }, [router, setActiveView])

  return null
}
