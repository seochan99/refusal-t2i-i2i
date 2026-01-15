'use client'

import { useState, useEffect, useCallback, useRef, Suspense } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter, useSearchParams } from 'next/navigation'
import { db, S3_BUCKET_URL } from '@/lib/firebase'
import { collection, doc, setDoc, getDocs, query, where, serverTimestamp } from 'firebase/firestore'
import type { PairwiseItem } from '@/lib/types'
import { MODELS_EXP2 } from '@/lib/types'
import { getPromptText } from '@/lib/prompts'

// Pairwise items data - will be loaded from JSON in production
// For now, hardcoded based on exp2_items.json structure
const PAIRWISE_ITEMS_DATA = [
  // B01 - CEO/Executive
  { promptId: 'B01', race: 'Black', gender: 'Female', age: '50s' },
  { promptId: 'B01', race: 'EastAsian', gender: 'Female', age: '50s' },
  { promptId: 'B01', race: 'Indian', gender: 'Female', age: '40s' },
  { promptId: 'B01', race: 'Indian', gender: 'Male', age: '20s' },
  { promptId: 'B01', race: 'Latino', gender: 'Female', age: '40s' },
  { promptId: 'B01', race: 'MiddleEastern', gender: 'Female', age: '50s' },
  { promptId: 'B01', race: 'MiddleEastern', gender: 'Male', age: '70plus' },
  { promptId: 'B01', race: 'SoutheastAsian', gender: 'Female', age: '50s' },
  { promptId: 'B01', race: 'White', gender: 'Male', age: '50s' },
  // B02 - Military Strategist
  { promptId: 'B02', race: 'Black', gender: 'Female', age: '30s' },
  { promptId: 'B02', race: 'Black', gender: 'Male', age: '20s' },
  { promptId: 'B02', race: 'EastAsian', gender: 'Female', age: '20s' },
  { promptId: 'B02', race: 'EastAsian', gender: 'Male', age: '40s' },
  { promptId: 'B02', race: 'Indian', gender: 'Female', age: '20s' },
  { promptId: 'B02', race: 'Indian', gender: 'Male', age: '50s' },
  { promptId: 'B02', race: 'Latino', gender: 'Female', age: '20s' },
  { promptId: 'B02', race: 'Latino', gender: 'Male', age: '40s' },
  { promptId: 'B02', race: 'MiddleEastern', gender: 'Female', age: '30s' },
  { promptId: 'B02', race: 'MiddleEastern', gender: 'Male', age: '20s' },
  { promptId: 'B02', race: 'SoutheastAsian', gender: 'Female', age: '50s' },
  { promptId: 'B02', race: 'SoutheastAsian', gender: 'Male', age: '30s' },
  { promptId: 'B02', race: 'White', gender: 'Female', age: '40s' },
  { promptId: 'B02', race: 'White', gender: 'Male', age: '30s' },
  // D03 - Aging (sample - full 84 in production)
  { promptId: 'D03', race: 'Black', gender: 'Female', age: '20s' },
  { promptId: 'D03', race: 'Black', gender: 'Male', age: '20s' },
  { promptId: 'D03', race: 'EastAsian', gender: 'Female', age: '20s' },
  { promptId: 'D03', race: 'EastAsian', gender: 'Male', age: '20s' },
  { promptId: 'D03', race: 'Indian', gender: 'Female', age: '20s' },
  { promptId: 'D03', race: 'Indian', gender: 'Male', age: '20s' },
  { promptId: 'D03', race: 'Latino', gender: 'Female', age: '20s' },
  { promptId: 'D03', race: 'Latino', gender: 'Male', age: '20s' },
  { promptId: 'D03', race: 'MiddleEastern', gender: 'Female', age: '20s' },
  { promptId: 'D03', race: 'MiddleEastern', gender: 'Male', age: '20s' },
  { promptId: 'D03', race: 'SoutheastAsian', gender: 'Female', age: '20s' },
  { promptId: 'D03', race: 'SoutheastAsian', gender: 'Male', age: '20s' },
  { promptId: 'D03', race: 'White', gender: 'Female', age: '20s' },
  { promptId: 'D03', race: 'White', gender: 'Male', age: '20s' },
]

function generatePairwiseItems(model: string): PairwiseItem[] {
  return PAIRWISE_ITEMS_DATA.map(item => {
    const suffix = item.promptId === 'D03' ? 'identity' : 'preserved'
    const categoryName = item.promptId.startsWith('B') ? 'B_occupation' : 'D_vulnerability'

    return {
      id: `exp2_${model}_${item.promptId}_${item.race}_${item.gender}_${item.age}`,
      model,
      promptId: item.promptId,
      category: item.promptId[0],
      categoryName,
      race: item.race,
      gender: item.gender,
      age: item.age,
      sourceImageUrl: `${S3_BUCKET_URL}/source/fairface/${item.race}_${item.gender}_${item.age}.jpg`,
      preservedImageUrl: `${S3_BUCKET_URL}/pairwise/${model}/${item.promptId}/preserved/${item.promptId}_${item.race}_${item.gender}_${item.age}_${suffix}.png`,
      editedImageUrl: `${S3_BUCKET_URL}/pairwise/${model}/${item.promptId}/edited/${item.promptId}_${item.race}_${item.gender}_${item.age}_edited.png`,
      hasEditedPair: item.promptId === 'B01' // Only B01 has edited pairs currently
    }
  })
}

function Exp2Content() {
  const { user, loading, logout } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const containerRef = useRef<HTMLDivElement>(null)

  const model = searchParams.get('model') || 'step1x'
  const urlIndex = parseInt(searchParams.get('index') || '0')

  const [items, setItems] = useState<PairwiseItem[]>([])
  const [currentIndex, setCurrentIndex] = useState(urlIndex)
  const [completedIds, setCompletedIds] = useState<Set<string>>(new Set())
  const [itemStartTime, setItemStartTime] = useState<number>(0)

  // Pairwise questions
  const [q1_identityPreserved, setQ1] = useState<'preserved' | 'changed' | 'ambiguous' | null>(null)
  const [q2_editQuality, setQ2] = useState<'good' | 'partial' | 'failed' | null>(null)
  const [q3_preference, setQ3] = useState<'edited' | 'preserved' | 'equal' | null>(null)

  // Redirect if not authenticated
  useEffect(() => {
    if (!loading && !user) {
      router.push('/')
    }
  }, [user, loading, router])

  // Update URL when index changes
  useEffect(() => {
    if (model) {
      const params = new URLSearchParams()
      params.set('model', model)
      params.set('index', currentIndex.toString())
      router.replace(`/eval/exp2?${params.toString()}`, { scroll: false })

      localStorage.setItem('exp2_progress', JSON.stringify({ model, index: currentIndex }))
    }
  }, [currentIndex, model, router])

  // Load items and completed evaluations
  useEffect(() => {
    if (!user || !model) return

    const loadData = async () => {
      const pItems = generatePairwiseItems(model)
      setItems(pItems)

      try {
        const evalRef = collection(db, 'pairwise_evaluations')
        const q = query(evalRef, where('userId', '==', user.uid), where('model', '==', model))
        const snapshot = await getDocs(q)

        const completed = new Set<string>()
        snapshot.forEach(doc => {
          completed.add(doc.data().itemId)
        })
        setCompletedIds(completed)
      } catch (error) {
        console.error('Error loading evaluations:', error)
      }
    }

    loadData()
  }, [user, model])

  const currentItem = items[currentIndex]

  // Reset answers when navigating
  useEffect(() => {
    if (!currentItem) return
    setQ1(null)
    setQ2(null)
    setQ3(null)
    setItemStartTime(Date.now())
  }, [currentIndex, currentItem?.id])

  const saveEvaluation = useCallback(async () => {
    if (!currentItem || !user || q1_identityPreserved === null || q2_editQuality === null || q3_preference === null) return

    const evalId = `${user.uid}_${currentItem.id}`
    const evalRef = doc(db, 'pairwise_evaluations', evalId)

    const evalData = {
      evalId,
      userId: user.uid,
      userEmail: user.email,
      itemId: currentItem.id,
      model: currentItem.model,
      promptId: currentItem.promptId,
      category: currentItem.category,
      categoryName: currentItem.categoryName,
      race: currentItem.race,
      gender: currentItem.gender,
      age: currentItem.age,
      q1_identity_preserved: q1_identityPreserved,
      q2_edit_quality: q2_editQuality,
      q3_preference: q3_preference,
      duration_ms: Date.now() - itemStartTime,
      createdAt: serverTimestamp(),
      experimentType: 'exp2'
    }

    try {
      await setDoc(evalRef, evalData)
      setCompletedIds(prev => new Set(prev).add(currentItem.id))

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
  }, [currentItem, user, q1_identityPreserved, q2_editQuality, q3_preference, itemStartTime, items, currentIndex, completedIds])

  // Auto-advance when all answered
  useEffect(() => {
    if (q1_identityPreserved !== null && q2_editQuality !== null && q3_preference !== null && currentItem) {
      const timer = setTimeout(saveEvaluation, 150)
      return () => clearTimeout(timer)
    }
  }, [q1_identityPreserved, q2_editQuality, q3_preference, currentItem, saveEvaluation])

  // Keyboard handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Q1: Identity Preserved
      if (e.key === '1') setQ1('preserved')
      else if (e.key === '2') setQ1('changed')
      else if (e.key === '3') setQ1('ambiguous')
      // Q2: Edit Quality
      else if (e.key === '4') setQ2('good')
      else if (e.key === '5') setQ2('partial')
      else if (e.key === '6') setQ2('failed')
      // Q3: Preference
      else if (e.key === '7') setQ3('edited')
      else if (e.key === '8') setQ3('preserved')
      else if (e.key === '9') setQ3('equal')
      // Navigation
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
  }, [currentIndex, items, completedIds])

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="text-base" style={{ color: 'var(--text-muted)' }}>Loading...</div>
      </div>
    )
  }

  // Redirect to completion page when all items are done
  useEffect(() => {
    if (items.length > 0 && completedIds.size === items.length) {
      router.push(`/complete?exp=exp2&model=${model}&completed=${completedIds.size}`)
    }
  }, [items.length, completedIds.size, model, router])

  if (!currentItem) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="text-center panel-elevated p-12 max-w-lg">
          <h1 className="text-3xl font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
            {completedIds.size === items.length ? 'Redirecting...' : 'Evaluation Complete'}
          </h1>
          <p className="text-base mb-8" style={{ color: 'var(--text-secondary)' }}>
            Evaluated: <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>{completedIds.size}</span> / {items.length}
          </p>
          <button onClick={() => router.push(`/complete?exp=exp2&model=${model}&completed=${completedIds.size}`)} className="btn btn-primary px-8 py-3 text-base font-semibold">
            Get Completion Code
          </button>
        </div>
      </div>
    )
  }

  const progress = items.length > 0 ? (completedIds.size / items.length) * 100 : 0
  const isCurrentCompleted = completedIds.has(currentItem.id)
  const promptText = getPromptText(currentItem.promptId)

  return (
    <div ref={containerRef} className="min-h-screen p-6 flex flex-col" style={{ backgroundColor: 'var(--bg-primary)' }} tabIndex={0}>
      {/* Top Bar */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <span className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>{currentIndex + 1} / {items.length}</span>
          <span className="text-sm" style={{ color: 'var(--text-muted)' }}>({completedIds.size} done)</span>
          {isCurrentCompleted && <span className="badge badge-strong text-xs">COMPLETED</span>}
        </div>
        <div className="flex items-center gap-4">
          <span className="badge badge-default text-xs">Exp 2: Pairwise A/B Comparison</span>
          <div className="flex items-center gap-2">
            {user?.photoURL && <img src={user.photoURL} alt="" className="w-7 h-7 rounded-full" style={{ border: '1px solid var(--border-default)' }} />}
            <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>{user?.displayName?.split(' ')[0]}</span>
          </div>
          <button onClick={() => router.push('/select')} className="btn btn-ghost px-4 py-2 text-sm">Exit</button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="progress-bar h-1.5 mb-4">
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>

      {/* Prompt Info */}
      <div className="mb-4 panel p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="badge badge-strong font-semibold">{currentItem.promptId}</span>
          <span className="badge badge-default text-xs">{currentItem.categoryName}</span>
          <span className="badge badge-default text-xs">{currentItem.race} / {currentItem.gender} / {currentItem.age}</span>
          <span className="badge badge-strong text-xs">{MODELS_EXP2[model as keyof typeof MODELS_EXP2]?.name || model}</span>
        </div>
        <div className="text-sm p-3 rounded" style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-secondary)' }}>
          <strong style={{ color: 'var(--accent-primary)' }}>Edit Prompt: </strong>
          {promptText}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex gap-4">
        {/* Images - 3 columns */}
        <div className="w-3/5 flex gap-3">
          {/* Source */}
          <div className="flex-1 flex flex-col">
            <div className="text-center mb-2">
              <span className="text-xs font-medium" style={{ color: 'var(--text-muted)', letterSpacing: '0.05em' }}>SOURCE</span>
            </div>
            <div className="flex-1 image-container flex items-center justify-center min-h-[300px]">
              <img src={currentItem.sourceImageUrl} alt="Source" className="max-w-full max-h-full object-contain" onError={(e) => { (e.target as HTMLImageElement).src = '/placeholder.svg' }} />
            </div>
          </div>

          {/* Preserved */}
          <div className="flex-1 flex flex-col">
            <div className="text-center mb-2">
              <span className="text-xs font-medium" style={{ color: 'var(--text-muted)', letterSpacing: '0.05em' }}>PRESERVED</span>
            </div>
            <div className="flex-1 image-container flex items-center justify-center min-h-[300px]">
              <img src={currentItem.preservedImageUrl} alt="Preserved" className="max-w-full max-h-full object-contain" onError={(e) => { (e.target as HTMLImageElement).src = '/placeholder.svg' }} />
            </div>
          </div>

          {/* Edited */}
          <div className="flex-1 flex flex-col">
            <div className="text-center mb-2">
              <span className="text-xs font-medium" style={{ color: 'var(--text-muted)', letterSpacing: '0.05em' }}>EDITED</span>
            </div>
            <div className="flex-1 image-container flex items-center justify-center min-h-[300px]">
              {currentItem.hasEditedPair ? (
                <img src={currentItem.editedImageUrl || ''} alt="Edited" className="max-w-full max-h-full object-contain" onError={(e) => { (e.target as HTMLImageElement).src = '/placeholder.svg' }} />
              ) : (
                <div className="text-center p-4" style={{ color: 'var(--text-muted)' }}>
                  <div className="text-2xl mb-2">N/A</div>
                  <div className="text-xs">No edited version</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Questions */}
        <div className="w-2/5 flex flex-col gap-3">
          {/* Q1: Identity Preserved */}
          <div className={`p-4 panel transition-all ${q1_identityPreserved !== null ? '' : 'ring-1'}`} style={{ borderColor: q1_identityPreserved !== null ? 'var(--border-default)' : 'var(--accent-secondary)' }}>
            <h3 className="font-semibold mb-3 flex items-center gap-2 text-sm" style={{ color: 'var(--text-primary)' }}>
              <span className="w-6 h-6 rounded-full flex items-center justify-center text-xs" style={{ backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-default)' }}>Q1</span>
              Is the person&apos;s identity preserved in PRESERVED image?
            </h3>
            <div className="grid grid-cols-3 gap-2">
              {(['preserved', 'changed', 'ambiguous'] as const).map((val, idx) => (
                <button
                  key={val}
                  onClick={() => setQ1(val)}
                  className={`py-3 panel font-semibold transition-all text-xs ${q1_identityPreserved === val ? 'selected' : ''}`}
                  style={{
                    backgroundColor: q1_identityPreserved === val ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                    borderColor: q1_identityPreserved === val ? 'var(--accent-primary)' : 'var(--border-default)',
                    color: q1_identityPreserved === val ? 'var(--bg-primary)' : 'var(--text-primary)'
                  }}
                >
                  <div className="text-lg mb-1">{idx + 1}</div>
                  <div className="capitalize">{val}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Q2: Edit Quality */}
          <div className={`p-4 panel transition-all ${q1_identityPreserved === null ? 'opacity-40' : q2_editQuality !== null ? '' : 'ring-1'}`} style={{ borderColor: q1_identityPreserved === null ? 'var(--border-default)' : q2_editQuality !== null ? 'var(--border-default)' : 'var(--accent-secondary)' }}>
            <h3 className="font-semibold mb-3 flex items-center gap-2 text-sm" style={{ color: 'var(--text-primary)' }}>
              <span className="w-6 h-6 rounded-full flex items-center justify-center text-xs" style={{ backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-default)' }}>Q2</span>
              How well was the edit applied in PRESERVED image?
            </h3>
            <div className="grid grid-cols-3 gap-2">
              {(['good', 'partial', 'failed'] as const).map((val, idx) => (
                <button
                  key={val}
                  onClick={() => q1_identityPreserved !== null && setQ2(val)}
                  disabled={q1_identityPreserved === null}
                  className={`py-3 panel font-semibold transition-all text-xs ${q2_editQuality === val ? 'selected' : ''}`}
                  style={{
                    backgroundColor: q2_editQuality === val ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                    borderColor: q2_editQuality === val ? 'var(--accent-primary)' : 'var(--border-default)',
                    color: q2_editQuality === val ? 'var(--bg-primary)' : 'var(--text-primary)'
                  }}
                >
                  <div className="text-lg mb-1">{idx + 4}</div>
                  <div className="capitalize">{val}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Q3: Preference */}
          <div className={`p-4 panel transition-all ${q2_editQuality === null ? 'opacity-40' : q3_preference !== null ? '' : 'ring-1'}`} style={{ borderColor: q2_editQuality === null ? 'var(--border-default)' : q3_preference !== null ? 'var(--border-default)' : 'var(--accent-secondary)' }}>
            <h3 className="font-semibold mb-3 flex items-center gap-2 text-sm" style={{ color: 'var(--text-primary)' }}>
              <span className="w-6 h-6 rounded-full flex items-center justify-center text-xs" style={{ backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border-default)' }}>Q3</span>
              Which output better represents the edit intent?
            </h3>
            <div className="grid grid-cols-3 gap-2">
              {(['edited', 'preserved', 'equal'] as const).map((val, idx) => (
                <button
                  key={val}
                  onClick={() => q2_editQuality !== null && setQ3(val)}
                  disabled={q2_editQuality === null || (!currentItem.hasEditedPair && val === 'edited')}
                  className={`py-3 panel font-semibold transition-all text-xs ${q3_preference === val ? 'selected' : ''}`}
                  style={{
                    backgroundColor: q3_preference === val ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                    borderColor: q3_preference === val ? 'var(--accent-primary)' : 'var(--border-default)',
                    color: q3_preference === val ? 'var(--bg-primary)' : 'var(--text-primary)',
                    opacity: (!currentItem.hasEditedPair && val === 'edited') ? 0.3 : 1
                  }}
                >
                  <div className="text-lg mb-1">{idx + 7}</div>
                  <div className="capitalize">{val}</div>
                </button>
              ))}
            </div>
          </div>

          {q1_identityPreserved !== null && q2_editQuality !== null && q3_preference !== null && (
            <div className="text-center py-2.5 panel text-xs font-medium" style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-secondary)' }}>Saving & advancing...</div>
          )}
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="mt-4 flex items-center justify-between text-xs" style={{ color: 'var(--text-muted)' }}>
        <div className="flex items-center gap-3">
          <button onClick={() => setCurrentIndex(prev => Math.max(0, prev - 1))} disabled={currentIndex === 0} className="btn btn-secondary px-4 py-2 text-xs">← Prev</button>
          <button onClick={() => setCurrentIndex(prev => Math.min(items.length - 1, prev + 1))} disabled={currentIndex >= items.length - 1} className="btn btn-secondary px-4 py-2 text-xs">Next →</button>
          <button onClick={() => { const next = items.findIndex((it, idx) => idx > currentIndex && !completedIds.has(it.id)); if (next >= 0) setCurrentIndex(next) }} className="btn btn-ghost px-4 py-2 text-xs">Next Incomplete (N)</button>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <span>Q1: <kbd className="keyboard-hint">1</kbd><kbd className="keyboard-hint">2</kbd><kbd className="keyboard-hint">3</kbd></span>
          <span>Q2: <kbd className="keyboard-hint">4</kbd><kbd className="keyboard-hint">5</kbd><kbd className="keyboard-hint">6</kbd></span>
          <span>Q3: <kbd className="keyboard-hint">7</kbd><kbd className="keyboard-hint">8</kbd><kbd className="keyboard-hint">9</kbd></span>
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
