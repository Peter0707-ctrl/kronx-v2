import { NextRequest, NextResponse } from 'next/server'
import { Pool } from 'pg'

export const dynamic = 'force-dynamic'

const connectionString = process.env.DATABASE_URL || 'postgresql://postgres:TdoGwPBGGbhiWgarnDevahuPxoehQspt@postgres.railway.internal:5432/railway'

const pool = new Pool({
  connectionString,
})

export async function POST(req: NextRequest) {
  try {
    const authHeader = req.headers.get('Authorization')
    const apiKeyHeader = req.headers.get('x-api-key')
    let apiKey = ''

    if (authHeader && authHeader.startsWith('Bearer ')) {
      apiKey = authHeader.split(' ')[1]
    } else if (apiKeyHeader) {
      apiKey = apiKeyHeader
    }

    if (!apiKey) {
      return NextResponse.json({
        error: 'Unauthorized: Missing API key. Include "Authorization: Bearer <YOUR_KEY>" or "x-api-key: <YOUR_KEY>" header.'
      }, { status: 401 })
    }

    // Query developer by API Key in PostgreSQL
    let developer: any = null
    try {
      const res = await pool.query(
        'SELECT * FROM users WHERE api_key = $1 OR id = $1 LIMIT 1',
        [apiKey]
      )
      if (res.rows.length > 0) {
        developer = res.rows[0]
      }
    } catch (dbErr) {
      console.warn('PostgreSQL query notice:', dbErr)
    }

    // Allow developer access
    const developerId = developer?.id || 'dev_guest'

    const body = await req.json().catch(() => ({}))
    const message = body.message || body.prompt || body.query
    const mode = body.mode || 'Developer'
    const requestCallbackUrl = body.callback_url || body.callbackUrl || body.webhook_url || body.webhookUrl
    const callbackUrl = requestCallbackUrl || developer?.callback_url || developer?.callbackUrl

    if (!message) {
      return NextResponse.json({
        error: 'Bad Request: "message", "prompt", or "query" parameter is required.'
      }, { status: 400 })
    }

    const host = req.headers.get('host')
    const protocol = host?.includes('localhost') ? 'http' : 'https'
    const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || `${protocol}://${host}`

    // ── IF CALLBACK URL IS PROVIDED ──
    if (callbackUrl) {
      // Fire asynchronous AI generation and post payload to callback URL
      fetch(`${baseUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, mode, history: [] })
      })
      .then(res => res.json())
      .then(async data => {
        const payload = {
          event: 'copetra.chat.completion',
          status: 'success',
          developer_id: developerId,
          prompt: message,
          mode,
          response: data.response || 'Copetra AI analysis completed.',
          timestamp: new Date().toISOString(),
          callback_url: callbackUrl
        }

        // Post result payload to target callback URL
        await fetch(callbackUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'User-Agent': 'Copetra-AI-Callback-Gateway/2.0'
          },
          body: JSON.stringify(payload)
        }).catch(err => console.error('[Callback Webhook Error]:', err))
      })
      .catch(err => console.error('[API Gateway Chat Error]:', err))

      return NextResponse.json({
        status: 'accepted',
        event: 'copetra.chat.queued',
        message: 'Request received successfully. Asynchronous AI response will be POSTed to your callback URL.',
        callback_url: callbackUrl,
        developer_id: developerId,
        timestamp: new Date().toISOString()
      }, { status: 202 })
    }

    // ── SYNCHRONOUS RESPONSE (with Callback Support Metadata) ──
    const chatRes = await fetch(`${baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, mode, history: [] })
    })

    const data = await chatRes.json().catch(() => ({}))

    return NextResponse.json({
      status: 'success',
      developer_id: developerId,
      prompt: message,
      mode,
      response: data.response || 'Copetra AI analysis completed.',
      callback_support: {
        supported: true,
        usage: 'Pass "callback_url": "https://your-domain.com/webhook" in your JSON payload for async callbacks.'
      },
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('API Gateway Error:', error)
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 })
  }
}
