import { NextRequest, NextResponse } from 'next/server'
import { promises as fs } from 'fs'
import path from 'path'
import os from 'os'

export const dynamic = 'force-dynamic'

const USERS_FILE = path.join(os.tmpdir(), 'kronx_users.json')

async function readUsers() {
  try {
    const data = await fs.readFile(USERS_FILE, 'utf-8')
    return JSON.parse(data)
  } catch (e) {
    return []
  }
}

export async function POST(req: NextRequest) {
  try {
    const authHeader = req.headers.get('Authorization')
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json({ error: 'Unauthorized: Missing or invalid API key' }, { status: 401 })
    }

    const apiKey = authHeader.split(' ')[1]
    const users = await readUsers()
    
    // Find authorized developer
    const developer = users.find((u: any) => u.apiKey === apiKey && u.isDeveloper)
    
    if (!developer) {
      return NextResponse.json({ error: 'Unauthorized: Invalid API key or not a developer' }, { status: 403 })
    }

    const body = await req.json()
    const message = body.message || body.prompt
    const mode = body.mode || 'Friend'
    const requestCallbackUrl = body.callbackUrl || body.callback_url
    const callbackUrl = requestCallbackUrl || developer.callbackUrl

    if (!message) {
      return NextResponse.json({ error: 'Bad Request: "message" or "prompt" field is required' }, { status: 400 })
    }

    const host = req.headers.get('host')
    const protocol = host?.includes('localhost') ? 'http' : 'https'
    const baseUrl = `${protocol}://${host}`

    if (callbackUrl) {
      // Asynchronous Processing
      // Fire and forget fetch to our own API
      fetch(`${baseUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, mode, history: [] })
      })
      .then(res => res.json())
      .then(data => {
        // Post the result to the webhook
        fetch(callbackUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            status: 'success',
            developerId: developer.id,
            response: data.response
          })
        }).catch(err => console.error('Failed to ping webhook', err))
      })
      .catch(err => console.error('Failed to generate response for webhook', err))

      return NextResponse.json({
        status: 'processing',
        message: 'Request received. Response will be posted to your webhook callback URL.',
        callbackUrl
      }, { status: 202 })
    }

    // Synchronous Processing
    const chatRes = await fetch(`${baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, mode, history: [] })
    })

    if (!chatRes.ok) {
      return NextResponse.json({ error: 'Internal Server Error: AI Engine failed' }, { status: 500 })
    }

    const data = await chatRes.json()
    return NextResponse.json({
      status: 'success',
      response: data.response
    })

  } catch (error) {
    console.error('API Gateway Error:', error)
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 })
  }
}
