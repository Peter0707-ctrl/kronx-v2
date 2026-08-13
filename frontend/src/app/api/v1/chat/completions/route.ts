import type { NextRequest } from 'next/server'
import { POST as gatewayPost } from '../../../gateway/route'

export const dynamic = 'force-dynamic'
export const maxDuration = 60

/** OpenAI-compatible alias for Copetra Developer API */
export async function POST(req: NextRequest) {
  return gatewayPost(req)
}
