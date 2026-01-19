'use client'

import { useState, useEffect, useMemo, Suspense } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter, useSearchParams } from 'next/navigation'
import { db } from '@/lib/firebase'
import { doc, setDoc, getDoc, serverTimestamp } from 'firebase/firestore'
import { readProlificSession } from '@/lib/prolific'
import { trackPageView, trackEvent } from '@/lib/analytics'

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

    // Track page view
    trackPageView('consent', { review_mode: isReviewMode })
  }, [user, loading, router, isReviewMode])

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
        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="panel p-4 text-center">
            <div className="text-2xl mb-1">15-20</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Minutes</div>
          </div>
          <div className="panel p-4 text-center">
            <div className="text-2xl mb-1">50</div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Items</div>
          </div>
        </div>

        {/* Main Content */}
        <div className="panel-elevated p-6 mb-6">
          {/* Consent Form Title */}
          <div className="mb-6 pb-6" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
            <h2 className="font-bold text-lg mb-4" style={{ color: 'var(--text-primary)' }}>
              Consent Form for Evaluating AI-Generated Image Edits
            </h2>
            <p className="text-sm leading-relaxed mb-3" style={{ color: 'var(--text-secondary)' }}>
              You are being asked to participate in a research study being conducted by the{' '}
              <strong style={{ color: 'var(--text-primary)' }}>Bot Intelligence Group at Carnegie Mellon University</strong>.
            </p>
            <p className="text-sm font-semibold" style={{ color: 'var(--accent-primary)' }}>
              Participation is voluntary.
            </p>
          </div>

          {/* Purpose */}
          <div className="mb-6 pb-6" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
            <h3 className="font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
              Purpose of the Study
            </h3>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              The purpose of this study is to understand ways to evaluate bias in AI-generated image edits.
              Any reports and presentations about the findings from this study will not include your name
              or any other information that could identify you.
            </p>
          </div>

          {/* What You&apos;ll Be Asked */}
          <div className="mb-6 pb-6" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
            <h3 className="font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
              What You Will Be Asked
            </h3>
            <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
              You will be asked the following questions per image:
            </p>
            <div className="space-y-3 text-sm">
              <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)' }}>
                <div className="font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>Text and Image Alignment</div>
                <p style={{ color: 'var(--text-muted)' }}>
                  Given a prompt, evaluate whether the AI-edited image matches the requested edit.
                </p>
              </div>
              <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)' }}>
                <div className="font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>Identity Preservation</div>
                <p style={{ color: 'var(--text-muted)' }}>
                  Evaluate whether the person&apos;s identity (skin tone, race, gender, age) was preserved after the edit.
                </p>
              </div>
              <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)' }}>
                <div className="font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>Unintended Changes</div>
                <p style={{ color: 'var(--text-muted)' }}>
                  Identify any unintended changes to the person&apos;s appearance that occurred during the edit.
                </p>
              </div>
            </div>
          </div>

          {/* Confidentiality */}
          <div className="mb-6 pb-6" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
            <h3 className="font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
              Confidentiality
            </h3>
            <p className="text-sm leading-relaxed mb-3" style={{ color: 'var(--text-secondary)' }}>
              Your Prolific Participant ID will be used to distribute the payment to you,
              but we will not store your participant ID with your survey responses.
            </p>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              Please be aware that your Prolific Participant ID can potentially be linked to
              information about you on your Prolific profile, however we will not access any
              personally identifying information. The ID information will be removed from
              the data and deleted completely.
            </p>
          </div>

          {/* Contact */}
          <div className="mb-6 pb-6" style={{ borderBottom: '1px solid var(--border-subtle)' }}>
            <h3 className="font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
              Contact Information
            </h3>
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              If you have questions about the research, you can email the research team at:{' '}
              <a href="mailto:chans@andrew.cmu.edu" style={{ color: 'var(--accent-primary)' }}>
                chans@andrew.cmu.edu
              </a>
            </p>
          </div>

          {/* IRB Info */}
          <div className="p-4 rounded-lg mb-6" style={{ backgroundColor: 'var(--bg-secondary)' }}>
            <div className="text-xs space-y-1" style={{ color: 'var(--text-muted)' }}>
              <p><strong style={{ color: 'var(--text-secondary)' }}>IRB Protocol Number:</strong> STUDY2022_00000005</p>
              <p><strong style={{ color: 'var(--text-secondary)' }}>Study Title:</strong> Evaluation of AI generated behaviors and artifacts</p>
              <p><strong style={{ color: 'var(--text-secondary)' }}>Principal Investigator:</strong> Jean Oh, Carnegie Mellon University</p>
              <p><strong style={{ color: 'var(--text-secondary)' }}>Exempt Category:</strong> Category 2 &amp; 3</p>
            </div>
          </div>

        </div>

        {/* Spacer for fixed footer */}
        <div className="h-36" />
      </div>

      {/* Fixed Footer - Consent & Button */}
      <div
        className="fixed bottom-0 left-0 right-0 p-4 border-t"
        style={{
          backgroundColor: 'var(--bg-elevated)',
          borderColor: 'var(--border-default)',
          boxShadow: '0 -4px 20px rgba(0,0,0,0.15)'
        }}
      >
        <div className="max-w-4xl mx-auto">
          {/* Consent Checkbox */}
          <label className="flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all mb-3"
            style={{
              backgroundColor: agreed ? 'var(--success-bg)' : 'var(--bg-secondary)',
              border: agreed ? '2px solid var(--success-text)' : '2px solid var(--border-default)'
            }}>
            <input
              type="checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
              className="w-6 h-6 rounded border-2 focus:ring-2 focus:ring-offset-2 transition-all flex-shrink-0"
              style={{
                borderColor: agreed ? 'var(--success-text)' : 'var(--border-default)',
                backgroundColor: agreed ? 'var(--success-text)' : 'transparent',
                accentColor: 'var(--success-text)'
              }}
            />
            <span className="text-sm" style={{ color: agreed ? 'var(--success-text)' : 'var(--text-secondary)' }}>
              I am 18+ years old, I have read the above, and I agree to participate.
            </span>
          </label>

          {/* Action Button */}
          <button
            onClick={handleConsent}
            disabled={!agreed}
            className="btn btn-primary w-full py-4 text-base font-bold"
          >
            {agreed ? 'Start Evaluation' : 'Check the box above to continue'}
          </button>
        </div>
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
