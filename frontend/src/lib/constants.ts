import { ModeConfig, SuggestionCard } from '@/types'

export const MODES: ModeConfig[] = [
  { key: 'Friend',   labelSw: 'Rafiki',   labelEn: 'Friend',   color: '#7c6ef7', pip: '#7c6ef7' },
  { key: 'Teacher',  labelSw: 'Mwalimu',  labelEn: 'Teacher',  color: '#3ecfa4', pip: '#3ecfa4' },
  { key: 'Business', labelSw: 'Biashara', labelEn: 'Business', color: '#f4a93b', pip: '#f4a93b' },
  { key: 'Research', labelSw: 'Utafiti',  labelEn: 'Research', color: '#e8604a', pip: '#e8604a' },
  { key: 'Quick',    labelSw: 'Haraka',   labelEn: 'Quick',    color: '#6b6b82', pip: '#6b6b82' },
]

export const SUGGESTION_CARDS: SuggestionCard[] = [
  {
    mode: 'Business',
    labelSw: 'Biashara',
    labelEn: 'Business',
    textEn: 'Start a poultry business in Dar',
    textSw: 'Kuanza biashara ya kuku Dar es Salaam',
    prompt: 'Nisaidie kuanza biashara ya kuku Dar es Salaam — mtaji, hatua, na mapato',
  },
  {
    mode: 'Teacher',
    labelSw: 'Mwalimu',
    labelEn: 'Teacher',
    textEn: 'Learn Python from scratch',
    textSw: 'Python kutoka mwanzo — hatua kwa hatua',
    prompt: 'Nifundishe Python kutoka mwanzo kabisa',
  },
  {
    mode: 'Research',
    labelSw: 'Utafiti',
    labelEn: 'Research',
    textEn: 'Save TZS 500k this month',
    textSw: 'Jinsi ya kuweka akiba ya TZS 500,000',
    prompt: 'Best way to save TZS 500,000 this month in Tanzania',
  },
  {
    mode: 'Friend',
    labelSw: 'Rafiki',
    labelEn: 'Friend',
    textEn: 'Tell me a business story',
    textSw: 'Hadithi ya biashara yenye mafunzo',
    prompt: 'Niambie hadithi ya biashara yenye mafunzo',
  },
]

export const QUICK_CHIPS = [
  { sw: 'Biashara', en: 'Business', prompt: 'Nisaidie na biashara yangu' },
  { sw: 'Kujifunza', en: 'Learn', prompt: 'Nifundishe kitu kipya leo' },
  { sw: 'Hadithi', en: 'Story', prompt: 'Niambie hadithi ya kuvutia' },
  { sw: 'Utafiti', en: 'Research', prompt: 'Nifanyie utafiti kuhusu' },
]

export const PLACEHOLDER: Record<string, string> = {
  sw: 'Andika ujumbe wako... · Type your message...',
  en: 'Type your message... · Andika ujumbe wako...',
}

export const MODE_CHIP_LABEL = (sw: string, en: string) => `${sw} · ${en}`