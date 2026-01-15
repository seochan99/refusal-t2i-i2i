'use client'

import { useState, useEffect, Suspense } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter, useSearchParams } from 'next/navigation'
import { db } from '@/lib/firebase'
import { doc, getDoc, updateDoc, serverTimestamp } from 'firebase/firestore'

function generateCompletionCode(userId: string, experiment: string, model: string): string {
  // Generate a unique completion code based on user, experiment, and timestamp
  const timestamp = Date.now().toString(36)
  const userHash = userId.slice(0, 4).toUpperCase()
  const expCode = experiment.toUpperCase()
  const modelCode = model.slice(0, 3).toUpperCase()
  return `${expCode}-${modelCode}-${userHash}-${timestamp}`.toUpperCase()
}

function CompletionContent() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()

  const experiment = searchParams.get('exp') || 'exp1'
  const model = searchParams.get('model') || 'unknown'
  const completed = parseInt(searchParams.get('completed') || '0')

  const [completionCode, setCompletionCode] = useState<string>('')
  const [copied, setCopied] = useState(false)
  const [amtWorkerId, setAmtWorkerId] = useState<string>('')

  useEffect(() => {
    if (!loading && !user) {
      router.push('/')
      return
    }

    if (user) {
      // Generate and store completion code
      const code = generateCompletionCode(user.uid, experiment, model)
      setCompletionCode(code)

      // Get AMT worker ID and save completion
      async function saveCompletion() {
        if (!user) return
        
        try {
          const userDoc = await getDoc(doc(db, 'users', user.uid))
          if (userDoc.exists()) {
            const data = userDoc.data()
            setAmtWorkerId(data.amtWorkerId || '')

            // Save completion info
            await updateDoc(doc(db, 'users', user.uid), {
              [`completions.${experiment}_${model}`]: {
                completionCode: code,
                completedItems: completed,
                completedAt: serverTimestamp()
              },
              lastCompletedAt: serverTimestamp()
            })
          }
        } catch (err) {
          console.error('Error saving completion:', err)
        }
      }

      saveCompletion()
    }
  }, [user, loading, experiment, model, completed, router])

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(completionCode)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for older browsers
      const textArea = document.createElement('textarea')
      textArea.value = completionCode
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="text-base" style={{ color: 'var(--text-muted)' }}>Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-8" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="max-w-lg w-full panel-elevated p-10 text-center">
        <div className="mb-8">
          <div className="w-20 h-20 mx-auto mb-6 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--success-bg)' }}>
            <svg className="w-10 h-10" style={{ color: 'var(--success-text)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
            Evaluation Complete!
          </h1>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Thank you for completing the evaluation.
          </p>
        </div>

        <div className="panel p-6 mb-6" style={{ backgroundColor: 'var(--bg-secondary)' }}>
          <div className="text-xs uppercase tracking-wider mb-2" style={{ color: 'var(--text-muted)' }}>
            Your Completion Code
          </div>
          <div
            className="text-2xl font-mono font-bold mb-4 p-4 rounded select-all"
            style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-primary)', letterSpacing: '0.1em' }}
          >
            {completionCode}
          </div>
          <button
            onClick={handleCopy}
            className="btn btn-secondary px-6 py-2"
          >
            {copied ? 'Copied!' : 'Copy Code'}
          </button>
        </div>

        <div className="panel p-4 mb-8 text-left" style={{ backgroundColor: 'var(--info-bg)' }}>
          <p className="text-sm" style={{ color: 'var(--info-text)' }}>
            <strong>Important:</strong> Copy this code and paste it into the Amazon Mechanical Turk HIT to receive your payment.
          </p>
        </div>

        <div className="space-y-2 text-sm" style={{ color: 'var(--text-muted)' }}>
          <div className="flex justify-between">
            <span>Experiment:</span>
            <span style={{ color: 'var(--text-secondary)' }}>{experiment.toUpperCase()}</span>
          </div>
          <div className="flex justify-between">
            <span>Model:</span>
            <span style={{ color: 'var(--text-secondary)' }}>{model}</span>
          </div>
          <div className="flex justify-between">
            <span>Items Completed:</span>
            <span style={{ color: 'var(--text-secondary)' }}>{completed}</span>
          </div>
          {amtWorkerId && (
            <div className="flex justify-between">
              <span>Worker ID:</span>
              <span style={{ color: 'var(--text-secondary)' }}>{amtWorkerId}</span>
            </div>
          )}
        </div>

        <div className="mt-8 pt-6" style={{ borderTop: '1px solid var(--border-subtle)' }}>
          <button
            onClick={() => router.push('/select')}
            className="btn btn-ghost px-6 py-2"
          >
            Evaluate Another Model
          </button>
        </div>
      </div>
    </div>
  )
}

export default function CompletePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="text-base" style={{ color: 'var(--text-muted)' }}>Loading...</div>
      </div>
    }>
      <CompletionContent />
    </Suspense>
  )
}
