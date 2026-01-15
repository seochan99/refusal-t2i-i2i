# Survey App: Before vs After Restructure

## Before (Single Page App)

```
┌─────────────────────────────────────────────────────┐
│                    page.tsx                         │
│  (1800+ lines - everything in one file)             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. IRB Consent (shown FIRST)                      │
│     └─→ No login required                          │
│                                                     │
│  2. Login Screen                                   │
│     └─→ Google Sign-In                             │
│                                                     │
│  3. Experiment Type Selector                       │
│     └─→ State: experimentType                      │
│                                                     │
│  4. Model Selector                                 │
│     └─→ State: selectedModel                       │
│                                                     │
│  5. Experiment 1 Evaluation                        │
│     └─→ State: currentIndex, q1, q2, q3            │
│                                                     │
│  6. Experiment 3 Evaluation                        │
│     └─→ State: currentIndex, stereotypeDetected    │
│                                                     │
└─────────────────────────────────────────────────────┘

Issues:
❌ Prompt text NOT visible (only ID shown)
❌ State lost on browser refresh
❌ Can't share current evaluation URL
❌ No back button support
❌ Everything in one massive file
```

## After (Multi-Page App Router)

```
┌─────────────────────────────────────────────────────┐
│              / (page.tsx - 62 lines)                │
│              Login Page ONLY                        │
└───────────────────────┬─────────────────────────────┘
                        │ Auth successful
                        ↓
┌─────────────────────────────────────────────────────┐
│       /consent/page.tsx (120 lines)                 │
│       IRB Consent (shown AFTER login)               │
└───────────────────────┬─────────────────────────────┘
                        │ Consent agreed
                        ↓
┌─────────────────────────────────────────────────────┐
│        /select/page.tsx (145 lines)                 │
│        1. Pick experiment type                      │
│        2. Pick model                                │
└───────┬────────────────────────┬────────────────────┘
        │                        │
        ↓                        ↓
┌───────────────────┐   ┌───────────────────┐
│ /eval/exp1?       │   │ /eval/exp3?       │
│   model=step1x    │   │   model=qwen      │
│   &index=42       │   │   &index=12       │
│                   │   │                   │
│ (580 lines)       │   │ (420 lines)       │
│                   │   │                   │
│ ✅ Prompt text    │   │ ✅ Prompt text    │
│    VISIBLE        │   │    VISIBLE        │
│ ✅ URL state      │   │ ✅ URL state      │
│ ✅ localStorage   │   │ ✅ localStorage   │
│ ✅ Auto-save      │   │ ✅ Auto-save      │
└───────────────────┘   └───────────────────┘
```

## File Comparison

### Before
```
survey/src/app/
└── page.tsx (1820 lines)
    ├── Constants
    ├── Interfaces
    ├── Helper functions
    ├── IRBConsentPage component
    ├── ExperimentSelector component
    ├── HumanEvaluationSurvey component
    │   ├── Model selection screen
    │   ├── Exp1 evaluation
    │   └── Exp3 evaluation
    └── All state management
```

### After
```
survey/src/
├── app/
│   ├── page.tsx (62 lines)                    ← Login only
│   ├── consent/page.tsx (120 lines)           ← NEW
│   ├── select/page.tsx (145 lines)            ← NEW
│   └── eval/
│       ├── exp1/page.tsx (580 lines)          ← NEW
│       └── exp3/page.tsx (420 lines)          ← NEW
└── lib/
    ├── prompts.ts (75 lines)                  ← NEW (prompt texts!)
    └── types.ts (35 lines)                    ← NEW (shared types)
```

## Prompt Display Fix

### Before ❌
```typescript
// Only showed the ID
<div className="mb-4 panel p-4">
  <span className="badge">{item.promptId}</span>  // "B01"
  <span className="badge">{category}</span>        // "Occupational"
</div>
// ⚠️ Evaluator has NO IDEA what the actual edit request was!
```

### After ✅
```typescript
// Shows the FULL prompt text
import { getPromptText } from '@/lib/prompts'

<div className="mb-4 panel p-5">
  <div className="flex items-center gap-2 mb-3">
    <span className="badge">{item.promptId}</span>
    <span className="badge">{category}</span>
  </div>
  <div className="prompt-text-box">
    <strong>Edit Prompt:</strong>
    {getPromptText(item.promptId)}
    // "Present the person as a senior executive leading a
    //  Fortune 500 company, conveying authority and
    //  professionalism through formal business attire..."
  </div>
</div>
// ✅ Evaluator can see EXACTLY what was requested!
```

## State Management

### Before ❌
```typescript
// All state in React component
const [currentIndex, setCurrentIndex] = useState(0)
const [experimentType, setExperimentType] = useState('')
const [selectedModel, setSelectedModel] = useState('')

// Lost on refresh!
// Can't bookmark
// Can't share URL
```

### After ✅
```typescript
// State in URL
/eval/exp1?model=flux&index=142

// Persist in localStorage
localStorage.setItem('exp1_progress', JSON.stringify({
  model: 'flux',
  index: 142
}))

// ✅ Survives refresh
// ✅ Shareable URL
// ✅ Back button works
// ✅ Resume from anywhere
```

## Navigation Flow Comparison

### Before
```
User visits site
  → IRB Consent (NO AUTH REQUIRED)
  → Google Sign In
  → Experiment Selector (in-memory state)
  → Model Selector (in-memory state)
  → Evaluation (in-memory state)

[Refresh browser] → BACK TO IRB CONSENT, ALL PROGRESS LOST
```

### After
```
User visits /
  → Google Sign In
  → /consent (check localStorage for prior consent)
  → /select (choose experiment + model)
  → /eval/exp1?model=flux&index=0

[Refresh browser] → /eval/exp1?model=flux&index=0
  → Loads completed IDs from Firestore
  → Continues from index 0 (or last completed)

[Share URL] → Friend opens same URL
  → Redirected to login
  → After auth, see same evaluation point
```

## Summary of Improvements

| Feature | Before | After |
|---------|--------|-------|
| **Prompt visibility** | ❌ Only ID shown | ✅ Full text displayed |
| **Consent timing** | ❌ Before login | ✅ After login |
| **Code organization** | ❌ 1 file, 1800 lines | ✅ 6 files, ~200 lines each |
| **State persistence** | ❌ Lost on refresh | ✅ URL + localStorage |
| **Shareable URLs** | ❌ No | ✅ Yes |
| **Back button** | ❌ Broken | ✅ Works |
| **Auto-save** | ⚠️ On submit only | ✅ Before navigation |
| **Type safety** | ⚠️ Inline types | ✅ Centralized types |
| **Prompt management** | ❌ Hardcoded | ✅ Centralized DB |

---

**Migration Impact**:
- Users must re-consent (same localStorage key)
- Old URLs won't work (redirect to login)
- Firestore data compatible (no changes needed)
- All keyboard shortcuts preserved
