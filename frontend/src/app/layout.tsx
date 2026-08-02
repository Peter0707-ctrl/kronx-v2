import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'PJKRONX AI — Akili Bandia ya Tanzania & Academic Companion | PJKRONX Plus',
  description: 'PJKRONX AI na PJ COPETRANOVA ni Mfumo Mkuu wa Akili Bandia nchini Tanzania unaomsaidia mwanafunzi kutatua assignments, hesabu, kutengeneza picha 8K za FLUX, na tafiti za kitaaluma kwa haraka na ufasaha wa hali ya juu.',
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
  manifest: '/manifest.json',
  themeColor: '#2563eb',
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="sw">
      <body>{children}</body>
    </html>
  )
}