import { NextRequest, NextResponse } from 'next/server'
import { promises as fs } from 'fs'
import path from 'path'
import os from 'os'

export const dynamic = 'force-dynamic'

const USERS_FILE = path.join(os.tmpdir(), 'kronx_users.json')

// Default admin
const DEFAULT_USERS = [
  {
    id: 'u-admin-master',
    name: 'Peter Joseph Msira (Master Admin)',
    email: 'pj0040280@gmail.com',
    role: 'admin',
    plan: 'pro',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Peter',
    lastActive: 'Active Now',
    conversationCount: 1
  }
]

async function readUsers() {
  try {
    const data = await fs.readFile(USERS_FILE, 'utf-8')
    return JSON.parse(data)
  } catch (e) {
    return DEFAULT_USERS
  }
}

async function writeUsers(users: any[]) {
  try {
    await fs.writeFile(USERS_FILE, JSON.stringify(users, null, 2), 'utf-8')
  } catch (e) {
    console.error('Failed to write users file', e)
  }
}

export async function GET() {
  const users = await readUsers()
  return NextResponse.json(users)
}

export async function POST(req: NextRequest) {
  try {
    const user = await req.json()
    const users = await readUsers()
    
    const existingIndex = users.findIndex((u: any) => u.email === user.email)
    
    if (existingIndex >= 0) {
      users[existingIndex] = { ...users[existingIndex], ...user }
    } else {
      users.push({
        ...user,
        conversationCount: 0,
        lastActive: 'Just now'
      })
    }

    await writeUsers(users)
    return NextResponse.json({ success: true, user })
  } catch (e) {
    return NextResponse.json({ success: false }, { status: 500 })
  }
}
