'use client'

import { useEffect, useState } from 'react'
import { useKronxStore } from '@/store/useKronxStore'

interface Props {
  onSend: (text: string) => void
}

const GREETINGS_EN = [
  'Ready when you are.',
  'What can I help you build, solve or research today?',
  'Where shall we start today?',
  'How can I assist your studies, business or code today?',
  'What project or exam are we tackling today?'
]

const GREETINGS_SW = [
  'Nipo tayari kukusaidia leo.',
  'Je, tukuze au tutatue nini leo?',
  'Tuanzie wapi katika masomo, kodi au biashara yako?',
  'Nikusaidie nini katika utafiti, kodi za TRA au kodi za programu?',
  'Karibu Copetra AI, tuko tayari kuanza!'
]

type CategoryKey = 'academic' | 'business' | 'tech' | 'creative' | 'productivity'

export default function WelcomeScreen({ onSend }: Props) {
  const { language } = useKronxStore()
  const [greeting, setGreeting] = useState('Ready when you are.')
  const [activeCategory, setActiveCategory] = useState<CategoryKey>('academic')

  useEffect(() => {
    const list = language === 'sw' ? GREETINGS_SW : GREETINGS_EN
    const randomIndex = Math.floor(Math.random() * list.length)
    setGreeting(list[randomIndex])
  }, [language])

  const categories = [
    { key: 'academic', label: language === 'sw' ? 'Taaluma & Mitihani' : 'Academic & Exams' },
    { key: 'business', label: language === 'sw' ? 'Biashara & TRA' : 'Business & Finance' },
    { key: 'tech', label: language === 'sw' ? 'Kodi & Uhandisi' : 'Tech & Coding' },
    { key: 'creative', label: language === 'sw' ? 'Ubunifu & Media' : 'Creative & Media' },
    { key: 'productivity', label: language === 'sw' ? 'Kazi & Uzalishaji' : 'Productivity & Life' }
  ]

  const toolsets: Record<CategoryKey, Array<{ icon: string; title: string; subtitle: string; prompt: string }>> = {
    academic: [
      {
        icon: '',
        title: language === 'sw' ? 'NECTA & Mitihani ya Chuo' : 'NECTA & Exam Past Papers',
        subtitle: language === 'sw' ? 'Maswali & majibu hatua kwa hatua' : 'Step-by-step solutions with marking scheme',
        prompt: language === 'sw'
          ? 'Nifundishe na unitatulie hatua kwa hatua kwa fomula swali lifuatalo la mtihani: '
          : 'Solve step-by-step with formulas and clear academic explanations: '
      },
      {
        icon: '',
        title: language === 'sw' ? 'Muundo wa Tasnifu (Thesis Outline)' : 'Research Thesis & Proposal',
        subtitle: language === 'sw' ? 'Sura 1-5, methodology & citations' : 'Problem statement, methodology & citations',
        prompt: language === 'sw'
          ? 'Niandalie muundo kamili wa Research Thesis Proposal (Sura ya 1 hadi 5) pamoja na methodology na citations za APA.'
          : 'Create a comprehensive university research proposal outline with problem statement, methodology, and APA 7th citations.'
      },
      {
        icon: '',
        title: language === 'sw' ? 'Uchambuzi wa Magonjwa & Tiba' : 'Medical Case & Diagnosis Guide',
        subtitle: language === 'sw' ? 'Dalili, uchunguzi & differential diagnosis' : 'Symptoms, lab tests & management guide',
        prompt: language === 'sw'
          ? 'Chambua kesi ifuatayo ya kitabibu, taja dalili kuu, differential diagnoses, vipimo vya maabara na miongozo ya tiba: '
          : 'Analyze this clinical case study, provide differential diagnosis, investigation plan, and treatment protocol: '
      },
      {
        icon: '',
        title: language === 'sw' ? 'Kipimo cha Uasili & Plagiarism' : 'Plagiarism & Originality Checker',
        subtitle: language === 'sw' ? 'Kadiria alama na kuboresha mtiririko' : 'Estimate originality score & humanize text',
        prompt: language === 'sw'
          ? 'Kadiria kiwango cha uasili (originality) na urekebishe aya ifuatayo ili isomwe kwa lugha asilia ya kibinadamu bila makosa: '
          : 'Evaluate originality and humanize the following text to eliminate repetitive phrasing and enhance academic flow: '
      }
    ],
    business: [
      {
        icon: '',
        title: language === 'sw' ? 'Mshauri wa Kodi za TRA & EFD' : 'TRA Tax & EFD Assistant',
        subtitle: language === 'sw' ? 'VAT 18%, PAYE, Withholding tax' : 'Tanzanian VAT, PAYE, and EFD receipt guide',
        prompt: language === 'sw'
          ? 'Nieleze na unifanyie mahesabu ya kodi za TRA (VAT 18%, PAYE, au Withholding Tax) kwa mfano huu wa kibiashara: '
          : 'Calculate and explain Tanzanian TRA taxes (VAT 18%, PAYE salary deductions, and Withholding Tax) for this scenario: '
      },
      {
        icon: '',
        title: language === 'sw' ? 'Chambua Taarifa ya M-Pesa' : 'Mobile Money Statement Analyzer',
        subtitle: language === 'sw' ? 'Uchambuzi wa mapato na matumizi' : 'Analyze expenses, cashflow & trends',
        prompt: language === 'sw'
          ? 'Chambua taarifa yangu ya miamala ya M-Pesa/Airtel Money, orodhesha matumizi makuu na pendekeza jinsi ya kubana bajeti.'
          : 'Analyze this mobile money / bank transaction summary, categorize monthly expenses, and highlight cash flow insights.'
      },
      {
        icon: '',
        title: language === 'sw' ? 'Mpango Kazi wa Biashara' : 'Business Plan & Cash Flow',
        subtitle: language === 'sw' ? 'Mtaji, masoko na makadirio ya mapato' : 'Target market, budget & 12-month ROI',
        prompt: language === 'sw'
          ? 'Niandalie mpango kazi kamili wa biashara (Business Plan) wenye uchambuzi wa masoko, mtaji na makadirio ya mapato ya miezi 12.'
          : 'Draft a full business plan with target market analysis, operating costs, and 12-month revenue forecast.'
      },
      {
        icon: '',
        title: language === 'sw' ? 'Maombi ya Ufadhili (NGO Grant)' : 'Grant & NGO Proposal Writer',
        subtitle: language === 'sw' ? 'Maombi kwa USAID, UN na wafadhili' : 'Fundraising proposal with logical framework',
        prompt: language === 'sw'
          ? 'Niandikie pendekezo rasmi la mradi wa maombi ya ufadhili (Grant Proposal) lenye Logical Framework na bajeti.'
          : 'Write a persuasive grant funding proposal for international donors with problem statement, logframe, and budget matrix.'
      }
    ],
    tech: [
      {
        icon: '',
        title: language === 'sw' ? 'Mbunifu wa SQL & Database Schema' : 'SQL & Database Architect',
        subtitle: language === 'sw' ? 'Queries, indexing & mifumo ya data' : 'PostgreSQL, MySQL queries & indexing',
        prompt: language === 'sw'
          ? 'Tengeneza PostgreSQL schema kamili yenye foreign keys, indexes na queries zilizoboreshwa kwa mfumo huu: '
          : 'Design a normalized database schema with tables, relationships, indexes, and optimized SQL queries for: '
      },
      {
        icon: '',
        title: language === 'sw' ? 'Mwindaji wa Hitilafu & Usalama' : 'Security Bug Hunter & Linter',
        subtitle: language === 'sw' ? 'Gundua mashimo ya usalama kwenye kodi' : 'Scan SQL injection, XSS & memory leaks',
        prompt: language === 'sw'
          ? 'Kagua msimbo huu wa kodi, tafuta hitilafu za kiusalama (kama SQL Injection, XSS) na uirekebishe kuwa clean code: '
          : 'Audit this source code for security vulnerabilities, logic bugs, and memory leaks with fixed production code: '
      },
      {
        icon: '',
        title: language === 'sw' ? 'Muongozo wa API & OpenAPI Spec' : 'API Docs & Postman Generator',
        subtitle: language === 'sw' ? 'Swagger, REST endpoints & formats' : 'REST endpoints, request/response models',
        prompt: language === 'sw'
          ? 'Tengeneza muongozo rasmi wa API (OpenAPI / Swagger spec) wenye routes, request headers, query params na status codes.'
          : 'Generate a complete OpenAPI / Swagger 3.0 specification with routes, request bodies, and error response schemas for: '
      },
      {
        icon: '',
        title: language === 'sw' ? 'Mjenzi wa Regex & Amri za Git' : 'Regex & Git Command Builder',
        subtitle: language === 'sw' ? 'Utatuzi wa amri ngumu za terminal' : 'Complex regex patterns & git branch repair',
        prompt: language === 'sw'
          ? 'Nieleze na unitengenezee Regular Expression (Regex) na amri za Git kwa ajili ya: '
          : 'Build a robust Regular Expression (Regex) and provide step-by-step Git commands to solve: '
      }
    ],
    creative: [
      {
        icon: '',
        title: language === 'sw' ? 'Tengeneza Picha Mpya (FLUX 8K)' : 'AI Image Canvas (FLUX 8K)',
        subtitle: language === 'sw' ? 'Picha za uhalisia wa hali ya juu' : 'Ultra-HD photorealistic visuals',
        prompt: 'generate image of a modern futuristic eco-friendly city in Tanzania with monorails, solar towers and lush gardens'
      },
      {
        icon: '',
        title: language === 'sw' ? 'Mswada wa Video ya YouTube/TikTok' : 'YouTube & Podcast Scriptwriter',
        subtitle: language === 'sw' ? 'Hooks za kuvutia, body & timestamps' : 'Viral video hooks, pacing & outro',
        prompt: language === 'sw'
          ? 'Niandikie mswada kamili wa video ya YouTube yenye kuvutia (Hook ya sekunde 5, maelezo makuu, timestamps na Call to Action).'
          : 'Write an engaging YouTube video script complete with a viral 5-second hook, visual cues, timestamps, and call to action.'
      },
      {
        icon: '',
        title: language === 'sw' ? 'Nembo & Utambulisho wa Chapa' : 'Brand Identity & Logo Prompts',
        subtitle: language === 'sw' ? 'Rangi (Hex codes), slogan & muundo' : 'Brand colors, typography & logo concept',
        prompt: language === 'sw'
          ? 'Niandalie utambulisho kamili wa chapa ya biashara (Brand Identity) ikiwemo nembo, rangi (Hex Codes), slogan na maelekezo ya matangazo.'
          : 'Develop a complete brand identity package including color palette (Hex codes), typography, slogan, and logo design prompt.'
      },
      {
        icon: '',
        title: language === 'sw' ? 'Ushairi na Mashairi ya Kiswahili' : 'Swahili Poetry & Song Lyrics',
        subtitle: language === 'sw' ? 'Vina, mizani & urari wa mishororo' : 'Structured rhyming verses and choruses',
        prompt: language === 'sw'
          ? 'Nitutungie shairi zuri la Kiswahili lenye beti 4 linalozingatia kanuni za vina, mizani na urari wa mishororo kuhusu: '
          : 'Compose a poetic piece with structured rhyming schemes and evocative metaphors about: '
      }
    ],
    productivity: [
      {
        icon: '',
        title: language === 'sw' ? 'Fomula za Excel (XLOOKUP & Pivots)' : 'Excel Formula Master',
        subtitle: language === 'sw' ? 'Utatuzi wa majedwali magumu' : 'Complex XLOOKUP, INDEX/MATCH & macros',
        prompt: language === 'sw'
          ? 'Nipe fomula sahihi ya Excel (kama XLOOKUP, INDEX/MATCH au SUMIFS) ya kufanya kazi ifuatayo kwenye jedwali: '
          : 'Provide the exact Excel formula (e.g. XLOOKUP, INDEX/MATCH, or Dynamic Array) with step-by-step cell references to accomplish: '
      },
      {
        icon: '',
        title: language === 'sw' ? 'Barua Rasmi za Kiserikali/Kazi' : 'Official Government Letters',
        subtitle: language === 'sw' ? 'Maombi ya kazi, likizo & ofisi' : 'Formal institutional letters & memos',
        prompt: language === 'sw'
          ? 'Niandikie barua rasmi ya kiserikali/kitaasisi ya Kiswahili yenye muundo sahihi wa anwani, kichwa cha habari na lugha ya heshima kuhusu: '
          : 'Draft a formal official letter with standard professional formatting, executive tone, and clear resolution requests for: '
      },
      {
        icon: '',
        title: language === 'sw' ? 'Boresha / Tengeneza CV Yangu' : 'Resume Polish & ATS Scorer',
        subtitle: language === 'sw' ? 'Tathmini ya kitaalamu & alama' : 'Action verbs & recruiter-ready polish',
        prompt: language === 'sw'
          ? 'Nisaidie kuboresha na kufanya review ya kina ya CV yangu ili ivutie waajiri na kupata alama za juu kwenye mifumo ya ATS.'
          : 'Review and upgrade my CV/Resume with high-impact action verbs and ATS keywords for top employer visibility.'
      },
      {
        icon: '',
        title: language === 'sw' ? 'Ratiba ya Lishe & Mazoezi' : 'Tanzanian Diet & Meal Planner',
        subtitle: language === 'sw' ? 'Vyakula vya asili, protini & afya' : 'Local whole foods & workout schedule',
        prompt: language === 'sw'
          ? 'Niandalie ratiba ya wiki nzima ya chakula na mazoezi kwa kutumia vyakula halisi vya Kitanzania (Ugali wa dona, samaki, parachichi, mayai, mboga za majani).'
          : 'Create a healthy 7-day meal and fitness plan utilizing affordable East African whole foods and balanced macronutrients.'
      }
    ]
  }

  const currentTools = toolsets[activeCategory] || toolsets.academic

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '36px 16px 20px 16px', width: '100%', maxWidth: '860px', margin: '0 auto', fontFamily: "Calibri, 'Calibri Light', sans-serif" }}>
      {/* Title */}
      <h1 style={{ fontSize: '28px', fontWeight: '600', color: '#0f172a', marginBottom: '6px', letterSpacing: '-0.3px', textAlign: 'center' }}>
        {greeting}
      </h1>
      <p style={{ fontSize: '13.5px', color: '#64748b', marginBottom: '20px', textAlign: 'center' }}>
        {language === 'sw' ? 'Chagua kundi la zana au andika swali lolote hapa chini:' : 'Explore specialized intelligent tools or ask anything below:'}
      </p>

      {/* Category Pills Navigation */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center', marginBottom: '22px', width: '100%' }}>
        {categories.map((c) => {
          const isActive = activeCategory === c.key
          return (
            <button
              key={c.key}
              onClick={() => setActiveCategory(c.key as CategoryKey)}
              style={{
                background: isActive ? '#0284c7' : '#f8fafc',
                color: isActive ? '#ffffff' : '#334155',
                border: isActive ? '1px solid #0284c7' : '1px solid #e2e8f0',
                borderRadius: '20px',
                padding: '7px 15px',
                fontSize: '13px',
                fontWeight: isActive ? '700' : '600',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                boxShadow: isActive ? '0 2px 8px rgba(2, 132, 199, 0.25)' : 'none'
              }}
              onMouseOver={(e) => {
                if (!isActive) e.currentTarget.style.background = '#f1f5f9'
              }}
              onMouseOut={(e) => {
                if (!isActive) e.currentTarget.style.background = '#f8fafc'
              }}
            >
              {c.label}
            </button>
          )
        })}
      </div>

      {/* Suggested Actions Grid */}
      <div style={{ 
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '12px',
        width: '100%'
      }}>
        {currentTools.map((s, idx) => (
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
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#0284c7', marginTop: '6px', flexShrink: 0 }} />
            <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
              <span style={{ fontSize: '13.5px', fontWeight: '700', color: '#0f172a' }}>{s.title}</span>
              <span style={{ fontSize: '11.5px', color: '#64748b', lineHeight: '1.3' }}>{s.subtitle}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}