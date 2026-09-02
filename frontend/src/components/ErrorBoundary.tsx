'use client'

import React, { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[Copetra AI Uncaught UI Error]', error, errorInfo)
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            padding: '24px',
            background: '#f8fafc',
            fontFamily: "Calibri, 'Calibri Light', sans-serif",
            textAlign: 'center',
          }}
        >
          <div
            style={{
              background: '#ffffff',
              borderRadius: '24px',
              padding: '36px 32px',
              maxWidth: '480px',
              boxShadow: '0 10px 30px rgba(0,0,0,0.08)',
              border: '1px solid #cbd5e1',
            }}
          >
            <div style={{ fontSize: '42px', marginBottom: '12px' }}></div>
            <h2 style={{ fontSize: '22px', fontWeight: '800', color: '#0f172a', margin: '0 0 8px 0' }}>
              Copetra AI Workspace Recovered
            </h2>
            <p style={{ fontSize: '14px', color: '#64748b', margin: '0 0 20px 0', lineHeight: '1.5' }}>
              An unexpected UI state occurred. Your active conversation data is safe. Click below to refresh your session seamlessly.
            </p>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null })
                window.location.reload()
              }}
              style={{
                width: '100%',
                padding: '12px 20px',
                borderRadius: '14px',
                background: '#0284c7',
                color: '#ffffff',
                border: 'none',
                fontWeight: '800',
                fontSize: '14px',
                cursor: 'pointer',
                boxShadow: '0 4px 14px rgba(2, 132, 199, 0.25)',
              }}
            >
               Refresh Copetra AI Session
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
