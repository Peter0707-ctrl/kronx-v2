import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

/** Lightweight liveness probe — must stay under ~200ms so clients can wake Copetra without blocking chat. */
export async function GET() {
  return NextResponse.json(
    {
      ok: true,
      service: 'copetra',
      timestamp: new Date().toISOString(),
    },
    { status: 200 }
  )
}
