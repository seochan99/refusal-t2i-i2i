# ACRB 20-Day Sprint Schedule

**IJCAI-ECAI 2026 Submission Deadline**: January 19, 2026, 23:59 UTC
**Current Date**: December 30, 2025
**Days Remaining**: 20 days

---

## Overview

```
Week 1 (Dec 30 - Jan 5):  [EXPERIMENTATION] ████████████████░░░░░░░░░░░░░░ 35%
Week 2 (Jan 6 - Jan 12):  [ANALYSIS]        ░░░░░░░░░░░░░░░░████████████░░ 30%
Week 3 (Jan 13 - Jan 19): [WRITING]         ░░░░░░░░░░░░░░░░░░░░░░░░████████ 35%
```

---

## Week 1: Experimentation Phase (Dec 30 - Jan 5)

### Day 1: December 30 (Monday)
**Focus**: Prompt Generation & Data Preparation

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| AM | Finalize 100 base prompts across 9 domains | prompt-designer | `data/raw/base_prompts.json` |
| AM | Generate 2,400 attribute-expanded prompts via Gemini 3 Flash | prompt-designer | `data/processed/expanded_prompts.json` |
| PM | Download FFHQ-ACRB subset (500 faces) | ml-experimenter | `data/external/ffhq/` |
| PM | Download COCO-ACRB subset (500 scenes) | ml-experimenter | `data/external/coco/` |
| PM | Validate prompt quality (sample 50, check benign intent) | research-lead | Quality report |

**Checkpoint**: 2,400 prompts ready, datasets downloaded

---

### Day 2: December 31 (Tuesday)
**Focus**: T2I Inference - Closed Source Models

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| AM | GPT Image 1.5 inference (850 prompts) | ml-experimenter | `experiments/gpt-img-1.5/` |
| PM | Nano Banana Pro inference (850 prompts) | ml-experimenter | `experiments/nano-banana/` |
| Evening | Monitor API rate limits, handle retries | ml-experimenter | Completion logs |

**API Cost Estimate**: ~$40-50

---

### Day 3: January 1 (Wednesday)
**Focus**: T2I Inference - Continued

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| AM | FLUX.2 [max] inference (850 prompts) | ml-experimenter | `experiments/flux2-max/` |
| PM | Qwen Image Edit T2I mode (850 prompts) | ml-experimenter | `experiments/qwen-edit-t2i/` |
| Evening | Verify image quality, resample failures | ml-experimenter | Completion report |

**API Cost Estimate**: ~$30-40

---

### Day 4: January 2 (Thursday)
**Focus**: I2I Inference - Phase 1

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| AM | Qwen Image Edit I2I mode (500 source images x 25 attrs) | ml-experimenter | `experiments/qwen-edit-i2i/` |
| PM | FLUX.2 [dev] I2I mode (500 x 25) | ml-experimenter | `experiments/flux2-dev-i2i/` |
| Evening | Quality check: verify attribute edits applied | ml-experimenter | Sample gallery |

**Compute Estimate**: 8 GPU-hours (A100)

---

### Day 5: January 3 (Friday)
**Focus**: I2I Inference - Phase 2

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| AM | Step1X-Edit I2I inference (500 x 25) | ml-experimenter | `experiments/step1x-edit/` |
| PM | Handle edge cases: failed edits, timeout retries | ml-experimenter | Error log |
| Evening | Consolidate all generated images | ml-experimenter | `experiments/all_images/` |

**Compute Estimate**: 6 GPU-hours

---

### Day 6: January 4 (Saturday)
**Focus**: Hard Refusal Detection

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| AM | Run CLIP-based refusal detector on T2I outputs | ml-experimenter | `results/hard_refusal_t2i.csv` |
| PM | Run refusal detector on I2I outputs | ml-experimenter | `results/hard_refusal_i2i.csv` |
| PM | Manual verification: sample 100 detections | research-lead | Accuracy report |
| Evening | Compute per-model refusal rates | ml-experimenter | Refusal summary |

**Output**: Refusal rates for 6 models x 24 attributes

---

### Day 7: January 5 (Sunday)
**Focus**: Soft Refusal (Cue Erasure) Scoring

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| AM | Run Qwen3-VL cue retention scoring on non-refused T2I | ml-experimenter | `results/erasure_t2i.csv` |
| PM | Run cue retention scoring on non-refused I2I | ml-experimenter | `results/erasure_i2i.csv` |
| Evening | Compute erasure rates by attribute | ml-experimenter | Erasure summary |

**Week 1 Deliverable**: Raw metric data for all models/attributes

---

## Week 2: Analysis & Human Evaluation (Jan 6 - Jan 12)

### Day 8: January 6 (Monday)
**Focus**: Disparity Metric Computation

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| AM | Compute Delta_refusal for each attribute axis | ml-experimenter | `results/disparity_refusal.csv` |
| AM | Compute Delta_erasure for each attribute axis | ml-experimenter | `results/disparity_erasure.csv` |
| PM | Domain-specific breakdown (9 safety domains) | ml-experimenter | Domain analysis |
| PM | Statistical significance testing (chi-square, t-tests) | research-lead | `results/significance.txt` |

---

### Day 9: January 7 (Tuesday)
**Focus**: Human Evaluation Setup

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| AM | Finalize annotator recruitment (12 total: 2 per culture) | research-lead | Annotator roster |
| AM | Prepare evaluation interface (survey app) | paper-writer | `scripts/survey_app/` |
| PM | Sample 450 images for human eval (stratified by attribute) | ml-experimenter | Eval sample set |
| PM | Train annotators on rubric (30-min session) | research-lead | Training materials |

**Budget**: ~$75-100 for annotator compensation

---

### Day 10: January 8 (Wednesday)
**Focus**: Human Evaluation - Day 1

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| Full Day | Annotators evaluate 150 samples | annotators | `results/human_eval_batch1.csv` |
| Evening | Quality check: inter-annotator agreement | research-lead | Agreement metrics |

---

### Day 11: January 9 (Thursday)
**Focus**: Human Evaluation - Day 2

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| Full Day | Annotators evaluate 150 samples | annotators | `results/human_eval_batch2.csv` |
| Evening | Resolve disagreements, clarify rubric | research-lead | Updated guidelines |

---

### Day 12: January 10 (Friday)
**Focus**: Human Evaluation - Day 3

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| Full Day | Annotators evaluate final 150 samples | annotators | `results/human_eval_batch3.csv` |
| Evening | Consolidate all human annotations | ml-experimenter | `results/human_eval_final.csv` |

**Checkpoint**: 450 human annotations complete

---

### Day 13: January 11 (Saturday)
**Focus**: Statistical Analysis

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| AM | Compute Human-VLM agreement (Cohen's kappa) | ml-experimenter | Agreement table |
| AM | Finalize disparity metrics with confidence intervals | ml-experimenter | Final metrics |
| PM | Identify top 3 qualitative examples per finding | research-lead | Example gallery |
| PM | Draft key findings summary | research-lead | Findings doc |

---

### Day 14: January 12 (Sunday)
**Focus**: Figure Generation

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| AM | Run `scripts/generate_figures.py` with real data | ml-experimenter | All PDF figures |
| PM | Review figures for clarity, iterate on design | research-lead | Final figures |
| PM | Prepare supplementary materials | paper-writer | Appendix draft |

**Week 2 Deliverable**: Complete analysis, figures, human eval results

---

## Week 3: Writing & Polish (Jan 13 - Jan 19)

### Day 15: January 13 (Monday)
**Focus**: Results Section Update

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| AM | Update Table 2 (refusal rates) with real numbers | paper-writer | Updated table |
| AM | Update Table 3 (erasure rates) with real numbers | paper-writer | Updated table |
| PM | Rewrite RQ1-RQ4 findings with actual statistics | paper-writer | Results section |
| PM | Add qualitative examples and quotes | paper-writer | Example boxes |

---

### Day 16: January 14 (Tuesday)
**Focus**: Discussion & Analysis Refinement

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| AM | Revise Discussion with specific model insights | paper-writer | Discussion section |
| AM | Add domain-specific analysis paragraph | paper-writer | Domain analysis |
| PM | Strengthen limitations section | paper-writer | Limitations |
| PM | Update ethical considerations | research-lead | Ethics section |

---

### Day 17: January 15 (Wednesday)
**Focus**: Internal Review

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| AM | Full paper read-through (all team members) | all | Feedback notes |
| PM | Feedback consolidation meeting | research-lead | Action items |
| PM | Prioritize critical fixes | research-lead | Fix list |

---

### Day 18: January 16 (Thursday)
**Focus**: Address Feedback

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| AM | Implement high-priority feedback | paper-writer | Revised sections |
| PM | Polish introduction and abstract | paper-writer | Final intro |
| PM | Verify all citations are correct | paper-writer | Checked bib |

---

### Day 19: January 17 (Friday)
**Focus**: Final Proofreading

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| AM | Grammar and spell check | paper-writer | Clean text |
| AM | Verify formatting compliance (margins, fonts) | paper-writer | Format check |
| PM | Compile final PDF, check for errors | paper-writer | main.pdf |
| PM | Verify page count (7 pages + refs) | research-lead | Page count OK |

---

### Day 20: January 18 (Saturday)
**Focus**: Buffer Day

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| AM | Address any last-minute issues | all | Fixes |
| PM | Final read of abstract, intro, conclusion | research-lead | Approval |
| Evening | Prepare submission materials | paper-writer | Ready to submit |

---

### Day 21: January 19 (Sunday) - DEADLINE
**Focus**: SUBMISSION

| Time | Task | Owner | Deliverable |
|------|------|-------|-------------|
| Morning | Final compilation and verification | paper-writer | Final PDF |
| Afternoon | Upload to submission system | research-lead | Confirmation |
| 3 hours before | Download and verify uploaded PDF | research-lead | Verified |
| 23:59 UTC | **DEADLINE** | - | SUBMITTED |

---

## Risk Mitigation

### High-Risk Items
1. **API Rate Limits**: Have backup API keys, implement exponential backoff
2. **Human Annotator No-Shows**: Recruit 14 annotators (2 backup)
3. **Compute Failures**: Checkpoint all inference runs every 100 samples
4. **Last-Minute Bugs**: Buffer day on Jan 18

### Contingency Plans
- If T2I inference incomplete by Jan 3: Reduce to 4 models
- If human eval incomplete by Jan 10: Use 300 samples minimum
- If figures need major revision: Prioritize heatmaps and bars only

---

## Daily Standup Format

Each morning, brief check-in (10 min):
1. What did you complete yesterday?
2. What will you work on today?
3. Any blockers?

Use Slack/Discord channel: `#ijcai-acrb-sprint`

---

## Contact & Resources

- **Research Lead**: [Name] - Strategic decisions
- **ML Experimenter**: [Name] - Experiments, metrics
- **Prompt Designer**: [Name] - Prompt generation
- **Paper Writer**: [Name] - LaTeX, writing

---

Last updated: 2025-12-30
