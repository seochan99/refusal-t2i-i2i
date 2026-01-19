// Import the functions you need from the SDKs you need
import { initializeApp, getApps } from "firebase/app";
import { getFirestore } from "firebase/firestore";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCYZNH-D5KEPc_2f1Gr9vcmFpyd29t97xU",
  authDomain: "acrb-e8cb4.firebaseapp.com",
  projectId: "acrb-e8cb4",
  storageBucket: "acrb-e8cb4.firebasestorage.app",
  messagingSenderId: "87810362498",
  appId: "1:87810362498:web:9a13c8f15886030ab6b89b"
};

// Initialize Firebase (prevent duplicate initialization)
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];

// Initialize Firebase services
export const db = getFirestore(app);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();

// Image base URL - Firebase Storage for production
const FIREBASE_STORAGE_BUCKET = "acrb-e8cb4.firebasestorage.app";
const STORAGE_PREFIX = "i2i-survey";

// Convert local image path to Firebase Storage URL
export function getImageUrl(localPath: string): string {
  // If already a full URL (Firebase or S3), return as is
  if (localPath.startsWith('http://') || localPath.startsWith('https://')) {
    return localPath;
  }
  
  // Convert /images/... to Firebase Storage URL
  if (localPath.startsWith('/images/')) {
    const storagePath = localPath.replace('/images/', `${STORAGE_PREFIX}/`);
    // Firebase Storage requires path segments to be encoded with %2F
    const encodedPath = storagePath.split('/').map(segment => encodeURIComponent(segment)).join('%2F');
    return `https://firebasestorage.googleapis.com/v0/b/${FIREBASE_STORAGE_BUCKET}/o/${encodedPath}?alt=media`;
  }
  
  // Return as is if doesn't match pattern
  return localPath;
}

// Legacy exports for compatibility
export const S3_BUCKET_URL = "/images";
export const USE_LOCAL_IMAGES = false;  // Use Firebase Storage in production

// Firestore collection names
export const COLLECTIONS = {
  EVALUATIONS: "evaluations",
  USERS: "users",
  SESSIONS: "sessions"
};

export default app;
