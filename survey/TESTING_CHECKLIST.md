# Survey App Testing Checklist

## Pre-Deployment Setup

### 1. Firebase Security Rules
```bash
# Go to Firebase Console → Firestore Database → Rules
# Update with the following:
```

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // User profiles
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    // Experiment 1 evaluations
    match /evaluations/{evalId} {
      allow read, write: if request.auth != null;
    }

    // Experiment 3 evaluations (WinoBias)
    match /winobias_evaluations/{evalId} {
      allow read, write: if request.auth != null;
    }

    // Sessions (if needed)
    match /sessions/{sessionId} {
      allow read, write: if request.auth != null;
    }
  }
}
```

### 2. Environment Variables
```bash
# Verify .env.local exists with Firebase config
cat survey/.env.local
```

### 3. Build Test
```bash
cd survey
npm run build
# Should complete without errors
```

---

## Manual Testing Flow

### Test 1: First-Time User Flow
- [ ] **1.1** Visit `/` → Should show login page
- [ ] **1.2** Click "Sign in with Google" → Firebase auth popup
- [ ] **1.3** After successful login → Redirects to `/consent`
- [ ] **1.4** Consent page shows user's name and photo in top right
- [ ] **1.5** Try clicking "Continue" without checkbox → Button disabled
- [ ] **1.6** Check the consent checkbox → Button becomes active
- [ ] **1.7** Click "Continue to Study" → Redirects to `/select`
- [ ] **1.8** Select page shows "Select Experiment Type"

### Test 2: Experiment 1 (VLM Scoring)
- [ ] **2.1** Click "Experiment 1: VLM Scoring"
- [ ] **2.2** Should show model selection (3 models: Step1X, FLUX, Qwen)
- [ ] **2.3** Select FLUX → Shows progress count
- [ ] **2.4** Click "START EVALUATION" → Redirects to `/eval/exp1?model=flux&index=0`
- [ ] **2.5** Page loads with:
  - [ ] Source image on left
  - [ ] Output image on right
  - [ ] **PROMPT TEXT VISIBLE** in highlighted box above Q1
  - [ ] Demographics badge (race/gender/age)
  - [ ] Progress bar at top
  - [ ] Counter showing "1 / 1680"
- [ ] **2.6** Verify prompt text matches promptId (e.g., B01 shows CEO prompt)
- [ ] **2.7** Try keyboard shortcuts:
  - [ ] Press `1` → Q1 selects "Yes"
  - [ ] Press `4` → Q2 selects "Same"
  - [ ] Press `7` → Q3 selects "Same"
  - [ ] After all answered → "Saving & advancing..." appears
  - [ ] After ~150ms → Auto-advances to next image
- [ ] **2.8** Check URL → Should update to `index=1`
- [ ] **2.9** Click "← Prev" → Returns to index 0
- [ ] **2.10** Refresh browser → Should stay at current index
- [ ] **2.11** Click "Exit" → Returns to `/select`

### Test 3: Experiment 3 (WinoBias)
- [ ] **3.1** From `/select`, click "Experiment 3: WinoBias"
- [ ] **3.2** Only Qwen model should be available
- [ ] **3.3** Select Qwen → Click "START EVALUATION"
- [ ] **3.4** Redirects to `/eval/exp3?model=qwen&index=0`
- [ ] **3.5** Page loads with:
  - [ ] AI generated image on left
  - [ ] **Prompt text visible** in quote box
  - [ ] Gender pronoun indicator (Male/Female)
  - [ ] Stereotyped occupation highlighted
  - [ ] Input images noted at bottom
  - [ ] Binary question on right
- [ ] **3.6** Try keyboard shortcuts:
  - [ ] Press `1` or `Y` → "Yes, Follows Stereotype" selected
  - [ ] Auto-advances after ~300ms
- [ ] **3.7** Navigate back, try `0` or `N` → "No, Breaks Stereotype"
- [ ] **3.8** Verify URL updates with each navigation

### Test 4: State Persistence
- [ ] **4.1** Start Exp1, evaluate 5 images
- [ ] **4.2** Copy current URL (e.g., `/eval/exp1?model=flux&index=4`)
- [ ] **4.3** Refresh browser → Should stay at same image
- [ ] **4.4** Open URL in incognito window → Redirects to login
- [ ] **4.5** After login → Should go to same evaluation point
- [ ] **4.6** Check localStorage:
  ```javascript
  // In browser console
  localStorage.getItem('irb_consent_i2i_bias') // "agreed"
  localStorage.getItem('exp1_progress') // {"model":"flux","index":4}
  ```

### Test 5: Completed Evaluations
- [ ] **5.1** Complete 3 evaluations in Exp1
- [ ] **5.2** Navigate back to first evaluation
- [ ] **5.3** Should show "COMPLETED" badge
- [ ] **5.4** Press `N` (next incomplete) → Skips to first unevaluated
- [ ] **5.5** Check Firestore:
  - [ ] Go to Firebase Console → Firestore Database
  - [ ] Collection: `evaluations`
  - [ ] Should see 3 documents with your userId
  - [ ] Each document should have: q1_edit_applied, q2_race_same, q3_gender_same

### Test 6: Navigation & Back Button
- [ ] **6.1** Start at index 0
- [ ] **6.2** Use arrow keys: `→` advances, `←` goes back
- [ ] **6.3** Use browser back button → Should go to previous index
- [ ] **6.4** Use browser forward button → Should go to next index
- [ ] **6.5** All navigation should update URL without page reload

### Test 7: Authentication & Logout
- [ ] **7.1** Click user name in top right → Should show "Sign out" link
- [ ] **7.2** Click "Sign out" → Redirects to `/` (login page)
- [ ] **7.3** Try to manually visit `/eval/exp1?model=flux&index=0` → Redirects to login
- [ ] **7.4** Sign in again → Consent already agreed, goes to `/select`

### Test 8: Mobile Responsiveness
- [ ] **8.1** Open on mobile device or resize browser to 375px width
- [ ] **8.2** Login page should be readable
- [ ] **8.3** Consent page should scroll properly
- [ ] **8.4** Evaluation pages should stack images vertically (if applicable)
- [ ] **8.5** Touch targets should be large enough for fingers

---

## Automated Testing (Optional)

### Playwright Test
```typescript
// tests/e2e/survey-flow.spec.ts
import { test, expect } from '@playwright/test'

test('complete evaluation flow', async ({ page }) => {
  // 1. Login
  await page.goto('/')
  await page.click('button:has-text("Sign in with Google")')
  // ... handle Google OAuth popup

  // 2. Consent
  await expect(page).toHaveURL('/consent')
  await page.check('input[type="checkbox"]')
  await page.click('button:has-text("Continue to Study")')

  // 3. Select experiment
  await expect(page).toHaveURL('/select')
  await page.click('button:has-text("Experiment 1")')
  await page.click('button:has-text("FLUX")')
  await page.click('button:has-text("START EVALUATION")')

  // 4. Evaluate
  await expect(page).toHaveURL(/\/eval\/exp1\?model=flux&index=0/)

  // Check prompt text is visible
  const promptText = await page.locator('text=/Present the person as/').textContent()
  expect(promptText).toBeTruthy()

  // Answer questions via keyboard
  await page.keyboard.press('1')
  await page.keyboard.press('4')
  await page.keyboard.press('7')

  // Should auto-advance
  await page.waitForURL(/index=1/)
})
```

---

## Performance Testing

### Load Time
- [ ] **P.1** Initial page load < 2s
- [ ] **P.2** Navigation between pages < 500ms
- [ ] **P.3** Image loading uses lazy loading
- [ ] **P.4** No console errors on any page

### Network
- [ ] **P.5** Check Network tab → Images loaded from S3
- [ ] **P.6** Firestore queries batched/cached properly
- [ ] **P.7** No unnecessary re-renders (React DevTools)

---

## Edge Cases

### Error Handling
- [ ] **E.1** No network connection → Show error message
- [ ] **E.2** Firestore permission denied → Show helpful error
- [ ] **E.3** Image fails to load → Show placeholder
- [ ] **E.4** Invalid model in URL → Redirect to select page

### Data Validation
- [ ] **E.5** Can't start evaluation without selecting model
- [ ] **E.6** Can't proceed past consent without checkbox
- [ ] **E.7** Duplicate evaluation (same itemId) → Updates existing document

---

## Browser Compatibility

Test on:
- [ ] Chrome (latest)
- [ ] Safari (latest)
- [ ] Firefox (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS 15+)
- [ ] Mobile Chrome (Android 11+)

---

## Accessibility

- [ ] **A.1** Keyboard navigation works throughout
- [ ] **A.2** Focus indicators visible
- [ ] **A.3** Screen reader friendly labels
- [ ] **A.4** Color contrast meets WCAG AA
- [ ] **A.5** Images have alt text

---

## Known Issues to Watch For

1. **Firestore Permission Error**: If you see "Missing or insufficient permissions", update security rules
2. **Image 404s**: Verify S3 bucket is public and CORS enabled
3. **localStorage Full**: Old browsers may have quota limits
4. **URL too long**: Not an issue with current param structure
5. **Next.js Suspense Warning**: Expected with useSearchParams, can be ignored

---

## Post-Deployment Checklist

- [ ] All routes accessible via direct URL
- [ ] Analytics tracking setup (if applicable)
- [ ] Error monitoring enabled (Sentry/LogRocket)
- [ ] User feedback mechanism in place
- [ ] Documentation updated with new URLs

---

**Testing Completed By**: _______________
**Date**: _______________
**Environment**: Production / Staging / Local
**Issues Found**: _______________
