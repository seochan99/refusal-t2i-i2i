# Survey UI/UX Improvements - Monotone Professional Design

## Overview
Redesigned the survey web app with a professional, monotone aesthetic focused on neutral grays, blacks, and whites. The design is clean, modern, and research-focused without looking AI-generated.

## Files Modified

### 1. `/survey/src/app/globals.css`
**Complete redesign of the color system and component styles**

#### Color Palette (CSS Variables)
```css
--bg-primary: #0f0f0f      /* Deep black background */
--bg-secondary: #1a1a1a    /* Card backgrounds */
--bg-tertiary: #242424     /* Subtle elevation */
--bg-elevated: #2a2a2a     /* Highest elevation */

--text-primary: #ffffff     /* Primary text */
--text-secondary: #a3a3a3   /* Secondary text */
--text-muted: #737373       /* Muted text */
--text-disabled: #525252    /* Disabled state */

--border-subtle: #262626    /* Subtle borders */
--border-default: #404040   /* Default borders */
--border-strong: #525252    /* Emphasized borders */

--accent-primary: #ffffff   /* Selection/active state */
--accent-secondary: #d4d4d4 /* Hover state */
--accent-muted: #737373     /* Muted accents */
```

#### Key Features Added
- **Professional Typography**: Inter/SF Pro font stack with refined letter spacing
- **Custom Scrollbar**: Styled webkit scrollbar matching the monotone theme
- **Reusable Button Classes**: `.btn-primary`, `.btn-secondary`, `.btn-ghost` with consistent hover states
- **Panel/Card System**: `.panel` and `.panel-elevated` for consistent elevation
- **Badge Components**: `.badge-default` and `.badge-strong` for labels
- **Progress Bar**: Grayscale gradient with smooth transitions
- **Keyboard Hints**: Professional monospace styling for keyboard shortcuts
- **Focus States**: Accessible focus rings using accent colors

### 2. `/survey/src/app/layout.tsx`
- Removed hardcoded Tailwind classes from body
- Styling now handled entirely by global CSS variables

### 3. `/survey/src/app/page.tsx`
**Comprehensive UI improvements across all components**

#### IRB Consent Form
- Larger, more spacious layout (`max-w-3xl`, `p-10`)
- Professional card elevation with subtle shadows
- Clean checkbox styling with inline CSS variables
- Primary button using `.btn-primary` class
- Better typography hierarchy

#### Experiment Selector
- Card-based layout with hover effects (`.hover-lift`)
- Cleaner spacing and typography
- Monotone badges for user info
- Arrow icons with muted color

#### Login Screen
- Centered card with professional spacing
- Monotone Google icon (single color)
- Clear hierarchy with size/weight variations
- Disabled text color for fine print

#### Model Selection Screen
- Selection cards with white borders when selected
- Inverted colors on selection (white bg, black text)
- Progress display with large numbers and muted labels
- Improved keyboard shortcuts grid
- Professional back button styling

#### Experiment 1 (VLM Scoring)
**Top Bar**:
- Reduced top bar prominence
- Monotone badges for experiment type
- Smaller, cleaner user avatar

**Progress Bar**:
- Minimal 1.5px height
- Grayscale gradient fill
- Smooth transitions

**Image Display**:
- Cleaner labels with letter-spacing
- Badge-based metadata display
- Subtle image containers with refined borders

**Question Panels**:
- Numbered question indicators with circular badges
- Selection state shows white background with black text
- Disabled states use 40% opacity instead of colorful styling
- All buttons use consistent panel class
- Active question has subtle ring instead of bright colors
- Saving indicator uses muted gray instead of green

**Bottom Navigation**:
- Ghost button for "Next Incomplete"
- Secondary buttons for Prev/Next
- Keyboard hints using `.keyboard-hint` class

#### Experiment 3 (WinoBias)
- Consistent styling with Experiment 1
- Binary choice buttons with same selection pattern
- Monotone throughout (no orange/red gradients)

#### Completion Screen
- Clean centered card
- Large heading with proper hierarchy
- Professional button sizing

## Design Principles Applied

1. **Monotone First**: All colors derive from grayscale palette
2. **Hierarchy Through Size & Weight**: Not color
3. **Subtle Elevation**: Using shadows and borders, not bright colors
4. **Consistent Spacing**: 4/8/12/16px increments
5. **Professional Typography**: Negative letter-spacing for headings, normal for body
6. **Selection Indication**: White/black inversion instead of bright colors
7. **State Communication**: Opacity, borders, and subtle rings
8. **Accessibility**: Maintained focus states and sufficient contrast
9. **No Emojis**: Professional text only
10. **Clean Transitions**: Subtle 150-300ms animations

## Visual Comparison

### Before
- Bright blues, greens, purples, oranges
- Gradient backgrounds (green-to-blue, orange-to-red)
- Colorful ring states (blue-400, green-400, etc.)
- Multiple color accents per screen
- Rounded corners everywhere (rounded-2xl, rounded-xl)

### After
- Pure grayscale palette
- White selection state on dark background
- Subtle gray borders and shadows
- Single accent color (white) for active states
- Minimal border radius (4-6px)
- Professional, research-tool aesthetic
- Clean, not "AI-generated" looking

## Browser Compatibility
- CSS variables supported in all modern browsers
- Webkit scrollbar styling (Chrome, Safari, Edge)
- Standard focus-visible for accessibility
- Fallback font stack for cross-platform consistency

## Accessibility Maintained
- Sufficient contrast ratios (white on black, light gray on dark)
- Focus indicators with outline
- Disabled states clearly indicated
- Keyboard shortcuts prominently displayed
- Semantic HTML structure unchanged

## Performance
- No external fonts added
- CSS-only styling (no JS changes)
- Minimal animation usage
- Reusable class system reduces bloat

---

**Result**: A professional, monotone survey tool that looks like a serious research instrument, not a colorful consumer app.
