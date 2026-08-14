import { NextRequest } from 'next/server'
import { authenticateApiKey, apiError } from '@/lib/developerAuth'

export const dynamic = 'force-dynamic'
export const maxDuration = 120

/**
 * Copetra Image Generation API
 * POST /api/images
 *
 * Auth: Bearer cpk_... or x-api-key
 * Body: { prompt, width?, height?, model?, seed? }
 * Returns OpenAI-ish image payload with url + base64 binary for studio apps (e.g. Muvika).
 */
export async function POST(req: NextRequest) {
  try {
    const auth = await authenticateApiKey(req)
    if (!auth.ok) return auth.response

    const body = await req.json().catch(() => ({}))
    const prompt = String(body.prompt || body.text || '').trim()
    if (!prompt) {
      return apiError('prompt is required.', 400, 'missing_prompt')
    }

    const width = clampInt(body.width, 512, 1440, 1024)
    const height = clampInt(body.height, 512, 1440, 1024)
    const model = String(body.model || 'flux').trim() || 'flux'
    const seed =
      typeof body.seed === 'number'
        ? body.seed
        : Math.floor(Math.random() * 100000)

    const encoded = encodeURIComponent(prompt.slice(0, 800))
    const url =
      `https://image.pollinations.ai/prompt/${encoded}` +
      `?width=${width}&height=${height}&model=${encodeURIComponent(model)}` +
      `&seed=${seed}&nologo=true&enhance=true`

    let binary: string | null = null
    let mediaType = 'image/jpeg'

    try {
      const imgRes = await fetch(url, {
        headers: { 'User-Agent': 'Copetra-Image-API/1.0' },
        signal: AbortSignal.timeout(90_000),
        cache: 'no-store',
      })
      if (imgRes.ok) {
        const buf = Buffer.from(await imgRes.arrayBuffer())
        binary = buf.toString('base64')
        mediaType = imgRes.headers.get('content-type') || 'image/jpeg'
      }
    } catch (e) {
      console.warn('[api/images] download failed, returning URL only', e)
    }

    return Response.json({
      created: Math.floor(Date.now() / 1000),
      data: [
        {
          url,
          b64_json: binary,
          revised_prompt: prompt,
          media_type: mediaType,
        },
      ],
      provider: 'copetra',
      model,
      project: auth.key.projectName,
      developer_id: auth.key.userId,
    })
  } catch (error: any) {
    console.error('[api/images]', error)
    return apiError(error?.message || 'Image generation failed', 500, 'internal_error', 'api_error')
  }
}

function clampInt(value: unknown, min: number, max: number, fallback: number): number {
  const n = typeof value === 'number' ? value : parseInt(String(value ?? ''), 10)
  if (!Number.isFinite(n)) return fallback
  return Math.max(min, Math.min(max, Math.round(n)))
}
