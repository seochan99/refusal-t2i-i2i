export interface SurveyItem {
  id: string
  type: 'quality' | 'attribute' | 'refusal' | 'attention'
  imageUrl: string
  prompt: string
  attribute?: string
  attributeValue?: string
  model?: string
  domain?: string
  isRefusal?: boolean
  refusalMessage?: string
  correctAnswer?: string
}

export interface Response {
  itemId: string
  type: string
  answer: string | number
  responseTimeMs: number
  timestamp: string
}

export interface Demographics {
  age: string
  gender: string
  nationality: string
  ethnicity: string
  aiExperience: string
}

export interface Participant {
  sessionId: string
  prolificId: string
  demographics: Demographics
  consentTimestamp: string
  startTime: string
  endTime?: string
}

export interface SurveySession {
  participant: Participant
  responses: Response[]
  metadata: {
    userAgent?: string
    completionCode?: string
    attentionChecksPassed: number
    totalAttentionChecks: number
  }
}

export interface AnalysisResult {
  totalParticipants: number
  completedParticipants: number
  averageCompletionTime: number
  attentionCheckPassRate: number
  responsesByType: {
    quality: number
    attribute: number
    refusal: number
  }
  demographicBreakdown: {
    byAge: Record<string, number>
    byGender: Record<string, number>
    byNationality: Record<string, number>
  }
}
