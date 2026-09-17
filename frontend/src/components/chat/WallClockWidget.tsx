'use client'

import React, { useEffect, useState, useMemo } from 'react'

interface WallClockWidgetProps {
  initialTime?: string
  date?: string
  timezone?: string
  location?: string
}

export const WallClockWidget: React.FC<WallClockWidgetProps> = ({
  initialTime,
  date,
  timezone = 'Africa/Dar_es_Salaam',
  location = 'Tanzania, East Africa'
}) => {
  const [currentTime, setCurrentTime] = useState<Date>(() => new Date())
  const [mounted, setMounted] = useState(false)
  const [is24Hour, setIs24Hour] = useState(false)

  useEffect(() => {
    setMounted(true)
    const interval = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  // Time calculations based on configured timezone
  const { hours, minutes, seconds, timeString12, timeString24, dateString } = useMemo(() => {
    let now = currentTime
    let opts: Intl.DateTimeFormatOptions = {
      timeZone: timezone || 'Africa/Dar_es_Salaam',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    }
    
    let t12 = initialTime || ''
    let t24 = ''
    let dStr = date || ''

    try {
      t12 = now.toLocaleTimeString('en-US', opts)
      t24 = now.toLocaleTimeString('en-US', { ...opts, hour12: false })
      dStr = now.toLocaleDateString('en-US', {
        timeZone: timezone || 'Africa/Dar_es_Salaam',
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    } catch {
      t12 = now.toLocaleTimeString('en-US', { hour12: true })
      t24 = now.toLocaleTimeString('en-US', { hour12: false })
      dStr = now.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
    }

    // Extract numerical hours, minutes, seconds in the specified timezone
    let h = now.getHours()
    let m = now.getMinutes()
    let s = now.getSeconds()

    try {
      const parts = new Intl.DateTimeFormat('en-US', {
        timeZone: timezone || 'Africa/Dar_es_Salaam',
        hour: 'numeric',
        minute: 'numeric',
        second: 'numeric',
        hour12: false
      }).formatToParts(now)

      for (const part of parts) {
        if (part.type === 'hour') h = parseInt(part.value, 10)
        if (part.type === 'minute') m = parseInt(part.value, 10)
        if (part.type === 'second') s = parseInt(part.value, 10)
      }
    } catch {}

    return {
      hours: h,
      minutes: m,
      seconds: s,
      timeString12: t12,
      timeString24: t24,
      dateString: dStr
    }
  }, [currentTime, timezone, initialTime, date])

  // Clock Hand Angles
  const secondAngle = (seconds / 60) * 360
  const minuteAngle = ((minutes + seconds / 60) / 60) * 360
  const hourAngle = (((hours % 12) + minutes / 60 + seconds / 3600) / 12) * 360

  const hourNumbers = [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

  return (
    <div
      style={{
        margin: '14px 0',
        padding: '16px',
        borderRadius: '16px',
        background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.95))',
        border: '1.5px solid #cbd5e1',
        boxShadow: '0 8px 24px rgba(2, 132, 199, 0.08), 0 2px 6px rgba(0, 0, 0, 0.04)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '14px',
        maxWidth: '380px',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Top Header Badge */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', borderBottom: '1px solid #f1f5f9', paddingBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: '#10b981',
            boxShadow: '0 0 8px #10b981',
            display: 'inline-block'
          }} />
          <span style={{ fontSize: '12px', fontWeight: '800', color: '#0f172a', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
            Copetra Live Wall Clock
          </span>
        </div>
        <span style={{ fontSize: '11px', fontWeight: '600', color: '#64748b', background: 'rgba(2, 132, 199, 0.08)', padding: '2px 8px', borderRadius: '12px' }}>
          {location.split(',')[0]}
        </span>
      </div>

      {/* Analog Wall Clock Face (SVG) */}
      <div style={{ position: 'relative', width: '200px', height: '200px', filter: 'drop-shadow(0 6px 16px rgba(15, 23, 42, 0.12))' }}>
        <svg width="200" height="200" viewBox="0 0 200 200" style={{ display: 'block' }}>
          {/* Bezel Outer Frame */}
          <circle
            cx="100"
            cy="100"
            r="96"
            fill="url(#clockBezelGrad)"
            stroke="#94a3b8"
            strokeWidth="2"
          />

          {/* Clock Dial Interior */}
          <circle
            cx="100"
            cy="100"
            r="88"
            fill="url(#clockFaceGrad)"
            stroke="#e2e8f0"
            strokeWidth="1.5"
          />

          {/* Inner Decorative Dial Ring */}
          <circle
            cx="100"
            cy="100"
            r="78"
            fill="none"
            stroke="#e2e8f0"
            strokeWidth="0.75"
            strokeDasharray="2, 4"
          />

          {/* Clock Dial Gradients */}
          <defs>
            <radialGradient id="clockFaceGrad" cx="50%" cy="40%" r="60%">
              <stop offset="0%" stopColor="#ffffff" />
              <stop offset="85%" stopColor="#f8fafc" />
              <stop offset="100%" stopColor="#f1f5f9" />
            </radialGradient>
            <linearGradient id="clockBezelGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#f1f5f9" />
              <stop offset="50%" stopColor="#cbd5e1" />
              <stop offset="100%" stopColor="#94a3b8" />
            </linearGradient>
            <linearGradient id="hourHandGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#0f172a" />
              <stop offset="100%" stopColor="#334155" />
            </linearGradient>
            <linearGradient id="minHandGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#0284c7" />
              <stop offset="100%" stopColor="#0369a1" />
            </linearGradient>
          </defs>

          {/* Minute Ticks */}
          {Array.from({ length: 60 }).map((_, i) => {
            const isHour = i % 5 === 0
            const angle = (i * 6) * (Math.PI / 180)
            const r1 = isHour ? 80 : 83
            const r2 = 86
            const x1 = 100 + r1 * Math.sin(angle)
            const y1 = 100 - r1 * Math.cos(angle)
            const x2 = 100 + r2 * Math.sin(angle)
            const y2 = 100 - r2 * Math.cos(angle)
            return (
              <line
                key={i}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke={isHour ? '#0f172a' : '#cbd5e1'}
                strokeWidth={isHour ? 2 : 1}
                strokeLinecap="round"
              />
            )
          })}

          {/* Hour Numerals 1 to 12 */}
          {hourNumbers.map((num, i) => {
            const angle = (i * 30) * (Math.PI / 180)
            const radius = 68
            const x = 100 + radius * Math.sin(angle)
            const y = 100 - radius * Math.cos(angle) + 4.5
            return (
              <text
                key={num}
                x={x}
                y={y}
                textAnchor="middle"
                fontSize={num === 12 || num === 6 || num === 3 || num === 9 ? '13' : '11'}
                fontWeight={num === 12 || num === 6 || num === 3 || num === 9 ? '800' : '600'}
                fill="#1e293b"
                fontFamily="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
              >
                {num}
              </text>
            )
          })}

          {/* Brand Inscription */}
          <text
            x="100"
            y="64"
            textAnchor="middle"
            fontSize="6.5"
            fontWeight="800"
            fill="#0284c7"
            letterSpacing="1px"
            fontFamily="system-ui, sans-serif"
          >
            COPETRA
          </text>
          <text
            x="100"
            y="72"
            textAnchor="middle"
            fontSize="5.5"
            fontWeight="600"
            fill="#64748b"
            letterSpacing="0.8px"
            fontFamily="system-ui, sans-serif"
          >
            CHRONOMETER
          </text>

          {/* Hour Hand */}
          <line
            x1="100"
            y1="100"
            x2="100"
            y2="52"
            stroke="url(#hourHandGrad)"
            strokeWidth="4.5"
            strokeLinecap="round"
            transform={`rotate(${hourAngle} 100 100)`}
          />

          {/* Minute Hand */}
          <line
            x1="100"
            y1="100"
            x2="100"
            y2="34"
            stroke="url(#minHandGrad)"
            strokeWidth="3"
            strokeLinecap="round"
            transform={`rotate(${minuteAngle} 100 100)`}
          />

          {/* Second Hand Counterweight */}
          <line
            x1="100"
            y1="100"
            x2="100"
            y2="118"
            stroke="#ef4444"
            strokeWidth="1.5"
            strokeLinecap="round"
            transform={`rotate(${secondAngle} 100 100)`}
          />

          {/* Second Hand Needle */}
          <line
            x1="100"
            y1="100"
            x2="100"
            y2="24"
            stroke="#ef4444"
            strokeWidth="1.5"
            strokeLinecap="round"
            transform={`rotate(${secondAngle} 100 100)`}
          />

          {/* Center Hub Caps */}
          <circle cx="100" cy="100" r="5" fill="#0f172a" />
          <circle cx="100" cy="100" r="2.5" fill="#ef4444" />
        </svg>
      </div>

      {/* Digital Time & Date Display */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', gap: '4px' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
          <span
            style={{
              fontSize: '24px',
              fontWeight: '900',
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
              color: '#0f172a',
              letterSpacing: '0.5px'
            }}
          >
            {is24Hour ? timeString24 : timeString12}
          </span>
          <button
            onClick={() => setIs24Hour(!is24Hour)}
            style={{
              background: 'none',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              padding: '2px 6px',
              fontSize: '10px',
              fontWeight: '700',
              color: '#64748b',
              cursor: 'pointer'
            }}
            title="Toggle 12-hour / 24-hour"
          >
            {is24Hour ? '24H' : '12H'}
          </button>
        </div>

        {/* Date Display */}
        <div style={{ fontSize: '13px', fontWeight: '600', color: '#334155', textAlign: 'center' }}>
          {dateString}
        </div>

        {/* Location & Timezone Details */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px', fontSize: '11px', color: '#64748b' }}>
          <svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke="#0284c7" strokeWidth={2}>
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
            <circle cx="12" cy="10" r="3" />
          </svg>
          <span style={{ fontWeight: '600', color: '#0284c7' }}>{location}</span>
          <span>({timezone})</span>
        </div>
      </div>
    </div>
  )
}
