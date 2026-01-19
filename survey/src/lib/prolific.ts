export type ProlificSession = {
  prolificPid: string
  studyId: string
  sessionId: string
}

const STORAGE_KEY = 'prolific_session'

// Default Prolific completion code - can be overridden via env variable
export const PROLIFIC_COMPLETION_CODE =
  process.env.NEXT_PUBLIC_PROLIFIC_COMPLETION_CODE || 'C17U36TG'

export const getProlificCompletionUrl = (code: string = PROLIFIC_COMPLETION_CODE) => {
  if (!code) return ''
  return `https://app.prolific.com/submissions/complete?cc=${code}`
}

export const normalizeProlificSession = (session: Partial<ProlificSession> | null) => {
  if (!session) return null
  const prolificPid = (session.prolificPid || '').trim()
  if (!prolificPid) return null
  return {
    prolificPid,
    studyId: (session.studyId || '').trim(),
    sessionId: (session.sessionId || '').trim()
  }
}

export const storeProlificSession = (session: ProlificSession | null) => {
  if (typeof window === 'undefined') return
  if (!session) return
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
}

export const readProlificSession = () => {
  if (typeof window === 'undefined') return null
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null
  try {
    return normalizeProlificSession(JSON.parse(raw))
  } catch {
    return null
  }
}
