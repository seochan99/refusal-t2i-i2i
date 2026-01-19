# Survey App Developer Guide

## Quick Start

```bash
cd survey
npm install
npm run dev
```

Open http://localhost:3000

---

## Project Structure

```
survey/
├── src/
│   ├── app/              # Next.js pages
│   │   ├── page.tsx      # Login
│   │   ├── consent/      # IRB consent
│   │   ├── amt/          # AMT Worker ID entry
│   │   ├── select/       # Model selection
│   │   ├── eval/
│   │   │   ├── exp1/     # VLM scoring (5 questions)
│   │   │   ├── exp2/     # Pairwise A/B
│   │   │   └── exp3/     # WinoBias stereotype
│   │   └── complete/     # Completion code
│   ├── components/       # Reusable UI
│   ├── contexts/         # Auth, theme
│   ├── lib/
│   │   ├── firebase.ts   # Firebase config
│   │   ├── types.ts      # TypeScript types
│   │   └── prompts.ts    # Prompt text loader
│   └── styles/
├── public/
│   └── data/
│       ├── exp2_items.json
│       └── exp3_items.json
└── BUGFIXES.md          # This update
```

---

## Key Files Modified (Jan 2026)

### 1. `/src/app/amt/page.tsx`
**What it does:** AMT Worker ID entry (optional)

**Key changes:**
- Removed redirect for existing users
- Pre-fills existing data
- Always allows editing

**Functions:**
- `handleSubmit()` - Saves AMT info
- `handleSkip()` - Skips without saving

### 2. `/src/app/select/page.tsx`
**What it does:** Experiment and model selection

**Key changes:**
- Clickable Worker ID
- "+ Add AMT ID" button
- Removed forced redirect

**Functions:**
- `loadAMT()` - Loads Worker ID
- `loadProgress()` - Loads evaluation counts
- `handleStart()` - Navigates to evaluation

### 3. `/src/app/eval/exp1/page.tsx`
**What it does:** 5-question VLM evaluation

**Key changes:**
- Error handling with alerts
- Null safety for missing data

**Functions:**
- `generateEvalItems()` - Creates 1680 items
- `loadData()` - Loads progress (with error handling)
- `saveEvaluation()` - Saves to Firebase

### 4. `/src/app/eval/exp2/page.tsx`
**What it does:** Pairwise A/B comparison

**Key changes:**
- Image loading states
- Retry button for errors
- Better error messages

**Functions:**
- `loadPairwiseItems()` - Loads from JSON
- `saveEvaluation()` - Saves preference
- Image state handlers

### 5. `/src/app/eval/exp3/page.tsx`
**What it does:** Binary stereotype detection

**Key changes:**
- Error alerts for Firebase failures
- Graceful degradation

**Functions:**
- `loadWinoBiasItems()` - Loads from JSON
- `saveEvaluation()` - Saves binary choice

### 6. `/src/app/complete/page.tsx`
**What it does:** Shows completion code

**Key changes:**
- Success logging
- Non-blocking errors

**Functions:**
- `generateCompletionCode()` - Creates unique code
- `saveCompletion()` - Updates user doc
- `handleCopy()` - Copies to clipboard

---

## Firebase Structure

### Collections

#### `users`
```typescript
{
  uid: string                    // Firebase Auth ID
  email: string
  displayName: string
  photoURL: string
  amtWorkerId: string | null     // ← NEW: Now editable
  amtAssignmentId: string | null
  amtHitId: string | null
  createdAt: Timestamp
  updatedAt: Timestamp
  completions: {
    [key: string]: {
      completionCode: string
      completedItems: number
      completedAt: Timestamp
    }
  }
}
```

#### `evaluations` (Exp1)
```typescript
{
  evalId: string                 // userId_itemId
  userId: string
  itemId: string
  model: string
  promptId: string
  category: string
  race: string
  gender: string
  age: string
  edit_success: number           // 1-5
  skin_tone: number              // 1-5
  race_drift: number             // 1-5
  gender_drift: number           // 1-5
  age_drift: number              // 1-5
  duration_ms: number
  createdAt: Timestamp
  experimentType: 'exp1'
}
```

#### `pairwise_evaluations` (Exp2)
```typescript
{
  evalId: string
  userId: string
  itemId: string
  model: string
  promptId: string
  category: string
  race: string
  gender: string
  age: string
  preference: 'preserved' | 'edited' | 'tie'
  leftWasPreserved: boolean      // Position bias tracking
  rawChoice: 'A' | 'B' | 'tie'
  duration_ms: number
  createdAt: Timestamp
  experimentType: 'exp2_pairwise'
}
```

#### `winobias_evaluations` (Exp3)
```typescript
{
  evalId: string
  userId: string
  itemId: string
  model: string
  promptId: number
  promptText: string
  genderCode: 'M' | 'F'
  stereotypeDetected: 0 | 1      // Binary
  duration_ms: number
  createdAt: Timestamp
  experimentType: 'exp3'
}
```

---

## Environment Variables

Create `.env.local`:

```bash
# Firebase
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=...
NEXT_PUBLIC_FIREBASE_PROJECT_ID=...
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=...
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=...
NEXT_PUBLIC_FIREBASE_APP_ID=...

# S3/R2 Bucket
NEXT_PUBLIC_S3_BUCKET_URL=https://your-bucket.s3.amazonaws.com
```

---

## Common Tasks

### Add New Model to Exp1

1. Edit `/src/lib/types.ts`:
```typescript
export const MODELS_EXP1 = {
  // ... existing models
  newmodel: {
    name: 'New Model',
    total: 1680,
    available: true
  }
}
```

2. Upload images to S3:
```
s3://bucket/newmodel/by_category/B_occupation/B01_White_Male_20-29_success.png
```

3. No code changes needed!

### Add New Prompt to Exp1

1. Edit prompt JSON (if external) or hardcoded prompts
2. Images must follow naming: `{promptId}_{race}_{gender}_{age}_success.png`
3. Update `CATEGORIES` in types.ts if new category

### Debug Firebase Errors

```typescript
// In any component:
import { db } from '@/lib/firebase'
import { collection, getDocs } from 'firebase/firestore'

// Test query:
try {
  const snapshot = await getDocs(collection(db, 'users'))
  console.log('✅ Firebase OK:', snapshot.size)
} catch (err) {
  console.error('❌ Firebase error:', err)
}
```

### Test Completion Code Generation

```typescript
// In browser console:
const userId = 'test123'
const exp = 'exp1'
const model = 'flux'

const timestamp = Date.now().toString(36)
const userHash = userId.slice(0, 4).toUpperCase()
const code = `${exp.toUpperCase()}-${model.slice(0,3).toUpperCase()}-${userHash}-${timestamp}`
console.log('Code:', code)
```

---

## Error Handling Patterns

### Pattern 1: User-Facing Alerts (Critical Errors)
```typescript
try {
  await saveData()
} catch (error) {
  console.error('Error:', error)
  alert('Failed to save. Please try again.')  // ← User sees this
}
```

### Pattern 2: Silent Logging (Non-Critical)
```typescript
try {
  await saveCompletion()
  console.log('✅ Saved')
} catch (error) {
  console.error('Error saving:', error)
  // Don't block - user can still continue
}
```

### Pattern 3: Graceful Degradation
```typescript
try {
  const data = await loadProgress()
  setProgress(data)
} catch (error) {
  console.error('Error loading:', error)
  setProgress({})  // ← Empty progress, not blocked
  alert('Continuing without saved progress.')
}
```

---

## Keyboard Shortcuts

### Exp1
- `1-5`: Answer current question
- `↑↓`: Switch between questions
- `←→`: Navigate items
- `N`: Next incomplete

### Exp2
- `A` or `1`: Select left
- `B` or `2`: Select right
- `T` or `3` or `=`: Tie
- `←→`: Navigate
- `N`: Next incomplete

### Exp3
- `1`: Stereotype detected
- `2`: No stereotype
- `←→`: Navigate
- `N`: Next incomplete

---

## Testing Locally

### 1. Run Dev Server
```bash
npm run dev
```

### 2. Open Browser
http://localhost:3000

### 3. Sign In
Use Google OAuth (real account or test account)

### 4. Test Flow
1. Accept consent
2. Skip AMT (or enter fake ID)
3. Select any experiment
4. Complete a few items
5. Sign out and back in
6. Verify progress persists

### 5. Test Errors
- Disconnect internet during save
- Use invalid model param
- Check console for errors

---

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Production
vercel --prod
```

### Environment Variables in Vercel
1. Go to Vercel dashboard
2. Settings → Environment Variables
3. Add all `NEXT_PUBLIC_*` vars
4. Redeploy

---

## Monitoring

### Firebase Console
- https://console.firebase.google.com
- Check Firestore for new evaluations
- Monitor Auth for sign-ins
- Check Usage tab for quota

### Vercel Logs
```bash
vercel logs
```

### Browser DevTools
- Console tab: Check for errors
- Network tab: Check Firebase requests
- Application → Local Storage: Check saved progress

---

## Common Issues

### Issue: "Module not found"
**Solution:** `npm install`

### Issue: Firebase auth error
**Solution:** Check `.env.local` has all vars

### Issue: Images not loading
**Solution:** Verify `NEXT_PUBLIC_S3_BUCKET_URL`

### Issue: Keyboard shortcuts not working
**Solution:** Click on page to focus

### Issue: Progress not saving
**Solution:** Check Firebase console for write errors

---

## Code Style

### Component Structure
```tsx
'use client'  // ← Client component

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'

export default function MyPage() {
  const { user, loading } = useAuth()
  const [data, setData] = useState(null)

  useEffect(() => {
    // Load data
  }, [user])

  if (loading) return <div>Loading...</div>

  return <div>Content</div>
}
```

### Error Handling
```typescript
async function loadData() {
  try {
    const result = await fetchData()
    setState(result)
  } catch (error) {
    console.error('Error:', error)
    alert('User-friendly message')
  }
}
```

### State Updates
```typescript
// ✅ Good
setItems(prevItems => [...prevItems, newItem])

// ❌ Bad
items.push(newItem)
setItems(items)
```

---

## Resources

- **Next.js Docs**: https://nextjs.org/docs
- **Firebase Docs**: https://firebase.google.com/docs
- **Tailwind CSS**: https://tailwindcss.com/docs
- **TypeScript**: https://www.typescriptlang.org/docs

---

## Changelog

### January 17, 2026
- Fixed AMT page redirect bug
- Added clickable AMT Worker ID in Select page
- Improved error handling across all eval pages
- Added image loading states and retry buttons
- Enhanced console logging
- Created comprehensive documentation

---

Last Updated: January 17, 2026
