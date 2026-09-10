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
    const jobTitle = (body.job_title || 'Professional Role').trim()
    const jobDescription = (body.job_description || body.jd || '').trim()
    const candidateAnswer = (body.candidate_answer || body.answer || '').trim()
    const currentQuestion = (body.current_question || body.question || '').trim()

    // Mode A: Evaluate Candidate's Answer
    if (candidateAnswer && currentQuestion) {
      const systemPrompt = `You are the Copetra AI Interactive Job Interview Coach.
Evaluate the candidate's answer against the given question and target job title.
Respond ONLY with a valid JSON object. No emojis.

{
  "answer_score": <number 0-100>,
  "strengths_in_answer": ["<what the candidate answered well>"],
  "areas_for_improvement": ["<what was vague, missing, or needs metrics/STAR format>"],
  "ideal_response_framework": "<exemplary way to structure the answer using Situation-Task-Action-Result>",
  "follow_up_challenge_question": "<a deeper follow-up question to test competence>"
}`

      const userPrompt = `ROLE: ${jobTitle}
INTERVIEW QUESTION: ${currentQuestion}
CANDIDATE ANSWER: ${candidateAnswer}`

      const messages = [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt }
      ]

      const result = await createCompletionWithFallback({
        messages,
        temperature: 0.3,
        maxTokens: 1200,
        stream: false,
        unlimited: true
      })

      const cleaned = cleanAiResponse(result.ok && result.stream === false ? result.text : '{}')
      const jsonMatch = cleaned.match(/\{[\s\S]*\}/)
      const parsed = jsonMatch ? JSON.parse(jsonMatch[0]) : { raw: cleaned }

      return NextResponse.json(
        { status: 'success', type: 'evaluation', data: parsed },
        { status: 200, headers: { 'Access-Control-Allow-Origin': '*' } }
      )
    }

    // Mode B: Generate 5 Tailored Interview Questions
    const systemPrompt = `You are the Copetra AI Executive Recruitment Interview Architect.
Generate 5 high-impact, realistic interview questions for the given role (2 Technical, 2 Behavioral/STAR Method, 1 Scenario Problem-Solving).
Respond ONLY with a valid JSON object. No emojis.

{
  "role": "${jobTitle}",
  "questions": [
    {
      "id": 1,
      "type": "Technical",
      "question": "<question text>",
      "evaluation_criteria": "<what a hiring manager looks for in the answer>"
    },
    {
      "id": 2,
      "type": "Technical",
      "question": "<question text>",
      "evaluation_criteria": "<what a hiring manager looks for in the answer>"
    },
    {
      "id": 3,
      "type": "Behavioral",
      "question": "<question text>",
      "evaluation_criteria": "<what a hiring manager looks for in the answer>"
    },
    {
      "id": 4,
      "type": "Behavioral",
      "question": "<question text>",
      "evaluation_criteria": "<what a hiring manager looks for in the answer>"
    },
    {
      "id": 5,
      "type": "Scenario / Problem Solving",
      "question": "<question text>",
      "evaluation_criteria": "<what a hiring manager looks for in the answer>"
    }
  ]
}`

    const userPrompt = `ROLE: ${jobTitle}\nJOB DESCRIPTION:\n${jobDescription.slice(0, 4000)}`
    const messages = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt }
    ]

    const result = await createCompletionWithFallback({
      messages,
      temperature: 0.3,
      maxTokens: 1800,
      stream: false,
      unlimited: true
    })

    const cleaned = cleanAiResponse(result.ok && result.stream === false ? result.text : '{}')
    const jsonMatch = cleaned.match(/\{[\s\S]*\}/)
    const parsed = jsonMatch ? JSON.parse(jsonMatch[0]) : { raw: cleaned }

    return NextResponse.json(
      { status: 'success', type: 'question_set', data: parsed },
      { status: 200, headers: { 'Access-Control-Allow-Origin': '*' } }
    )
  } catch (err: any) {
    console.error('[Recruitment Interview Coach API Error]', err)
    return NextResponse.json(
      { error: err?.message || 'Internal server error.', status: 'error' },
      { status: 500, headers: { 'Access-Control-Allow-Origin': '*' } }
    )
  }
}
