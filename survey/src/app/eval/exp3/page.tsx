'use client'

import { useState, useEffect, useCallback, useRef, Suspense } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter, useSearchParams } from 'next/navigation'
import { trackPageView, trackEvaluationStart, trackEvaluationComplete } from '@/lib/analytics'
import { db, S3_BUCKET_URL } from '@/lib/firebase'
import { collection, doc, setDoc, getDocs, query, where, serverTimestamp } from 'firebase/firestore'
import type { WinoBiasItem } from '@/lib/types'
import { MODELS_EXP3 } from '@/lib/types'

// Load WinoBias items from JSON file
async function loadWinoBiasItems(model: string): Promise<WinoBiasItem[]> {
  try {
    console.log('Loading exp3_items.json for model:', model)
    const response = await fetch('/data/exp3_items.json')
    if (!response.ok) {
      console.error('Failed to load exp3_items.json:', response.status, response.statusText)
      throw new Error(`Failed to load exp3_items.json: ${response.status} ${response.statusText}`)
    }
    const data = await response.json()
    console.log('Loaded JSON data:', { totalItems: data.items?.length, model })
    
    // Filter items for the specified model
    const modelItems = data.items.filter((item: any) => item.model === model)
    console.log(`Filtered items for ${model}:`, modelItems.length)
    
    if (modelItems.length === 0) {
      console.warn(`No items found for model: ${model}`)
    }
    
    // Map to WinoBiasItem format
    const mappedItems = modelItems.map((item: any) => {
      // Determine gender code: prompts 1-25 are male-centered, 26-50 are female-centered
      const genderCode = item.promptId <= 25 ? 'M' : 'F'
      
      return {
        id: item.id,
        model: item.model,
        promptId: item.promptId,
        promptText: item.promptText,
        outputImageUrl: item.s3Url,
        genderCode,
        stereotype: item.stereotype,
        input1: item.inputImage1?.replace('.jpg', '') || '',
        input2: item.inputImage2?.replace('.jpg', '') || '',
        sourceInput1Url: item.sourceInput1Url,
        sourceInput2Url: item.sourceInput2Url
      }
    })
    
    // Log first item for debugging
    if (mappedItems.length > 0) {
      console.log('First item URLs:', {
        output: mappedItems[0].outputImageUrl,
        source1: mappedItems[0].sourceInput1Url,
        source2: mappedItems[0].sourceInput2Url
      })
    }
    
    return mappedItems
  } catch (error) {
    console.error('Error loading WinoBias items:', error)
    return []
  }
}

function Exp3Content() {
  const { user, loading, logout } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const containerRef = useRef<HTMLDivElement>(null)

  const model = searchParams.get('model') || 'qwen'
  const urlIndex = parseInt(searchParams.get('index') || '0')

  const [items, setItems] = useState<WinoBiasItem[]>([])
  const [loadingItems, setLoadingItems] = useState(true)
  const [itemsError, setItemsError] = useState<string | null>(null)
  const [currentIndex, setCurrentIndex] = useState(urlIndex)
  const [completedIds, setCompletedIds] = useState<Set<string>>(new Set())
  const [itemStartTime, setItemStartTime] = useState<number>(0)
  const [stereotypeDetected, setStereotypeDetected] = useState<boolean | null>(null)

  // Redirect if not authenticated
  useEffect(() => {
    if (!loading && !user) {
      router.push('/')
    }
  }, [user, loading, router])

  // Track page view and evaluation start
  useEffect(() => {
    if (user && model) {
      trackPageView('eval_exp3', { model })
      trackEvaluationStart('exp3', model)
    }
  }, [user, model])

  // Update URL when index changes
  useEffect(() => {
    if (model) {
      const params = new URLSearchParams()
      params.set('model', model)
      params.set('index', currentIndex.toString())
      router.replace(`/eval/exp3?${params.toString()}`, { scroll: false })

      // Save to localStorage
      localStorage.setItem('exp3_progress', JSON.stringify({ model, index: currentIndex }))
    }
  }, [currentIndex, model, router])

  // Load items and completed evaluations
  useEffect(() => {
    if (!user || !model) return

    async function loadItems() {
      setLoadingItems(true)
      setItemsError(null)
      try {
        const loadedItems = await loadWinoBiasItems(model)
        if (loadedItems.length === 0) {
          setItemsError(`No items found for model: ${model}. Please check exp3_items.json`)
        } else {
          setItems(loadedItems)
        }
      } catch (error: any) {
        console.error('Failed to load items:', error)
        setItemsError(`Failed to load items: ${error.message}`)
      } finally {
        setLoadingItems(false)
      }
    }
    loadItems()

    // Load completed evaluations
    async function loadCompleted() {
      if (!user) return
      
      try {
        const evalRef = collection(db, 'winobias_evaluations')
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
    loadCompleted()
  }, [user, model])

  const currentItem = items[currentIndex]

  // Reset answers when navigating
  useEffect(() => {
    if (!currentItem) return
    setStereotypeDetected(null)
    setItemStartTime(Date.now())
  }, [currentIndex, currentItem?.id])

  const saveEvaluation = useCallback(async () => {
    if (!currentItem || !user || stereotypeDetected === null) return

    const evalId = `${user.uid}_${currentItem.id}`
    const evalRef = doc(db, 'winobias_evaluations', evalId)

    const evalData = {
      evalId,
      userId: user.uid,
      userEmail: user.email,
      itemId: currentItem.id,
      model: currentItem.model,
      promptId: currentItem.promptId,
      promptText: currentItem.promptText,
      genderCode: currentItem.genderCode,
      stereotypeDetected: stereotypeDetected ? 1 : 0,
      duration_ms: Date.now() - itemStartTime,
      createdAt: serverTimestamp(),
      experimentType: 'exp3'
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
  }, [currentItem, user, stereotypeDetected, itemStartTime, items, currentIndex, completedIds])

  // Auto-advance when answered
  useEffect(() => {
    if (stereotypeDetected !== null && currentItem) {
      const timer = setTimeout(saveEvaluation, 300)
      return () => clearTimeout(timer)
    }
  }, [stereotypeDetected, currentItem, saveEvaluation])

  // Keyboard handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '1') {
        setStereotypeDetected(true)
      } else if (e.key === '2') {
        setStereotypeDetected(false)
      } else if (e.key === 'ArrowLeft' && currentIndex > 0) {
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

  // Show loading state while items are being loaded
  if (loadingItems) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="text-center panel-elevated p-12 max-w-lg">
          <div className="text-base mb-4" style={{ color: 'var(--text-primary)' }}>Loading evaluation items...</div>
          <div className="text-sm" style={{ color: 'var(--text-muted)' }}>Fetching from exp3_items.json</div>
        </div>
      </div>
    )
  }

  // Show error if items failed to load
  if (itemsError) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="text-center panel-elevated p-12 max-w-lg">
          <h1 className="text-2xl font-semibold mb-4" style={{ color: 'var(--error-text)' }}>Error Loading Items</h1>
          <p className="text-base mb-4" style={{ color: 'var(--text-secondary)' }}>{itemsError}</p>
          <p className="text-sm mb-8" style={{ color: 'var(--text-muted)' }}>
            Model: {model}<br />
            Please check the browser console for details.
          </p>
          <button onClick={() => window.location.reload()} className="btn btn-primary px-8 py-3 text-base font-semibold">
            Reload Page
          </button>
        </div>
      </div>
    )
  }

  // Redirect to completion page when all items are done
  useEffect(() => {
    if (items.length > 0 && completedIds.size === items.length) {
      trackEvaluationComplete('exp3', model, Date.now() - itemStartTime, items.length)
      router.push(`/complete?exp=exp3&model=${model}&completed=${completedIds.size}`)
    }
  }, [items.length, completedIds.size, model, router])

  if (!currentItem || items.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="text-center panel-elevated p-12 max-w-lg">
          <h1 className="text-3xl font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
            {completedIds.size === items.length ? 'Redirecting...' : 'Evaluation Complete'}
          </h1>
          <p className="text-base mb-8" style={{ color: 'var(--text-secondary)' }}>
            Evaluated: <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>{completedIds.size}</span> / {items.length}
          </p>
          <button onClick={() => router.push(`/complete?exp=exp3&model=${model}&completed=${completedIds.size}`)} className="btn btn-primary px-8 py-3 text-base font-semibold">
            Get Completion Code
          </button>
        </div>
      </div>
    )
  }

  const progress = items.length > 0 ? (completedIds.size / items.length) * 100 : 0
  const isCurrentCompleted = completedIds.has(currentItem.id)

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
          <span className="badge badge-default text-xs">Exp 3: WinoBias Gender Stereotype</span>
          <div className="flex items-center gap-2">
            {user?.photoURL && <img src={user.photoURL} alt="" className="w-7 h-7 rounded-full" style={{ border: '1px solid var(--border-default)' }} />}
            <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>{user?.displayName?.split(' ')[0]}</span>
          </div>
          <button onClick={() => router.push('/select')} className="btn btn-ghost px-4 py-2 text-sm">Exit</button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="progress-bar h-1.5 mb-6">
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex gap-6">
        {/* Image */}
        <div className="w-1/2 flex flex-col">
          <div className="text-center mb-2">
            <span className="text-xs font-medium" style={{ color: 'var(--text-muted)', letterSpacing: '0.05em' }}>AI GENERATED OUTPUT</span>
            <div className="mt-1">
              <span className="badge badge-strong text-xs">{MODELS_EXP3[model as keyof typeof MODELS_EXP3]?.name || model}</span>
            </div>
          </div>
          <div className="flex-1 image-container flex items-center justify-center min-h-[500px]">
            <img
              src={currentItem.outputImageUrl}
              alt="Output"
              className="max-w-full max-h-full object-contain"
              onError={(e) => {
                const img = e.target as HTMLImageElement
                img.src = '/placeholder.svg'
              }}
            />
          </div>
          <div className="mt-2 text-center text-sm" style={{ color: 'var(--text-muted)' }}>
            Inputs: {currentItem.input1} + {currentItem.input2}
          </div>
        </div>

        {/* Question Panel */}
        <div className="w-1/2 flex flex-col">
          {/* Prompt Info */}
          <div className="mb-4 panel p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="badge badge-strong font-semibold">{currentItem.promptId}</span>
              <span className={`px-2 py-1 rounded text-xs`} style={{
                backgroundColor: currentItem.genderCode === 'M' ? 'var(--accent-primary)' : 'var(--accent-secondary)',
                color: 'var(--bg-primary)'
              }}>
                {currentItem.genderCode === 'M' ? 'Male pronoun (he)' : 'Female pronoun (she)'}
              </span>
            </div>
            <div className="text-base leading-relaxed p-4 rounded" style={{ backgroundColor: 'var(--bg-elevated)' }}>
              <strong style={{ color: 'var(--accent-primary)' }}>Prompt: </strong>
              &ldquo;{currentItem.promptText}&rdquo;
            </div>
          </div>

          {/* Stereotype Info */}
          <div className="mb-4 p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)', border: '2px solid var(--accent-primary)' }}>
            <div className="text-sm font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Stereotyped Occupation:</div>
            <div className="text-2xl font-bold capitalize mb-2" style={{ color: 'var(--accent-primary)' }}>{currentItem.stereotype}</div>
            <div className="flex items-center gap-2">
              <span className="text-sm" style={{ color: 'var(--text-primary)' }}>Traditionally associated with:</span>
              <span className="text-sm font-bold px-3 py-1 rounded" style={{
                backgroundColor: currentItem.genderCode === 'M' ? '#1e3a5f' : '#5f1e3a',
                color: currentItem.genderCode === 'M' ? '#60a5fa' : '#f472b6'
              }}>
                {currentItem.genderCode === 'M' ? 'MALES ♂' : 'FEMALES ♀'}
              </span>
            </div>
          </div>

          {/* Binary Question */}
          <div className={`p-5 panel transition-all flex-1 ${stereotypeDetected !== null ? '' : 'ring-1'}`} style={{ borderColor: stereotypeDetected !== null ? 'var(--border-default)' : 'var(--accent-secondary)' }}>
            <h3 className="font-bold text-lg mb-3" style={{ color: 'var(--text-primary)' }}>Does the image follow the gender stereotype?</h3>
            <p className="mb-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
              Does the AI show the <strong style={{ color: 'var(--accent-primary)' }}>{currentItem.stereotype}</strong> as {currentItem.genderCode === 'M' ? 'male' : 'female'},
              matching the traditional stereotype?
            </p>

            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => setStereotypeDetected(true)}
                className={`py-6 panel font-semibold transition-all ${stereotypeDetected === true ? 'selected' : ''}`}
                style={{
                  backgroundColor: stereotypeDetected === true ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                  borderColor: stereotypeDetected === true ? 'var(--accent-primary)' : 'var(--border-default)',
                  color: stereotypeDetected === true ? 'var(--bg-primary)' : 'var(--text-primary)'
                }}
              >
                <div className="text-2xl mb-2">1</div>
                <div className="text-xs">Yes, Follows Stereotype</div>
              </button>
              <button
                onClick={() => setStereotypeDetected(false)}
                className={`py-6 panel font-semibold transition-all ${stereotypeDetected === false ? 'selected' : ''}`}
                style={{
                  backgroundColor: stereotypeDetected === false ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                  borderColor: stereotypeDetected === false ? 'var(--accent-primary)' : 'var(--border-default)',
                  color: stereotypeDetected === false ? 'var(--bg-primary)' : 'var(--text-primary)'
                }}
              >
                <div className="text-2xl mb-2">2</div>
                <div className="text-xs">No, Breaks Stereotype</div>
              </button>
            </div>

            {stereotypeDetected !== null && (
              <div className="mt-4 text-center py-2.5 panel text-xs font-medium" style={{ backgroundColor: 'var(--bg-elevated)', color: 'var(--text-secondary)' }}>
                Saving & advancing...
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="mt-6 flex items-center justify-between text-xs" style={{ color: 'var(--text-muted)' }}>
        <div className="flex items-center gap-3">
          <button onClick={() => setCurrentIndex(prev => Math.max(0, prev - 1))} disabled={currentIndex === 0} className="btn btn-secondary px-4 py-2 text-xs">← Prev</button>
          <button onClick={() => setCurrentIndex(prev => Math.min(items.length - 1, prev + 1))} disabled={currentIndex >= items.length - 1} className="btn btn-secondary px-4 py-2 text-xs">Next →</button>
          <button onClick={() => { const next = items.findIndex((it, idx) => idx > currentIndex && !completedIds.has(it.id)); if (next >= 0) setCurrentIndex(next) }} className="btn btn-ghost px-4 py-2 text-xs">Next Incomplete (N)</button>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <span>Stereotype: <kbd className="keyboard-hint">1</kbd></span>
          <span>No Stereotype: <kbd className="keyboard-hint">2</kbd></span>
        </div>
      </div>
    </div>
  )
}

export default function Exp3Page() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="text-base" style={{ color: 'var(--text-muted)' }}>Loading...</div>
      </div>
    }>
      <Exp3Content />
    </Suspense>
  )
}
