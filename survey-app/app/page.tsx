'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'

export default function LandingPage() {
  const router = useRouter()
  const [prolificId, setProlificId] = useState('')

  const handleStart = () => {
    if (prolificId.trim()) {
      localStorage.setItem('prolificId', prolificId.trim())
      router.push('/consent')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="survey-card">
        <div className="mb-10">
          <p className="text-xs tracking-widest text-neutral-500 uppercase mb-3">
            Research Study
          </p>
          <h1 className="text-2xl font-light text-neutral-900 mb-2">
            Image Generation Model Evaluation
          </h1>
          <div className="w-12 h-px bg-neutral-300 mt-4" />
        </div>

        <div className="space-y-6 text-sm text-neutral-600 leading-relaxed mb-10">
          <p>
            This study examines how AI image generation models respond to
            diverse prompts across different demographic attributes.
          </p>

          <div className="border-l-2 border-neutral-200 pl-4 py-2 space-y-2">
            <p><span className="text-neutral-900">Duration</span> — 15-20 minutes</p>
            <p><span className="text-neutral-900">Tasks</span> — Evaluate ~50 images</p>
            <p><span className="text-neutral-900">ID</span> — ACRB-2025-001</p>
          </div>

          <p className="text-neutral-500 text-xs">
            Some images may contain content that was refused or modified by AI systems.
          </p>
        </div>

        <div className="mb-8">
          <label className="block text-xs tracking-widest text-neutral-500 uppercase mb-3">
            Prolific ID
          </label>
          <input
            type="text"
            value={prolificId}
            onChange={(e) => setProlificId(e.target.value)}
            placeholder="Enter your ID"
            className="w-full"
          />
        </div>

        <button
          onClick={handleStart}
          disabled={!prolificId.trim()}
          className="btn-primary w-full"
        >
          Begin Study
        </button>
      </div>
    </div>
  )
}
