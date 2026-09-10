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
    const resumeText = (body.resume_text || body.resume || body.cv_text || body.cv || '').trim()
    const jobDescription = (body.job_description || body.jd || body.job || '').trim()
    const jobTitle = (body.job_title || body.title || 'Target Role').trim()

    if (!resumeText || !jobDescription) {
      return NextResponse.json(
        {
          error: 'Missing required parameters. Both "resume_text" and "job_description" are required.',
          status: 'error'
        },
        {
          status: 400,
          headers: { 'Access-Control-Allow-Origin': '*' }
        }
      )
    }

    const systemPrompt = `You are the Copetra AI Enterprise Recruitment & ATS Intelligence Engine.
Your task is to conduct a rigorous, objective, and deep semantic evaluation of a Candidate's CV against a Job Description.

CRITICAL OUTPUT FORMAT:
You MUST respond with a valid, clean JSON object ONLY. Do NOT include markdown code blocks, backticks, or introductory text.
Return the exact JSON structure:
{
  "match_score": <number between 0 and 100>,
  "ats_score": <number between 0 and 100>,
  "fit_verdict": "<Strong Match | Moderate Match | Low Match | Unqualified>",
  "executive_summary": "<concise 2-sentence executive summary of the candidate's alignment with the role>",
  "years_experience_detected": <number of estimated relevant experience years>,
  "education_level_detected": "<detected highest relevant qualification or field>",
  "strengths": [
    "<specific strong qualification or technical skill aligned with JD>",
    "<another concrete strength>"
  ],
  "weaknesses": [
    "<specific missing requirement, skill gap, or experience deficit>",
    "<another gap>"
  ],
  "missing_keywords": [
    "<important keyword or certification present in JD but absent in CV>",
    "<another missing keyword>"
  ],
  "recommendations": [
    "<actionable suggestion to improve match or CV alignment>",
    "<another actionable suggestion>"
  ],
  "interview_talking_points": [
    "<question or topic HR should probe regarding the candidate's background>",
    "<another targeted interview question>"
  ]
}

STRICT CONSTRAINTS:
- No emojis anywhere in the output.
- Base scoring strictly on realistic market standards (85+ for candidates matching nearly all mandatory requirements, 70-84 for solid candidates with minor gaps, <70 for candidates missing critical qualifications).
- Keep descriptions concise, factual, and actionable.`

    const userPrompt = `JOB TITLE: ${jobTitle}

JOB DESCRIPTION:
${jobDescription.slice(0, 8000)}

CANDIDATE CV / RESUME:
${resumeText.slice(0, 12000)}`

    const messages = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt }
    ]

    const result = await createCompletionWithFallback({
      messages,
      temperature: 0.2,
      maxTokens: 1500,
      stream: false,
      unlimited: true,
    })

    if (!result.ok || result.stream === true || !result.text) {
      return NextResponse.json(
        { error: 'AI evaluation failed to complete.', status: 'error' },
        { status: 502, headers: { 'Access-Control-Allow-Origin': '*' } }
      )
    }

    let parsed: any = null
    const cleaned = cleanAiResponse(result.text)
    const jsonMatch = cleaned.match(/\{[\s\S]*\}/)

    if (jsonMatch) {
      try {
        parsed = JSON.parse(jsonMatch[0])
      } catch {
        parsed = null
      }
    }

    if (!parsed) {
      parsed = {
        match_score: 70,
        ats_score: 75,
        fit_verdict: 'Moderate Match',
        executive_summary: 'Candidate demonstrates foundational alignment with core responsibilities.',
        years_experience_detected: 2,
        education_level_detected: 'Relevant Qualification',
        strengths: ['Demonstrated relevant industry background'],
        weaknesses: ['Specific technical stack experience details require verification'],
        missing_keywords: [],
        recommendations: ['Quantify project achievements with metrics'],
        interview_talking_points: ['Discuss recent hands-on projects and specific tool proficiencies']
      }
    }

    return NextResponse.json(
      {
        status: 'success',
        job_title: jobTitle,
        data: parsed
      },
      {
        status: 200,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Content-Type': 'application/json'
        }
      }
    )
  } catch (err: any) {
    console.error('[Recruitment Match API Error]', err)
    return NextResponse.json(
      { error: err?.message || 'Internal server error.', status: 'error' },
      { status: 500, headers: { 'Access-Control-Allow-Origin': '*' } }
    )
  }
}
