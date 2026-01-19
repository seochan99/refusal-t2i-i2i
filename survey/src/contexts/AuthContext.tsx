'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { User, signInWithPopup, signOut, onAuthStateChanged, signInAnonymously } from 'firebase/auth'
import { doc, setDoc, getDoc, serverTimestamp } from 'firebase/firestore'
import { auth, googleProvider, db, COLLECTIONS } from '@/lib/firebase'
import { normalizeProlificSession, readProlificSession, storeProlificSession, type ProlificSession } from '@/lib/prolific'

interface AuthContextType {
  user: User | null
  loading: boolean
  signInWithGoogle: () => Promise<void>
  signInAnonymouslyWithProlific: (session: ProlificSession) => Promise<void>
  logout: () => Promise<void>
  userProfile: UserProfile | null
}

interface UserProfile {
  uid: string
  email: string
  displayName: string
  photoURL: string
  assignedModel: string | null
  totalEvaluations: number
  createdAt: Date
  lastActiveAt: Date
  authProvider: 'google' | 'anonymous'
  prolificPid: string | null
  prolificStudyId: string | null
  prolificSessionId: string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setUser(user)

      if (user) {
        try {
          // Get or create user profile in Firestore
          const userRef = doc(db, COLLECTIONS.USERS, user.uid)
          const userSnap = await getDoc(userRef)

          const prolificSession = readProlificSession()
          if (prolificSession) {
            await setDoc(userRef, {
              prolificPid: prolificSession.prolificPid,
              prolificStudyId: prolificSession.studyId,
              prolificSessionId: prolificSession.sessionId,
              authProvider: user.isAnonymous ? 'anonymous' : 'google',
              updatedAt: serverTimestamp()
            }, { merge: true })
          }

          if (userSnap.exists()) {
            const data = userSnap.data()
            setUserProfile({
              uid: user.uid,
              email: user.email || '',
              displayName: user.displayName || '',
              photoURL: user.photoURL || '',
              assignedModel: data.assignedModel || null,
              totalEvaluations: data.totalEvaluations || 0,
              createdAt: data.createdAt?.toDate() || new Date(),
              lastActiveAt: new Date(),
              authProvider: data.authProvider || (user.isAnonymous ? 'anonymous' : 'google'),
              prolificPid: data.prolificPid || prolificSession?.prolificPid || null,
              prolificStudyId: data.prolificStudyId || prolificSession?.studyId || null,
              prolificSessionId: data.prolificSessionId || prolificSession?.sessionId || null
            })

            // Update last active
            await setDoc(userRef, { lastActiveAt: serverTimestamp() }, { merge: true })
          } else {
            // Create new user profile
            const newProfile = {
              uid: user.uid,
              email: user.email || '',
              displayName: user.displayName || '',
              photoURL: user.photoURL || '',
              assignedModel: null,
              totalEvaluations: 0,
              createdAt: serverTimestamp(),
              lastActiveAt: serverTimestamp(),
              authProvider: user.isAnonymous ? 'anonymous' : 'google',
              prolificPid: prolificSession?.prolificPid || null,
              prolificStudyId: prolificSession?.studyId || null,
              prolificSessionId: prolificSession?.sessionId || null
            }
            await setDoc(userRef, newProfile)
            setUserProfile({
              ...newProfile,
              createdAt: new Date(),
              lastActiveAt: new Date()
            } as UserProfile)
          }
        } catch (error: any) {
          // Ignore permission errors during logout/auth state changes
          if (error?.code === 'permission-denied' || error?.code === 'unauthenticated') {
            console.log('Auth state changed, skipping Firestore operations')
            setUserProfile(null)
          } else {
            console.error('Error loading user profile:', error)
          }
        }
      } else {
        setUserProfile(null)
      }

      setLoading(false)
    })

    return () => unsubscribe()
  }, [])

  const signInWithGoogle = async () => {
    try {
      await signInWithPopup(auth, googleProvider)
    } catch (error) {
      console.error('Error signing in with Google:', error)
      throw error
    }
  }

  const signInAnonymouslyWithProlific = async (session: ProlificSession) => {
    const normalized = normalizeProlificSession(session)
    if (!normalized) {
      throw new Error('Missing Prolific participant ID')
    }

    storeProlificSession(normalized)
    const credential = await signInAnonymously(auth)
    const user = credential.user

    const userRef = doc(db, COLLECTIONS.USERS, user.uid)
    await setDoc(userRef, {
      prolificPid: normalized.prolificPid,
      prolificStudyId: normalized.studyId,
      prolificSessionId: normalized.sessionId,
      authProvider: 'anonymous',
      updatedAt: serverTimestamp()
    }, { merge: true })
  }

  const logout = async () => {
    try {
      await signOut(auth)
    } catch (error) {
      console.error('Error signing out:', error)
      throw error
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, signInWithGoogle, signInAnonymouslyWithProlific, logout, userProfile }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
