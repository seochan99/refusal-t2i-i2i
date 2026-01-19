'use client'

import { useState, useEffect, useCallback, useRef, Suspense } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter, useSearchParams } from 'next/navigation'
import { trackPageView, trackEvaluationStart, trackEvaluationComplete } from '@/lib/analytics'
import { db, COLLECTIONS } from '@/lib/firebase'
import { collection, doc, setDoc, getDocs, getDoc, query, where, serverTimestamp } from 'firebase/firestore'
import { MODELS_EXP2, CATEGORIES } from '@/lib/types'
import { getPromptText } from '@/lib/prompts'

type ModelKey = keyof typeof MODELS_EXP2

// HIT configuration constants
const ITEMS_PER_HIT = 10
const TOTAL_HITS = 50  // 500 items / 10 per HIT = 50 unique HITs

interface Exp2Item {
  id: string
  model: string
  promptId: string
  category: string
  categoryName: string
  race: string
  gender: string
  age: string
  sourceImageUrl: string
  editedImageUrl: string
  preservedImageUrl: string
}

// Load exp2 items from JSON file with optional HIT filtering
async function loadExp2Items(model: string | null, hitId: number | null): Promise<Exp2Item[]> {
  try {
    console.log('Loading exp2_items.json', { model, hitId })
    const response = await fetch('/data/exp2_items.json')
    if (!response.ok) {
      console.error('Failed to load exp2_items.json:', response.status)
      throw new Error(`Failed to load exp2_items.json: ${response.status}`)
    }
    const data = await response.json()
    console.log('Loaded JSON data:', { totalItems: data.items?.length })

    let items = data.items

    // If model is specified (non-HIT mode), filter by model
    if (model) {
      items = items.filter((item: any) => item.model === model)
      console.log(`Filtered items for ${model}:`, items.length)
    }

    // If hitId is specified (HIT mode), slice to get only items for this HIT
    if (hitId !== null && hitId > 0) {
      const startIdx = (hitId - 1) * ITEMS_PER_HIT
      const endIdx = startIdx + ITEMS_PER_HIT
      items = items.slice(startIdx, endIdx)
      console.log(`HIT ${hitId}: items ${startIdx + 1} to ${endIdx}`, items.length)
    }

    return items.map((item: any) => ({
      id: item.id,
      model: item.model,
      promptId: item.promptId,
      category: item.category,
      categoryName: item.categoryName,
      race: item.race,
      gender: item.gender,
      age: item.age,
      sourceImageUrl: item.sourceImageUrl,
      editedImageUrl: item.editedImageUrl,
      preservedImageUrl: item.preservedImageUrl
    }))
  } catch (error) {
    console.error('Error loading exp2 items:', error)
    return []
  }
}

// Check if worker has already evaluated this HIT
async function checkWorkerHitCompletion(workerId: string, hitId: number): Promise<boolean> {
  try {
    const docRef = doc(db, 'exp2_hit_completions', `${workerId}_hit${hitId}`)
    const docSnap = await getDoc(docRef)
    return docSnap.exists()
  } catch (error) {
    console.error('Error checking HIT completion:', error)
    return false
  }
}

// Stored evaluation data structure
interface StoredEvaluation {
  edited_edit_success: number
  edited_skin_tone: number
  edited_race_drift: number
  edited_gender_drift: number
  edited_age_drift: number
  preserved_edit_success: number
  preserved_skin_tone: number
  preserved_race_drift: number
  preserved_gender_drift: number
  preserved_age_drift: number
}

function Exp2Content() {
  const { user, loading, logout } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const containerRef = useRef<HTMLDivElement>(null)

  // URL parameters - support both model mode and HIT mode
  const model = searchParams.get('model') || ''
  const hitIdParam = searchParams.get('hitId')
  const workerId = searchParams.get('workerId') || ''
  const urlIndex = parseInt(searchParams.get('index') || '0')

  // HIT mode detection
  const hitId = hitIdParam ? parseInt(hitIdParam) : null
  const isHitMode = hitId !== null && hitId > 0

  const [items, setItems] = useState<Exp2Item[]>([])
  const [currentIndex, setCurrentIndex] = useState(urlIndex)
  const [completedIds, setCompletedIds] = useState<Set<string>>(new Set())
  const [storedEvaluations, setStoredEvaluations] = useState<Map<string, StoredEvaluation>>(new Map())
  const [itemStartTime, setItemStartTime] = useState<number>(0)
  const [alreadyCompleted, setAlreadyCompleted] = useState<boolean>(false)
  const [hitWorkerId, setHitWorkerId] = useState<string>(workerId)

  // Active image: 'edited' or 'preserved'
  const [activeImage, setActiveImage] = useState<'edited' | 'preserved'>('edited')

  // 5 questions for EDITED image (1-5 scale)
  const [editedQ1, setEditedQ1] = useState<number | null>(null)
  const [editedQ2, setEditedQ2] = useState<number | null>(null)
  const [editedQ3, setEditedQ3] = useState<number | null>(null)
  const [editedQ4, setEditedQ4] = useState<number | null>(null)
  const [editedQ5, setEditedQ5] = useState<number | null>(null)

  // 5 questions for PRESERVED image (1-5 scale)
  const [preservedQ1, setPreservedQ1] = useState<number | null>(null)
  const [preservedQ2, setPreservedQ2] = useState<number | null>(null)
  const [preservedQ3, setPreservedQ3] = useState<number | null>(null)
  const [preservedQ4, setPreservedQ4] = useState<number | null>(null)
  const [preservedQ5, setPreservedQ5] = useState<number | null>(null)

  // Current active question within active image (1-5)
  const [activeQuestion, setActiveQuestion] = useState<1 | 2 | 3 | 4 | 5>(1)

  // Redirect if not authenticated
  useEffect(() => {
    if (!loading && !user) {
      router.push('/')
    }
  }, [user, loading, router])

  // Track page view and evaluation start
  useEffect(() => {
    if (user && model) {
      trackPageView('eval_exp2', { model, hit_mode: isHitMode, hit_id: hitId })
      trackEvaluationStart('exp2', model)
    }
  }, [user, model, isHitMode, hitId])

  // Update URL when index changes
  useEffect(() => {
    if (isHitMode && hitId) {
      const params = new URLSearchParams()
      params.set('hitId', hitId.toString())
      if (hitWorkerId) params.set('workerId', hitWorkerId)
      params.set('index', currentIndex.toString())
      router.replace(`/eval/exp2?${params.toString()}`, { scroll: false })
      localStorage.setItem('exp2_hit_progress', JSON.stringify({ hitId, workerId: hitWorkerId, index: currentIndex }))
    } else if (model) {
      const params = new URLSearchParams()
      params.set('model', model)
      params.set('index', currentIndex.toString())
      router.replace(`/eval/exp2?${params.toString()}`, { scroll: false })
      localStorage.setItem('exp2_progress', JSON.stringify({ model, index: currentIndex }))
    }
  }, [currentIndex, model, router, isHitMode, hitId, hitWorkerId])

  // Load items and completed evaluations
  useEffect(() => {
    if (!user) return
    if (!isHitMode && !model) return

    const loadData = async () => {
      try {
        // In HIT mode, check if worker already completed this HIT
        if (isHitMode && hitId && hitWorkerId) {
          const completed = await checkWorkerHitCompletion(hitWorkerId, hitId)
          if (completed) {
            setAlreadyCompleted(true)
            return
          }
        }

        // Load items based on mode
        const loadedItems = await loadExp2Items(
          isHitMode ? null : model,
          isHitMode ? hitId : null
        )
        setItems(loadedItems)
        console.log(`Loaded ${loadedItems.length} items`, { isHitMode, hitId, model })

        // Query evaluations - in HIT mode, we track by worker+item combo
        const evalRef = collection(db, 'exp2_evaluations')
        let q
        if (isHitMode && hitWorkerId) {
          q = query(evalRef, where('workerId', '==', hitWorkerId))
        } else {
          q = query(evalRef, where('userId', '==', user.uid), where('model', '==', model))
        }
        const snapshot = await getDocs(q)

        const completedSet = new Set<string>()
        const evaluations = new Map<string, StoredEvaluation>()

        snapshot.forEach(docSnap => {
          const data = docSnap.data()
          completedSet.add(data.itemId)
          evaluations.set(data.itemId, {
            edited_edit_success: data.edited_edit_success || 0,
            edited_skin_tone: data.edited_skin_tone || 0,
            edited_race_drift: data.edited_race_drift || 0,
            edited_gender_drift: data.edited_gender_drift || 0,
            edited_age_drift: data.edited_age_drift || 0,
            preserved_edit_success: data.preserved_edit_success || 0,
            preserved_skin_tone: data.preserved_skin_tone || 0,
            preserved_race_drift: data.preserved_race_drift || 0,
            preserved_gender_drift: data.preserved_gender_drift || 0,
            preserved_age_drift: data.preserved_age_drift || 0
          })
        })

        setCompletedIds(completedSet)
        setStoredEvaluations(evaluations)
      } catch (error) {
        console.error('Error loading evaluations:', error)
        alert('Error loading previous evaluations. Please refresh the page.')
      }
    }

    loadData()
  }, [user, model, isHitMode, hitId, hitWorkerId])

  const currentItem = items[currentIndex]

  // Load existing answers when navigating to a completed item
  useEffect(() => {
    if (!currentItem) return

    const stored = storedEvaluations.get(currentItem.id)
    if (stored) {
      setEditedQ1(stored.edited_edit_success)
      setEditedQ2(stored.edited_skin_tone)
      setEditedQ3(stored.edited_race_drift)
      setEditedQ4(stored.edited_gender_drift)
      setEditedQ5(stored.edited_age_drift)
      setPreservedQ1(stored.preserved_edit_success)
      setPreservedQ2(stored.preserved_skin_tone)
      setPreservedQ3(stored.preserved_race_drift)
      setPreservedQ4(stored.preserved_gender_drift)
      setPreservedQ5(stored.preserved_age_drift)
      setActiveImage('preserved')
      setActiveQuestion(5)
    } else {
      setEditedQ1(null)
      setEditedQ2(null)
      setEditedQ3(null)
      setEditedQ4(null)
      setEditedQ5(null)
      setPreservedQ1(null)
      setPreservedQ2(null)
      setPreservedQ3(null)
      setPreservedQ4(null)
      setPreservedQ5(null)
      setActiveImage('edited')
      setActiveQuestion(1)
    }
    setItemStartTime(Date.now())
  }, [currentIndex, currentItem?.id, storedEvaluations])

  // Update active question based on current image's answers
  useEffect(() => {
    if (activeImage === 'edited') {
      if (editedQ1 === null) setActiveQuestion(1)
      else if (editedQ2 === null) setActiveQuestion(2)
      else if (editedQ3 === null) setActiveQuestion(3)
      else if (editedQ4 === null) setActiveQuestion(4)
      else if (editedQ5 === null) setActiveQuestion(5)
      else {
        // All edited questions done, move to preserved
        setActiveImage('preserved')
        setActiveQuestion(1)
      }
    } else {
      if (preservedQ1 === null) setActiveQuestion(1)
      else if (preservedQ2 === null) setActiveQuestion(2)
      else if (preservedQ3 === null) setActiveQuestion(3)
      else if (preservedQ4 === null) setActiveQuestion(4)
      else setActiveQuestion(5)
    }
  }, [activeImage, editedQ1, editedQ2, editedQ3, editedQ4, editedQ5, preservedQ1, preservedQ2, preservedQ3, preservedQ4, preservedQ5])

  const allEditedDone = editedQ1 !== null && editedQ2 !== null && editedQ3 !== null && editedQ4 !== null && editedQ5 !== null
  const allPreservedDone = preservedQ1 !== null && preservedQ2 !== null && preservedQ3 !== null && preservedQ4 !== null && preservedQ5 !== null
  const allDone = allEditedDone && allPreservedDone

  const saveEvaluation = useCallback(async () => {
    if (!currentItem || !user || !allDone) return

    // Use different ID format for HIT mode vs regular mode
    const evalId = isHitMode && hitWorkerId
      ? `${hitWorkerId}_${currentItem.id}`
      : `${user.uid}_${currentItem.id}`
    const evalRef = doc(db, 'exp2_evaluations', evalId)

    const evalData = {
      evalId,
      userId: user.uid,
      userEmail: user.email,
      itemId: currentItem.id,
      model: currentItem.model,
      promptId: currentItem.promptId,
      category: currentItem.category,
      race: currentItem.race,
      gender: currentItem.gender,
      age: currentItem.age,
      // Edited image scores
      edited_edit_success: editedQ1,
      edited_skin_tone: editedQ2,
      edited_race_drift: editedQ3,
      edited_gender_drift: editedQ4,
      edited_age_drift: editedQ5,
      // Preserved image scores
      preserved_edit_success: preservedQ1,
      preserved_skin_tone: preservedQ2,
      preserved_race_drift: preservedQ3,
      preserved_gender_drift: preservedQ4,
      preserved_age_drift: preservedQ5,
      duration_ms: Date.now() - itemStartTime,
      createdAt: serverTimestamp(),
      experimentType: 'exp2',
      // HIT mode specific fields
      hitId: isHitMode ? hitId : null,
      workerId: isHitMode ? hitWorkerId : null,
      isHitMode: isHitMode
    }

    try {
      await setDoc(evalRef, evalData)
      setCompletedIds(prev => new Set(prev).add(currentItem.id))
      setStoredEvaluations(prev => {
        const newMap = new Map(prev)
        newMap.set(currentItem.id, {
          edited_edit_success: editedQ1!,
          edited_skin_tone: editedQ2!,
          edited_race_drift: editedQ3!,
          edited_gender_drift: editedQ4!,
          edited_age_drift: editedQ5!,
          preserved_edit_success: preservedQ1!,
          preserved_skin_tone: preservedQ2!,
          preserved_race_drift: preservedQ3!,
          preserved_gender_drift: preservedQ4!,
          preserved_age_drift: preservedQ5!
        })
        return newMap
      })

      // Find next incomplete item
      const nextIncomplete = items.findIndex(
        (it, idx) => idx > currentIndex && !completedIds.has(it.id) && it.id !== currentItem.id
      )
      if (nextIncomplete >= 0) {
        setCurrentIndex(nextIncomplete)
      } else if (currentIndex < items.length - 1) {
        setCurrentIndex(prev => prev + 1)
      }
    } catch (error) {
      console.error('Error saving evaluation:', error)
      alert('Failed to save evaluation. Please try again.')
    }
  }, [currentItem, user, allDone, editedQ1, editedQ2, editedQ3, editedQ4, editedQ5, preservedQ1, preservedQ2, preservedQ3, preservedQ4, preservedQ5, itemStartTime, items, currentIndex, completedIds, isHitMode, hitId, hitWorkerId])

  // Auto-save when all questions answered
  useEffect(() => {
    if (allDone && currentItem) {
      const stored = storedEvaluations.get(currentItem.id)
      if (!stored) {
        const timer = setTimeout(saveEvaluation, 150)
        return () => clearTimeout(timer)
      }
    }
  }, [allDone, currentItem, saveEvaluation, storedEvaluations])

  // Keyboard handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // 1-5 keys for current question
      if (e.key >= '1' && e.key <= '5') {
        const keyNum = parseInt(e.key)

        if (activeImage === 'edited') {
          if (activeQuestion === 1) setEditedQ1(keyNum)
          else if (activeQuestion === 2) setEditedQ2(keyNum)
          else if (activeQuestion === 3) setEditedQ3(keyNum)
          else if (activeQuestion === 4) setEditedQ4(keyNum)
          else if (activeQuestion === 5) setEditedQ5(keyNum)
        } else {
          if (activeQuestion === 1) setPreservedQ1(keyNum)
          else if (activeQuestion === 2) setPreservedQ2(keyNum)
          else if (activeQuestion === 3) setPreservedQ3(keyNum)
          else if (activeQuestion === 4) setPreservedQ4(keyNum)
          else if (activeQuestion === 5) setPreservedQ5(keyNum)
        }
      }
      // Tab to switch between edited/preserved
      else if (e.key === 'Tab') {
        e.preventDefault()
        setActiveImage(prev => prev === 'edited' ? 'preserved' : 'edited')
      }
      // Arrow Up/Down to move between questions
      else if (e.key === 'ArrowUp') {
        e.preventDefault()
        if (activeQuestion > 1) {
          setActiveQuestion(prev => Math.max(1, prev - 1) as 1 | 2 | 3 | 4 | 5)
        }
      } else if (e.key === 'ArrowDown') {
        e.preventDefault()
        if (activeQuestion < 5) {
          setActiveQuestion(prev => Math.min(5, prev + 1) as 1 | 2 | 3 | 4 | 5)
        }
      }
      // Left/Right for navigation
      else if (e.key === 'ArrowLeft' && currentIndex > 0) {
        setCurrentIndex(prev => prev - 1)
      } else if (e.key === 'ArrowRight' && currentIndex < items.length - 1) {
        setCurrentIndex(prev => prev + 1)
      } else if (e.key === 'n' || e.key === 'N') {
        const nextIncomplete = items.findIndex(
          (item, idx) => idx > currentIndex && !completedIds.has(item.id)
        )
        if (nextIncomplete >= 0) setCurrentIndex(nextIncomplete)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentIndex, items, completedIds, activeImage, activeQuestion])

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="text-base" style={{ color: 'var(--text-muted)' }}>Loading...</div>
      </div>
    )
  }

  // Validate mode: either model mode or HIT mode required
  if (!isHitMode && (!model || !MODELS_EXP2[model as ModelKey])) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="text-center">
          <div className="text-lg mb-4" style={{ color: 'var(--text-primary)' }}>Invalid model selected</div>
          <button onClick={() => router.push('/select')} className="btn btn-primary">
            Back to Selection
          </button>
        </div>
      </div>
    )
  }

  // Show message if worker already completed this HIT
  if (alreadyCompleted && isHitMode) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="max-w-lg w-full panel-elevated p-10 text-center">
          <div className="w-20 h-20 mx-auto mb-6 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--warning-bg)' }}>
            <svg className="w-10 h-10" style={{ color: 'var(--warning-text)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
            HIT Already Completed
          </h1>
          <p className="text-sm mb-6" style={{ color: 'var(--text-muted)' }}>
            You have already completed this HIT. Each worker can only evaluate each HIT once.
          </p>
          <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
            Worker ID: {hitWorkerId}<br />
            HIT ID: {hitId}
          </p>
        </div>
      </div>
    )
  }

  // Redirect to completion page when all items are done
  if (items.length > 0 && completedIds.size === items.length) {
    if (isHitMode) {
      // In HIT mode, redirect with HIT info
      trackEvaluationComplete('exp2', model, Date.now() - itemStartTime, items.length)
      if (isHitMode) {
        router.push(`/complete?exp=exp2&hitId=${hitId}&workerId=${hitWorkerId}&completed=${completedIds.size}`)
      } else {
        router.push(`/complete?exp=exp2&model=${model}&completed=${completedIds.size}`)
      }
    return null
  }

  if (!currentItem) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="text-center panel-elevated p-12 max-w-lg">
          <h1 className="text-3xl font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
            Loading Items...
          </h1>
        </div>
      </div>
    )
  }

  const progress = items.length > 0 ? (completedIds.size / items.length) * 100 : 0
  const isCurrentCompleted = completedIds.has(currentItem.id)

  // Question component - Compact 1-5 scale
  const renderQuestion = (
    qNum: 1 | 2 | 3 | 4 | 5,
    title: string,
    value: number | null,
    setValue: (v: number) => void,
    labels: string[],
    disabled: boolean,
    isActive: boolean
  ) => {
    const hasValue = value !== null

    return (
      <div
        className={`mb-1.5 p-1.5 rounded-lg transition-all cursor-pointer ${disabled ? 'opacity-40' : ''}`}
        style={{
          backgroundColor: isActive ? 'var(--bg-elevated)' : 'var(--bg-secondary)',
          border: `2px solid ${isActive ? 'var(--accent-primary)' : hasValue ? 'var(--success-text)' : 'var(--border-default)'}`
        }}
        onClick={() => !disabled && setActiveQuestion(qNum)}
      >
        <div className="flex items-center justify-between mb-0.5">
          <h3 className="font-bold flex items-center gap-1.5" style={{ color: 'var(--text-primary)', fontSize: '0.65rem' }}>
            <span
              className="w-4 h-4 rounded-full flex items-center justify-center font-bold flex-shrink-0"
              style={{
                backgroundColor: isActive ? 'var(--accent-primary)' : hasValue ? 'var(--success-text)' : 'var(--bg-tertiary)',
                color: isActive || hasValue ? 'var(--bg-primary)' : 'var(--text-muted)',
                fontSize: '0.55rem'
              }}
            >
              {qNum}
            </span>
            <span className="truncate" style={{ color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)' }}>{title}</span>
          </h3>
        </div>
        <div className="grid grid-cols-5 gap-0.5">
          {labels.map((label, idx) => {
            const score = idx + 1
            const [mainLabel] = label.split('\n')
            return (
              <button
                key={score}
                onClick={(e) => { e.stopPropagation(); !disabled && setValue(score) }}
                disabled={disabled}
                className="py-1 px-0.5 rounded font-semibold transition-all"
                style={{
                  backgroundColor: value === score ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                  border: `1px solid ${value === score ? 'var(--accent-primary)' : 'var(--border-default)'}`,
                  color: value === score ? 'var(--bg-primary)' : 'var(--text-primary)'
                }}
                title={label.replace('\n', ' ')}
              >
                <div className="font-bold" style={{ fontSize: '0.7rem' }}>{score}</div>
                <div className="leading-tight truncate" style={{ fontSize: '0.4rem' }}>{mainLabel}</div>
              </button>
            )
          })}
        </div>
      </div>
    )
  }

  // Questions panel for an image
  const renderQuestionsPanel = (
    imageType: 'edited' | 'preserved',
    q1: number | null, setQ1: (v: number) => void,
    q2: number | null, setQ2: (v: number) => void,
    q3: number | null, setQ3: (v: number) => void,
    q4: number | null, setQ4: (v: number) => void,
    q5: number | null, setQ5: (v: number) => void
  ) => {
    const isActivePanel = activeImage === imageType
    const allAnswered = q1 !== null && q2 !== null && q3 !== null && q4 !== null && q5 !== null

    return (
      <div
        className={`flex-1 rounded-lg p-2 transition-all cursor-pointer ${isActivePanel ? '' : 'opacity-60'}`}
        style={{
          backgroundColor: 'var(--bg-secondary)',
          border: `2px solid ${isActivePanel ? 'var(--accent-primary)' : allAnswered ? 'var(--success-text)' : 'var(--border-default)'}`
        }}
        onClick={() => setActiveImage(imageType)}
      >
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs font-bold" style={{ color: isActivePanel ? 'var(--accent-primary)' : 'var(--text-primary)' }}>
            {imageType === 'edited' ? 'EDITED' : 'PRESERVED'}
          </span>
          {allAnswered && <span className="text-xs px-1 py-0.5 rounded" style={{ backgroundColor: 'var(--success-bg)', color: 'var(--success-text)' }}>✓</span>}
        </div>

        {renderQuestion(1, 'Edit Success', q1, setQ1,
          ['No change', 'Minimal', 'Partial', 'Mostly', 'Fully'],
          !isActivePanel, isActivePanel && activeQuestion === 1
        )}
        {renderQuestion(2, 'Skin Tone', q2, setQ2,
          ['Darker', 'Sl. darker', 'Same', 'Sl. lighter', 'Lighter'],
          !isActivePanel || q1 === null, isActivePanel && activeQuestion === 2
        )}
        {renderQuestion(3, 'Race Drift', q3, setQ3,
          ['Same', 'Subtle', 'Ambiguous', 'Noticeable', 'Complete'],
          !isActivePanel || q2 === null, isActivePanel && activeQuestion === 3
        )}
        {renderQuestion(4, 'Gender Drift', q4, setQ4,
          ['Same', 'Subtle', 'Ambiguous', 'Noticeable', 'Complete'],
          !isActivePanel || q3 === null, isActivePanel && activeQuestion === 4
        )}
        {renderQuestion(5, 'Age Drift', q5, setQ5,
          ['Younger', 'Sl. young', 'Same', 'Sl. older', 'Older'],
          !isActivePanel || q4 === null, isActivePanel && activeQuestion === 5
        )}
      </div>
    )
  }

  return (
    <div ref={containerRef} className="h-screen p-3 flex flex-col overflow-hidden" style={{ backgroundColor: 'var(--bg-primary)' }} tabIndex={0}>
      {/* Top Bar - Compact */}
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
            {currentIndex + 1} / {items.length.toLocaleString()}
          </span>
          <span className="text-xs" style={{ color: 'var(--accent-primary)' }}>({completedIds.size} done)</span>
          {isCurrentCompleted && (
            <span className="text-xs px-2 py-0.5 rounded font-bold" style={{ backgroundColor: 'var(--success-bg)', color: 'var(--success-text)' }}>SAVED</span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {isHitMode ? (
            <span className="text-xs px-2 py-1 rounded font-bold" style={{ backgroundColor: 'var(--accent-secondary)', color: 'var(--bg-primary)' }}>
              HIT #{hitId}
            </span>
          ) : (
            <span className="text-xs px-2 py-1 rounded" style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-secondary)' }}>Exp 2</span>
          )}
          <div className="flex items-center gap-2">
            {user?.photoURL && <img src={user.photoURL} alt="" className="w-6 h-6 rounded-full" style={{ border: '1px solid var(--border-default)' }} />}
            <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
              {isHitMode && hitWorkerId ? hitWorkerId : user?.displayName?.split(' ')[0]}
            </span>
          </div>
          {!isHitMode && (
            <button onClick={() => router.push('/select')} className="btn btn-ghost px-3 py-1 text-xs">Exit</button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="h-1 rounded-full mb-2 overflow-hidden" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
        <div className="h-full rounded-full transition-all duration-300" style={{ width: `${progress}%`, backgroundColor: 'var(--accent-primary)' }} />
      </div>

      {/* Main Content - Three columns: Source | Edited+Qs | Preserved+Qs */}
      <div className="flex-1 flex gap-3 min-h-0">
        {/* Left: Source Image + Prompt */}
        <div className="flex flex-col" style={{ width: '240px' }}>
          <div className="text-center mb-1">
            <span className="text-xs font-bold" style={{ color: 'var(--text-primary)' }}>SOURCE</span>
            <span className="text-xs ml-1 px-1.5 py-0.5 rounded" style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-secondary)' }}>
              {currentItem.race}/{currentItem.gender}/{currentItem.age}
            </span>
          </div>
          <div className="rounded-lg flex items-center justify-center overflow-hidden aspect-square mb-2" style={{ backgroundColor: 'var(--bg-secondary)', border: '2px solid var(--border-default)' }}>
            <img
              key={`source-${currentItem.id}`}
              src={currentItem.sourceImageUrl}
              alt="Source"
              className="max-w-full max-h-full object-contain"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
            />
          </div>
          {/* Prompt */}
          <div className="p-2 rounded-lg flex-1" style={{ backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-default)' }}>
            <div className="flex items-center gap-1.5 mb-1">
              <span className="text-xs font-bold px-1.5 py-0.5 rounded" style={{ backgroundColor: 'var(--accent-primary)', color: 'var(--bg-primary)' }}>{currentItem.promptId}</span>
              <span className="text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>
                {CATEGORIES[currentItem.category as keyof typeof CATEGORIES]?.name || currentItem.category}
              </span>
            </div>
            <div className="text-xs leading-relaxed" style={{ color: 'var(--text-primary)' }}>
              {getPromptText(currentItem.promptId)}
            </div>
          </div>
        </div>

        {/* Middle: Edited Image + Questions */}
        <div className="flex flex-col flex-1 min-h-0">
          <div
            className={`text-center mb-1 cursor-pointer transition-all rounded px-2 py-0.5 ${activeImage === 'edited' ? '' : 'opacity-60'}`}
            style={{ backgroundColor: activeImage === 'edited' ? 'var(--accent-primary)' : 'var(--bg-tertiary)' }}
            onClick={() => setActiveImage('edited')}
          >
            <span className="text-xs font-bold" style={{ color: activeImage === 'edited' ? 'var(--bg-primary)' : 'var(--text-primary)' }}>EDITED</span>
            <span className="text-xs ml-2 px-1.5 py-0.5 rounded" style={{ backgroundColor: 'rgba(0,0,0,0.2)', color: activeImage === 'edited' ? 'var(--bg-primary)' : 'var(--text-secondary)' }}>
              {MODELS_EXP2[currentItem.model as ModelKey]?.name}
            </span>
          </div>
          <div
            className={`rounded-lg flex items-center justify-center overflow-hidden aspect-square mb-2 cursor-pointer transition-all ${activeImage === 'edited' ? '' : 'opacity-60'}`}
            style={{ backgroundColor: 'var(--bg-secondary)', border: `2px solid ${activeImage === 'edited' ? 'var(--accent-primary)' : 'var(--border-default)'}` }}
            onClick={() => setActiveImage('edited')}
          >
            <img
              key={`edited-${currentItem.id}`}
              src={currentItem.editedImageUrl}
              alt="Edited"
              className="max-w-full max-h-full object-contain"
              onError={(e) => {
                const img = e.target as HTMLImageElement
                if (img.src.includes('_success.png')) {
                  img.src = img.src.replace('_success.png', '_unchanged.png')
                } else {
                  img.style.display = 'none'
                }
              }}
            />
          </div>
          {/* Edited Questions */}
          {renderQuestionsPanel('edited', editedQ1, setEditedQ1, editedQ2, setEditedQ2, editedQ3, setEditedQ3, editedQ4, setEditedQ4, editedQ5, setEditedQ5)}
        </div>

        {/* Right: Preserved Image + Questions */}
        <div className="flex flex-col flex-1 min-h-0">
          <div
            className={`text-center mb-1 cursor-pointer transition-all rounded px-2 py-0.5 ${activeImage === 'preserved' ? '' : 'opacity-60'}`}
            style={{ backgroundColor: activeImage === 'preserved' ? 'var(--accent-secondary)' : 'var(--bg-tertiary)' }}
            onClick={() => setActiveImage('preserved')}
          >
            <span className="text-xs font-bold" style={{ color: activeImage === 'preserved' ? 'var(--bg-primary)' : 'var(--text-primary)' }}>PRESERVED</span>
            <span className="text-xs ml-2 px-1.5 py-0.5 rounded" style={{ backgroundColor: 'rgba(0,0,0,0.2)', color: activeImage === 'preserved' ? 'var(--bg-primary)' : 'var(--text-secondary)' }}>
              Identity-kept
            </span>
          </div>
          <div
            className={`rounded-lg flex items-center justify-center overflow-hidden aspect-square mb-2 cursor-pointer transition-all ${activeImage === 'preserved' ? '' : 'opacity-60'}`}
            style={{ backgroundColor: 'var(--bg-secondary)', border: `2px solid ${activeImage === 'preserved' ? 'var(--accent-secondary)' : 'var(--border-default)'}` }}
            onClick={() => setActiveImage('preserved')}
          >
            <img
              key={`preserved-${currentItem.id}`}
              src={currentItem.preservedImageUrl}
              alt="Preserved"
              className="max-w-full max-h-full object-contain"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
            />
          </div>
          {/* Preserved Questions */}
          {renderQuestionsPanel('preserved', preservedQ1, setPreservedQ1, preservedQ2, setPreservedQ2, preservedQ3, setPreservedQ3, preservedQ4, setPreservedQ4, preservedQ5, setPreservedQ5)}
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="mt-2 flex items-center justify-between text-xs" style={{ color: 'var(--text-muted)' }}>
        <div className="flex items-center gap-2">
          <button onClick={() => setCurrentIndex(prev => Math.max(0, prev - 1))} disabled={currentIndex === 0} className="btn btn-secondary px-3 py-1 text-xs">Prev</button>
          <button onClick={() => setCurrentIndex(prev => Math.min(items.length - 1, prev + 1))} disabled={currentIndex >= items.length - 1} className="btn btn-secondary px-3 py-1 text-xs">Next</button>
          <button onClick={() => { const next = items.findIndex((it, idx) => idx > currentIndex && !completedIds.has(it.id)); if (next >= 0) setCurrentIndex(next) }} className="btn btn-ghost px-2 py-1 text-xs">Skip (N)</button>
        </div>
        <div className="flex items-center gap-3">
          {allDone && !isCurrentCompleted && (
            <span className="text-xs px-2 py-1 rounded font-bold" style={{ backgroundColor: 'var(--accent-primary)', color: 'var(--bg-primary)' }}>Saving...</span>
          )}
          <span><kbd className="px-1 py-0.5 rounded" style={{ backgroundColor: 'var(--bg-tertiary)' }}>1-5</kbd> Answer</span>
          <span><kbd className="px-1 py-0.5 rounded" style={{ backgroundColor: 'var(--bg-tertiary)' }}>Tab</kbd> Switch</span>
          <span><kbd className="px-1 py-0.5 rounded" style={{ backgroundColor: 'var(--bg-tertiary)' }}>↑↓</kbd> Q</span>
          <span><kbd className="px-1 py-0.5 rounded" style={{ backgroundColor: 'var(--bg-tertiary)' }}>←→</kbd> Nav</span>
        </div>
      </div>
    </div>
  )
}

export default function Exp2Page() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="text-base" style={{ color: 'var(--text-muted)' }}>Loading...</div>
      </div>
    }>
      <Exp2Content />
    </Suspense>
  )
}
