import { NextRequest, NextResponse } from 'next/server'
import { createCompletionWithFallback } from '@/lib/gateway'
import { cleanAiResponse } from '@/lib/fastChat'

export const dynamic = 'force-dynamic'
export const maxDuration = 120

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key',
    },
  })
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}))
    const resumeText = (body.resume_text || body.resume || body.cv_text || '').trim()
    const targetRole = (body.target_role || body.role || 'Industry Professional').trim()

    if (!resumeText) {
      return NextResponse.json(
        { error: 'Missing required parameter "resume_text".', status: 'error' },
        { status: 400, headers: { 'Access-Control-Allow-Origin': '*' } }
      )
    }

    const systemPrompt = `You are the Copetra AI ATS Resume Optimizer & Career Polish Engine.
Analyze the candidate's resume and provide concrete, metric-driven improvements for applicant tracking systems.
Respond ONLY with a valid JSON object. No emojis.

{
  "current_ats_score": <number 0-100>,
  "potential_ats_score": <number 0-100>,
  "formatting_verdict": "<Clean | Needs Formatting Improvements | Unreadable By Old ATS>",
  "quantified_bullet_point_upgrades": [
    {
      "original": "<original weak or unmeasured bullet point from CV>",
      "optimized": "<action verb + task + quantified metric result upgrade>",
      "rationale": "<why this upgrade scores higher in employer ATS>"
    }
  ],
  "recommended_industry_keywords": [
    "<critical keyword or tool to add>"
  ],
  "critical_sections_audit": {
    "contact_info": "<status / feedback>",
    "work_experience": "<status / feedback>",
    "education": "<status / feedback>",
    "skills_matrix": "<status / feedback>"
  },
  "executive_summary_rewrite": "<polished 3-line professional executive summary ready to paste on top of the CV>"
}`

    const userPrompt = `TARGET ROLE: ${targetRole}\n\nRESUME CONTENT:\n${resumeText.slice(0, 10000)}`
    const messages = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt }
    ]

    const result = await createCompletionWithFallback({
      messages,
      temperature: 0.25,
      maxTokens: 2000,
      stream: false,
      unlimited: true
    })

    const cleaned = cleanAiResponse(result.ok && result.stream === false ? result.text : '{}')
    const jsonMatch = cleaned.match(/\{[\s\S]*\}/)
    const parsed = jsonMatch ? JSON.parse(jsonMatch[0]) : { raw: cleaned }

    return NextResponse.json(
      { status: 'success', data: parsed },
      { status: 200, headers: { 'Access-Control-Allow-Origin': '*' } }
    )
  } catch (err: any) {
    console.error('[ATS Optimize API Error]', err)
    return NextResponse.json(
      { error: err?.message || 'Internal server error.', status: 'error' },
      { status: 500, headers: { 'Access-Control-Allow-Origin': '*' } }
    )
  }
}
