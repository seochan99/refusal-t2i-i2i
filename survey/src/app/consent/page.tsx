'use client'

import { useState, useEffect, useMemo, Suspense } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter, useSearchParams } from 'next/navigation'
import { db } from '@/lib/firebase'
import { doc, setDoc, getDoc, serverTimestamp } from 'firebase/firestore'
import { readProlificSession } from '@/lib/prolific'

function ConsentContent() {
  const { user, loading, logout } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const [agreed, setAgreed] = useState(false)
  const [checkingConsent, setCheckingConsent] = useState(true)
  const isReviewMode = searchParams.get('review') === '1' || searchParams.get('review') === 'true'

  // Check if this is a Prolific participant
  const prolificSession = useMemo(() => readProlificSession(), [])
  const isProlific = Boolean(prolificSession?.prolificPid) || user?.isAnonymous

  // Redirect to login if not authenticated (check first)
  useEffect(() => {
    if (!loading && !user) {
      if (window.location.pathname === '/consent') {
        router.push('/')
      }
      return
    }
  }, [user, loading, router])

  // Check if user already consented (Firebase + localStorage)
  useEffect(() => {
    async function checkConsent() {
      if (loading || !user) {
        setCheckingConsent(false)
        return
      }

      try {
        // Check Firebase first (authoritative source)
        const userDoc = await getDoc(doc(db, 'users', user.uid))
        if (userDoc.exists()) {
          const data = userDoc.data()
          if (data.irbConsent === true) {
            // Also update localStorage for quick checks
            localStorage.setItem('irb_consent_i2i_bias', 'agreed')
            setAgreed(true)
            if (!isReviewMode && window.location.pathname === '/consent') {
              router.push('/tasks')
              return
            }
            setCheckingConsent(false)
            return
          }
        }

        // Fallback to localStorage (for backward compatibility)
        const localConsent = localStorage.getItem('irb_consent_i2i_bias')
        if (localConsent === 'agreed') {
          // Sync to Firebase
          await setDoc(doc(db, 'users', user.uid), {
            irbConsent: true,
            irbConsentAt: serverTimestamp(),
            email: user.email,
            displayName: user.displayName,
          }, { merge: true })

          setAgreed(true)
          if (!isReviewMode && window.location.pathname === '/consent') {
            router.push('/tasks')
            return
          }
          setCheckingConsent(false)
          return
        }
      } catch (err) {
        console.error('Error checking consent:', err)
      }

      setCheckingConsent(false)
    }

    checkConsent()
  }, [user, loading, router, isReviewMode])

  const handleConsent = async () => {
    if (!user) return

    try {
      // Save consent to Firebase (per-user)
      await setDoc(doc(db, 'users', user.uid), {
        email: user.email || '',
        displayName: user.displayName || (isProlific ? `Prolific_${prolificSession?.prolificPid?.slice(0, 8) || 'user'}` : ''),
        photoURL: user.photoURL || '',
        irbConsent: true,
        irbConsentAt: serverTimestamp(),
        updatedAt: serverTimestamp(),
        // Include Prolific data if available
        ...(prolificSession && {
          prolificPid: prolificSession.prolificPid,
          prolificStudyId: prolificSession.studyId,
          prolificSessionId: prolificSession.sessionId,
          authProvider: 'anonymous'
        })
      }, { merge: true })

      // Also save to localStorage for quick checks
      localStorage.setItem('irb_consent_i2i_bias', 'agreed')

      router.push('/tasks')
    } catch (err) {
      console.error('Error saving consent:', err)
      alert('Failed to save consent. Please try again.')
    }
  }

  if (loading || !user || checkingConsent) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="text-base" style={{ color: 'var(--text-muted)' }}>Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-4 md:p-8" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Research Consent</h1>
            <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>Carnegie Mellon University</p>
          </div>
          <div className="flex items-center gap-3">
            {user.photoURL ? (
              <img src={user.photoURL} alt="" className="w-8 h-8 rounded-full" style={{ border: '1px solid var(--border-default)' }} />
            ) : (
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
                style={{ backgroundColor: 'var(--accent-primary)', color: 'white' }}>
                {isProlific ? 'P' : (user.email?.charAt(0).toUpperCase() || 'U')}
              </div>
            )}
            <div className="text-right">
              <div className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>
                {user.displayName || (isProlific ? `Prolific: ${prolificSession?.prolificPid?.slice(0, 8)}...` : user.email?.split('@')[0] || 'User')}
              </div>
              {!isProlific && (
                <button onClick={logout} className="text-xs transition-colors" style={{ color: 'var(--text-muted)' }}>
                  Sign out
                </button>
              )}
              {isProlific && (
                <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  via Prolific
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Quick Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <div className="panel p-4 text-center">
            <div className="text-2xl mb-1">15-20</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Minutes</div>
          </div>
          <div className="panel p-4 text-center">
            <div className="text-2xl mb-1">50</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Items</div>
          </div>
          <div className="panel p-4 text-center">
            <div className="text-2xl mb-1">$3</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Payment</div>
          </div>
          <div className="panel p-4 text-center">
            <div className="text-2xl mb-1" style={{ color: 'var(--success-text)' }}>Low</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Risk</div>
          </div>
        </div>

        {/* Main Content */}
        <div className="panel-elevated p-6 mb-6">
          {/* Study Overview */}
          <div className="mb-6 pb-6" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
            <h2 className="font-semibold text-lg mb-3" style={{ color: 'var(--text-primary)' }}>
              What is this study about?
            </h2>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              You will evaluate AI-generated image edits by answering questions about image quality,
              identity preservation, and potential biases. Your responses will help improve fairness in AI systems.
            </p>
          </div>

          {/* What You&apos;ll Do */}
          <div className="mb-6 pb-6" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
            <h2 className="font-semibold text-lg mb-3" style={{ color: 'var(--text-primary)' }}>
              What will I do?
            </h2>
            <div className="grid md:grid-cols-3 gap-3 text-sm">
              <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)' }}>
                <div className="font-medium mb-1" style={{ color: 'var(--text-primary)' }}>1. View Images</div>
                <p style={{ color: 'var(--text-muted)' }}>Compare source and AI-edited images</p>
              </div>
              <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)' }}>
                <div className="font-medium mb-1" style={{ color: 'var(--text-primary)' }}>2. Answer Questions</div>
                <p style={{ color: 'var(--text-muted)' }}>Rate edit quality and identity changes</p>
              </div>
              <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)' }}>
                <div className="font-medium mb-1" style={{ color: 'var(--text-primary)' }}>3. Get Paid</div>
                <p style={{ color: 'var(--text-muted)' }}>Receive payment via Prolific</p>
              </div>
            </div>
          </div>

          {/* Key Points */}
          <div className="mb-6 pb-6" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
            <h2 className="font-semibold text-lg mb-3" style={{ color: 'var(--text-primary)' }}>
              Key Points
            </h2>
            <ul className="space-y-2 text-sm">
              <li className="flex items-start gap-2">
                <span style={{ color: 'var(--success-text)' }}>&#10003;</span>
                <span style={{ color: 'var(--text-secondary)' }}><strong>Voluntary:</strong> You can stop at any time</span>
              </li>
              <li className="flex items-start gap-2">
                <span style={{ color: 'var(--success-text)' }}>&#10003;</span>
                <span style={{ color: 'var(--text-secondary)' }}><strong>Anonymous:</strong> No identifying info is stored with responses</span>
              </li>
              <li className="flex items-start gap-2">
                <span style={{ color: 'var(--success-text)' }}>&#10003;</span>
                <span style={{ color: 'var(--text-secondary)' }}><strong>Low Risk:</strong> Standard computer/internet use only</span>
              </li>
              <li className="flex items-start gap-2">
                <span style={{ color: 'var(--success-text)' }}>&#10003;</span>
                <span style={{ color: 'var(--text-secondary)' }}><strong>IRB Approved:</strong> STUDY2022_00000005 (Exempt Cat. 2 &amp; 3)</span>
              </li>
            </ul>
          </div>

          {/* Detailed Information (Collapsible) */}
          <details className="mb-6">
            <summary className="cursor-pointer font-semibold text-sm py-2" style={{ color: 'var(--accent-primary)' }}>
              View Full Consent Details
            </summary>
            <div className="mt-4 p-4 rounded-lg text-sm leading-relaxed space-y-4" style={{ backgroundColor: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}>
              <div>
                <h4 className="font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Purpose</h4>
                <p>
                  The goal of this study is to get human evaluation on the quality of AI generated artifacts.
                  The research questions include whether the quality of output by one algorithm is better than another,
                  and to understand ways to evaluate bias in AI-generated images.
                </p>
              </div>

              <div>
                <h4 className="font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Confidentiality</h4>
                <p>
                  Any reports and presentations about the findings from this study will not include your name or any other
                  information that could identify you. Your Prolific Participant ID will be used only for payment distribution
                  and will be removed from the data completely.
                </p>
              </div>

              <div>
                <h4 className="font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Risks and Benefits</h4>
                <p>
                  There are no risks beyond normal computer use. You will learn about cutting-edge AI image generation
                  and your participation will contribute to improving fairness in AI systems.
                </p>
              </div>

              <div>
                <h4 className="font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>Contact</h4>
                <p>
                  Questions? Email: <span style={{ color: 'var(--accent-primary)' }}>chans@andrew.cmu.edu</span>
                </p>
              </div>

              <div className="p-3 rounded" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  <strong>IRB Protocol:</strong> STUDY2022_00000005<br/>
                  <strong>Study:</strong> Evaluation of AI generated behaviors and artifacts<br/>
                  <strong>PI:</strong> Jean Oh, Carnegie Mellon University
                </p>
              </div>
            </div>
          </details>

          {/* Consent Checkbox */}
          <label className="flex items-start gap-4 p-4 rounded-lg cursor-pointer transition-all"
            style={{
              backgroundColor: agreed ? 'var(--success-bg)' : 'var(--bg-secondary)',
              border: agreed ? '2px solid var(--success-text)' : '2px solid transparent'
            }}>
            <input
              type="checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
              className="mt-0.5 w-5 h-5 rounded border-2 focus:ring-2 focus:ring-offset-2 transition-all flex-shrink-0"
              style={{
                borderColor: agreed ? 'var(--success-text)' : 'var(--border-default)',
                backgroundColor: agreed ? 'var(--success-text)' : 'transparent',
                accentColor: 'var(--success-text)'
              }}
            />
            <span className="text-sm leading-relaxed" style={{ color: agreed ? 'var(--success-text)' : 'var(--text-secondary)' }}>
              <strong>I agree to participate.</strong> I have read and understood the information above.
              I am 18 years of age or older and provide my informed consent.
            </span>
          </label>
        </div>

        {/* Action Button */}
        <button
          onClick={handleConsent}
          disabled={!agreed}
          className="btn btn-primary w-full py-4 text-base font-semibold"
        >
          {agreed ? 'Start Evaluation' : 'Please agree to continue'}
        </button>

        {/* Footer Info */}
        <p className="text-center text-xs mt-4" style={{ color: 'var(--text-muted)' }}>
          Bot Intelligence Group &middot; Carnegie Mellon University
        </p>
      </div>
    </div>
  )
}

/**
 * IRB Consent page
 * Shown AFTER login, before experiment selection
 * Consent is stored per-user in Firebase (not just localStorage)
 */
export default function ConsentPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="text-base" style={{ color: 'var(--text-muted)' }}>Loading...</div>
      </div>
    }>
      <ConsentContent />
    </Suspense>
  )
}
