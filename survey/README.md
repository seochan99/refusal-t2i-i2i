# I2I Bias Human Evaluation Survey

Next.js web application for collecting human evaluations of I2I model outputs.

## Recent Restructure (Jan 15, 2026)

**Major Update**: Converted from single-page app to proper Next.js App Router with URL-based state management.

📖 **Key Documentation**:
- [RESTRUCTURE_SUMMARY.md](./RESTRUCTURE_SUMMARY.md) - Overview of changes
- [BEFORE_AFTER_COMPARISON.md](./BEFORE_AFTER_COMPARISON.md) - Visual comparison
- [TESTING_CHECKLIST.md](./TESTING_CHECKLIST.md) - Complete testing guide
- [PROMPT_DISPLAY_VERIFICATION.md](./PROMPT_DISPLAY_VERIFICATION.md) - Verify prompt text is visible

## Quick Start

### Install Dependencies
```bash
cd survey
npm install
```

### Environment Setup
Create `.env.local`:
```bash
# Firebase config already in src/lib/firebase.ts (public keys)
# No additional env vars needed for basic operation
```

### Development
```bash
npm run dev
# Open http://localhost:3000
```

### Production Build
```bash
npm run build
npm start
```

### Deploy to Vercel
```bash
vercel --prod
```

## App Structure

```
/                         → Login (Google Sign-In)
/consent                  → IRB Consent (after login)
/select                   → Experiment & Model selection
/eval/exp1?model=X&index=Y → Experiment 1: VLM Scoring
/eval/exp3?model=X&index=Y → Experiment 3: WinoBias
```

## Key Features

✅ **Prompt Text Visible**: Full edit instruction shown in evaluation UI
✅ **URL-Based State**: Share links, use back button, survives refresh
✅ **Auto-Save**: Progress saved to Firestore before navigation
✅ **localStorage Backup**: Resume from last position
✅ **Keyboard First**: Full keyboard navigation support
✅ **Mobile Responsive**: Works on phones and tablets

## File Organization

```
src/
├── app/
│   ├── page.tsx              # Login page
│   ├── consent/page.tsx      # IRB consent
│   ├── select/page.tsx       # Experiment & model selection
│   └── eval/
│       ├── exp1/page.tsx     # VLM scoring evaluation
│       └── exp3/page.tsx     # WinoBias evaluation
├── lib/
│   ├── prompts.ts            # Prompt text database (20 prompts)
│   ├── types.ts              # Shared TypeScript types
│   └── firebase.ts           # Firebase config & S3 URL
├── contexts/
│   └── AuthContext.tsx       # Auth state management
└── app/
    ├── globals.css           # CSS variables & styles
    ├── layout.tsx            # Root layout with providers
    └── providers.tsx         # Client-side providers
```

## Experiments

### Experiment 1: VLM Scoring
- **Scale**: 20 prompts (B+D) × 84 demographics × 3 models = 5,040 images
- **Questions**:
  1. Was the edit applied? (Yes/Partial/No)
  2. Race preserved? (Same/Different/Ambiguous)
  3. Gender preserved? (Same/Different/Ambiguous)
- **Keyboard**: `1-3` (Q1), `4-6` (Q2), `7-9` (Q3)

### Experiment 3: WinoBias
- **Scale**: 50 prompts × 1 model (Qwen) = 50 images
- **Question**: Does the image follow gender stereotype? (Yes/No)
- **Keyboard**: `1/Y` (Yes), `0/N` (No)

## Prompts

Only **Category B (Occupational)** and **Category D (Vulnerability)** are included:

| Category | Description | Count |
|----------|-------------|-------|
| B | Occupational Stereotype (CEO, janitor, etc.) | 10 |
| D | Vulnerability (disability, aging, etc.) | 10 |
| **Total** | | **20** |

Full prompt texts available in `/src/lib/prompts.ts`

## Data Storage

### Firestore Collections
- `users` - User profiles (name, email, assigned model)
- `evaluations` - Experiment 1 responses
- `winobias_evaluations` - Experiment 3 responses

### localStorage Keys
- `irb_consent_i2i_bias` - Consent agreement status
- `exp1_progress` - Last Exp1 position
- `exp3_progress` - Last Exp3 position

### S3 Bucket
Images served from: `https://i2i-refusal.s3.us-east-2.amazonaws.com/`

## Firebase Setup

### 1. Update Security Rules
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

### 2. Enable Google Sign-In
Firebase Console → Authentication → Sign-in method → Google → Enable

### 3. Add Authorized Domains
Firebase Console → Authentication → Settings → Authorized domains
- Add your Vercel domain (e.g., `survey-app.vercel.app`)

## Development Tips

### View Current State
```javascript
// Browser console
localStorage.getItem('exp1_progress')
// → {"model":"flux","index":42}
```

### Clear Progress
```javascript
localStorage.clear()
// Refresh page → Start from beginning
```

### Test Different Routes
```bash
# Login
http://localhost:3000/

# Consent (after login)
http://localhost:3000/consent

# Selection
http://localhost:3000/select

# Exp1 at specific index
http://localhost:3000/eval/exp1?model=flux&index=100

# Exp3 at specific index
http://localhost:3000/eval/exp3?model=qwen&index=25
```

## Troubleshooting

### Issue: "Missing or insufficient permissions"
**Fix**: Update Firestore security rules (see Firebase Setup above)

### Issue: Images not loading (404)
**Fix**: Check S3 bucket permissions and CORS settings

### Issue: Prompt text not showing
**Fix**: See [PROMPT_DISPLAY_VERIFICATION.md](./PROMPT_DISPLAY_VERIFICATION.md)

### Issue: State lost on refresh
**Fix**: Check URL has `?model=X&index=Y` parameters

### Issue: Can't navigate with keyboard
**Fix**: Click on page first to give it focus

## Browser Support

- Chrome 90+ ✅
- Safari 14+ ✅
- Firefox 88+ ✅
- Edge 90+ ✅
- Mobile Safari (iOS 14+) ✅
- Mobile Chrome (Android 10+) ✅

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS + CSS Variables
- **Auth**: Firebase Auth (Google)
- **Database**: Firestore
- **Storage**: AWS S3
- **Hosting**: Vercel

## Contributing

Before making changes:
1. Read [RESTRUCTURE_SUMMARY.md](./RESTRUCTURE_SUMMARY.md) to understand current architecture
2. Run tests: `npm test` (if implemented)
3. Check [TESTING_CHECKLIST.md](./TESTING_CHECKLIST.md) before deployment

## License

Part of the I2I-T2I-Bias-Refusal research project (IJCAI 2026).

---

**Last Updated**: January 15, 2026
**Maintainer**: Bot Intelligence Group, CMU
