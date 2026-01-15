'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'

/**
 * IRB Consent page
 * Shown AFTER login, before experiment selection
 */
export default function ConsentPage() {
  const { user, loading, logout } = useAuth()
  const router = useRouter()
  const [agreed, setAgreed] = useState(false)

  // Redirect to login if not authenticated (check first)
  useEffect(() => {
    if (!loading && !user) {
      if (window.location.pathname === '/consent') {
        router.push('/')
      }
      return
    }
  }, [user, loading, router])

  // Check if user already consented (only if authenticated)
  useEffect(() => {
    if (loading || !user) return
    
    const consent = localStorage.getItem('irb_consent_i2i_bias')
    if (consent === 'agreed' && window.location.pathname === '/consent') {
      router.push('/amt')
    }
  }, [user, loading, router])

  const handleConsent = () => {
    localStorage.setItem('irb_consent_i2i_bias', 'agreed')
    router.push('/amt')
  }

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <div className="text-base" style={{ color: 'var(--text-muted)' }}>Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-8" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="max-w-3xl w-full panel-elevated p-10">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-semibold" style={{ color: 'var(--text-primary)' }}>Research Study Consent Form</h1>
          <div className="flex items-center gap-3">
            {user.photoURL && (
              <img src={user.photoURL} alt="" className="w-8 h-8 rounded-full" style={{ border: '1px solid var(--border-default)' }} />
            )}
            <div className="text-right">
              <div className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>{user.displayName}</div>
              <button onClick={logout} className="text-xs transition-colors" style={{ color: 'var(--text-muted)' }}>
                Sign out
              </button>
            </div>
          </div>
        </div>

        <div className="panel p-8 mb-8 max-h-96 overflow-y-auto text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          <h2 className="font-bold text-lg mb-4">Study Information</h2>

          <p className="mb-4">
            You are being asked to participate in a research study being conducted by the
            <strong> Bot Intelligence Group at Carnegie Mellon University</strong>.
          </p>

          <p className="mb-4 font-semibold">Participation is voluntary.</p>

          <h3 className="font-bold mt-4 mb-2">Purpose</h3>
          <p className="mb-4">
            The purpose of this study is to understand ways to evaluate bias in AI-generated
            images, specifically examining how image-to-image editing models handle requests
            across different demographic groups.
          </p>

          <h3 className="font-bold mt-4 mb-2">What You Will Be Asked To Do</h3>
          <ul className="list-disc pl-5 mb-4 space-y-2">
            <li><strong>Text and Image Alignment:</strong> Evaluate whether AI-edited images match the requested edits.</li>
            <li><strong>Identity Preservation:</strong> Assess whether the person&apos;s identity is maintained after editing.</li>
            <li><strong>Stereotype Detection:</strong> Identify if images reflect occupational or gender stereotypes.</li>
          </ul>

          <h3 className="font-bold mt-4 mb-2">Confidentiality</h3>
          <p className="mb-4">
            Any reports and presentations about the findings from this study will not include
            your name or any other information that could identify you. Your responses will be
            anonymized and used only for research purposes.
          </p>

          <h3 className="font-bold mt-4 mb-2">Time Commitment</h3>
          <p className="mb-4">
            Each evaluation session takes approximately 15-30 minutes depending on the
            experiment type selected.
          </p>

          <h3 className="font-bold mt-4 mb-2">Risk and Benefits</h3>
          <p className="mb-4">
            This study involves minimal risk. Some images may contain AI-generated content
            that could be perceived as biased or stereotypical, as this is the focus of our
            research. Your participation will contribute to improving fairness in AI systems.
          </p>

          <h3 className="font-bold mt-4 mb-2">Contact Information</h3>
          <p className="mb-4">
            If you have questions about this research, please contact the research team at
            the Bot Intelligence Group, Carnegie Mellon University.
          </p>

          <div className="panel p-4 mt-6" style={{ backgroundColor: 'var(--bg-elevated)', borderColor: 'var(--border-strong)' }}>
            <p className="text-xs leading-relaxed" style={{ color: 'var(--text-muted)' }}>
              <strong style={{ color: 'var(--text-secondary)' }}>IRB Protocol:</strong> STUDY2022_00000005<br/>
              <strong style={{ color: 'var(--text-secondary)' }}>Title:</strong> Evaluation of AI generated behaviors and artifacts<br/>
              <strong style={{ color: 'var(--text-secondary)' }}>Category:</strong> Exempt Category 2/3
            </p>
          </div>
        </div>

        <label className="flex items-start gap-4 mb-8 cursor-pointer group">
          <input
            type="checkbox"
            checked={agreed}
            onChange={(e) => setAgreed(e.target.checked)}
            className="mt-1 w-5 h-5 rounded border-2 focus:ring-2 focus:ring-offset-2 transition-all"
            style={{
              borderColor: agreed ? 'var(--accent-primary)' : 'var(--border-default)',
              backgroundColor: agreed ? 'var(--accent-primary)' : 'transparent',
              accentColor: 'var(--accent-primary)'
            }}
          />
          <span className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
            I have read and understood the information above. I am 18 years of age or older,
            and I agree to participate in this research study. By checking this box and
            proceeding, I am providing my informed consent.
          </span>
        </label>

        <button
          onClick={handleConsent}
          disabled={!agreed}
          className="btn btn-primary w-full py-4 text-base font-semibold"
        >
          Continue to Study
        </button>
      </div>
    </div>
  )
}
