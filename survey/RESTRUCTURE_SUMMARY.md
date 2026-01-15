# Survey App Restructure Summary

## Overview
Restructured the survey app from a single-page application to a proper Next.js App Router multi-page structure with URL-based state management and persistent progress tracking.

## Key Issues Fixed

### 1. ✅ Edit Prompt Text Now Visible
- **Before**: Only showed prompt ID (e.g., "B01")
- **After**: Prominently displays the full prompt text in a highlighted box above the questions
- Location: `/src/lib/prompts.ts` - centralized prompt text database
- Display: Shown in Exp1 evaluation page with accent styling

### 2. ✅ IRB Consent After Login
- **Before**: Consent shown BEFORE login
- **After**: Login → Consent → Experiment Selection flow
- Route: `/consent/page.tsx`

### 3. ✅ Proper Page Separation
```
/ (page.tsx)              → Login only
/consent/page.tsx         → IRB Consent (after login)
/select/page.tsx          → Experiment & Model selection
/eval/exp1/page.tsx       → Experiment 1: VLM Scoring
/eval/exp3/page.tsx       → Experiment 3: WinoBias
```

### 4. ✅ State Management
- **URL Query Params**: `?model=step1x&index=42`
- **localStorage**: Backup for browser refresh
- **Auto-save**: Before navigation, on answer completion
- **Resume Support**: Returns to last evaluated index

### 5. ⚠️ Firebase Permission Error
**Manual Fix Required**: Update Firestore security rules to allow the new collection structure.

## New File Structure

```
survey/src/
├── app/
│   ├── page.tsx                    # Login page (updated)
│   ├── consent/
│   │   └── page.tsx                # IRB consent (new)
│   ├── select/
│   │   └── page.tsx                # Experiment & model selection (new)
│   └── eval/
│       ├── exp1/
│       │   └── page.tsx            # VLM scoring evaluation (new)
│       └── exp3/
│           └── page.tsx            # WinoBias evaluation (new)
├── lib/
│   ├── prompts.ts                  # Prompt text database (new)
│   ├── types.ts                    # Shared TypeScript types (new)
│   └── firebase.ts                 # (existing)
└── contexts/
    └── AuthContext.tsx             # (existing)
```

## Navigation Flow

```
┌─────────────┐
│   / (Login) │
└──────┬──────┘
       │ Login successful
       ↓
┌─────────────┐
│   /consent  │ Check localStorage: irb_consent_i2i_bias
└──────┬──────┘
       │ Consent agreed
       ↓
┌─────────────┐
│   /select   │ 1. Choose experiment type
└──────┬──────┘ 2. Choose model
       │
       ├─→ /eval/exp1?model=step1x&index=0
       │   └─→ URL updates on navigation
       │
       └─→ /eval/exp3?model=qwen&index=0
           └─→ URL updates on navigation
```

## Key Features

### URL-Based State
```typescript
// Example URL: /eval/exp1?model=flux&index=142
const searchParams = useSearchParams()
const model = searchParams.get('model')
const index = parseInt(searchParams.get('index') || '0')

// Updates on navigation (without page reload)
router.replace(`/eval/exp1?model=${model}&index=${newIndex}`, { scroll: false })
```

### localStorage Backup
```typescript
// Saved on every navigation
localStorage.setItem('exp1_progress', JSON.stringify({ model, index }))

// IRB consent tracking
localStorage.setItem('irb_consent_i2i_bias', 'agreed')
```

### Auto-save on Navigation
- Evaluations auto-save when all questions answered (150ms delay)
- Progress persists across browser refreshes
- Can use back button without losing progress

### Prompt Display (Fixed!)
```typescript
// /src/lib/prompts.ts
export const PROMPT_TEXTS = {
  B01: "Present the person as a senior executive leading a Fortune 500 company...",
  // ... all 20 prompts (B01-B10, D01-D10)
}

// In Exp1 page
import { getPromptText } from '@/lib/prompts'

<div className="prompt-display">
  <strong>Edit Prompt:</strong>
  {getPromptText(currentItem.promptId)}
</div>
```

## Keyboard Shortcuts (Preserved)

### Experiment 1
- `1, 2, 3` - Q1 answers
- `4, 5, 6` - Q2 answers
- `7, 8, 9` - Q3 answers
- `←/→` - Navigate prev/next
- `N` - Jump to next incomplete

### Experiment 3
- `1` or `Y` - Yes, follows stereotype
- `0` or `N` - No, breaks stereotype
- `←/→` - Navigate prev/next
- `N` - Jump to next incomplete

## Firebase Collections

### Existing
- `evaluations` - Experiment 1 data
- `users` - User profiles

### New (for Exp3)
- `winobias_evaluations` - Experiment 3 data

## Manual Setup Required

### 1. Firestore Security Rules
Update rules to allow the new structure:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    match /evaluations/{evalId} {
      allow read, write: if request.auth != null;
    }

    match /winobias_evaluations/{evalId} {
      allow read, write: if request.auth != null;
    }
  }
}
```

### 2. Test the Flow
1. Clear localStorage: `localStorage.clear()`
2. Visit `/` → Should show login
3. Sign in → Should redirect to `/consent`
4. Accept consent → Should redirect to `/select`
5. Select Exp1 + Model → Should redirect to `/eval/exp1?model=...&index=0`
6. Verify prompt text is visible above questions ✓
7. Answer questions → Should auto-save and advance
8. Refresh page → Should resume at same index

## Migration Notes

### Breaking Changes
- Old bookmarks to `/` will now show login instead of the full app
- Users must complete consent flow again (localStorage key unchanged)
- URL structure changed: use `/eval/exp1?model=...` instead of state-based navigation

### Backward Compatibility
- Existing Firestore data unchanged
- localStorage consent key preserved: `irb_consent_i2i_bias`
- Auth flow unchanged (Google Sign-In)

## Next Steps

1. **Deploy to Vercel**: Test the full flow in production
2. **Update Firestore Rules**: Apply the security rules above
3. **Clear Old Data**: If needed, reset localStorage for all users
4. **Monitor**: Check for console errors related to navigation/state

## Prompt Text Locations

All 20 prompts (B01-B10, D01-D10) are now centralized in `/src/lib/prompts.ts`:
- Category B: Occupational Stereotypes (10 prompts)
- Category D: Vulnerability Attributes (10 prompts)
- Categories A, C, E excluded from human evaluation

---

**Last Updated**: January 15, 2026
**Status**: Ready for testing
