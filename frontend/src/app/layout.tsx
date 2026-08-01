import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Kronx — AI Companion',
  description: 'Mshauri wako wa akili bandia · Your intelligent AI companion',
  verification: {
    google: 'googlef5f0aa224a2f0db3',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="sw">
      <body>{children}</body>
    </html>
  )
}