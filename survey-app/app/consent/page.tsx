'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'

export default function ConsentPage() {
  const router = useRouter()
  const [agreed, setAgreed] = useState(false)

  const handleContinue = () => {
    if (agreed) {
      localStorage.setItem('consentGiven', 'true')
      localStorage.setItem('consentTimestamp', new Date().toISOString())
      router.push('/demographics')
    }
  }

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="survey-card">
        <div className="mb-10">
          <p className="text-xs tracking-widest text-neutral-500 uppercase mb-3">
            Step 1 of 4
          </p>
          <h1 className="text-2xl font-light text-neutral-900">
            Informed Consent
          </h1>
          <div className="w-12 h-px bg-neutral-300 mt-4" />
        </div>

        <div className="space-y-8 text-sm text-neutral-600 leading-relaxed mb-10">
          <section>
            <h2 className="text-xs tracking-widest text-neutral-500 uppercase mb-2">
              Study Title
            </h2>
            <p>
              Evaluating Fairness and Refusal Bias in AI Image Generation Models
            </p>
          </section>

          <section>
            <h2 className="text-xs tracking-widest text-neutral-500 uppercase mb-2">
              Purpose
            </h2>
            <p>
              This research investigates how AI image generation systems respond
              to prompts involving different demographic attributes. Your participation
              helps identify potential biases in these systems.
            </p>
          </section>

          <section>
            <h2 className="text-xs tracking-widest text-neutral-500 uppercase mb-2">
              Procedure
            </h2>
            <ul className="space-y-1">
              <li>— View approximately 50 AI-generated images</li>
              <li>— Answer questions about image quality and content</li>
              <li>— Identify whether requests were blocked or modified</li>
              <li>— Provide basic demographic information</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xs tracking-widest text-neutral-500 uppercase mb-2">
              Risks
            </h2>
            <p>
              Some images may depict content that was refused or modified by AI systems.
              While explicit content has been screened, some images may touch on sensitive
              topics. You may skip any question or withdraw at any time.
            </p>
          </section>

          <section>
            <h2 className="text-xs tracking-widest text-neutral-500 uppercase mb-2">
              Confidentiality
            </h2>
            <p>
              Responses are anonymized and stored securely. Your Prolific ID is used
              only for compensation and will not be linked to responses in publications.
            </p>
          </section>
        </div>

        <div className="border-t border-neutral-200 pt-8">
          <label className="flex items-start gap-4 cursor-pointer">
            <input
              type="checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
              className="mt-0.5"
            />
            <span className="text-sm text-neutral-600">
              I have read and understood the above information. I agree to
              participate and understand I can withdraw at any time.
            </span>
          </label>
        </div>

        <div className="mt-8 flex gap-4">
          <button
            onClick={() => router.push('/')}
            className="btn-secondary flex-1"
          >
            Decline
          </button>
          <button
            onClick={handleContinue}
            disabled={!agreed}
            className="btn-primary flex-1"
          >
            Continue
          </button>
        </div>
      </div>
    </div>
  )
}
