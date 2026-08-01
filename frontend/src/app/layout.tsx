import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'PJKRONX AI — Akili Bandia ya Tanzania & Academic Companion | PJKRONX Plus',
  description: 'PJKRONX AI by PJ COPETRANOVA - Mshauri wako mkuu wa masomo, tafiti na akili bandia nchini Tanzania.',
  keywords: [
    'pjkronx',
    'pjkronx ai',
    'pjkronxai',
    'pj copetranova',
    'pjkronx plus',
    'pjkronx tanzania',
    'akili bandia tanzania',
    'mwalimu ai tanzania'
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