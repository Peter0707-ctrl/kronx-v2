import type { Metadata, Viewport } from 'next'
import './globals.css'

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: '#2563eb',
}

export const metadata: Metadata = {
  title: 'Copetra AI — Premier Academic Companion & Advanced Intelligence Engine',
  description: 'Copetra AI is an advanced artificial intelligence platform engineered by PJ Copetranova for students, researchers, and professionals. Solve complex academic assignments, mathematics, software development, research thesis writing, and creative AI generation with precision.',
  keywords: [
    'Copetra AI',
    'Copetra',
    'CopetraAI',
    'copetra ai',
    'copetraai',
    'copetra artificial intelligence',
    'pj copetranova',
    'copetra tanzania',
    'copetra academic ai',
    'academic ai companion',
    'ai homework solver',
    'ai research assistant',
    'Tanzania AI',
    'East Africa AI',
    'AI academic platform',
    'ai assistant tanzania',
    'msaada wa masomo AI',
  ],
  authors: [{ name: 'PJ Copetranova', url: 'https://miraculous-forgiveness-production-10d4.up.railway.app' }],
  creator: 'PJ Copetranova',
  publisher: 'Copetra AI',
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://miraculous-forgiveness-production-10d4.up.railway.app',
    siteName: 'Copetra AI',
    title: 'Copetra AI — Premier Academic Companion & Advanced Intelligence Engine',
    description: 'Copetra AI is an advanced AI platform by PJ Copetranova for students, researchers, and professionals. Get real AI-powered answers instantly.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Copetra AI — Premier Academic Companion',
    description: 'Advanced AI platform by PJ Copetranova for academic excellence.',
    creator: '@copetraai',
  },
  alternates: {
    canonical: 'https://miraculous-forgiveness-production-10d4.up.railway.app',
  },
  verification: {
    google: '4jBwESfIU4dUQ8-AJiw6Otam1M-JDsIGmQJ2WJnZZ8U',
  },
  manifest: '/manifest.json',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'Copetra AI',
    alternateName: ['Copetra', 'CopetraAI', 'PJ Copetranova AI'],
    operatingSystem: 'All',
    applicationCategory: 'EducationalApplication',
    description: 'Copetra AI is an advanced artificial intelligence platform engineered by PJ Copetranova for students, researchers, and professionals.',
    url: 'https://miraculous-forgiveness-production-10d4.up.railway.app',
    author: {
      '@type': 'Person',
      name: 'PJ Copetranova',
    },
    publisher: {
      '@type': 'Organization',
      name: 'PJ Copetranova',
      url: 'https://miraculous-forgiveness-production-10d4.up.railway.app',
    },
  }

  return (
    <html lang="en">
      <head>
        <link rel="canonical" href="https://miraculous-forgiveness-production-10d4.up.railway.app" />
        <meta name="application-name" content="Copetra AI" />
        <meta name="apple-mobile-web-app-title" content="Copetra AI" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="mobile-web-app-capable" content="yes" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body>{children}</body>
    </html>
  )
}