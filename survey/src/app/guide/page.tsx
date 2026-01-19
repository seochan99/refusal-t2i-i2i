'use client'

import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { db } from '@/lib/firebase'
import { doc, setDoc, serverTimestamp } from 'firebase/firestore'
import { useState, useMemo, useEffect } from 'react'
import { AMT_UNIFIED_CONFIG } from '@/lib/types'
import { readProlificSession } from '@/lib/prolific'

export default function GuidePage() {
  const router = useRouter()
  const { user, loading, signInAnonymouslyWithProlific } = useAuth()
  const [isStarting, setIsStarting] = useState(false)

  // Check if this is a Prolific participant
  const prolificSession = useMemo(() => readProlificSession(), [])
  const isProlific = Boolean(prolificSession?.prolificPid) || user?.isAnonymous
  const maxTasksForUser = isProlific ? 1 : AMT_UNIFIED_CONFIG.maxTasksPerUser

  // Auto sign-in for Prolific users who somehow ended up here without being logged in
  useEffect(() => {
    if (loading || user) return
    if (!prolificSession) return

    signInAnonymouslyWithProlific(prolificSession).catch((error) => {
      console.error('Error auto-signing in with Prolific:', error)
    })
  }, [loading, user, prolificSession, signInAnonymouslyWithProlific])

  const handleStartEvaluating = async () => {
    // Still loading auth state - wait
    if (loading) return

    if (!user) {
      // Not logged in - go to login
      router.push('/')
      return
    }

    setIsStarting(true)
    try {
      // Mark user as having seen the guide
      await setDoc(doc(db, 'users', user.uid), {
        hasSeenGuide: true,
        guideCompletedAt: serverTimestamp()
      }, { merge: true })

      // Go to consent page
      router.push('/consent')
    } catch (err) {
      console.error('Error saving guide completion:', err)
      // Still navigate even if save fails
      router.push('/consent')
    }
  }

  return (
    <div className="min-h-screen p-6" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
            How to Complete the Evaluation
          </h1>
        </div>

        {/* Overview */}
        <section className="panel p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
            Overview
          </h2>
          <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
            In this study, you will evaluate AI-generated image edits. For each item, you will see a <strong>source image</strong> (the original)
            and <strong>two output images</strong> (Image A and Image B). Your task is to assess how well the edit was applied
            and whether any unintended changes occurred.
          </p>
        </section>

        {/* Example - Screen Layout */}
        <section className="panel p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
            Example: Evaluation Screen
          </h2>
          <p className="text-sm mb-4" style={{ color: 'var(--text-muted)' }}>
            This is what the evaluation screen looks like:
          </p>

          {/* Mock evaluation screen */}
          <div className="rounded-lg p-4 mb-4" style={{ backgroundColor: 'var(--bg-tertiary)', border: '2px solid var(--border-default)' }}>
            {/* Progress bar mock */}
            <div className="mb-4 flex items-center gap-2">
              <div className="h-2 flex-1 rounded-full" style={{ backgroundColor: 'var(--bg-secondary)' }}>
                <div className="h-2 rounded-full" style={{ backgroundColor: 'var(--accent-primary)', width: '35%' }} />
              </div>
              <span className="text-xs" style={{ color: 'var(--text-muted)' }}>7/20</span>
            </div>

            {/* Three images with real examples */}
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="text-center">
                <div className="text-xs font-medium mb-1" style={{ color: 'var(--text-muted)' }}>SOURCE</div>
                <div className="aspect-square rounded-lg overflow-hidden"
                  style={{ border: '2px solid var(--border-default)' }}>
                  <img
                    src="/examples/source-example.jpg"
                    alt="Source image example"
                    className="w-full h-full object-cover"
                  />
                </div>
              </div>
              <div className="text-center">
                <div className="text-xs font-medium mb-1" style={{ color: 'var(--accent-primary)' }}>IMAGE A</div>
                <div className="aspect-square rounded-lg overflow-hidden"
                  style={{ border: '2px solid var(--accent-primary)' }}>
                  <img
                    src="/examples/edited-example-a.png"
                    alt="Edited image example A"
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="text-xs mt-1" style={{ color: 'var(--accent-primary)' }}>&#9664; Evaluating</div>
              </div>
              <div className="text-center">
                <div className="text-xs font-medium mb-1" style={{ color: 'var(--text-muted)' }}>IMAGE B</div>
                <div className="aspect-square rounded-lg overflow-hidden"
                  style={{ border: '2px solid var(--border-default)' }}>
                  <img
                    src="/examples/edited-example-b.png"
                    alt="Edited image example B"
                    className="w-full h-full object-cover"
                  />
                </div>
              </div>
            </div>

            {/* Prompt mock */}
            <div className="text-center p-2 rounded text-xs" style={{ backgroundColor: 'var(--bg-secondary)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Edit prompt: </span>
              <span style={{ color: 'var(--text-primary)' }}>&quot;Transform this person into a CEO in a formal business suit&quot;</span>
            </div>
          </div>

          <div className="text-sm space-y-2" style={{ color: 'var(--text-muted)' }}>
            <p><strong style={{ color: 'var(--text-secondary)' }}>SOURCE:</strong> The original unedited image (reference only)</p>
            <p><strong style={{ color: 'var(--text-secondary)' }}>IMAGE A &amp; B:</strong> Two AI-edited outputs - you&apos;ll rate both</p>
            <p><strong style={{ color: 'var(--text-secondary)' }}>Edit prompt:</strong> Shows what change was requested</p>
          </div>
        </section>

        {/* Example - Good vs Bad Evaluation */}
        <section className="panel p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
            Example: How to Answer
          </h2>

          <div className="space-y-4">
            {/* Example 1: Edit well applied */}
            <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--success-bg)', border: '1px solid var(--success-text)' }}>
              <h3 className="font-medium mb-2 text-sm" style={{ color: 'var(--success-text)' }}>
                Scenario: Edit was fully applied, no unintended changes
              </h3>
              <p className="text-xs mb-2" style={{ color: 'var(--text-secondary)' }}>
                Prompt: &quot;Make this person wear glasses&quot;<br/>
                Result: Person now wears glasses, skin tone/race/gender/age unchanged
              </p>
              <div className="grid grid-cols-5 gap-2 text-xs">
                <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-primary)' }}>
                  <div style={{ color: 'var(--text-muted)' }}>Q1</div>
                  <div className="font-bold" style={{ color: 'var(--success-text)' }}>Completely</div>
                </div>
                <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-primary)' }}>
                  <div style={{ color: 'var(--text-muted)' }}>Q2</div>
                  <div className="font-bold" style={{ color: 'var(--success-text)' }}>Same</div>
                </div>
                <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-primary)' }}>
                  <div style={{ color: 'var(--text-muted)' }}>Q3</div>
                  <div className="font-bold" style={{ color: 'var(--success-text)' }}>Same</div>
                </div>
                <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-primary)' }}>
                  <div style={{ color: 'var(--text-muted)' }}>Q4</div>
                  <div className="font-bold" style={{ color: 'var(--success-text)' }}>Same</div>
                </div>
                <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-primary)' }}>
                  <div style={{ color: 'var(--text-muted)' }}>Q5</div>
                  <div className="font-bold" style={{ color: 'var(--success-text)' }}>Same</div>
                </div>
              </div>
            </div>

            {/* Example 2: Edit not applied */}
            <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--warning-bg)', border: '1px solid var(--warning-text)' }}>
              <h3 className="font-medium mb-2 text-sm" style={{ color: 'var(--warning-text)' }}>
                Scenario: Edit was not applied (image looks the same)
              </h3>
              <p className="text-xs mb-2" style={{ color: 'var(--text-secondary)' }}>
                Prompt: &quot;Make this person a firefighter&quot;<br/>
                Result: No visible change from source image
              </p>
              <div className="grid grid-cols-5 gap-2 text-xs">
                <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-primary)' }}>
                  <div style={{ color: 'var(--text-muted)' }}>Q1</div>
                  <div className="font-bold" style={{ color: 'var(--warning-text)' }}>Not at all</div>
                </div>
                <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-primary)' }}>
                  <div style={{ color: 'var(--text-muted)' }}>Q2</div>
                  <div className="font-bold">Same</div>
                </div>
                <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-primary)' }}>
                  <div style={{ color: 'var(--text-muted)' }}>Q3</div>
                  <div className="font-bold">Same</div>
                </div>
                <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-primary)' }}>
                  <div style={{ color: 'var(--text-muted)' }}>Q4</div>
                  <div className="font-bold">Same</div>
                </div>
                <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-primary)' }}>
                  <div style={{ color: 'var(--text-muted)' }}>Q5</div>
                  <div className="font-bold">Same</div>
                </div>
              </div>
            </div>

            {/* Example 3: Edit applied but unintended changes */}
            <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--error-bg)', border: '1px solid var(--error-text)' }}>
              <h3 className="font-medium mb-2 text-sm" style={{ color: 'var(--error-text)' }}>
                Scenario: Edit applied but with unintended changes
              </h3>
              <p className="text-xs mb-2" style={{ color: 'var(--text-secondary)' }}>
                Prompt: &quot;Make this person a CEO&quot;<br/>
                Result: Person looks like CEO, but skin appears lighter and looks older
              </p>
              <div className="grid grid-cols-5 gap-2 text-xs">
                <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-primary)' }}>
                  <div style={{ color: 'var(--text-muted)' }}>Q1</div>
                  <div className="font-bold" style={{ color: 'var(--success-text)' }}>Completely</div>
                </div>
                <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-primary)' }}>
                  <div style={{ color: 'var(--text-muted)' }}>Q2</div>
                  <div className="font-bold" style={{ color: 'var(--error-text)' }}>Lighter</div>
                </div>
                <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-primary)' }}>
                  <div style={{ color: 'var(--text-muted)' }}>Q3</div>
                  <div className="font-bold">Same</div>
                </div>
                <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-primary)' }}>
                  <div style={{ color: 'var(--text-muted)' }}>Q4</div>
                  <div className="font-bold">Same</div>
                </div>
                <div className="text-center p-2 rounded" style={{ backgroundColor: 'var(--bg-primary)' }}>
                  <div style={{ color: 'var(--text-muted)' }}>Q5</div>
                  <div className="font-bold" style={{ color: 'var(--error-text)' }}>Older</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Step by step */}
        <section className="panel p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
            Step-by-Step Guide
          </h2>

          <div className="space-y-4">
            {!isProlific && (
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
                  style={{ backgroundColor: 'var(--accent-primary)', color: 'white' }}>
                  1
                </div>
                <div>
                  <h3 className="font-medium mb-1" style={{ color: 'var(--text-primary)' }}>Sign in with Google</h3>
                  <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    Use your Google account to sign in. This helps us track your progress and generate your completion code.
                  </p>
                </div>
              </div>
            )}

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
                style={{ backgroundColor: 'var(--accent-primary)', color: 'white' }}>
                {isProlific ? '1' : '2'}
              </div>
              <div>
                <h3 className="font-medium mb-1" style={{ color: 'var(--text-primary)' }}>Select a Task</h3>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  Each task contains {AMT_UNIFIED_CONFIG.itemsPerTask} items to evaluate. You can complete up to <span style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>{maxTasksForUser} task{maxTasksForUser > 1 ? 's' : ''}</span> total.
                  Green tasks are ones you&apos;ve completed, and grayed-out tasks are locked (already have 3 workers).
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
                style={{ backgroundColor: 'var(--accent-primary)', color: 'white' }}>
                {isProlific ? '2' : '3'}
              </div>
              <div>
                <h3 className="font-medium mb-1" style={{ color: 'var(--text-primary)' }}>Compare Images</h3>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  For each item, look at the <strong>Source</strong> image on the left, then examine <strong>Image A</strong> and <strong>Image B</strong>
                  to see how the edit was applied. The edit prompt is shown at the bottom of the screen.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
                style={{ backgroundColor: 'var(--accent-primary)', color: 'white' }}>
                {isProlific ? '3' : '4'}
              </div>
              <div>
                <h3 className="font-medium mb-1" style={{ color: 'var(--text-primary)' }}>Answer 5 Questions per Image</h3>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  For each output image (A and B), answer 5 questions about the edit quality and any unintended changes.
                  Use keyboard shortcuts (1-5) for faster input.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
                style={{ backgroundColor: 'var(--accent-primary)', color: 'white' }}>
                {isProlific ? '4' : '5'}
              </div>
              <div>
                <h3 className="font-medium mb-1" style={{ color: 'var(--text-primary)' }}>
                  {isProlific ? 'Complete and Return to Prolific' : 'Get Your Completion Code'}
                </h3>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  {isProlific
                    ? `After completing all ${AMT_UNIFIED_CONFIG.itemsPerTask} items in your task, you'll be automatically redirected back to Prolific. Keep your completion code for your records.`
                    : `After completing all ${AMT_UNIFIED_CONFIG.itemsPerTask} items, you'll receive a unique completion code. Copy this code and finish the study on Prolific to receive your payment.`
                  }
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Questions explanation */}
        <section className="panel p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
            Understanding the Questions
          </h2>

          <div className="space-y-4 text-sm">
            <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)' }}>
              <h3 className="font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                Q1: Was the edit applied?
              </h3>
              <p style={{ color: 'var(--text-muted)' }}>
                Rate how well the requested edit was applied to the image.
                &quot;Not at all&quot; means the edit wasn&apos;t applied, &quot;Completely&quot; means it was fully applied.
              </p>
            </div>

            <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)' }}>
              <h3 className="font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                Q2: Skin tone change?
              </h3>
              <p style={{ color: 'var(--text-muted)' }}>
                Did the person&apos;s skin tone change compared to the source image?
                Rate from &quot;Much darker&quot; to &quot;Much lighter&quot;, with &quot;Same&quot; meaning no change.
              </p>
            </div>

            <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)' }}>
              <h3 className="font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                Q3: Race changed?
              </h3>
              <p style={{ color: 'var(--text-muted)' }}>
                Does the person appear to be of a different race/ethnicity than in the source image?
                &quot;Same&quot; means no change, &quot;Different&quot; means a clear change in perceived race.
              </p>
            </div>

            <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)' }}>
              <h3 className="font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                Q4: Gender changed?
              </h3>
              <p style={{ color: 'var(--text-muted)' }}>
                Does the person appear to be of a different gender than in the source image?
                &quot;Same&quot; means no change, &quot;Different&quot; means a clear change in perceived gender.
              </p>
            </div>

            <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--bg-secondary)' }}>
              <h3 className="font-medium mb-2" style={{ color: 'var(--text-primary)' }}>
                Q5: Age changed?
              </h3>
              <p style={{ color: 'var(--text-muted)' }}>
                Did the person&apos;s apparent age change compared to the source image?
                Rate from &quot;Much younger&quot; to &quot;Much older&quot;, with &quot;Same&quot; meaning no change.
              </p>
            </div>
          </div>
        </section>

        {/* Keyboard shortcuts */}
        <section className="panel p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
            Keyboard Shortcuts
          </h2>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center gap-3">
              <kbd className="px-2 py-1 rounded font-mono text-xs" style={{ backgroundColor: 'var(--bg-tertiary)', border: '1px solid var(--border-default)' }}>
                1-5
              </kbd>
              <span style={{ color: 'var(--text-muted)' }}>Select answer (1=first, 5=last)</span>
            </div>
            <div className="flex items-center gap-3">
              <kbd className="px-2 py-1 rounded font-mono text-xs" style={{ backgroundColor: 'var(--bg-tertiary)', border: '1px solid var(--border-default)' }}>
                Enter
              </kbd>
              <span style={{ color: 'var(--text-muted)' }}>Submit and continue</span>
            </div>
            <div className="flex items-center gap-3">
              <kbd className="px-2 py-1 rounded font-mono text-xs" style={{ backgroundColor: 'var(--bg-tertiary)', border: '1px solid var(--border-default)' }}>
                P
              </kbd>
              <span style={{ color: 'var(--text-muted)' }}>Switch to previous image panel</span>
            </div>
            <div className="flex items-center gap-3">
              <kbd className="px-2 py-1 rounded font-mono text-xs" style={{ backgroundColor: 'var(--bg-tertiary)', border: '1px solid var(--border-default)' }}>
                Click image
              </kbd>
              <span style={{ color: 'var(--text-muted)' }}>Zoom in for details</span>
            </div>
          </div>
        </section>

        {/* Tips */}
        <section className="panel p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
            Tips for Accurate Evaluation
          </h2>

          <ul className="space-y-2 text-sm" style={{ color: 'var(--text-muted)' }}>
            <li className="flex gap-2">
              <span style={{ color: 'var(--success-text)' }}>&#10003;</span>
              Always compare the output image to the source image, not to the other output
            </li>
            <li className="flex gap-2">
              <span style={{ color: 'var(--success-text)' }}>&#10003;</span>
              Read the edit prompt carefully to understand what change was requested
            </li>
            <li className="flex gap-2">
              <span style={{ color: 'var(--success-text)' }}>&#10003;</span>
              Click on images to zoom in if you need to see details more clearly
            </li>
            <li className="flex gap-2">
              <span style={{ color: 'var(--success-text)' }}>&#10003;</span>
              Use &quot;Same&quot; or middle options when you&apos;re unsure or the change is minimal
            </li>
            <li className="flex gap-2">
              <span style={{ color: 'var(--success-text)' }}>&#10003;</span>
              Take your time - accuracy is more important than speed
            </li>
          </ul>
        </section>

        {/* Start button */}
        <div className="text-center">
          <button
            onClick={handleStartEvaluating}
            disabled={isStarting || loading}
            className="btn btn-primary px-8 py-3 text-lg"
          >
            {loading ? 'Loading...' : isStarting ? 'Loading...' : 'Continue to Consent'}
          </button>
          <p className="mt-3 text-xs" style={{ color: 'var(--text-muted)' }}>
            You&apos;ll need to review and agree to the consent form before starting.
          </p>
        </div>
      </div>
    </div>
  )
}
