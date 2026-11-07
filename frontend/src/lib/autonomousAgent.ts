import { v4 as uuid } from 'uuid'
import { ensureDb, pool } from './db'
import { resolveSecret } from './secretVault'
import {
  introspectDatabaseSchema,
  runSafeReadonlySql,
  searchAndReadInternet,
  learnAndSaveSkill,
  callConnectedSystemApi,
  securitySelfDefense,
} from './autonomousTools'

export interface AutonomousStep {
  stepIndex: number
  thought: string
  action: string
  actionInput: any
  observation: any
  timestamp: string
}

export interface AutonomousWorkflowResult {
  ok: boolean
  taskId: string
  goal: string
  status: 'completed' | 'failed'
  result: string
  steps: AutonomousStep[]
  durationMs: number
  error?: string
}

const GROQ_MODELS = [
  'openai/gpt-oss-120b',
  'qwen/qwen3.8-27b',
  'openai/gpt-oss-20b',
]

const GEMINI_MODELS = ['gemini-3.5-flash', 'gemini-3-flash-preview', 'gemini-3.8-flash']

async function queryLlm(prompt: string): Promise<string> {
  const groqKeys = [
    resolveSecret('GROQ_API_KEY'),
    resolveSecret('GROQ_API_KEY_2'),
  ].filter(Boolean) as string[]

  for (const k of groqKeys) {
    for (const model of GROQ_MODELS) {
      try {
        const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${k}`,
          },
          body: JSON.stringify({
            model,
            messages: [{ role: 'user', content: prompt }],
            temperature: 0.2,
            max_tokens: 1500,
          }),
          signal: AbortSignal.timeout(20000),
        })

        if (res.ok) {
          const data = await res.json()
          const text = data.choices?.[0]?.message?.content?.trim()
          if (text) return text
        }
      } catch {}
    }
  }

  const geminiKeys = [
    resolveSecret('GEMINI_API_KEY'),
    resolveSecret('GOOGLE_API_KEY'),
  ].filter(Boolean) as string[]

  for (const gk of geminiKeys) {
    for (const gm of GEMINI_MODELS) {
      try {
        const res = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models/${gm}:generateContent`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-goog-api-key': gk,
            },
            body: JSON.stringify({
              contents: [{ role: 'user', parts: [{ text: prompt }] }],
              generationConfig: { temperature: 0.2, maxOutputTokens: 1500 },
            }),
            signal: AbortSignal.timeout(20000),
          }
        )

        if (res.ok) {
          const data = await res.json()
          const text = data?.candidates?.[0]?.content?.parts?.[0]?.text?.trim()
          if (text) return text
        }
      } catch {}
    }
  }

  throw new Error('All AI providers (Groq and Gemini) unavailable.')
}

/**
 * Executes a full multi-step autonomous goal.
 */
export async function runAutonomousWorkflow(
  goal: string,
  opts?: {
    userId?: string
    userEmail?: string
    maxSteps?: number
  }
): Promise<AutonomousWorkflowResult> {
  const startTime = Date.now()
  const taskId = `task-${uuid().slice(0, 12)}`
  const maxSteps = Math.min(Math.max(opts?.maxSteps || 4, 1), 6)
  const steps: AutonomousStep[] = []

  await ensureDb()

  // Save task initiation
  await pool
    .query(
      `
    INSERT INTO autonomous_tasks (id, goal, steps, status, user_id, created_at, updated_at)
    VALUES ($1, $2, $3, 'running', $4, NOW(), NOW())
  `,
      [taskId, goal, JSON.stringify([]), opts?.userId || null]
    )
    .catch(() => {})

  // Fetch initial system awareness (schema + active skills)
  const [schemaInfo, skillsRes] = await Promise.all([
    introspectDatabaseSchema(),
    pool.query(`SELECT skill_name, trigger_pattern, execution_logic FROM autonomous_skills LIMIT 10`),
  ])

  const tableSummary = Object.keys(schemaInfo.tables)
    .map((tbl) => `${tbl} (${schemaInfo.tables[tbl].map((c) => c.column).join(', ')})`)
    .join('\n')

  const connectedSummary = schemaInfo.connectedSystems
    .map((s) => `${s.systemName} [${s.systemType}]: ${JSON.stringify(s.schema)}`)
    .join('\n')

  const knownSkills = skillsRes.rows
    .map((s) => `- ${s.skill_name}: ${s.execution_logic}`)
    .join('\n')

  let conversationHistory = `SYSTEM: You are Copetra Autonomous Brain (v2026.11).
Your mission is to accomplish the user goal with 100% accuracy, zero speculation, and rigorous verification.

AVAILABLE KNOWLEDGE:
Database Tables:
${tableSummary || 'None loaded'}

Connected External Systems (POS / Academic / ERP):
${connectedSummary || 'None currently registered'}

Previously Learned Skills:
${knownSkills || 'None yet'}

AVAILABLE ACTIONS:
1. [ACTION: INTROSPECT_SCHEMA]
2. [ACTION: SAFE_SQL {"query": "SELECT count(*) FROM users;"}]
3. [ACTION: WEB_SEARCH {"query": "recent tech news"}]
4. [ACTION: CALL_SYSTEM {"endpointUrl": "https://...", "method": "POST", "payload": {}}]
5. [ACTION: SAVE_SKILL {"skillName": "xyz", "description": "...", "triggerPattern": "...", "executionLogic": "..."}]
6. [ACTION: SELF_DEFEND {"targetType": "api_key", "targetValue": "...", "reason": "..."}]
7. [FINAL_ANSWER: your conclusive report and response here]

FORMAT RULE:
Always output your reasoning, followed by exactly one [ACTION: ...] or [FINAL_ANSWER: ...].
Do not use emojis under any circumstances.

USER GOAL: ${goal}`

  let finalResult = ''
  let status: 'completed' | 'failed' = 'completed'

  for (let stepIndex = 1; stepIndex <= maxSteps; stepIndex++) {
    try {
      const llmOutput = await queryLlm(conversationHistory)

      // Check if Final Answer reached
      if (llmOutput.includes('[FINAL_ANSWER:')) {
        const parts = llmOutput.split('[FINAL_ANSWER:')
        finalResult = parts[1].replace(/\]\s*$/, '').trim()
        steps.push({
          stepIndex,
          thought: parts[0].trim(),
          action: 'FINAL_ANSWER',
          actionInput: {},
          observation: 'Goal completed successfully.',
          timestamp: new Date().toISOString(),
        })
        break
      }

      // Check for actions
      const actionMatch = llmOutput.match(/\[ACTION:\s*([A-Z_]+)(?:\s*(\{[\s\S]*?\}))?\]/)
      if (!actionMatch) {
        finalResult = llmOutput.trim()
        steps.push({
          stepIndex,
          thought: 'Concluded without extra tool call.',
          action: 'DIRECT_RESPONSE',
          actionInput: {},
          observation: 'Direct response generated.',
          timestamp: new Date().toISOString(),
        })
        break
      }

      const actionName = actionMatch[1].trim()
      let actionInput: any = {}
      try {
        if (actionMatch[2]) {
          actionInput = JSON.parse(actionMatch[2])
        }
      } catch {
        actionInput = { raw: actionMatch[2] }
      }

      let observation: any = null

      if (actionName === 'INTROSPECT_SCHEMA') {
        observation = await introspectDatabaseSchema()
      } else if (actionName === 'SAFE_SQL') {
        const q = actionInput.query || actionInput.sql || ''
        observation = await runSafeReadonlySql(q)
      } else if (actionName === 'WEB_SEARCH') {
        const q = actionInput.query || goal
        observation = await searchAndReadInternet(q)
      } else if (actionName === 'CALL_SYSTEM') {
        observation = await callConnectedSystemApi({
          endpointUrl: actionInput.endpointUrl,
          method: actionInput.method,
          payload: actionInput.payload,
        })
      } else if (actionName === 'SAVE_SKILL') {
        observation = await learnAndSaveSkill({
          skillName: actionInput.skillName || `skill_${Date.now()}`,
          description: actionInput.description || '',
          triggerPattern: actionInput.triggerPattern || '',
          executionLogic: actionInput.executionLogic || '',
        })
      } else if (actionName === 'SELF_DEFEND') {
        observation = await securitySelfDefense({
          targetType: actionInput.targetType || 'api_key',
          targetValue: actionInput.targetValue || '',
          reason: actionInput.reason || 'Autonomous detected threat',
        })
      } else {
        observation = { error: `Unknown action: ${actionName}` }
      }

      steps.push({
        stepIndex,
        thought: llmOutput.replace(actionMatch[0], '').trim(),
        action: actionName,
        actionInput,
        observation,
        timestamp: new Date().toISOString(),
      })

      // Append observation for the next step iteration
      conversationHistory += `\n\nAI STEP ${stepIndex} OUTPUT:\n${llmOutput}\n\nTOOL OBSERVATION:\n${JSON.stringify(observation).slice(0, 2000)}\n\nNow review the observation and proceed to the next action or output [FINAL_ANSWER: ...].`
    } catch (err: any) {
      status = 'failed'
      finalResult = `Autonomous loop encountered error: ${err.message}`
      break
    }
  }

  if (!finalResult) {
    finalResult = steps[steps.length - 1]?.thought || 'Task completed with step observations.'
  }

  const durationMs = Date.now() - startTime

  // Update task completion in database
  await pool
    .query(
      `
    UPDATE autonomous_tasks
    SET steps = $1, status = $2, result = $3, updated_at = NOW()
    WHERE id = $4
  `,
      [JSON.stringify(steps), status, finalResult, taskId]
    )
    .catch(() => {})

  return {
    ok: status === 'completed',
    taskId,
    goal,
    status,
    result: finalResult,
    steps,
    durationMs,
  }
}
