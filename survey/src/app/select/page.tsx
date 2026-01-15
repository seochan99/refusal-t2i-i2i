'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { db, COLLECTIONS } from '@/lib/firebase'
import { doc, getDoc, collection, query, where, getDocs } from 'firebase/firestore'
import { MODELS_EXP1, MODELS_EXP2, MODELS_EXP3 } from '@/lib/types'

const EXPERIMENT_TYPES = {
  exp1: {
    name: 'Experiment 1: VLM Scoring',
    desc: 'Rate edit quality, identity preservation',
    categories: 'Categories B (Occupation), D (Vulnerability)',
    route: '/eval/exp1',
    models: MODELS_EXP1
  },
  exp2: {
    name: 'Experiment 2: Pairwise A/B',
    desc: 'Compare edited vs identity-preserved images',
    categories: 'Soft Erasure Detection',
    route: '/eval/exp2',
    models: MODELS_EXP2
  },
  exp3: {
    name: 'Experiment 3: WinoBias',
    desc: 'Binary stereotype detection',
    categories: 'Gender-Occupation Prompts',
    route: '/eval/exp3',
    models: MODELS_EXP3
  }
}

interface ProgressData {
  [key: string]: number
}

export default function SelectPage() {
  const { user, loading, logout } = useAuth()
  const router = useRouter()
  const [experimentType, setExperimentType] = useState<string>('')
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [amtWorkerId, setAmtWorkerId] = useState<string | null>(null)
  const [checkingAmt, setCheckingAmt] = useState(true)
  const [progress, setProgress] = useState<ProgressData>({})
  const [loadingProgress, setLoadingProgress] = useState(true)

  // Redirect to login if not authenticated (check first)
  useEffect(() => {
    if (!loading && !user) {
      if (window.location.pathname === '/select') {
        router.push('/')
      }
      return
    }
  }, [user, loading, router])

  // Check consent (only if authenticated)
  useEffect(() => {
    if (loading || !user) return
    
    const consent = localStorage.getItem('irb_consent_i2i_bias')
    if (consent !== 'agreed' && window.location.pathname === '/select') {
      router.push('/consent')
      return
    }
  }, [user, loading, router])

  // Check AMT info (only if authenticated and consented)
  useEffect(() => {
    async function checkAMT() {
      if (!user || loading) {
        setCheckingAmt(false)
        return
      }

      const consent = localStorage.getItem('irb_consent_i2i_bias')
      if (consent !== 'agreed') {
        setCheckingAmt(false)
        return
      }

      try {
        const userDoc = await getDoc(doc(db, 'users', user.uid))
        if (userDoc.exists()) {
          const data = userDoc.data()
          if (!data.createdAt) {
            if (window.location.pathname === '/select') {
              router.push('/amt')
            }
            return
          }
          setAmtWorkerId(data.amtWorkerId || null)
        } else {
          if (window.location.pathname === '/select') {
            router.push('/amt')
          }
          return
        }
      } catch (err) {
        console.error('Error checking AMT:', err)
        const localWorkerId = localStorage.getItem('amt_worker_id')
        setAmtWorkerId(localWorkerId || null)
      }
      setCheckingAmt(false)
    }

    checkAMT()
  }, [user, loading, router])

  // Load progress for all experiments
  useEffect(() => {
    async function loadProgress() {
      if (!user) return

      try {
        const progressData: ProgressData = {}

        // Load exp1 evaluations
        const exp1Ref = collection(db, COLLECTIONS.EVALUATIONS)
        const exp1Query = query(exp1Ref, where('userId', '==', user.uid), where('experimentType', '==', 'exp1'))
        const exp1Snapshot = await getDocs(exp1Query)

        exp1Snapshot.forEach(doc => {
          const data = doc.data()
          const key = `exp1_${data.model}`
          progressData[key] = (progressData[key] || 0) + 1
        })

        // Load exp2 evaluations (pairwise)
        const exp2Ref = collection(db, 'pairwise_evaluations')
        const exp2Query = query(exp2Ref, where('userId', '==', user.uid))
        const exp2Snapshot = await getDocs(exp2Query)

        exp2Snapshot.forEach(doc => {
          const data = doc.data()
          const key = `exp2_${data.model}`
          progressData[key] = (progressData[key] || 0) + 1
        })

        // Load exp3 evaluations (winobias)
        const exp3Ref = collection(db, 'winobias_evaluations')
        const exp3Query = query(exp3Ref, where('userId', '==', user.uid))
        const exp3Snapshot = await getDocs(exp3Query)

        exp3Snapshot.forEach(doc => {
          const data = doc.data()
          const key = `exp3_${data.model}`
          progressData[key] = (progressData[key] || 0) + 1
        })

        setProgress(progressData)
      } catch (error) {
        console.error('Error loading progress:', error)
      }
      setLoadingProgress(false)
    }

    if (!loading && user) {
      loadProgress()
    }
  }, [user, loading])

  useEffect(() => {
    setSelectedModel('')
  }, [experimentType])

  const handleStart = () => {
    if (!experimentType || !selectedModel) {
      alert('Please select both experiment type and model')
      return
    }

    const expInfo = EXPERIMENT_TYPES[experimentType as keyof typeof EXPERIMENT_TYPES]
    const progressKey = `${experimentType}_${selectedModel}`
    const completed = progress[progressKey] || 0

    router.push(`${expInfo.route}?model=${selectedModel}&index=${completed}`)
  }

  const getProgressPercent = (expKey: string, modelKey: string, total: number) => {
    const key = `${expKey}_${modelKey}`
    const completed = progress[key] || 0
    return Math.round((completed / total) * 100)
  }

  const getProgressCount = (expKey: string, modelKey: string) => {
    const key = `${expKey}_${modelKey}`
    return progress[key] || 0
  }

  // Calculate total progress across all experiments
  const getTotalProgress = () => {
    let totalCompleted = 0
    let totalItems = 0

    Object.entries(EXPERIMENT_TYPES).forEach(([expKey, expInfo]) => {
      Object.entries(expInfo.models).forEach(([modelKey, modelInfo]) => {
        const key = `${expKey}_${modelKey}`
        totalCompleted += progress[key] || 0
        totalItems += modelInfo.total
      })
    })

    return { completed: totalCompleted, total: totalItems, percent: totalItems > 0 ? Math.round((totalCompleted / totalItems) * 100) : 0 }
  }

  if (loading || !user || checkingAmt) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="text-base" style={{ color: 'var(--text-muted)' }}>Loading...</div>
      </div>
    )
  }

  const currentExp = experimentType ? EXPERIMENT_TYPES[experimentType as keyof typeof EXPERIMENT_TYPES] : null
  const totalProgress = getTotalProgress()

  return (
    <div className="min-h-screen flex items-center justify-center p-8" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="max-w-2xl w-full panel-elevated p-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
            {experimentType ? 'Select Model' : 'Human Evaluation'}
          </h1>
          <div className="flex items-center gap-3">
            {user.photoURL && (
              <img src={user.photoURL} alt="" className="w-8 h-8 rounded-full" style={{ border: '1px solid var(--border-default)' }} />
            )}
            <div className="text-right">
              <div className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>{user.displayName}</div>
              {amtWorkerId && (
                <div className="text-xs" style={{ color: 'var(--accent-primary)' }}>Worker: {amtWorkerId}</div>
              )}
              <button onClick={logout} className="text-xs transition-colors hover:underline" style={{ color: 'var(--text-muted)' }}>
                Sign out
              </button>
            </div>
          </div>
        </div>

        {/* Overall Progress */}
        {!loadingProgress && (
          <div className="mb-8 p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-default)' }}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Your Overall Progress</span>
              <span className="text-sm font-bold" style={{ color: 'var(--accent-primary)' }}>
                {totalProgress.completed.toLocaleString()} / {totalProgress.total.toLocaleString()} ({totalProgress.percent}%)
              </span>
            </div>
            <div className="h-3 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${totalProgress.percent}%`, backgroundColor: 'var(--accent-primary)' }}
              />
            </div>
          </div>
        )}

        {!experimentType ? (
          // Step 1: Select Experiment Type
          <div className="space-y-4">
            <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
              Select an experiment to begin evaluation
            </p>
            {Object.entries(EXPERIMENT_TYPES).map(([key, info]) => {
              // Calculate experiment-level progress
              let expCompleted = 0
              let expTotal = 0
              Object.entries(info.models).forEach(([modelKey, modelInfo]) => {
                expCompleted += getProgressCount(key, modelKey)
                expTotal += modelInfo.total
              })
              const expPercent = expTotal > 0 ? Math.round((expCompleted / expTotal) * 100) : 0

              return (
                <button
                  key={key}
                  onClick={() => setExperimentType(key)}
                  className="w-full p-5 text-left transition-all hover-lift group rounded-lg"
                  style={{
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--border-default)'
                  }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="font-bold text-base" style={{ color: 'var(--text-primary)' }}>
                      {info.name}
                    </div>
                    <svg className="w-5 h-5 transition-transform group-hover:translate-x-1" style={{ color: 'var(--accent-primary)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                  <div className="text-sm mb-1" style={{ color: 'var(--text-primary)' }}>{info.desc}</div>
                  <div className="text-xs mb-3" style={{ color: 'var(--accent-primary)' }}>{info.categories}</div>

                  {/* Progress bar */}
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${expPercent}%`,
                          backgroundColor: expPercent === 100 ? 'var(--success-text)' : 'var(--accent-primary)'
                        }}
                      />
                    </div>
                    <span className="text-xs font-semibold min-w-[80px] text-right" style={{ color: expPercent === 100 ? 'var(--success-text)' : 'var(--text-secondary)' }}>
                      {expCompleted.toLocaleString()} / {expTotal.toLocaleString()}
                    </span>
                  </div>
                </button>
              )
            })}
          </div>
        ) : (
          // Step 2: Select Model
          <div className="space-y-6">
            <button
              onClick={() => setExperimentType('')}
              className="text-sm transition-colors flex items-center gap-2 hover:underline"
              style={{ color: 'var(--accent-primary)' }}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to experiments
            </button>

            <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-default)' }}>
              <div className="font-bold text-base mb-1" style={{ color: 'var(--text-primary)' }}>{currentExp?.name}</div>
              <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>{currentExp?.desc}</div>
              <div className="text-sm mt-1" style={{ color: 'var(--accent-primary)' }}>{currentExp?.categories}</div>
            </div>

            <div>
              <label className="block text-sm font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
                Select Model to Evaluate
              </label>
              <div className="grid grid-cols-1 gap-3">
                {currentExp && Object.entries(currentExp.models).map(([key, info]) => {
                  const isAvailable = 'available' in info ? info.available : true
                  const isSelected = selectedModel === key
                  const completed = getProgressCount(experimentType, key)
                  const percent = getProgressPercent(experimentType, key, info.total)
                  const isCompleted = percent === 100

                  return (
                    <button
                      key={key}
                      onClick={() => isAvailable && setSelectedModel(key)}
                      disabled={!isAvailable}
                      className={`p-5 text-left transition-all rounded-lg ${isAvailable ? 'hover-lift cursor-pointer' : 'cursor-not-allowed'}`}
                      style={{
                        border: `2px solid ${isSelected ? 'var(--accent-primary)' : 'var(--border-default)'}`,
                        backgroundColor: isSelected ? 'var(--accent-primary)' : 'var(--bg-secondary)',
                        opacity: isAvailable ? 1 : 0.5
                      }}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="font-bold" style={{ color: isSelected ? 'var(--bg-primary)' : 'var(--text-primary)' }}>
                          {info.name}
                        </div>
                        <div className="flex items-center gap-2">
                          {!isAvailable && (
                            <span className="text-xs px-2 py-1 rounded font-semibold" style={{ backgroundColor: 'var(--warning-bg)', color: 'var(--warning-text)' }}>
                              Coming Soon
                            </span>
                          )}
                          {isCompleted && isAvailable && (
                            <span className="text-xs px-2 py-1 rounded font-semibold" style={{ backgroundColor: 'var(--success-bg)', color: 'var(--success-text)' }}>
                              ✓ Complete
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Progress */}
                      <div className="flex items-center gap-3">
                        <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ backgroundColor: isSelected ? 'rgba(0,0,0,0.2)' : 'var(--bg-tertiary)' }}>
                          <div
                            className="h-full rounded-full transition-all"
                            style={{
                              width: `${percent}%`,
                              backgroundColor: isSelected ? 'var(--bg-primary)' : (isCompleted ? 'var(--success-text)' : 'var(--accent-primary)')
                            }}
                          />
                        </div>
                        <span className="text-xs font-semibold min-w-[100px] text-right" style={{ color: isSelected ? 'var(--bg-primary)' : 'var(--text-secondary)' }}>
                          {completed.toLocaleString()} / {info.total.toLocaleString()}
                        </span>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>

            <button
              onClick={handleStart}
              disabled={!selectedModel}
              className="w-full py-4 text-base font-bold rounded-lg transition-all"
              style={{
                backgroundColor: selectedModel ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                color: selectedModel ? 'var(--bg-primary)' : 'var(--text-muted)',
                cursor: selectedModel ? 'pointer' : 'not-allowed'
              }}
            >
              {selectedModel ? (
                getProgressCount(experimentType, selectedModel) > 0
                  ? `CONTINUE EVALUATION (${getProgressCount(experimentType, selectedModel)} done)`
                  : 'START EVALUATION'
              ) : 'SELECT A MODEL'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
