# IJCAI26 Progress Meeting
Date: 2026-01-17 (D-3)
Deadline: 2026-01-19

---

## 1. Paper Status

| Item | Status | Next Step |
|------|--------|-----------|
| Research Proposal | ✅ Done | - |
| Experiment Design | ✅ Done | - |
| Paper Draft | 🔄 In Progress | Finalize docs → Move to Overleaf |

---

## 2. Experiments Overview

### Exp1: Identity Drift Analysis
- Goal: Do I2I models behave differently based on source image race?
- Metrics: Race Drift, Gender Drift, Age Drift, Skin Tone Change
- Scale: 7 races × 2 genders × 6 ages × 20 prompts × 3 models = 5,040 images

### Exp2: Identity Preservation Test
- Goal: Can identity preservation prompts mitigate drift observed in Exp1?
- Method: Re-run severe drift cases with "preserve identity" prompt
- Design: Same source images + identity preservation instruction

### Exp3: Stereotype Analysis (WinoBias)
- Goal: Do I2I models reinforce gender-occupation stereotypes?
- Method: Apply WinoBias prompts to test stereotype congruence
- Scale: 50 WinoBias prompts × 2 models (FLUX, Qwen)

---

## 3. VLM Evaluation Results

### Exp1 Results (N=5,030, 3 models)

| Metric | Disparity | Key Finding |
|--------|-----------|-------------|
| Skin Lightening | ~32pp | Black/Indian 72-80% vs White 40-47% |
| Race Drift | 12-16pp | White 1-2% vs Non-White 13-17% |
| Gender Drift | +0.14~0.40 | Female drifts more than Male |
| Age Drift | 0.10-0.20 | Minimal racial disparity |

Cross-Model Consistency: FLUX, Qwen, Step1X all show the same pattern

### Exp2 Results (Preliminary)
- Identity preservation prompt significantly improves race/gender/person preservation
- Visible improvement even in visual inspection

### Exp3 Results (N=100)
- 80%+ of generated images follow stereotype-congruent patterns
- All models reinforce gender-occupation stereotypes

---

## 4. Human Evaluation Plan

### Open Questions

1. Sampling Strategy
   - How many images from 5,000+ total?
   - Stratified sampling: Race × Gender × Model?
   - Extreme cases vs Random sampling?

2. Evaluation Metrics
   - Same as VLM? (Race Drift 1-5 scale)
   - Simplified binary? (Identity preserved: Yes/No)
   - Pairwise preference? (A vs B comparison)

3. Platform & Resources
   - AMT? Prolific?
   - Estimated cost and time?

---

## 5. Research Questions & Claims

### Proposed RQs

| RQ | Question | Supporting Evidence |
|----|----------|---------------------|
| RQ1 | Do I2I models behave differently based on race? | Exp1: 32pp skin gap, 16pp race drift |
| RQ2 | Can identity prompts mitigate this bias? | Exp2: Significant preservation improvement |
| RQ3 | Do models reinforce stereotypes? | Exp3: 80%+ follow stereotypes |

### Paper Storyline

> "I2I editing models (1) disproportionately alter non-White faces (Exp1),
> (2) can be partially mitigated with identity preservation prompts (Exp2),
> (3) but still reinforce gender-occupation stereotypes (Exp3)"

---

## 6. Questions for Advisor

### Key Discussion Points

1. Sufficiency of Results
   - Are current VLM results (32pp skin gap, 80% stereotype) strong enough as main claims?
   - Is there acceptance potential with VLM-only evaluation (before human eval)?

2. Human Evaluation Scope
   - Given timeline (D-3), how extensive should human eval be?
   - VLM validation level? Or full re-evaluation?

3. Contribution Positioning
   - Emphasize "I2I bias audit framework" or "Empirical findings"?
   - How much weight on mitigation results (Exp2)?

4. Writing Priority
   - With 3 days remaining, which sections need most focus?

---

## 7. Timeline (D-3)

| Day | Task |
|-----|------|
| D-3 (Today) | Advisor meeting, Finalize paper structure |
| D-2 | Overleaf writing, Complete figures |
| D-1 | Human eval (minimal), Final revision |
| D-0 | Submit |

---

## Appendix: Generated Figures

### Exp1 Summary
- `paper/figures/exp1_analysis/cross_model_race_comparison.png`
- `paper/figures/exp1_analysis/comprehensive_heatmap_v2.png`

### Per-Model Analysis
- `paper/figures/exp1_analysis/flux_2_dev_race_analysis.png`
- `paper/figures/exp1_analysis/qwen_edit_race_analysis.png`
- `paper/figures/exp1_analysis/step1x_edit_race_analysis.png`

### Gender & Age Analysis
- `paper/figures/exp1_analysis/gender_drift_analysis.png`
- `paper/figures/exp1_analysis/age_drift_by_race.png`
