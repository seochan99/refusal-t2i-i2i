'use client'

import { useState, useEffect, useMemo } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { trackPageView, trackEvent } from '@/lib/analytics'
import { db } from '@/lib/firebase'
import { doc, setDoc, getDoc, getDocs, collection, serverTimestamp, query, where, runTransaction, Timestamp, updateDoc } from 'firebase/firestore'
import { AMT_UNIFIED_CONFIG } from '@/lib/types'
import { readProlificSession, getProlificCompletionUrl } from '@/lib/prolific'

interface TaskStatus {
  taskId: number
  completedUsers: string[]  // User UIDs who completed this task
  isLocked: boolean
  available: number         // Slots available for claiming
  inProgress: number        // Slots currently in progress
  completed: number         // Slots completed
}

// Slot timeout: 2 hours (if a user claims a slot but doesn't complete within 2 hours, it becomes available again)
const SLOT_TIMEOUT_MS = 2 * 60 * 60 * 1000

/**
 * Check if user already has an in_progress slot (can only have one at a time)
 */
async function getUserInProgressSlot(userId: string): Promise<{ taskId: number; slotId: string } | null> {
  const now = Date.now()
  const allSlotsSnapshot = await getDocs(collection(db, 'amt_task_slots'))

  for (const slotDoc of allSlotsSnapshot.docs) {
    const data = slotDoc.data()
    if (data.claimedBy === userId && data.status === 'in_progress') {
      // Check if not timed out
      if (data.claimedAt) {
        const claimedTime = data.claimedAt instanceof Timestamp
          ? data.claimedAt.toMillis()
          : new Date(data.claimedAt).getTime()
        if (now - claimedTime <= SLOT_TIMEOUT_MS) {
          return { taskId: data.taskId, slotId: slotDoc.id }
        }
      }
    }
  }
  return null
}

/**
 * Release all in_progress slots for a user
 */
async function releaseUserSlots(userId: string): Promise<number> {
  const allSlotsSnapshot = await getDocs(collection(db, 'amt_task_slots'))
  let released = 0

  for (const slotDoc of allSlotsSnapshot.docs) {
    const data = slotDoc.data()
    if (data.claimedBy === userId && data.status === 'in_progress') {
      await updateDoc(slotDoc.ref, {
        claimedBy: null,
        claimedAt: null,
        status: 'available'
      })
      released++
    }
  }
  return released
}

/**
 * Atomically claim a task slot using Firestore Transaction.
 * This prevents race conditions where multiple users try to claim the same slot.
 * A user can only have ONE in_progress slot at a time.
 *
 * @param taskId - The task ID to claim a slot for
 * @param userId - The user's UID
 * @returns { success: boolean, error?: string }
 */
async function claimTaskSlot(taskId: number, userId: string): Promise<{ success: boolean; error?: string }> {
  const now = Date.now()

  try {
    // First check if user already has an in_progress slot
    const existingSlot = await getUserInProgressSlot(userId)
    if (existingSlot) {
      return {
        success: false,
        error: `You already have Task ${existingSlot.taskId} in progress. Complete or abandon it first.`
      }
    }

    // Query for available or timed-out slots for this task
    const slotsQuery = query(
      collection(db, 'amt_task_slots'),
      where('taskId', '==', taskId)
    )
    const slotsSnapshot = await getDocs(slotsQuery)

    if (slotsSnapshot.empty) {
      console.warn(`No slots found for task ${taskId}`)
      return { success: false, error: 'No slots found for this task' }
    }

    // Find an available or timed-out slot
    let targetSlotRef = null
    for (const slotDoc of slotsSnapshot.docs) {
      const data = slotDoc.data()

      // Case 1: Available slot
      if (data.status === 'available') {
        targetSlotRef = slotDoc.ref
        break
      }

      // Case 2: Timed-out in_progress slot (user abandoned)
      if (data.status === 'in_progress' && data.claimedAt) {
        const claimedTime = data.claimedAt instanceof Timestamp
          ? data.claimedAt.toMillis()
          : new Date(data.claimedAt).getTime()

        if (now - claimedTime > SLOT_TIMEOUT_MS) {
          console.log(`Slot ${slotDoc.id} timed out, reclaiming...`)
          targetSlotRef = slotDoc.ref
          break
        }
      }
    }

    if (!targetSlotRef) {
      console.log(`No available slots for task ${taskId}`)
      return { success: false, error: 'This task is full. Please select another task.' }
    }

    // Atomic claim with transaction
    await runTransaction(db, async (transaction) => {
      const snap = await transaction.get(targetSlotRef!)
      const data = snap.data()

      if (!data) {
        throw new Error('Slot document not found')
      }

      // Re-validate availability (another user might have claimed it)
      const isAvailable = data.status === 'available'
      const isTimedOut = data.status === 'in_progress' &&
        data.claimedAt &&
        (now - (data.claimedAt instanceof Timestamp
          ? data.claimedAt.toMillis()
          : new Date(data.claimedAt).getTime()) > SLOT_TIMEOUT_MS)

      if (!isAvailable && !isTimedOut) {
        throw new Error('Slot no longer available')
      }

      transaction.update(targetSlotRef!, {
        claimedBy: userId,
        claimedAt: serverTimestamp(),
        status: 'in_progress'
      })
    })

    console.log(`✅ Successfully claimed slot for task ${taskId}`)
    return { success: true }
  } catch (error) {
    console.error(`Failed to claim slot for task ${taskId}:`, error)
    return { success: false, error: 'Failed to claim slot. Please try again.' }
  }
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
  const [userInProgressTask, setUserInProgressTask] = useState<number | null>(null)
  const [isLoadingTasks, setIsLoadingTasks] = useState(true)
  const [isSelecting, setIsSelecting] = useState(false)
  const [isAbandoning, setIsAbandoning] = useState(false)
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

  // Load task statuses from Firebase (using slot-based tracking)
  useEffect(() => {
    async function loadTaskStatuses() {
      if (!user) return

      setIsLoadingTasks(true)
      const now = Date.now()

      try {
        // Get all task slots
        const slotsRef = collection(db, 'amt_task_slots')
        const slotsSnapshot = await getDocs(slotsRef)

        const statusMap = new Map<number, TaskStatus>()

        // Initialize all tasks
        for (let i = 1; i <= AMT_UNIFIED_CONFIG.totalTasks; i++) {
          statusMap.set(i, {
            taskId: i,
            completedUsers: [],
            isLocked: false,
            available: 3,
            inProgress: 0,
            completed: 0
          })
        }

        // Process slots to calculate availability and find user's in_progress task
        let userInProgress: number | null = null

        slotsSnapshot.forEach(docSnap => {
          const data = docSnap.data()
          const taskId = data.taskId as number
          const status = statusMap.get(taskId)

          if (!status) return

          if (data.status === 'completed') {
            status.completed++
            status.available--
            // Track completed users
            if (data.claimedBy && !status.completedUsers.includes(data.claimedBy)) {
              status.completedUsers.push(data.claimedBy)
            }
          } else if (data.status === 'in_progress') {
            // Check timeout
            const claimedTime = data.claimedAt instanceof Timestamp
              ? data.claimedAt.toMillis()
              : data.claimedAt ? new Date(data.claimedAt).getTime() : 0

            const isTimedOut = claimedTime && (now - claimedTime > SLOT_TIMEOUT_MS)

            if (!isTimedOut) {
              status.inProgress++
              status.available--

              // Check if this is current user's in_progress slot
              if (data.claimedBy === user.uid) {
                userInProgress = taskId
              }
            }
            // Timed-out slots remain as available
          }

          // Task is locked if no available slots
          status.isLocked = status.available <= 0
        })

        setTaskStatuses(statusMap)
        setUserInProgressTask(userInProgress)

        // Find which tasks current user has completed (from amt_task_completions)
        const completionsRef = collection(db, 'amt_task_completions')
        const completionsSnapshot = await getDocs(completionsRef)

        const userTasks = new Set<number>()
        completionsSnapshot.forEach(docSnap => {
          const data = docSnap.data()
          if (data.userId === user.uid) {
            userTasks.add(data.taskId as number)
          }
        })
        setUserCompletedTasks(userTasks)

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

  const handleSelectTask = async (taskId: number) => {
    if (consentStatus !== 'agreed') {
      setError('Please review and agree to the IRB consent before starting a task')
      return
    }

    if (!user) {
      setError('Please sign in to continue')
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

    // Check if user already has an in_progress task
    if (userInProgressTask && userInProgressTask !== taskId) {
      setError(`You already have Task ${userInProgressTask} in progress. Complete or abandon it first.`)
      return
    }

    // Clear any previous error
    setError('')
    setIsSelecting(true)

    try {
      // Atomically claim a slot for this task
      const result = await claimTaskSlot(taskId, user.uid)

      if (!result.success) {
        setError(result.error || 'This task is full. Please select another task.')
        // Reload task statuses to reflect the latest state
        setIsLoadingTasks(true)
        const slotsRef = collection(db, 'amt_task_slots')
        const slotsSnapshot = await getDocs(slotsRef)
        const now = Date.now()

        const statusMap = new Map<number, TaskStatus>()
        for (let i = 1; i <= AMT_UNIFIED_CONFIG.totalTasks; i++) {
          statusMap.set(i, {
            taskId: i,
            completedUsers: [],
            isLocked: false,
            available: 3,
            inProgress: 0,
            completed: 0
          })
        }

        slotsSnapshot.forEach(docSnap => {
          const data = docSnap.data()
          const taskId = data.taskId as number
          const taskStatus = statusMap.get(taskId)
          if (!taskStatus) return

          if (data.status === 'completed') {
            taskStatus.completed++
            taskStatus.available--
            if (data.claimedBy && !taskStatus.completedUsers.includes(data.claimedBy)) {
              taskStatus.completedUsers.push(data.claimedBy)
            }
          } else if (data.status === 'in_progress') {
            const claimedTime = data.claimedAt instanceof Timestamp
              ? data.claimedAt.toMillis()
              : data.claimedAt ? new Date(data.claimedAt).getTime() : 0
            const isTimedOut = claimedTime && (now - claimedTime > SLOT_TIMEOUT_MS)
            if (!isTimedOut) {
              taskStatus.inProgress++
              taskStatus.available--
            }
          }
          taskStatus.isLocked = taskStatus.available <= 0
        })

        setTaskStatuses(statusMap)
        setIsLoadingTasks(false)
        return
      }

      // Successfully claimed - navigate to evaluation page
      router.push(`/tasks/eval?taskId=${taskId}`)
    } catch (err) {
      console.error('Error selecting task:', err)
      setError('An error occurred. Please try again.')
    } finally {
      setIsSelecting(false)
    }
  }

  // Handle abandoning current in_progress task
  const handleAbandonTask = async () => {
    if (!user || !userInProgressTask) return

    setIsAbandoning(true)
    setError('')

    try {
      const released = await releaseUserSlots(user.uid)
      console.log(`✅ Released ${released} slot(s) for user`)

      // Reload task statuses
      setUserInProgressTask(null)

      // Trigger a reload of task statuses
      const slotsRef = collection(db, 'amt_task_slots')
      const slotsSnapshot = await getDocs(slotsRef)
      const now = Date.now()

      const statusMap = new Map<number, TaskStatus>()
      for (let i = 1; i <= AMT_UNIFIED_CONFIG.totalTasks; i++) {
        statusMap.set(i, {
          taskId: i,
          completedUsers: [],
          isLocked: false,
          available: 3,
          inProgress: 0,
          completed: 0
        })
      }

      slotsSnapshot.forEach(docSnap => {
        const data = docSnap.data()
        const taskId = data.taskId as number
        const taskStatus = statusMap.get(taskId)
        if (!taskStatus) return

        if (data.status === 'completed') {
          taskStatus.completed++
          taskStatus.available--
          if (data.claimedBy && !taskStatus.completedUsers.includes(data.claimedBy)) {
            taskStatus.completedUsers.push(data.claimedBy)
          }
        } else if (data.status === 'in_progress') {
          const claimedTime = data.claimedAt instanceof Timestamp
            ? data.claimedAt.toMillis()
            : data.claimedAt ? new Date(data.claimedAt).getTime() : 0
          const isTimedOut = claimedTime && (now - claimedTime > SLOT_TIMEOUT_MS)
          if (!isTimedOut) {
            taskStatus.inProgress++
            taskStatus.available--
          }
        }
        taskStatus.isLocked = taskStatus.available <= 0
      })

      setTaskStatuses(statusMap)
    } catch (err) {
      console.error('Error abandoning task:', err)
      setError('Failed to abandon task. Please try again.')
    } finally {
      setIsAbandoning(false)
    }
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
                onClick={() => window.open(getProlificCompletionUrl(), '_blank')}
                className="btn btn-primary mt-3 px-6 py-2"
              >
                Finish on Prolific
              </button>
            )}
          </div>
        )}

        {/* Current in-progress task banner */}
        {userInProgressTask && (
          <div className="mb-4 p-4 rounded-lg flex items-center justify-between" style={{ backgroundColor: 'var(--info-bg)', border: '1px solid var(--info-text)' }}>
            <div>
              <div className="text-xs uppercase tracking-wider mb-0.5" style={{ color: 'var(--info-text)' }}>
                Task In Progress
              </div>
              <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                You have Task {userInProgressTask} in progress
              </div>
              <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                Complete it or abandon to select a different task
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => router.push(`/tasks/eval?taskId=${userInProgressTask}`)}
                className="btn btn-primary px-4 py-2 text-sm"
              >
                Continue Task {userInProgressTask}
              </button>
              <button
                onClick={handleAbandonTask}
                disabled={isAbandoning}
                className="px-4 py-2 text-sm rounded-lg transition-colors"
                style={{
                  backgroundColor: 'var(--error-bg)',
                  color: 'var(--error-text)',
                  border: '1px solid var(--error-text)'
                }}
              >
                {isAbandoning ? 'Abandoning...' : 'Abandon'}
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 rounded text-sm" style={{ backgroundColor: 'var(--error-bg)', color: 'var(--error-text)' }}>
            {error}
          </div>
        )}

        {isSelecting && (
          <div className="mb-4 p-3 rounded text-sm flex items-center gap-2" style={{ backgroundColor: 'var(--info-bg)', color: 'var(--info-text)' }}>
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Reserving your task slot...
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
                  disabled={!isAvailable || isSelecting}
                  className={`p-4 rounded-lg transition-all ${isAvailable && !isSelecting ? 'hover:scale-105 cursor-pointer' : 'cursor-not-allowed'}`}
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
                    {[0, 1, 2].map(slot => {
                      // Determine slot state: completed, in_progress, or available
                      const completedCount = status?.completed || 0
                      const inProgressCount = status?.inProgress || 0

                      let slotState: 'completed' | 'in_progress' | 'available'
                      if (slot < completedCount) {
                        slotState = 'completed'
                      } else if (slot < completedCount + inProgressCount) {
                        slotState = 'in_progress'
                      } else {
                        slotState = 'available'
                      }

                      return (
                        <div
                          key={slot}
                          className="w-3 h-3 rounded-full"
                          style={{
                            backgroundColor: slotState === 'completed'
                              ? 'var(--success-text)'
                              : slotState === 'in_progress'
                                ? 'var(--warning-text)'
                                : 'var(--bg-tertiary)',
                            border: '1px solid var(--border-default)'
                          }}
                          title={slotState === 'completed' ? 'Completed' : slotState === 'in_progress' ? 'In Progress' : 'Available'}
                        />
                      )
                    })}
                  </div>
                  <div className="text-xs mt-1" style={{
                    color: isCompletedByMe
                      ? 'var(--success-text)'
                      : isLocked
                        ? 'var(--error-text)'
                        : 'var(--text-muted)'
                  }}>
                    {isCompletedByMe
                      ? 'Completed ✓'
                      : isLocked
                        ? 'FULL 🔒'
                        : `${status?.available || 0} avail`}
                  </div>
                </button>
              )
            })}
          </div>
        )}

        {/* Legend */}
        <div className="mt-6 flex flex-wrap items-center justify-center gap-4 text-xs" style={{ color: 'var(--text-muted)' }}>
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
            <span>Full</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-medium">Slots:</span>
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: 'var(--success-text)' }} />
            <span>Done</span>
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: 'var(--warning-text)' }} />
            <span>In Progress</span>
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: 'var(--bg-tertiary)', border: '1px solid var(--border-default)' }} />
            <span>Open</span>
          </div>
        </div>
      </div>
    </div>
  )
}
