'use client'

import { useState, useEffect, Suspense } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter, useSearchParams } from 'next/navigation'
import { db } from '@/lib/firebase'
import { collection, doc, getDoc, getDocs, setDoc, updateDoc, serverTimestamp, query, where } from 'firebase/firestore'
import { AMT_UNIFIED_CONFIG } from '@/lib/types'
import { getProlificCompletionUrl, readProlificSession } from '@/lib/prolific'

function generateCompletionCode(userId: string, experiment: string, model: string): string {
  // Generate a unique completion code based on user, experiment, and timestamp
  const timestamp = Date.now().toString(36)
  const userHash = userId.slice(0, 4).toUpperCase()
  const expCode = experiment.toUpperCase()
  const modelCode = model.slice(0, 3).toUpperCase()
  return `${expCode}-${modelCode}-${userHash}-${timestamp}`.toUpperCase()
}

function generateTaskCompletionCode(userId: string, taskId: number): string {
  // Generate a deterministic completion code for AMT Task
  const timestamp = Date.now().toString(36)
  const userHash = userId.slice(0, 6).toUpperCase()
  const taskCode = `T${taskId.toString().padStart(2, '0')}`
  return `AMT-${taskCode}-${userHash}-${timestamp}`.toUpperCase()
}

function CompletionContent() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()

  const experiment = searchParams.get('exp') || 'exp1'
  const model = searchParams.get('model') || 'unknown'
  const completed = parseInt(searchParams.get('completed') || '0')

  // Task mode parameters (for AMT)
  const taskIdParam = searchParams.get('taskId')
  const taskId = taskIdParam ? parseInt(taskIdParam) : null
  const isTaskMode = taskId !== null && taskId > 0

  const [completionCode, setCompletionCode] = useState<string>('')
  const [copied, setCopied] = useState(false)
  const [prolificPid, setProlificPid] = useState<string>('')
  const [tasksCompletedCount, setTasksCompletedCount] = useState<number | null>(null)
  const [isProlific, setIsProlific] = useState(false)
  const completionUrl = getProlificCompletionUrl()

  useEffect(() => {
    if (!loading && !user) {
      router.push('/')
      return
    }

    if (user) {
      const session = readProlificSession()
      const isProlificUser = Boolean(session) || user.isAnonymous
      setIsProlific(isProlificUser)
      if (session?.prolificPid) {
        setProlificPid(session.prolificPid)
      }

      // Generate completion code based on mode (only for non-Prolific users)
      let code: string | null = null
      if (!isProlificUser) {
        if (isTaskMode && taskId) {
          code = generateTaskCompletionCode(user.uid, taskId)
        } else {
          code = generateCompletionCode(user.uid, experiment, model)
        }
        setCompletionCode(code)
      }

      // Save completion
      async function saveCompletion() {
        if (!user) return

        try {
          // Load Prolific PID if saved in profile
          const userDoc = await getDoc(doc(db, 'users', user.uid))
          if (userDoc.exists()) {
            const data = userDoc.data()
            if (data.prolificPid) {
              setProlificPid(data.prolificPid)
              setIsProlific(true)
            }
          }

          if (isTaskMode && taskId) {
            // Save Task completion record to prevent re-evaluation (keyed by user UID)
            const taskCompletionRef = doc(db, 'amt_task_completions', `${user.uid}_task${taskId}`)
            
            await setDoc(taskCompletionRef, {
              taskId,
              userId: user.uid,
              userEmail: user.email,
              completionCode: isProlificUser ? null : code,  // No code for Prolific users
              completedItems: completed,
              experimentType: 'amt',
              prolificPid: session?.prolificPid || null,
              prolificStudyId: session?.studyId || null,
              prolificSessionId: session?.sessionId || null,
              completedAt: serverTimestamp()
            })
            console.log(`✅ AMT Task completion saved:`, { taskId, userId: user.uid, code: isProlificUser ? 'N/A (Prolific)' : code })

            const completionsQuery = query(
              collection(db, 'amt_task_completions'),
              where('userId', '==', user.uid)
            )
            const completionsSnapshot = await getDocs(completionsQuery)
            setTasksCompletedCount(completionsSnapshot.size)
          } else {
            // Regular completion flow
            const userDoc = await getDoc(doc(db, 'users', user.uid))
            if (userDoc.exists()) {
              const data = userDoc.data()
              if (data.prolificPid) setProlificPid(data.prolificPid)

              // Save completion info
              await updateDoc(doc(db, 'users', user.uid), {
                [`completions.${experiment}_${model}`]: {
                  completionCode: isProlificUser ? null : code,  // No code for Prolific users
                  completedItems: completed,
                  completedAt: serverTimestamp()
                },
                lastCompletedAt: serverTimestamp()
              })
              console.log('✅ Completion saved:', { experiment, model, code: isProlificUser ? 'N/A (Prolific)' : code })
            }
          }
        } catch (err) {
          console.error('Error saving completion:', err)
          // Non-critical error - user can still see and copy the code
        }
      }

      saveCompletion()
    }
  }, [user, loading, experiment, model, completed, router, isTaskMode, taskId])

  // Prolific users: auto-redirect after completing 1 task
  // Non-Prolific users: can continue up to maxTasksPerUser
  useEffect(() => {
    if (!isTaskMode || !isProlific || !completionUrl) return
    if (tasksCompletedCount === null) return

    // Prolific users redirect after 1 task completion (open in new window)
    if (tasksCompletedCount >= 1) {
      const timer = setTimeout(() => {
        window.open(completionUrl, '_blank')
      }, 2500)
      return () => clearTimeout(timer)
    }
  }, [isTaskMode, isProlific, completionUrl, tasksCompletedCount])

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

        {/* Only show completion code for non-Prolific users */}
        {!isProlific && (
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
        )}

        {/* Important message - only for non-Prolific users */}
        {!isProlific && (
          <div className="panel p-4 mb-8 text-left" style={{ backgroundColor: 'var(--info-bg)' }}>
            <p className="text-sm" style={{ color: 'var(--info-text)' }}>
              <strong>Important:</strong> Keep the code above for your records.
            </p>
          </div>
        )}

        <div className="space-y-2 text-sm" style={{ color: 'var(--text-muted)' }}>
          {isTaskMode ? (
            <>
              <div className="flex justify-between">
                <span>Experiment:</span>
                <span style={{ color: 'var(--text-secondary)' }}>Task Set</span>
              </div>
              <div className="flex justify-between">
                <span>Task ID:</span>
                <span style={{ color: 'var(--text-secondary)' }}>#{taskId}</span>
              </div>
              <div className="flex justify-between">
                <span>Items Evaluated:</span>
                <span style={{ color: 'var(--text-secondary)' }}>{completed}</span>
              </div>
              {tasksCompletedCount !== null && (
                <div className="flex justify-between">
                  <span>Tasks Completed:</span>
                  <span style={{ color: 'var(--text-secondary)' }}>
                    {tasksCompletedCount} / {AMT_UNIFIED_CONFIG.maxTasksPerUser}
                  </span>
                </div>
              )}
              {prolificPid && (
                <div className="flex justify-between">
                  <span>Prolific PID:</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{prolificPid}</span>
                </div>
              )}
            </>
          ) : (
            <>
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
              {prolificPid && (
                <div className="flex justify-between">
                  <span>Prolific PID:</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{prolificPid}</span>
                </div>
              )}
            </>
          )}
        </div>

        <div className="mt-8 pt-6" style={{ borderTop: '1px solid var(--border-subtle)' }}>
          {isTaskMode ? (
            <div className="space-y-4">
              {/* Prolific users: show redirect message after 1 task */}
              {isProlific && completionUrl && tasksCompletedCount !== null && tasksCompletedCount >= 1 && (
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  Redirecting you to Prolific to finish the study...
                </p>
              )}
              {/* Non-Prolific users: can continue tasks */}
              {!isProlific && tasksCompletedCount !== null && tasksCompletedCount < AMT_UNIFIED_CONFIG.maxTasksPerUser && (
                <button
                  onClick={() => router.push('/tasks')}
                  className="btn btn-ghost px-6 py-2"
                >
                  Continue Tasks
                </button>
              )}
              {isProlific && completionUrl ? (
                <button
                  onClick={() => window.open(completionUrl, '_blank')}
                  className="btn btn-primary px-6 py-2"
                >
                  Finish on Prolific
                </button>
              ) : (
                <button
                  onClick={() => router.push('/tasks')}
                  className="btn btn-ghost px-6 py-2"
                >
                  Return to Task List
                </button>
              )}
              {isProlific && !completionUrl && (
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  Prolific completion URL is not configured. Set `NEXT_PUBLIC_PROLIFIC_COMPLETION_CODE`.
                </p>
              )}
              <button
                onClick={() => router.push('/')}
                className="btn btn-ghost px-6 py-2 w-full"
              >
                Go to Home
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <button
                onClick={() => router.push('/select')}
                className="btn btn-ghost px-6 py-2"
              >
                Evaluate Another Model
              </button>
              <button
                onClick={() => router.push('/')}
                className="btn btn-ghost px-6 py-2 w-full"
              >
                Go to Home
              </button>
            </div>
          )}
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
