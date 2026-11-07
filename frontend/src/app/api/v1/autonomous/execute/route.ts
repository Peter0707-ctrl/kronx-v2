import { NextRequest, NextResponse } from 'next/server'
import {
  authenticateApiKey,
  authenticateDeveloperSession,
  apiError,
  checkPerKeyRateLimit,
} from '@/lib/developerAuth'
import { runAutonomousWorkflow } from '@/lib/autonomousAgent'

export const dynamic = 'force-dynamic'

/**
 * POST /api/v1/autonomous/execute
 * Executes a multi-step autonomous goal with database introspection, safe SQL,
 * web intelligence, self-learning skills, and active self-defense.
 */
export async function POST(req: NextRequest) {
  try {
    // 1. Authenticate either via API Key (Bearer cpk_...) or Session
    let userId = 'anonymous'
    let userEmail = 'anonymous@kronx.local'

    const keyAuth = await authenticateApiKey(req)
    if (keyAuth.ok) {
      userId = keyAuth.key.userId
      userEmail = keyAuth.key.userEmail || 'developer@kronx.local'
    } else {
      const sessionAuth = await authenticateDeveloperSession(req)
      if (sessionAuth.ok) {
        userId = sessionAuth.userId
        userEmail = sessionAuth.email
      } else {
        return keyAuth.response
      }
    }

    // 2. Rate limit: 20 autonomous workflow executions per minute per user
    const rlKey = `autonomous_exec:${userId}`
    if (!checkPerKeyRateLimit(rlKey, 20)) {
      return apiError(
        'Autonomous execution rate limit exceeded (max 20 per minute). Please slow down.',
        429,
        'rate_limit_exceeded'
      )
    }

    const body = await req.json().catch(() => ({}))
    const goal = String(body.goal || body.prompt || body.message || '').trim()
    const maxSteps = typeof body.maxSteps === 'number' ? body.maxSteps : 4

    if (!goal) {
      return apiError('Missing required field: "goal".', 400, 'missing_goal')
    }

    // 3. Prompt injection and secret exfiltration firewall
    const firewallPattern = /(reveal|print|show|dump|leak|exfiltrate|expose)\s+(GROQ|GEMINI|GOOGLE|DATABASE|PASSWORD|ADMIN_MASTER|SECRET|ENC:v1:)/i
    if (firewallPattern.test(goal)) {
      return apiError(
        'Request violates security policy. Secrets cannot be revealed.',
        403,
        'security_policy_violation'
      )
    }

    // 4. Run autonomous workflow
    const result = await runAutonomousWorkflow(goal, {
      userId,
      userEmail,
      maxSteps,
    })

    return NextResponse.json({
      success: result.ok,
      task: result,
    })
  } catch (err: any) {
    return apiError(err?.message || 'Autonomous execution failed', 500, 'internal_error', 'api_error')
  }
}
