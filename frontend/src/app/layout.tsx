import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Nexora AI (Kronx) by PJ COPETRANOVA — Akili Bandia ya Tanzania | Nexora Plus',
  description: 'Nexora AI (KronxAI) by PJ COPETRANOVA - Mshauri wako mkuu wa masomo, tafiti na akili bandia nchini Tanzania.',
  keywords: [
    'nexora ai',
    'nexora',
    'nexorai',
    'kronxai',
    'kronx ai',
    'pj copetranova',
    'nexora ai tanzania',
    'akili bandia tanzania'
  ],
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