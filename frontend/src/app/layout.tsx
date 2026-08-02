import type { Metadata, Viewport } from 'next'
import './globals.css'

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: '#2563eb',
}

export const metadata: Metadata = {
  title: 'Kronex AI — Premier Academic Companion & Advanced Intelligence Engine',
  description: 'Kronex AI is an advanced artificial intelligence platform engineered for students, researchers, and professionals to solve complex academic assignments, mathematics, software development, research thesis writing, and creative AI generation with precision.',
  keywords: [
    'kronex',
    'kronex ai',
    'kronexai',
    'academic ai',
    'student ai companion',
    'ai research assistant',
    'tanzania ai',
    'ai homework solver'
  ],
  verification: {
    google: '4jBwESfIU4dUQ8-AJiw6Otam1M-JDsIGmQJ2WJnZZ8U',
  },
  manifest: '/manifest.json',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="sw">
      <body>{children}</body>
    </html>
  )
}