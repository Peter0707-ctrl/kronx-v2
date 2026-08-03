import { NextRequest, NextResponse } from 'next/server'
import { promises as fs } from 'fs'
import path from 'path'
import os from 'os'

export const dynamic = 'force-dynamic'

const USERS_FILE = path.join(os.tmpdir(), 'kronx_users.json')

// Default admin and initial mock users
const DEFAULT_USERS = [
  {
    id: 'u-admin-master',
    name: 'Admin at pjcopetranovax',
    email: 'pj0040280@gmail.com',
    role: 'admin',
    plan: 'premium',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Admin',
    lastActive: 'Active Now',
    conversationCount: 1
  },
  {
    id: 'u-1',
    name: 'John Mwangi',
    email: 'john.mwangi@kronx.ai',
    role: 'admin',
    plan: 'pro',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=John',
    lastActive: 'Leo 13:42',
    conversationCount: 14
  },
  {
    id: 'u-2',
    name: 'Amina Hassan',
    email: 'amina.hassan@gmail.com',
    role: 'user',
    plan: 'free',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Amina',
    lastActive: 'Jana 18:20',
    conversationCount: 6
  },
  {
    id: 'u-3',
    name: 'Emmanuel Kimaro',
    email: 'e.kimaro@tech.tz',
    role: 'user',
    plan: 'plus',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Emmanuel',
    lastActive: 'Juzi 09:15',
    conversationCount: 9
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
