'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useKronxStore } from '@/store/useKronxStore'

export default function AdminRoute() {
  const router = useRouter()
  const { user, setActiveView } = useKronxStore()

  useEffect(() => {
    const isAdmin = user?.role === 'admin' || user?.email === 'pj0040280@gmail.com'
    if (isAdmin) {
      setActiveView('admin')
    } else {
      setActiveView('chat')
    }
    router.replace('/')
  }, [router, setActiveView, user])

  return null
}
