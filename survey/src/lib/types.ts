/**
 * Shared TypeScript types for the survey app
 */

export interface EvalItem {
  id: string
  sourceImageUrl: string
  outputImageUrl: string
  promptId: string
  category: string
  race: string
  gender: string
  age: string
  model: string
  filename: string
}

export interface WinoBiasItem {
  id: string
  promptId: string
  promptText: string
  outputImageUrl: string
  model: string
  genderCode: 'M' | 'F'
  stereotype: string
  input1: string
  input2: string
}

export interface PairwiseItem {
  id: string
  model: string
  promptId: string
  category: string
  categoryName: string
  race: string
  gender: string
  age: string
  sourceImageUrl: string
  preservedImageUrl: string
  editedImageUrl: string | null
  hasEditedPair: boolean
}

// Models for each experiment (available: true = ready, false = coming soon)
export const MODELS_EXP1 = {
  step1x: { name: 'Step1X-Edit', total: 1680, available: true },
  flux: { name: 'FLUX.2-dev', total: 1680, available: false },
  qwen: { name: 'Qwen-Image-Edit', total: 1680, available: false },
  gemini: { name: 'Gemini (Example)', total: 1680, available: true }
} as const

export const MODELS_EXP2 = {
  step1x: { name: 'Step1X-Edit', total: 107, available: true },
  qwen: { name: 'Qwen-Image-Edit', total: 107, available: false },
  flux: { name: 'FLUX.2-dev', total: 107, available: false }
} as const

export const MODELS_EXP3 = {
  qwen: { name: 'Qwen-Image-Edit', total: 50, available: true },
  flux: { name: 'FLUX.2-dev', total: 50, available: false }
} as const

// Legacy export for backward compatibility
export const MODELS = MODELS_EXP1

export const CATEGORIES = {
  B: { name: 'Occupational Stereotype', prompts: 10 },
  D: { name: 'Vulnerability', prompts: 10 }
} as const

export const RACES = ['Black', 'EastAsian', 'Indian', 'Latino', 'MiddleEastern', 'SoutheastAsian', 'White'] as const
export const GENDERS = ['Female', 'Male'] as const
export const AGES = ['20s', '30s', '40s', '50s', '60s', '70plus'] as const

export type ModelKey = keyof typeof MODELS
export type CategoryKey = keyof typeof CATEGORIES
export type Race = typeof RACES[number]
export type Gender = typeof GENDERS[number]
export type Age = typeof AGES[number]
