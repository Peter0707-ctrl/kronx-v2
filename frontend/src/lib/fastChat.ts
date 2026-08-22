/** Shared fast-path helpers for Copetra chat APIs. */

export const SIMPLE_GREETINGS: Record<string, string> = {
  hello: `Hello! 👋 Welcome to **Copetra AI**! How can I help you today?`,
  hi: `Hi there! 👋 How can I assist you today?`,
  hey: `Hey! 👋 What can I do for you?`,
  habari: `Habari njema! 👋 Karibu **Copetra AI**! Ninaweza kukusaidia nini leo?`,
  'habari yako': `Nzuri sana! 👋 Karibu! Una swali gani leo?`,
  'habari za leo': `Salama! 👋 Karibu **Copetra AI**! Una swali gani leo?`,
  mambo: `Poa sana! 🤙 Karibu **Copetra AI**! Unaweza kuniuliza chochote.`,
  'mambo vipi': `Poa kabisa! 🤙 Karibu! Nikusaidie nini?`,
  niaje: `Poa! 🤙 Nikusaidie nini leo?`,
  shikamoo: `Marahaba! 🙇 Karibu sana **Copetra AI**! Nikusaidie nini?`,
  jambo: `Jambo! 👋 Karibu **Copetra AI**! Una swali gani?`,
  sasa: `Sasa hivi! 👋 Nikusaidie nini leo?`,
  'sasa hivi': `Fiti! 👋 Karibu **Copetra AI**! Nikusaidie nini?`,
  'za uzima': `Salama kabisa! 👋 Nikusaidie nini leo?`,
  'who are you': `I am **Copetra AI** 🤖, your AI Assistant powered by **PJ COPETRANOVA**. How can I help you?`,
  'wewe ni nani': `Mimi ni **Copetra AI** 🤖, msaidizi wako wa AI uliotengenezwa na **PJ COPETRANOVA**. Nikusaidie nini?`,
}

export function matchSimpleGreeting(query: string): string | null {
  if (!query) return null
  const q = query.toLowerCase().trim().replace(/[!?.،,]+$/g, '').trim()
  return SIMPLE_GREETINGS[q] ?? null
}

export function lastUserText(messages: { role?: string; content?: unknown }[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    if (String(messages[i]?.role || '') !== 'user') continue
    const content = messages[i]?.content
    return typeof content === 'string' ? content : JSON.stringify(content ?? '')
  }
  return ''
}

export function groqApiKeys(): string[] {
  const keys = [
    process.env.GROQ_API_KEY,
    process.env.GROQ_API_KEY_2,
    process.env.GROQ_KEY,
    process.env.GROQ_SECRET_KEY,
    process.env.NEXT_PUBLIC_GROQ_API_KEY,
  ].filter(
    (k): k is string => Boolean(k && k.trim() && !k.includes('placeholder') && k.startsWith('gsk_'))
  )
  return Array.from(new Set(keys))
}

export const GROQ_FAST_MODEL = 'llama-3.3-70b-versatile'
export const GROQ_STRONG_MODEL = 'llama-3.3-70b-versatile'
export const GROQ_VISION_MODELS = [
  'llama-3.2-11b-vision-preview',
  'llama-3.2-90b-vision-preview'
]

export function preferFastGroqModels(opts: {
  vision?: boolean
  document?: boolean
  long?: boolean
}): string[] {
  if (opts.vision) {
    return [
      'llama-3.2-11b-vision-preview',
      'llama-3.2-90b-vision-preview',
      'llama-3.3-70b-versatile'
    ]
  }
  return [
    'llama-3.3-70b-versatile',
    'llama-3.1-8b-instant',
    'mixtral-8x7b-32768',
    'gemma2-9b-it'
  ]
}

export function needsLiveWebSearch(query: string): boolean {
  const clean = query
    .replace(/\[IMAGE:.*?\]/gi, '')
    .replace(/\[(WORD|PDF|EXCEL|POWERPOINT|TEXT|CODE) DOCUMENT ATTACHED:.*?\][\s\S]*/gi, '')
    .replace(/\[PERSISTENT USER BRAIN MEMORY\][\s\S]*/gi, '')
    .trim()

  if (!clean || clean.length < 8) return false
  if (matchSimpleGreeting(clean)) return false

  return /\b(current news|breaking news|live score|today's weather|current price of|who is the current (president|prime minister|ceo)|election results? (2025|2026)|match score)\b/i.test(
    clean
  )
}

/** 
 * Authoritative response cleaner: removes all thinking processes, internal headers,
 * system prompt echoes, and reasoning traces to guarantee 100% brand protection and direct answers.
 */
export function cleanAiResponse(text: string): string {
  if (!text) return ''
  let cleaned = text

  // 1. Remove XML/think/reasoning tags
  cleaned = cleaned.replace(/<think>[\s\S]*?(?:<\/think>|$)/gi, '')
  cleaned = cleaned.replace(/<reasoning>[\s\S]*?(?:<\/reasoning>|$)/gi, '')

  // 2. Remove plain-text thinking process blocks
  cleaned = cleaned.replace(/^Here('?s| is) a thinking process:[\s\S]*?(?=\n\n(?:[#A-Z0-9`]|```|\d+\.)|$)/gi, '')
  cleaned = cleaned.replace(/^Thinking Process:[\s\S]*?(?=\n\n(?:[#A-Z0-9`]|```|\d+\.)|$)/gi, '')
  cleaned = cleaned.replace(/^Here is my thought process:[\s\S]*?(?=\n\n(?:[#A-Z0-9`]|```|\d+\.)|$)/gi, '')

  // 3. Remove internal system/attachment tags if echoed
  cleaned = cleaned.replace(/\[IMAGE ATTACHMENT ANALYZED\]:[^\n]*/gi, '')
  cleaned = cleaned.replace(/\[PERSISTENT USER BRAIN MEMORY\][\s\S]*?(?=\n\n|$)/gi, '')
  cleaned = cleaned.replace(/\[REAL-TIME VERIFIED WEB SEARCH DATA\][\s\S]*?(?=\n\n|$)/gi, '')
  cleaned = cleaned.replace(/Key Constraints from System Prompt:[\s\S]*?(?=\n\n(?:[#A-Z0-9`]|```|\d+\.)|$)/gi, '')

  return cleaned.trim()
}
