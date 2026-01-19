'use client'

import { useEffect, useMemo, useState, Suspense } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter, useSearchParams } from 'next/navigation'
import { db } from '@/lib/firebase'
import { doc, getDoc, getDocs, collection } from 'firebase/firestore'
import { normalizeProlificSession, storeProlificSession, readProlificSession } from '@/lib/prolific'
import { AMT_UNIFIED_CONFIG } from '@/lib/types'

// Skeleton loader component
function SkeletonLoader() {
  return (
    <div className="min-h-screen p-6" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="max-w-4xl mx-auto animate-pulse">
        {/* Header skeleton */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="h-8 w-48 rounded mb-2" style={{ backgroundColor: 'var(--bg-tertiary)' }} />
            <div className="h-4 w-72 rounded" style={{ backgroundColor: 'var(--bg-secondary)' }} />
          </div>
          <div className="flex items-center gap-4">
            <div className="h-10 w-24 rounded" style={{ backgroundColor: 'var(--bg-tertiary)' }} />
          </div>
        </div>

        {/* Stats skeleton */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="panel p-4" style={{ backgroundColor: 'var(--bg-secondary)' }}>
              <div className="h-8 w-12 mx-auto rounded mb-2" style={{ backgroundColor: 'var(--bg-tertiary)' }} />
              <div className="h-3 w-16 mx-auto rounded" style={{ backgroundColor: 'var(--bg-tertiary)' }} />
            </div>
          ))}
        </div>

        {/* Task grid skeleton */}
        <div className="grid grid-cols-5 gap-3">
          {Array.from({ length: 25 }, (_, i) => (
            <div
              key={i}
              className="p-4 rounded-lg"
              style={{
                backgroundColor: 'var(--bg-secondary)',
                border: '2px solid var(--border-default)'
              }}
            >
              <div className="h-5 w-16 rounded mb-2" style={{ backgroundColor: 'var(--bg-tertiary)' }} />
              <div className="h-3 w-12 rounded mb-3" style={{ backgroundColor: 'var(--bg-tertiary)' }} />
              <div className="flex justify-center gap-1">
                {[0, 1, 2].map(j => (
                  <div key={j} className="w-3 h-3 rounded-full" style={{ backgroundColor: 'var(--bg-tertiary)' }} />
                ))}
              </div>
              <div className="h-3 w-8 mx-auto rounded mt-2" style={{ backgroundColor: 'var(--bg-tertiary)' }} />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function LoginContent() {
  const { user, loading, signInWithGoogle, signInAnonymouslyWithProlific, logout } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const [checking, setChecking] = useState(false)
  const [userCompletedTasks, setUserCompletedTasks] = useState<Set<number>>(new Set())
  const [isLoadingTasks, setIsLoadingTasks] = useState(false)

  const prolificSession = useMemo(() => {
    // First try URL params
    const prolificPid = searchParams.get('PROLIFIC_PID') || searchParams.get('prolific_pid') || ''
    const studyId = searchParams.get('STUDY_ID') || searchParams.get('study_id') || ''
    const sessionId = searchParams.get('SESSION_ID') || searchParams.get('session_id') || ''
    const fromUrl = normalizeProlificSession({ prolificPid, studyId, sessionId })
    if (fromUrl) return fromUrl

    // Fallback to localStorage (for page refreshes/redirects)
    return readProlificSession()
  }, [searchParams])

  useEffect(() => {
    if (!prolificSession) return
    storeProlificSession(prolificSession)
  }, [prolificSession])

  // Track page view
  useEffect(() => {
    trackPageView('login')
  }, [])

  // Track page view
  useEffect(() => {
    trackPageView('login')
  }, [])

  useEffect(() => {
    if (!prolificSession) return
    if (loading || user) return

    setChecking(true)
    signInAnonymouslyWithProlific(prolificSession)
      .catch((error) => console.error('Error signing in with Prolific:', error))
      .finally(() => setChecking(false))
  }, [prolificSession, loading, user, signInAnonymouslyWithProlific])

  useEffect(() => {
    async function checkUserState() {
      if (!loading && user && window.location.pathname === '/') {
        setChecking(true)
        try {
          // Check if user has consented in Firebase
          const userDoc = await getDoc(doc(db, 'users', user.uid))
          if (userDoc.exists()) {
            const data = userDoc.data()

            // Check if user has seen the guide (onboarding)
            if (!data.hasSeenGuide) {
              // First time user - send to guide page
              router.push('/guide')
              return
            }

            if (data.irbConsent === true) {
              // User already consented - set localStorage but don't redirect
              localStorage.setItem('irb_consent_i2i_bias', 'agreed')
              // Don't auto-redirect - let user stay on home page
              setChecking(false)
              return
            }
          } else {
            // New user - send to guide page
            router.push('/guide')
            return
          }

          // Check localStorage as fallback
          const localConsent = localStorage.getItem('irb_consent_i2i_bias')
          if (localConsent === 'agreed') {
            // Don't auto-redirect - let user stay on home page
            setChecking(false)
            return
          }

          // No consent found - go to consent page
          router.push('/consent')
        } catch (err: any) {
          // Ignore permission errors during logout
          if (err?.code === 'permission-denied' || err?.code === 'unauthenticated') {
            console.log('User logged out, skipping Firebase check')
            setChecking(false)
            return
          }
          console.error('Error checking user state:', err)
          // Only redirect if it's not a permission error
          if (user) {
            router.push('/consent')
          }
        } finally {
          setChecking(false)
        }
      }
    }

    checkUserState()
  }, [user, loading, router])

  // Load user's completed tasks from Firebase
  useEffect(() => {
    async function loadUserCompletedTasks() {
      if (!user) {
        setUserCompletedTasks(new Set())
        setIsLoadingTasks(false)
        return
      }

      setIsLoadingTasks(true)
      try {
        // Get all task completions
        const completionsRef = collection(db, 'amt_task_completions')
        const snapshot = await getDocs(completionsRef)

        // Find which tasks current user has completed
        const userTasks = new Set<number>()
        snapshot.forEach(docSnap => {
          const data = docSnap.data()
          if (data.userId === user.uid) {
            userTasks.add(data.taskId as number)
          }
        })
        setUserCompletedTasks(userTasks)
      } catch (err: any) {
        // Ignore permission errors during logout
        if (err?.code === 'permission-denied' || err?.code === 'unauthenticated') {
          console.log('User logged out, skipping task loading')
          setUserCompletedTasks(new Set())
        } else {
          console.error('Error loading user completed tasks:', err)
        }
      } finally {
        setIsLoadingTasks(false)
      }
    }

    loadUserCompletedTasks()
  }, [user])

  // Show skeleton loader while loading/checking
  if (loading || checking || isLoadingTasks) {
    return <SkeletonLoader />
  }

  // If user is logged in and has consent, show tasks page link with completion status
  if (user) {
    const hasConsent = localStorage.getItem('irb_consent_i2i_bias') === 'agreed'
    if (hasConsent) {
      const completedCount = userCompletedTasks.size
      const totalTasks = AMT_UNIFIED_CONFIG.totalTasks
      
      return (
        <div className="min-h-screen flex items-center justify-center p-8" style={{ backgroundColor: 'var(--bg-primary)' }}>
          <div className="max-w-md w-full panel-elevated p-10 text-center">
            <h1 className="text-3xl font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>I2I Bias Evaluation</h1>
            <p className="mb-2 text-sm" style={{ color: 'var(--text-muted)' }}>Welcome back!</p>
            {completedCount > 0 && (
              <p className="mb-6 text-sm" style={{ color: 'var(--text-muted)' }}>
                Completed: {completedCount} / {totalTasks} tasks
              </p>
            )}
            <button
              onClick={() => router.push('/tasks')}
              className="btn btn-primary w-full py-4 text-base font-semibold"
            >
              Go to Tasks
            </button>
            <div className="mt-6 pt-6" style={{ borderTop: '1px solid var(--border-subtle)' }}>
              <button
                onClick={logout}
                className="text-sm underline hover:no-underline"
                style={{ color: 'var(--text-muted)' }}
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      )
    }
  }

  // Login screen
  return (
    <div className="min-h-screen flex items-center justify-center p-8" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="max-w-md w-full panel-elevated p-10 text-center">
        <h1 className="text-3xl font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>I2I Bias Evaluation</h1>
        <p className="mb-10 text-sm" style={{ color: 'var(--text-muted)' }}>Sign in to start evaluating</p>

        <button
          onClick={signInWithGoogle}
          className="btn btn-primary w-full py-4 text-base font-semibold flex items-center justify-center gap-3"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Sign in with Google
        </button>

        <div className="mt-8 pt-6" style={{ borderTop: '1px solid var(--border-subtle)' }}>
          <button
            onClick={() => router.push('/guide')}
            className="text-sm underline hover:no-underline"
            style={{ color: 'var(--text-muted)' }}
          >
            How to complete the evaluation
          </button>
        </div>

        <p className="mt-4 text-xs" style={{ color: 'var(--text-disabled)' }}>
          Only authorized evaluators can access this tool
        </p>
      </div>
    </div>
  )
}

/**
 * Root page - Login + Redirect to AMT Task Selection
 */
export default function LoginPage() {
  return (
    <Suspense fallback={<SkeletonLoader />}>
      <LoginContent />
    </Suspense>
  )
}
