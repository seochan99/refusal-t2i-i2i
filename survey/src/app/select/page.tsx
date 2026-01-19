'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { db, COLLECTIONS } from '@/lib/firebase'
import { doc, getDoc, setDoc, collection, query, where, getDocs, serverTimestamp } from 'firebase/firestore'
import { MODELS_EXP1, MODELS_EXP2, MODELS_EXP3 } from '@/lib/types'
import { readProlificSession } from '@/lib/prolific'

const EXPERIMENT_TYPES = {
  exp1: {
    name: 'Experiment 1: VLM Scoring',
    desc: 'Rate edit quality, identity preservation',
    categories: 'Categories B (Occupation), D (Vulnerability)',
    route: '/eval/exp1',
    models: MODELS_EXP1
  },
  exp2: {
    name: 'Experiment 2: Pairwise Comparison',
    desc: 'Compare edited vs identity-preserved: rate both',
    categories: 'Source + Edited + Preserved',
    route: '/eval/exp2',
    models: MODELS_EXP2
  }
  // exp3 temporarily disabled - uncomment when needed
  // exp3: {
  //   name: 'Experiment 3: WinoBias',
  //   desc: 'Binary stereotype detection',
  //   categories: 'Gender-Occupation Prompts',
  //   route: '/eval/exp3',
  //   models: MODELS_EXP3
  // }
}

interface ProgressData {
  [key: string]: number
}

interface IrbConsentInfo {
  consented: boolean
  consentedAt: Date | null
}

export default function SelectPage() {
  const { user, loading, logout } = useAuth()
  const router = useRouter()
  const [experimentType, setExperimentType] = useState<string>('')
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [prolificPid, setProlificPid] = useState<string | null>(null)
  const [checkingAmt, setCheckingAmt] = useState(true)
  const [progress, setProgress] = useState<ProgressData>({})
  const [loadingProgress, setLoadingProgress] = useState(true)
  const [irbConsent, setIrbConsent] = useState<IrbConsentInfo>({ consented: false, consentedAt: null })
  const [showIrbModal, setShowIrbModal] = useState(false)
  const [showWithdrawConfirm, setShowWithdrawConfirm] = useState(false)
  const [isWithdrawing, setIsWithdrawing] = useState(false)

  // Redirect to login if not authenticated (check first)
  useEffect(() => {
    if (!loading && !user) {
      if (window.location.pathname === '/select') {
        router.push('/')
      }
      return
    }
  }, [user, loading, router])

  // Check consent and load AMT info (combined for efficiency)
  useEffect(() => {
    async function checkConsentAndLoadAMT() {
      if (!user || loading) {
        setCheckingAmt(false)
        return
      }

      try {
        const userDoc = await getDoc(doc(db, 'users', user.uid))

        if (userDoc.exists()) {
          const data = userDoc.data()

          // Check consent (Firebase is authoritative)
          if (data.irbConsent !== true) {
            // Also check localStorage as fallback
            const localConsent = localStorage.getItem('irb_consent_i2i_bias')
            if (localConsent !== 'agreed' && window.location.pathname === '/select') {
              router.push('/consent')
              return
            }
          } else {
            // Sync to localStorage
            localStorage.setItem('irb_consent_i2i_bias', 'agreed')
          }

          // Load IRB consent info
          setIrbConsent({
            consented: data.irbConsent === true,
            consentedAt: data.irbConsentAt?.toDate() || null
          })

          // Load Prolific PID if it exists (optional)
          setProlificPid(data.prolificPid || null)
        } else {
          // No user doc - check localStorage consent
          const localConsent = localStorage.getItem('irb_consent_i2i_bias')
          if (localConsent !== 'agreed' && window.location.pathname === '/select') {
            router.push('/consent')
            return
          }
        }
      } catch (err) {
        console.error('Error checking consent/AMT:', err)
        // Fallback to localStorage
        const localConsent = localStorage.getItem('irb_consent_i2i_bias')
        if (localConsent !== 'agreed' && window.location.pathname === '/select') {
          router.push('/consent')
          return
        }
        const session = readProlificSession()
        setProlificPid(session?.prolificPid || null)
      }

      setCheckingAmt(false)
    }

    checkConsentAndLoadAMT()
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

  // Handle withdrawing IRB consent
  const handleWithdrawConsent = async () => {
    if (!user) return

    setIsWithdrawing(true)
    try {
      // Update Firebase to withdraw consent
      await setDoc(doc(db, 'users', user.uid), {
        irbConsent: false,
        irbWithdrawnAt: serverTimestamp(),
        updatedAt: serverTimestamp()
      }, { merge: true })

      // Clear localStorage
      localStorage.removeItem('irb_consent_i2i_bias')

      // Update local state
      setIrbConsent({ consented: false, consentedAt: null })
      setShowWithdrawConfirm(false)
      setShowIrbModal(false)

      // Redirect to consent page
      router.push('/consent')
    } catch (err) {
      console.error('Error withdrawing consent:', err)
      alert('Failed to withdraw consent. Please try again.')
    } finally {
      setIsWithdrawing(false)
    }
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
              {prolificPid ? (
                <button
                  onClick={() => router.push('/tasks')}
                  className="text-xs transition-colors hover:underline"
                  style={{ color: 'var(--accent-primary)' }}
                  title="Click to edit Prolific info"
                >
                  Prolific: {prolificPid}
                </button>
              ) : (
                <button
                  onClick={() => router.push('/tasks')}
                  className="text-xs transition-colors hover:underline"
                  style={{ color: 'var(--text-muted)' }}
                  title="Click to add Prolific PID"
                >
                  + Add Prolific ID
                </button>
              )}
              <button onClick={logout} className="text-xs transition-colors hover:underline block mt-0.5" style={{ color: 'var(--text-muted)' }}>
                Sign out
              </button>
            </div>
          </div>
        </div>

        {/* IRB Consent Status */}
        <div className="mb-6 p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-default)' }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: irbConsent.consented ? 'var(--success-bg)' : 'var(--warning-bg)' }}>
                {irbConsent.consented ? (
                  <span style={{ color: 'var(--success-text)' }}>✓</span>
                ) : (
                  <span style={{ color: 'var(--warning-text)' }}>!</span>
                )}
              </div>
              <div>
                <div className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                  IRB Consent: {irbConsent.consented ? 'Agreed' : 'Not Agreed'}
                </div>
                {irbConsent.consentedAt && (
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    Agreed on {irbConsent.consentedAt.toLocaleDateString()} at {irbConsent.consentedAt.toLocaleTimeString()}
                  </div>
                )}
              </div>
            </div>
            <button
              onClick={() => setShowIrbModal(true)}
              className="text-xs px-3 py-1.5 rounded transition-colors hover:opacity-80"
              style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}
            >
              View Details
            </button>
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

      {/* IRB Consent Modal */}
      {showIrbModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(0,0,0,0.7)' }}>
          <div className="max-w-2xl w-full max-h-[80vh] overflow-auto rounded-lg" style={{ backgroundColor: 'var(--bg-elevated)' }}>
            <div className="sticky top-0 p-4 flex items-center justify-between" style={{ backgroundColor: 'var(--bg-elevated)', borderBottom: '1px solid var(--border-default)' }}>
              <h2 className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>IRB Consent Information</h2>
              <button
                onClick={() => setShowIrbModal(false)}
                className="w-8 h-8 rounded-full flex items-center justify-center hover:opacity-80"
                style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}
              >
                ✕
              </button>
            </div>
            <div className="p-6">
              {/* Consent Status */}
              <div className="mb-6 p-4 rounded-lg" style={{ backgroundColor: irbConsent.consented ? 'var(--success-bg)' : 'var(--warning-bg)' }}>
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{irbConsent.consented ? '✓' : '!'}</span>
                  <div>
                    <div className="font-bold" style={{ color: irbConsent.consented ? 'var(--success-text)' : 'var(--warning-text)' }}>
                      {irbConsent.consented ? 'Consent Provided' : 'Consent Not Provided'}
                    </div>
                    {irbConsent.consentedAt && (
                      <div className="text-sm" style={{ color: irbConsent.consented ? 'var(--success-text)' : 'var(--warning-text)' }}>
                        {irbConsent.consentedAt.toLocaleDateString()} at {irbConsent.consentedAt.toLocaleTimeString()}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Study Information */}
              <div className="space-y-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
                <div className="panel p-3" style={{ backgroundColor: 'var(--bg-secondary)' }}>
                  <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>
                    <strong>IRB Protocol:</strong> STUDY2022_00000005<br/>
                    <strong>Exempt Category:</strong> Category 2 &amp; 3
                  </p>
                  <div className="text-xs space-y-1" style={{ color: 'var(--text-disabled)' }}>
                    <p><strong>Cat 2:</strong> Surveys/interviews of adults with anonymous data collection</p>
                    <p><strong>Cat 3:</strong> Benign behavioral interventions with prospective consent</p>
                  </div>
                </div>

                <div>
                  <h3 className="font-bold mb-2" style={{ color: 'var(--text-primary)' }}>Study Title</h3>
                  <p>Evaluation of AI generated behaviors and artifacts</p>
                </div>

                <div>
                  <h3 className="font-bold mb-2" style={{ color: 'var(--text-primary)' }}>Principal Investigator</h3>
                  <p>Jean Oh, Carnegie Mellon University</p>
                </div>

                <div>
                  <h3 className="font-bold mb-2" style={{ color: 'var(--text-primary)' }}>Research Group</h3>
                  <p>Bot Intelligence Group at Carnegie Mellon University</p>
                </div>

                <div>
                  <h3 className="font-bold mb-2" style={{ color: 'var(--text-primary)' }}>Purpose</h3>
                  <p>To get human evaluation on the quality of AI generated artifacts. The research questions include whether the quality of output by one algorithm is better than another, and to understand ways to evaluate bias in AI-generated images.</p>
                </div>

                <div>
                  <h3 className="font-bold mb-2" style={{ color: 'var(--text-primary)' }}>What You Agreed To</h3>
                  <ul className="list-disc list-inside space-y-1">
                    <li>Viewing and evaluating AI-generated images</li>
                    <li>Text and Image Alignment evaluation</li>
                    <li>Identity Preservation assessment</li>
                    <li>Stereotype Detection tasks</li>
                    <li>Your responses being used for research purposes</li>
                    <li>Anonymous data collection (no identifying information stored)</li>
                  </ul>
                </div>

                <div>
                  <h3 className="font-bold mb-2" style={{ color: 'var(--text-primary)' }}>Confidentiality</h3>
                  <p>Your Prolific Participant ID (if applicable) will be used only for payment distribution and will not be stored with your survey responses. The ID information will be removed from the data and deleted completely.</p>
                </div>

                <div>
                  <h3 className="font-bold mb-2" style={{ color: 'var(--text-primary)' }}>Your Rights</h3>
                  <ul className="list-disc list-inside space-y-1">
                    <li>Participation is voluntary</li>
                    <li>You may stop at any time without penalty</li>
                    <li>Your data will be kept confidential</li>
                    <li>You may contact the research team with questions</li>
                  </ul>
                </div>

                <div>
                  <h3 className="font-bold mb-2" style={{ color: 'var(--text-primary)' }}>Contact</h3>
                  <p>For questions about this study, contact: <span style={{ color: 'var(--accent-primary)' }}>chans@andrew.cmu.edu</span></p>
                </div>
              </div>

              <div className="mt-6 pt-4 space-y-3" style={{ borderTop: '1px solid var(--border-default)' }}>
                {irbConsent.consented ? (
                  <>
                    {/* Withdraw Consent Confirmation */}
                    {showWithdrawConfirm ? (
                      <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--error-bg)', border: '1px solid var(--error-text)' }}>
                        <p className="text-sm mb-3" style={{ color: 'var(--error-text)' }}>
                          <strong>Are you sure you want to withdraw your consent?</strong><br/>
                          You will need to re-consent before continuing with the evaluation.
                        </p>
                        <div className="flex gap-2">
                          <button
                            onClick={handleWithdrawConsent}
                            disabled={isWithdrawing}
                            className="flex-1 py-2 rounded-lg font-semibold text-sm"
                            style={{ backgroundColor: 'var(--error-text)', color: 'white' }}
                          >
                            {isWithdrawing ? 'Withdrawing...' : 'Yes, Withdraw'}
                          </button>
                          <button
                            onClick={() => setShowWithdrawConfirm(false)}
                            disabled={isWithdrawing}
                            className="flex-1 py-2 rounded-lg font-semibold text-sm"
                            style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => setShowWithdrawConfirm(true)}
                        className="w-full py-3 rounded-lg font-semibold text-sm"
                        style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-muted)', border: '1px solid var(--border-default)' }}
                      >
                        Withdraw Consent
                      </button>
                    )}
                    <button
                      onClick={() => { setShowIrbModal(false); setShowWithdrawConfirm(false); }}
                      className="w-full py-3 rounded-lg font-semibold"
                      style={{ backgroundColor: 'var(--accent-primary)', color: 'var(--bg-primary)' }}
                    >
                      Close
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => router.push('/consent')}
                      className="w-full py-3 rounded-lg font-semibold"
                      style={{ backgroundColor: 'var(--accent-primary)', color: 'var(--bg-primary)' }}
                    >
                      Go to Consent Page
                    </button>
                    <button
                      onClick={() => setShowIrbModal(false)}
                      className="w-full py-3 rounded-lg font-semibold"
                      style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}
                    >
                      Close
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
