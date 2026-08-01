import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Kronx AI — Akili Bandia ya Tanzania & Academic Companion | KronxAI Plus',
  description: 'Kronx AI (KronxAI) by Kopetra Nova - Mshauri wako mkuu wa masomo, tafiti na akili bandia nchini Tanzania. Direct WhatsApp 0673190931 support & Lipa Namba 45342017.',
  keywords: [
    'kronxai',
    'kronx ai',
    'kronx',
    'kronx plus',
    'kronx tanzania',
    'kronx ai copetranova',
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