'use client'

import { useEffect, useState } from 'react'
import { useKronxStore } from '@/store/useKronxStore'

interface Props {
  onSend: (text: string) => void
}

const GREETINGS_EN = [
  'Ready when you are.',
  'What can I help you build or solve today?',
  'Where shall we start today?',
  'How can I assist your studies, work or research?',
  'What project are we tackling today?'
]

const GREETINGS_SW = [
  'Nipo tayari kukusaidia leo.',
  'Je, tukuze au tutatue nini leo?',
  'Tuanzie wapi katika masomo au kazi yako?',
  'Nikusaidie nini katika utafiti, kodi au biashara?',
  'Karibu Copetra AI, tuko tayari kuanza!'
]

export default function WelcomeScreen({ onSend }: Props) {
  const { language } = useKronxStore()
  const [greeting, setGreeting] = useState('Ready when you are.')

  useEffect(() => {
    const list = language === 'sw' ? GREETINGS_SW : GREETINGS_EN
    const randomIndex = Math.floor(Math.random() * list.length)
    setGreeting(list[randomIndex])
  }, [language])

  const suggestions = [
    {
      icon: '📝',
      title: language === 'sw' ? 'Boresha / Tengeneza CV' : 'CV Review & ATS Optimization',
      subtitle: language === 'sw' ? 'Tathmini ya kitaalamu & alama za CV' : 'Professional resume scoring & polish',
      prompt: language === 'sw'
        ? 'Nisaidie kuboresha na kufanya review ya kina ya CV yangu ili ivutie waajiri na kupita mifumo ya ATS.'
        : 'Help me review and optimize my CV/Resume with strong achievement bullet points and ATS keywords.'
    },
    {
      icon: '💼',
      title: language === 'sw' ? 'Barua ya Maombi ya Kazi' : 'Job Cover Letter Generator',
      subtitle: language === 'sw' ? 'Andika barua rasmi ya kazi' : 'High-impact tailored application letter',
      prompt: language === 'sw'
        ? 'Niandikie barua rasmi na yenye ushawishi mkubwa ya maombi ya kazi (Cover Letter).'
        : 'Write a persuasive, professional job application cover letter tailored for a competitive role.'
    },
    {
      icon: '🎓',
      title: language === 'sw' ? 'Tatua Swali la Hesabu/Sayansi' : 'Math & Science Step Solver',
      subtitle: language === 'sw' ? 'Mifumo, physics & mahesabu' : 'Detailed derivations and formulas',
      prompt: language === 'sw'
        ? 'Nifundishe na unitatulie hatua kwa hatua kwa fomula swali lifuatalo la hesabu/sayansi: '
        : 'Derive and solve step-by-step with formulas and clear explanations: '
    },
    {
      icon: '💡',
      title: language === 'sw' ? 'Mpango Kazi wa Biashara' : 'Business Plan & Strategy',
      subtitle: language === 'sw' ? 'Bajeti, masoko na uwekezaji' : 'Financial projections & execution plan',
      prompt: language === 'sw'
        ? 'Niandalie mpango kazi kamili wa biashara (Business Plan) wenye uchambuzi wa masoko, mtaji na mapato.'
        : 'Draft a comprehensive business plan including executive summary, target market, and 12-month financial projections.'
    },
    {
      icon: '💻',
      title: language === 'sw' ? 'Kodi & Uhandisi wa Programu' : 'Code Master & Bug Fixer',
      subtitle: language === 'sw' ? 'Python, React, TypeScript, SQL' : 'Robust architectures & scripts',
      prompt: language === 'sw'
        ? 'Niandikie msimbo wa kodi wa kiwango cha juu (clean code) wenye usalama na maelezo ya kina.'
        : 'Write a clean, production-ready script with strict type safety and error handling.'
    },
    {
      icon: '🎨',
      title: language === 'sw' ? 'Tengeneza Picha Mpya (FLUX)' : 'AI Image Canvas (FLUX 8K)',
      subtitle: language === 'sw' ? 'Picha za uhalisia wa hali ya juu' : 'Ultra-HD photorealistic visuals',
      prompt: 'generate image of a futuristic smart university campus in Africa with green solar architecture and digital libraries'
    }
  ]

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 16px 20px 16px', width: '100%', maxWidth: '820px', margin: '0 auto', fontFamily: "Calibri, 'Calibri Light', sans-serif" }}>
      {/* Title */}
      <h1 style={{ fontSize: '28px', fontWeight: '600', color: '#0f172a', marginBottom: '8px', letterSpacing: '-0.3px', textAlign: 'center' }}>
        {greeting}
      </h1>
      <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '28px', textAlign: 'center' }}>
        {language === 'sw' ? 'Chagua kazi ya haraka au andika chochote hapa chini:' : 'Select a quick action or ask anything below:'}
      </p>

      {/* Suggested Actions Grid */}
      <div style={{ 
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '12px',
        width: '100%'
      }}>
        {suggestions.map((s, idx) => (
          <button
            key={idx}
            onClick={() => onSend(s.prompt)}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
              padding: '14px 16px',
              borderRadius: '14px',
              border: '1px solid #e2e8f0',
              background: '#ffffff',
              color: '#0f172a',
              cursor: 'pointer',
              textAlign: 'left',
              boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
              transition: 'all 0.15s ease'
            }}
            onMouseOver={e => {
              e.currentTarget.style.borderColor = '#0284c7'
              e.currentTarget.style.transform = 'translateY(-2px)'
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(2, 132, 199, 0.08)'
            }}
            onMouseOut={e => {
              e.currentTarget.style.borderColor = '#e2e8f0'
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.04)'
            }}
          >
            <span style={{ fontSize: '22px', flexShrink: 0 }}>{s.icon}</span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#0f172a' }}>{s.title}</span>
              <span style={{ fontSize: '12px', color: '#64748b' }}>{s.subtitle}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}