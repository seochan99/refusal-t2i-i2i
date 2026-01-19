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

export interface Exp1Evaluation {
  edit_success: number      // 1-5: Soft Erasure Detection
  skin_tone: number         // 1-5: Unintended skin tone change
  race_drift: number        // 1-5: Unintended race drift
  gender_drift: number      // 1-5: Unintended gender drift
  age_drift: number         // 1-5: Age drift (general or D03-specific)
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
  sourceInput1Url?: string
  sourceInput2Url?: string
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

// Unified AMT Item (combines exp1 + exp2 items, shuffled)
export interface AmtItem {
  id: string              // amt_0001, amt_0002, ...
  taskId: number          // Task ID (1-25)
  originalId: string      // original exp2 item ID
  model: string
  promptId: string
  category: string
  categoryName: string
  race: string
  gender: string
  age: string
  sourceImageUrl: string
  editedImageUrl: string
  preservedImageUrl: string
}

// Models for each experiment - AMT sampled counts (500 items each)
export const MODELS_EXP1 = {
  step1x: { name: 'Step1X-Edit', total: 167, available: true },
  flux: { name: 'FLUX.2-dev', total: 167, available: true },
  qwen: { name: 'Qwen-Image-Edit', total: 166, available: true }
} as const

export const MODELS_EXP2 = {
  qwen: { name: 'Qwen-Image-Edit', total: 166, available: true },
  step1x: { name: 'Step1X-Edit', total: 167, available: true },
  flux: { name: 'FLUX.2-dev', total: 167, available: true }
} as const

// AMT HIT Configuration for Exp2 (legacy)
export const AMT_HIT_CONFIG = {
  itemsPerHit: 10,           // 10 items per HIT
  totalItems: 500,           // Total items in exp2
  totalHits: 50,             // 500 / 10 = 50 unique HITs
  ratersPerItem: 3,          // 3 raters per item
  totalAssignments: 150,     // 50 HITs * 3 raters = 150 total assignments
  paymentPerHit: 6.00,       // $6.00 per HIT
  estimatedMinutes: 35       // ~35 minutes per HIT
} as const

// Unified AMT Configuration (500 items, shuffled across models)
export const AMT_UNIFIED_CONFIG = {
  itemsPerTask: 50,          // 50 items per Task
  totalItems: 500,           // Total items (shuffled from exp2)
  totalTasks: 10,            // 500 / 50 = 10 Tasks
  maxWorkersPerTask: 3,      // 3 workers per task (slots)
  maxTasksPerUser: 3,        // Max 3 tasks per user (150 items max)
  totalAssignments: 30,      // 10 Tasks * 3 workers = 30 total assignments
  questionsPerItem: 10,      // 5 for edited + 5 for preserved
  paymentPerTask: 15.00,     // $15.00 per Task (50 items, ~15-20 min)
  estimatedMinutes: 20       // ~15-20 minutes per Task
} as const

// Explicit export to ensure Vercel build cache recognizes it
export type AmtUnifiedConfig = typeof AMT_UNIFIED_CONFIG

export const MODELS_EXP3 = {
  qwen: { name: 'Qwen-Image-Edit', total: 50, available: true },
  flux: { name: 'FLUX.2-dev', total: 50, available: true }
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
