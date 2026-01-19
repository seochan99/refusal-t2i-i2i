# Survey App Test Scenarios

## Critical Path Testing

### Scenario 1: AMT Worker - Full Flow
**Steps:**
1. Navigate to app (logged out)
2. Click "Sign in with Google"
3. Accept IRB consent
4. Enter AMT Worker ID: `A1B2C3D4E5F6G7`
5. Click "Continue"
6. Select Exp1 → flux model
7. Complete 5 evaluations
8. Check completion code

**Expected:**
- ✅ AMT ID visible in Select page header
- ✅ AMT ID is clickable
- ✅ All evaluations save to Firebase
- ✅ Completion code generated

---

### Scenario 2: Skip AMT, Add Later
**Steps:**
1. Sign in
2. Accept consent
3. Click "Skip" on AMT page
4. See "+ Add AMT ID" in Select page
5. Click "+ Add AMT ID"
6. Enter Worker ID
7. Return to Select page

**Expected:**
- ✅ Not forced to enter AMT ID
- ✅ Can access evaluation without AMT ID
- ✅ AMT ID shows after adding
- ✅ No redirect loop

---

### Scenario 3: Edit Existing AMT Info
**Steps:**
1. Sign in (user with existing AMT ID)
2. Click on Worker ID in Select page
3. See pre-filled AMT information
4. Update Worker ID
5. Click "Continue"
6. Verify updated ID shows in Select page

**Expected:**
- ✅ Existing data pre-filled
- ✅ Can update fields
- ✅ Changes persist
- ✅ No data loss

---

### Scenario 4: Exp1 - 5 Question Flow
**Steps:**
1. Select Exp1 → any model
2. Use keyboard: Press `1` for Q1
3. Verify Q2 becomes active
4. Answer all 5 questions with keys 1-5
5. Check auto-advance to next item
6. Press `←` to go back
7. Verify previous answers loaded

**Expected:**
- ✅ Active question highlighted
- ✅ Keyboard shortcuts work (1-5)
- ✅ Auto-advance after 5th answer
- ✅ Previous answers restored
- ✅ "SAVED" badge shows

---

### Scenario 5: Exp2 - Image Loading & Error
**Steps:**
1. Select Exp2 → any model
2. Wait for images to load
3. See loading indicators
4. If image fails, see error message
5. Click "Retry" button
6. Make selection (A/B/Tie)
7. Use keyboard shortcuts

**Expected:**
- ✅ "Loading..." shown while loading
- ✅ Smooth fade-in when loaded
- ✅ Error message if load fails
- ✅ Retry button works
- ✅ Keyboard A/B/T works
- ✅ Position randomization (leftIsPreserved)

---

### Scenario 6: Exp3 - Stereotype Detection
**Steps:**
1. Select Exp3 → qwen model
2. Check input images displayed
3. Check output image loads
4. Read prompt and stereotype info
5. Press `1` for "Yes, stereotype"
6. Check auto-save and advance
7. Navigate back
8. Verify answer restored

**Expected:**
- ✅ 2 input images shown
- ✅ Output image loads
- ✅ Image error handling works
- ✅ Keyboard 1/2 works
- ✅ Auto-saves on answer
- ✅ Previous answer restored

---

### Scenario 7: Completion Flow
**Steps:**
1. Complete all items in an experiment
2. Automatically redirect to /complete
3. See completion code
4. Click "Copy Code"
5. See "Copied!" feedback
6. Click "Evaluate Another Model"
7. Return to Select page

**Expected:**
- ✅ Auto-redirect when done
- ✅ Unique completion code shown
- ✅ Copy button works
- ✅ Code saved to Firebase
- ✅ Can start new evaluation

---

### Scenario 8: Error Recovery
**Steps:**
1. **Simulate Firebase error** (disconnect internet)
2. Try to save evaluation
3. See error message
4. Reconnect internet
5. Try again

**Expected:**
- ✅ User-friendly error message
- ✅ App doesn't crash
- ✅ Can retry after reconnecting
- ✅ Console shows error details

---

### Scenario 9: Progress Tracking
**Steps:**
1. Complete 10 items
2. Sign out
3. Sign back in
4. Check progress bar
5. Start evaluation
6. Verify continues from item 10

**Expected:**
- ✅ Progress bar shows 10 items
- ✅ Auto-jumps to item 11
- ✅ "Next Incomplete (N)" works
- ✅ Progress persists across sessions

---

### Scenario 10: URL Parameters (MTurk)
**Steps:**
1. Visit with URL params:
   `/?workerId=ABC123&assignmentId=XYZ789&hitId=HIT123`
2. Complete consent
3. Check AMT page

**Expected:**
- ✅ Fields auto-filled from URL
- ✅ Worker ID: ABC123
- ✅ Assignment ID: XYZ789
- ✅ HIT ID: HIT123

---

## Edge Cases

### Edge Case 1: Empty Firebase Response
- No previous evaluations
- Fresh user
**Expected:** ✅ Shows 0 progress, starts from item 0

### Edge Case 2: Missing Image URLs
- exp2_items.json has null image URL
**Expected:** ✅ Shows "No image available"

### Edge Case 3: Invalid Model Parameter
- Navigate to `/eval/exp1?model=invalid`
**Expected:** ✅ Shows error, "Back to Selection" button

### Edge Case 4: Rapid Keyboard Input
- Press keys very fast
**Expected:** ✅ Debounced, saves correctly

### Edge Case 5: Browser Back Button
- Complete item, press back
**Expected:** ✅ Previous answers loaded, can edit

---

## Mobile Testing

### Mobile Scenario 1: Touch Navigation
**Steps:**
1. Open on mobile device
2. Tap answer buttons (not keyboard)
3. Swipe between items (if implemented)

**Expected:**
- ✅ Large touch targets
- ✅ Responsive layout
- ✅ No horizontal scroll
- ✅ Images fit screen

### Mobile Scenario 2: Copy Code
**Steps:**
1. Complete evaluation on mobile
2. Long-press completion code
3. Copy to clipboard

**Expected:**
- ✅ Selectable text
- ✅ Copy button works
- ✅ Fallback copy method works

---

## Performance Testing

### Load Time Test
**Metrics:**
- Page load < 2 seconds
- Image load < 5 seconds
- Firebase query < 1 second

### Memory Test
**Metrics:**
- No memory leaks after 100 items
- Cleanup on unmount
- No zombie listeners

---

## Accessibility Testing

### Keyboard Navigation
- ✅ Tab through all buttons
- ✅ Enter to activate
- ✅ Escape to close (if modals)

### Screen Reader
- ✅ Alt text on images
- ✅ ARIA labels on buttons
- ✅ Semantic HTML

### Color Contrast
- ✅ Text readable
- ✅ Meets WCAG AA standards

---

## Security Testing

### Firebase Rules
- ✅ Users can only read/write own data
- ✅ Authentication required
- ✅ No unauthorized access

### Data Validation
- ✅ Response values 1-5 only
- ✅ Timestamps server-side
- ✅ User ID verification

---

## Test Results Template

```
Date: _______________
Tester: _______________
Browser: _______________

Scenario 1: ☐ Pass ☐ Fail - Notes: _______________
Scenario 2: ☐ Pass ☐ Fail - Notes: _______________
...
```

---

Last Updated: January 17, 2026
