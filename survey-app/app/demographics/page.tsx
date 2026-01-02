'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'

interface Demographics {
  age: string
  gender: string
  nationality: string
  ethnicity: string
  aiExperience: string
}

export default function DemographicsPage() {
  const router = useRouter()
  const [demographics, setDemographics] = useState<Demographics>({
    age: '',
    gender: '',
    nationality: '',
    ethnicity: '',
    aiExperience: '',
  })

  const updateField = (field: keyof Demographics, value: string) => {
    setDemographics((prev) => ({ ...prev, [field]: value }))
  }

  const isComplete = Object.values(demographics).every((v) => v !== '')

  const handleContinue = () => {
    if (isComplete) {
      localStorage.setItem('demographics', JSON.stringify(demographics))
      router.push('/survey')
    }
  }

  const ageOptions = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+']
  const genderOptions = ['Male', 'Female', 'Non-binary', 'Prefer not to say']
  const nationalityOptions = [
    'United States', 'United Kingdom', 'India', 'China', 'Japan', 'South Korea',
    'Germany', 'France', 'Brazil', 'Mexico', 'Nigeria', 'South Africa', 'Other'
  ]
  const ethnicityOptions = [
    'Asian', 'Black/African', 'Hispanic/Latino', 'Middle Eastern',
    'White/Caucasian', 'Mixed/Multiple', 'Prefer not to say', 'Other'
  ]
  const aiExperienceOptions = [
    'Never used',
    'Used a few times',
    'Use occasionally',
    'Use regularly',
    'Use daily'
  ]

  const OptionButton = ({
    selected,
    onClick,
    children
  }: {
    selected: boolean
    onClick: () => void
    children: React.ReactNode
  }) => (
    <button
      onClick={onClick}
      className={`p-3 border text-sm transition-all text-left ${
        selected
          ? 'border-neutral-900 bg-neutral-50'
          : 'border-neutral-200 hover:border-neutral-400'
      }`}
    >
      {children}
    </button>
  )

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="survey-card">
        <div className="mb-10">
          <p className="text-xs tracking-widest text-neutral-500 uppercase mb-3">
            Step 2 of 4
          </p>
          <h1 className="text-2xl font-light text-neutral-900">
            About You
          </h1>
          <div className="w-12 h-px bg-neutral-300 mt-4" />
        </div>

        <div className="space-y-10">
          <div>
            <label className="block text-xs tracking-widest text-neutral-500 uppercase mb-4">
              Age Group
            </label>
            <div className="grid grid-cols-3 gap-2">
              {ageOptions.map((option) => (
                <OptionButton
                  key={option}
                  selected={demographics.age === option}
                  onClick={() => updateField('age', option)}
                >
                  {option}
                </OptionButton>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs tracking-widest text-neutral-500 uppercase mb-4">
              Gender
            </label>
            <div className="grid grid-cols-2 gap-2">
              {genderOptions.map((option) => (
                <OptionButton
                  key={option}
                  selected={demographics.gender === option}
                  onClick={() => updateField('gender', option)}
                >
                  {option}
                </OptionButton>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs tracking-widest text-neutral-500 uppercase mb-4">
              Country of Residence
            </label>
            <select
              value={demographics.nationality}
              onChange={(e) => updateField('nationality', e.target.value)}
              className="w-full"
            >
              <option value="">Select country</option>
              {nationalityOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs tracking-widest text-neutral-500 uppercase mb-4">
              Ethnicity
            </label>
            <div className="grid grid-cols-2 gap-2">
              {ethnicityOptions.map((option) => (
                <OptionButton
                  key={option}
                  selected={demographics.ethnicity === option}
                  onClick={() => updateField('ethnicity', option)}
                >
                  {option}
                </OptionButton>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs tracking-widest text-neutral-500 uppercase mb-4">
              AI Image Generator Experience
            </label>
            <div className="space-y-2">
              {aiExperienceOptions.map((option) => (
                <OptionButton
                  key={option}
                  selected={demographics.aiExperience === option}
                  onClick={() => updateField('aiExperience', option)}
                >
                  {option}
                </OptionButton>
              ))}
            </div>
          </div>
        </div>

        <button
          onClick={handleContinue}
          disabled={!isComplete}
          className="btn-primary w-full mt-10"
        >
          Continue
        </button>
      </div>
    </div>
  )
}
