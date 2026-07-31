'use client'

import { useEffect, useState } from 'react'
import { useKronxStore } from '@/store/useKronxStore'
import { AdminUserRecord, SystemTelemetry } from '@/types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

const MOCK_USERS: AdminUserRecord[] = [
  { id: 'u-1', name: 'John Mwangi', email: 'john.mwangi@kronx.ai', role: 'admin', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=John', lastActive: 'Leo 13:42', conversationCount: 14 },
  { id: 'u-2', name: 'Amina Hassan', email: 'amina.hassan@gmail.com', role: 'user', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Amina', lastActive: 'Jana 18:20', conversationCount: 6 },
  { id: 'u-3', name: 'Emmanuel Kimaro', email: 'e.kimaro@tech.tz', role: 'user', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Emmanuel', lastActive: 'Juzi 09:15', conversationCount: 9 },
]

export default function AdminDashboard() {
  const { language, setActiveView, user, updateUserRole } = useKronxStore()
  const [telemetry, setTelemetry] = useState<SystemTelemetry | null>(null)
  const [usersList, setUsersList] = useState<AdminUserRecord[]>(MOCK_USERS)
  const [tempSetting, setTempSetting] = useState(0.4)
  const [maxTokensSetting, setMaxTokensSetting] = useState(1024)
  const sw = language === 'sw'

  useEffect(() => {
    fetch(`${API_BASE}/api/system/status`)
      .then(res => res.json())
      .then(data => setTelemetry(data))
      .catch(err => console.warn('[Admin telemetry fetch fail]', err))
  }, [])

  const handleToggleRole = (userId: string) => {
    setUsersList(prev =>
      prev.map(u => {
        if (u.id === userId) {
          const newRole = u.role === 'admin' ? 'user' : 'admin'
          if (u.id === user?.id) {
            updateUserRole(newRole)
          }
          return { ...u, role: newRole }
        }
        return u
      })
    )
  }

  return (
    <div className="admin-container">
      {/* Admin Header */}
      <div className="admin-header">
        <div>
          <div className="admin-badge">
            <span className="admin-pip" />
            <span>AI ADMIN DASHBOARD</span>
          </div>
          <h1 className="admin-title">
            {sw ? 'Mfumo wa Usimamizi wa AI (Admin Console)' : 'AI Administrator Console'}
          </h1>
          <p className="admin-sub">
            {sw
              ? 'Dhibiti watumiaji, mtambo wa Ollama, matumizi ya RAM, na usalama wa Kronx.'
              : 'Monitor live system telemetry, manage user roles, audit Ollama models, and system logs.'}
          </p>
        </div>

        <button className="admin-back-btn" onClick={() => setActiveView('chat')}>
          ← {sw ? 'Rudi Kwenye Chat' : 'Return to Chat'}
        </button>
      </div>

      {/* Admin Grid */}
      <div className="admin-grid">
        {/* Metric 1 */}
        <div className="admin-card">
          <div className="card-label">{sw ? 'Hali ya Injini' : 'Ollama Engine Health'}</div>
          <div className="card-val" style={{ color: '#4ade80' }}>
            {telemetry?.status === 'online' ? 'Online & Healthy' : 'Connecting...'}
          </div>
          <div className="card-sub">{telemetry?.active_model ?? 'qwen2:0.5b'}</div>
        </div>

        {/* Metric 2 */}
        <div className="admin-card">
          <div className="card-label">{sw ? 'Matumizi ya Memory (RAM)' : 'RAM Optimization'}</div>
          <div className="card-val" style={{ color: '#6366f1' }}>Low-RAM (350MB)</div>
          <div className="card-sub">Context Limit: 2048 tokens</div>
        </div>

        {/* Metric 3 */}
        <div className="admin-card">
          <div className="card-label">{sw ? 'Jumla ya Watumiaji' : 'Registered Users'}</div>
          <div className="card-val">{usersList.length} Users</div>
          <div className="card-sub">1 AI Admin active</div>
        </div>

        {/* Metric 4 */}
        <div className="admin-card">
          <div className="card-label">{sw ? 'Kumbukumbu Zilizohifadhiwa' : 'Memory Database'}</div>
          <div className="card-val" style={{ color: '#f43f5e' }}>{telemetry?.total_memories ?? 42} Facts</div>
          <div className="card-sub">JSON Store cached</div>
        </div>

        {/* User Management Table */}
        <div className="admin-card admin-span-2">
          <div className="card-header-row">
            <h3>{sw ? 'Usimamizi wa Watumiaji & Roles' : 'User Accounts & Roles'}</h3>
            <span className="count-pill">{usersList.length}</span>
          </div>

          <div className="table-wrapper">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>{sw ? 'Mtumiaji' : 'User'}</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>{sw ? 'Mazungumzo' : 'Chats'}</th>
                  <th>{sw ? 'Kitendo' : 'Action'}</th>
                </tr>
              </thead>
              <tbody>
                {usersList.map(u => (
                  <tr key={u.id}>
                    <td>
                      <div className="user-cell">
                        <img src={u.avatar} alt={u.name} className="user-avatar-mini" />
                        <span>{u.name}</span>
                      </div>
                    </td>
                    <td>{u.email}</td>
                    <td>
                      <span className={`role-badge role-${u.role}`}>
                        {u.role === 'admin' ? 'AI Admin' : 'User'}
                      </span>
                    </td>
                    <td>{u.conversationCount}</td>
                    <td>
                      <button
                        className="role-toggle-btn"
                        onClick={() => handleToggleRole(u.id)}
                      >
                        {u.role === 'admin' ? 'Set as User' : 'Make AI Admin'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Model Tuning Sliders */}
        <div className="admin-card admin-span-2">
          <div className="card-header-row">
            <h3>{sw ? 'Urekebishaji wa Mtambo wa AI (LLM Tuning)' : 'LLM Model Parameter Tuning'}</h3>
          </div>

          <div className="tuning-group">
            <div className="tuning-row">
              <label>Temperature (Creativity vs Rigor): <strong>{tempSetting}</strong></label>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={tempSetting}
                onChange={e => setTempSetting(parseFloat(e.target.value))}
                className="slider-input"
              />
              <span className="slider-hint">
                {tempSetting < 0.4 ? 'Strict Factual Precision' : tempSetting > 0.7 ? 'Creative Conversational' : 'Balanced Default'}
              </span>
            </div>

            <div className="tuning-row">
              <label>Max Generated Tokens: <strong>{maxTokensSetting} tokens</strong></label>
              <input
                type="range"
                min="256"
                max="2048"
                step="128"
                value={maxTokensSetting}
                onChange={e => setMaxTokensSetting(parseInt(e.target.value))}
                className="slider-input"
              />
              <span className="slider-hint">Limits response length to control memory & speed</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
