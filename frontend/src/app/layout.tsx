import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Kronx — AI Companion',
  description: 'Mshauri wako wa akili bandia · Your intelligent AI companion',
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