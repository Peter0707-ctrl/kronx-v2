import { NextRequest, NextResponse } from 'next/server'
import { createCompletionWithFallback } from '@/lib/gateway'
import { cleanAiResponse } from '@/lib/fastChat'

export const dynamic = 'force-dynamic'
export const maxDuration = 300

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
    const jobDescription = (body.job_description || body.jd || '').trim()
    const jobTitle = (body.job_title || 'Open Position').trim()
    const candidates: Array<{ candidate_id?: string; id?: string; name?: string; resume_text?: string; cv?: string }> = Array.isArray(body.candidates) ? body.candidates : []

    if (!jobDescription || candidates.length === 0) {
      return NextResponse.json(
        {
          error: 'Missing required parameters. Provide "job_description" and an array of "candidates" (up to 300).',
          status: 'error'
        },
        { status: 400, headers: { 'Access-Control-Allow-Origin': '*' } }
      )
    }

    // Process up to 50 candidates in high-speed batches
    const batchList = candidates.slice(0, 50).map((c, idx) => ({
      id: c.candidate_id || c.id || `candidate_${idx + 1}`,
      name: c.name || `Applicant ${idx + 1}`,
      cv_snippet: (c.resume_text || c.cv || '').slice(0, 2000)
    }))

    const systemPrompt = `You are the Copetra AI Enterprise HR Screening & Candidate Auto-Ranking Engine.
Your task is to review multiple candidates against a job description, compute their Match Score (0-100), and categorize them for the HR Director.

CRITICAL OUTPUT FORMAT:
Respond ONLY with a valid JSON object. No backticks, no code blocks, no emojis.
{
  "total_screened": ${batchList.length},
  "strong_matches_count": <number>,
  "moderate_matches_count": <number>,
  "unqualified_count": <number>,
  "ranked_candidates": [
    {
      "id": "<candidate_id>",
      "name": "<candidate_name>",
      "match_score": <number 0-100>,
      "category": "<Strong Match | Moderate Match | Unqualified>",
      "top_strength": "<single key selling point>",
      "key_risk_or_gap": "<primary deficit or missing requirement>",
      "verdict": "<Short 1-line recommendation for HR>"
    }
  ],
  "executive_hr_summary": "<Brief 3-sentence executive overview of the candidate pool quality and recommended interview shortlist>"
}`

    const userPrompt = `JOB TITLE: ${jobTitle}
JOB DESCRIPTION:
${jobDescription.slice(0, 4000)}

CANDIDATES TO SCREEN:
${JSON.stringify(batchList, null, 2)}`

    const messages = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt }
    ]

    const result = await createCompletionWithFallback({
      messages,
      temperature: 0.2,
      maxTokens: 3000,
      stream: false,
      unlimited: true,
    })

    if (!result.ok || result.stream === true || !result.text) {
      return NextResponse.json(
        { error: 'Batch screening failed to complete.', status: 'error' },
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

    return NextResponse.json(
      {
        status: 'success',
        job_title: jobTitle,
        data: parsed || { raw: cleaned }
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
    console.error('[Recruitment Batch Screen API Error]', err)
    return NextResponse.json(
      { error: err?.message || 'Internal server error.', status: 'error' },
      { status: 500, headers: { 'Access-Control-Allow-Origin': '*' } }
    )
  }
}
