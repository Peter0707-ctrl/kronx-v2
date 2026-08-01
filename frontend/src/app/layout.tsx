import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Kronx AI — Akili Bandia & Academic Companion | KronxAI',
  description: 'Kronx AI (KronxAI) - Mshauri wako mkuu wa masomo na akili bandia. Advanced AI companion for students and professionals.',
  keywords: ['kronxai', 'kronx ai', 'kronx', 'kronx plus', 'akili bandia', 'tanzania ai'],
  verification: {
    google: '4jBwESfIU4dUQ8-AJiw6Otam1M-JDsIGmQJ2WJnZZ8U',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="sw">
      <body>{children}</body>
    </html>
  )
}