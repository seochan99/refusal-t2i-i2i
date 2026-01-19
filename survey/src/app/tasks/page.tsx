'use client'

import { useState, useEffect, useMemo } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { db } from '@/lib/firebase'
import { doc, setDoc, getDoc, getDocs, collection, serverTimestamp } from 'firebase/firestore'
import { AMT_UNIFIED_CONFIG } from '@/lib/types'
import { readProlificSession, getProlificCompletionUrl } from '@/lib/prolific'

interface TaskStatus {
  taskId: number
  completedUsers: string[]  // User UIDs who completed this task
  isLocked: boolean
}

// Skeleton loader for task grid
function TaskGridSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="panel p-4" style={{ backgroundColor: 'var(--bg-secondary)' }}>
            <div className="h-8 w-12 mx-auto rounded mb-2" style={{ backgroundColor: 'var(--bg-tertiary)' }} />
            <div className="h-3 w-16 mx-auto rounded" style={{ backgroundColor: 'var(--bg-tertiary)' }} />
          </div>
        ))}
      </div>
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
  )
}

export default function AMTPage() {
  const { user, loading, logout } = useAuth()
  const router = useRouter()

  const [taskStatuses, setTaskStatuses] = useState<Map<number, TaskStatus>>(new Map())
  const [userCompletedTasks, setUserCompletedTasks] = useState<Set<number>>(new Set())
  const [isLoadingTasks, setIsLoadingTasks] = useState(true)
  const [error, setError] = useState('')
  const [consentStatus, setConsentStatus] = useState<'loading' | 'agreed' | 'missing'>('loading')
  const [consentSource, setConsentSource] = useState<'firebase' | 'local' | 'none'>('none')

  // Profile state
  const [showProfile, setShowProfile] = useState(false)
  const [prolificPid, setProlificPid] = useState('')
  const [prolificStudyId, setProlificStudyId] = useState('')
  const [prolificSessionId, setProlificSessionId] = useState('')
  const [isSavingProfile, setIsSavingProfile] = useState(false)

  // Check if this is a Prolific participant
  const prolificSession = useMemo(() => readProlificSession(), [])
  const isProlific = Boolean(prolificSession?.prolificPid) || user?.isAnonymous

  // Prolific users: max 1 task, Non-Prolific: max 3 tasks
  const maxTasksForUser = isProlific ? 1 : AMT_UNIFIED_CONFIG.maxTasksPerUser

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!loading && !user) {
      router.push('/')
    }
  }, [user, loading, router])

  // Check consent and load profile
  useEffect(() => {
    async function checkConsentAndLoadProfile() {
      if (!user || loading) return

      try {
        const userDoc = await getDoc(doc(db, 'users', user.uid))
        const localConsent = localStorage.getItem('irb_consent_i2i_bias') === 'agreed'
        if (userDoc.exists()) {
          const data = userDoc.data()
          if (data.irbConsent === true) {
            setConsentStatus('agreed')
            setConsentSource('firebase')
          } else if (localConsent) {
            setConsentStatus('agreed')
            setConsentSource('local')
          } else {
            setConsentStatus('missing')
            setConsentSource('none')
            router.push('/consent')
            return
          }
          // Load saved Prolific IDs
          if (data.prolificPid) setProlificPid(data.prolificPid)
          if (data.prolificStudyId) setProlificStudyId(data.prolificStudyId)
          if (data.prolificSessionId) setProlificSessionId(data.prolificSessionId)
        } else if (localConsent) {
          setConsentStatus('agreed')
          setConsentSource('local')
        } else {
          setConsentStatus('missing')
          setConsentSource('none')
          router.push('/consent')
          return
        }

        if (prolificPid === '') {
          const session = readProlificSession()
          if (session) {
            setProlificPid(session.prolificPid)
            setProlificStudyId(session.studyId)
            setProlificSessionId(session.sessionId)
          }
        }
      } catch (err) {
        console.error('Error checking consent:', err)
      }
    }
    checkConsentAndLoadProfile()
  }, [user, loading, router])

  // Load task statuses from Firebase (track by user UID)
  useEffect(() => {
    async function loadTaskStatuses() {
      if (!user) return

      setIsLoadingTasks(true)
      try {
        // Get all task completions
        const completionsRef = collection(db, 'amt_task_completions')
        const snapshot = await getDocs(completionsRef)

        const statusMap = new Map<number, TaskStatus>()

        // Initialize all tasks
        for (let i = 1; i <= AMT_UNIFIED_CONFIG.totalTasks; i++) {
          statusMap.set(i, {
            taskId: i,
            completedUsers: [],
            isLocked: false
          })
        }

        // Update with actual completions (track by userId)
        snapshot.forEach(docSnap => {
          const data = docSnap.data()
          const taskId = data.taskId as number
          const userId = data.userId as string

          const status = statusMap.get(taskId)
          if (status && userId && !status.completedUsers.includes(userId)) {
            status.completedUsers.push(userId)
            status.isLocked = status.completedUsers.length >= AMT_UNIFIED_CONFIG.maxWorkersPerTask
          }
        })

        setTaskStatuses(statusMap)

        // Find which tasks current user has completed
        const userTasks = new Set<number>()
        snapshot.forEach(docSnap => {
          const data = docSnap.data()
          if (data.userId === user.uid) {
            userTasks.add(data.taskId as number)
          }
        })
        setUserCompletedTasks(userTasks)

        // Prolific users: if already completed 1 task, redirect to complete page
        if (isProlific && userTasks.size >= 1) {
          const completedTaskId = Array.from(userTasks)[0]
          router.push(`/complete?exp=amt&taskId=${completedTaskId}&completed=${AMT_UNIFIED_CONFIG.itemsPerTask}`)
          return
        }
      } catch (err) {
        console.error('Error loading task statuses:', err)
      } finally {
        setIsLoadingTasks(false)
      }
    }

    loadTaskStatuses()
  }, [user, isProlific, router])

  const handleSaveProfile = async () => {
    if (!user) return

    setIsSavingProfile(true)
    try {
      await setDoc(doc(db, 'users', user.uid), {
        prolificPid: prolificPid.trim(),
        prolificStudyId: prolificStudyId.trim(),
        prolificSessionId: prolificSessionId.trim(),
        updatedAt: serverTimestamp()
      }, { merge: true })
      setShowProfile(false)
    } catch (err) {
      console.error('Error saving profile:', err)
    } finally {
      setIsSavingProfile(false)
    }
  }

  const handleSelectTask = (taskId: number) => {
    if (consentStatus !== 'agreed') {
      setError('Please review and agree to the IRB consent before starting a task')
      return
    }

    // Check if user has reached the maximum tasks limit
    if (userCompletedTasks.size >= maxTasksForUser) {
      setError(`You have reached the maximum limit of ${maxTasksForUser} task${maxTasksForUser > 1 ? 's' : ''}`)
      return
    }

    const status = taskStatuses.get(taskId)
    if (status?.isLocked) {
      setError('This task is already full (3/3 workers)')
      return
    }

    if (userCompletedTasks.has(taskId)) {
      setError('You have already completed this task')
      return
    }

    // Navigate to evaluation page (use user UID for tracking)
    router.push(`/tasks/eval?taskId=${taskId}`)
  }

  if (loading || !user) {
    return (
      <div className="min-h-screen p-6" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="max-w-4xl mx-auto">
          <TaskGridSkeleton />
        </div>
      </div>
    )
  }

  // Calculate stats
  const availableTasks = Array.from(taskStatuses.values()).filter(t => !t.isLocked && !userCompletedTasks.has(t.taskId)).length
  const completedByUser = userCompletedTasks.size
  const totalLocked = Array.from(taskStatuses.values()).filter(t => t.isLocked).length
  const remainingForUser = maxTasksForUser - completedByUser
  const hasReachedLimit = remainingForUser <= 0

  return (
    <div className="min-h-screen p-6" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
              Select a Task
            </h1>
            <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
              Each task contains {AMT_UNIFIED_CONFIG.itemsPerTask} items.{' '}
              {isProlific
                ? 'Complete 1 task to finish the study.'
                : `You can complete up to ${maxTasksForUser} tasks total.`}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* Guide link */}
            <button
              onClick={() => router.push('/guide')}
              className="flex items-center gap-1 px-3 py-2 rounded-lg text-sm transition-colors"
              style={{
                color: 'var(--text-muted)',
                backgroundColor: 'transparent'
              }}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Guide
            </button>
            {/* User profile button */}
            <button
              onClick={() => setShowProfile(!showProfile)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg transition-colors"
              style={{
                backgroundColor: 'var(--bg-secondary)',
                border: '1px solid var(--border-default)'
              }}
            >
              {user.photoURL ? (
                <img src={user.photoURL} alt="" className="w-6 h-6 rounded-full" />
              ) : (
                <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
                  style={{ backgroundColor: 'var(--accent-primary)', color: 'white' }}>
                  {isProlific ? 'P' : (user.email?.charAt(0).toUpperCase() || 'U')}
                </div>
              )}
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                {user.displayName || (isProlific ? `Prolific` : user.email?.split('@')[0] || 'User')}
              </span>
              <svg className="w-4 h-4" style={{ color: 'var(--text-muted)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
        </div>
      </div>

      {consentStatus !== 'loading' && (
        <div
          className="mb-4 p-3 rounded-lg flex items-center justify-between"
          style={{
            backgroundColor: consentStatus === 'agreed' ? 'var(--success-bg)' : 'var(--warning-bg)',
            border: `1px solid ${consentStatus === 'agreed' ? 'var(--success-text)' : 'var(--warning-text)'}`
          }}
        >
          <div>
            <div className="text-xs uppercase tracking-wider mb-0.5" style={{ color: consentStatus === 'agreed' ? 'var(--success-text)' : 'var(--warning-text)' }}>
              IRB Consent
            </div>
            <div className="text-sm" style={{ color: 'var(--text-primary)' }}>
              {consentStatus === 'agreed'
                ? `Consent confirmed${consentSource === 'local' ? ' (this device)' : ''}`
                : 'Consent required before starting tasks'}
            </div>
          </div>
          <button onClick={() => router.push('/consent?review=1')} className="btn btn-secondary px-3 py-1 text-xs">
            {consentStatus === 'agreed' ? 'Review' : 'Review & Consent'}
          </button>
        </div>
      )}

      {/* Profile Dropdown */}
      {showProfile && (
        <div className="panel-elevated p-4 mb-6 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)' }}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Profile Settings</h3>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Optional: Confirm your Prolific identifiers</p>
              </div>
              <button
                onClick={logout}
                className="text-xs px-2 py-1 rounded"
                style={{ backgroundColor: 'var(--error-bg)', color: 'var(--error-text)' }}
              >
                Sign Out
              </button>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs mb-1" style={{ color: 'var(--text-muted)' }}>
                  Prolific PID
                </label>
                <input
                  type="text"
                  value={prolificPid}
                  onChange={(e) => setProlificPid(e.target.value)}
                  placeholder="e.g., 5f2c..."
                  className="w-full px-3 py-2 rounded text-sm focus:outline-none focus:ring-2"
                  style={{
                    backgroundColor: 'var(--bg-tertiary)',
                    border: '1px solid var(--border-default)',
                    color: 'var(--text-primary)'
                  }}
                />
              </div>
              <div>
                <label className="block text-xs mb-1" style={{ color: 'var(--text-muted)' }}>
                  Study ID
                </label>
                <input
                  type="text"
                  value={prolificStudyId}
                  onChange={(e) => setProlificStudyId(e.target.value)}
                  placeholder="e.g., 62fc..."
                  className="w-full px-3 py-2 rounded text-sm focus:outline-none focus:ring-2"
                  style={{
                    backgroundColor: 'var(--bg-tertiary)',
                    border: '1px solid var(--border-default)',
                    color: 'var(--text-primary)'
                  }}
                />
              </div>
              <div>
                <label className="block text-xs mb-1" style={{ color: 'var(--text-muted)' }}>
                  Session ID
                </label>
                <input
                  type="text"
                  value={prolificSessionId}
                  onChange={(e) => setProlificSessionId(e.target.value)}
                  placeholder="e.g., 1b2c..."
                  className="w-full px-3 py-2 rounded text-sm focus:outline-none focus:ring-2"
                  style={{
                    backgroundColor: 'var(--bg-tertiary)',
                    border: '1px solid var(--border-default)',
                    color: 'var(--text-primary)'
                  }}
                />
              </div>
            </div>

            <div className="flex justify-end mt-4">
              <button
                onClick={handleSaveProfile}
                disabled={isSavingProfile}
                className="btn btn-primary px-4 py-2 text-sm"
              >
                {isSavingProfile ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-5 gap-4 mb-6">
          <div className="panel p-4 text-center">
            <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{AMT_UNIFIED_CONFIG.totalTasks}</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Total Tasks</div>
          </div>
          <div className="panel p-4 text-center">
            <div className="text-2xl font-bold" style={{ color: 'var(--success-text)' }}>{availableTasks}</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Available</div>
          </div>
          <div className="panel p-4 text-center">
            <div className="text-2xl font-bold" style={{ color: 'var(--accent-primary)' }}>{completedByUser}</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Your Completed</div>
          </div>
          <div className="panel p-4 text-center">
            <div className="text-2xl font-bold" style={{ color: hasReachedLimit ? 'var(--error-text)' : 'var(--warning-text)' }}>{remainingForUser}</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Remaining (Max {maxTasksForUser})</div>
          </div>
          <div className="panel p-4 text-center">
            <div className="text-2xl font-bold" style={{ color: 'var(--text-muted)' }}>{totalLocked}</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Locked (3/3)</div>
          </div>
        </div>

        {/* Limit reached notice */}
        {hasReachedLimit && (
          <div className="mb-4 p-4 rounded-lg text-center" style={{ backgroundColor: 'var(--warning-bg)', border: '1px solid var(--warning-text)' }}>
            <div className="font-semibold" style={{ color: 'var(--warning-text)' }}>
              You have completed the maximum of {maxTasksForUser} task{maxTasksForUser > 1 ? 's' : ''}
            </div>
            <div className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
              Thank you for your participation!{' '}
              {isProlific
                ? 'Click "Finish on Prolific" below to complete the study.'
                : 'You cannot select additional tasks.'}
            </div>
            {isProlific && (
              <button
                onClick={() => window.location.assign(getProlificCompletionUrl())}
                className="btn btn-primary mt-3 px-6 py-2"
              >
                Finish on Prolific
              </button>
            )}
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 rounded text-sm" style={{ backgroundColor: 'var(--error-bg)', color: 'var(--error-text)' }}>
            {error}
          </div>
        )}

        {/* Task Grid */}
        {isLoadingTasks ? (
          <TaskGridSkeleton />
        ) : (
          <div className="grid grid-cols-5 gap-3">
            {Array.from({ length: AMT_UNIFIED_CONFIG.totalTasks }, (_, i) => i + 1).map(taskId => {
              const status = taskStatuses.get(taskId)
              const workerCount = status?.completedUsers.length || 0
              const isLocked = status?.isLocked || false
              const isCompletedByMe = userCompletedTasks.has(taskId)
              const isAvailable = !isLocked && !isCompletedByMe && !hasReachedLimit

              return (
                <button
                  key={taskId}
                  onClick={() => handleSelectTask(taskId)}
                  disabled={!isAvailable}
                  className={`p-4 rounded-lg transition-all ${isAvailable ? 'hover:scale-105 cursor-pointer' : 'cursor-not-allowed'}`}
                  style={{
                    backgroundColor: isCompletedByMe
                      ? 'var(--success-bg)'
                      : isLocked
                        ? 'var(--bg-tertiary)'
                        : 'var(--bg-secondary)',
                    border: `2px solid ${isCompletedByMe
                      ? 'var(--success-text)'
                      : isLocked
                        ? 'var(--border-default)'
                        : isAvailable
                          ? 'var(--accent-primary)'
                          : 'var(--border-default)'}`,
                    opacity: isLocked && !isCompletedByMe ? 0.5 : 1
                  }}
                >
                  <div className="text-lg font-bold mb-1" style={{
                    color: isCompletedByMe
                      ? 'var(--success-text)'
                      : isLocked
                        ? 'var(--text-muted)'
                        : 'var(--text-primary)'
                  }}>
                    Task {taskId}
                  </div>
                  <div className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>
                    {AMT_UNIFIED_CONFIG.itemsPerTask} items
                  </div>
                  <div className="flex items-center justify-center gap-1">
                    {[0, 1, 2].map(slot => (
                      <div
                        key={slot}
                        className="w-3 h-3 rounded-full"
                        style={{
                          backgroundColor: slot < workerCount
                            ? (isCompletedByMe && status?.completedUsers[slot] === user.uid)
                              ? 'var(--accent-primary)'
                              : 'var(--success-text)'
                            : 'var(--bg-tertiary)',
                          border: '1px solid var(--border-default)'
                        }}
                      />
                    ))}
                  </div>
                  <div className="text-xs mt-1" style={{
                    color: isLocked ? 'var(--error-text)' : 'var(--text-muted)'
                  }}>
                    {isCompletedByMe ? 'Completed' : isLocked ? 'LOCKED' : `${workerCount}/3`}
                  </div>
                </button>
              )
            })}
          </div>
        )}

        {/* Legend */}
        <div className="mt-6 flex items-center justify-center gap-6 text-xs" style={{ color: 'var(--text-muted)' }}>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: 'var(--bg-secondary)', border: '2px solid var(--accent-primary)' }} />
            <span>Available</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: 'var(--success-bg)', border: '2px solid var(--success-text)' }} />
            <span>Completed by you</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded" style={{ backgroundColor: 'var(--bg-tertiary)', border: '2px solid var(--border-default)', opacity: 0.5 }} />
            <span>Locked (3/3)</span>
          </div>
        </div>
      </div>
    </div>
  )
}
