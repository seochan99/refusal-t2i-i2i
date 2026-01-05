# IJCAI-ECAI 2026 Submission Checklist

**Paper Title**: ACRB: A Unified Framework for Auditing Attribute-Conditioned Refusal Bias via Dynamic LLM-Driven Red-Teaming

**Deadline**: January 19, 2026, 23:59 UTC
**Current Date**: December 30, 2025
**Days Remaining**: 20 days

---

## Pre-Submission Technical Checklist

### Paper Content
- [ ] Abstract is within 150 words
- [ ] Paper is within 7 pages (excluding references)
- [ ] All figures are high-resolution (300+ DPI)
- [ ] All tables have captions above
- [ ] All figures have captions below
- [ ] No orphaned references (all cited works appear in bibliography)
- [ ] No undefined references or citations
- [ ] Line numbers enabled for review version (`\linenumbers`)
- [ ] Author information is anonymized

### Required Sections
- [x] Abstract - compelling with key findings (3.2x, 45%)
- [x] Introduction - clear problem statement and contributions
- [x] Related Work - positions against OVERT, Stable Bias, Selective Refusal
- [x] Methodology - Algorithm 1 present
- [x] Experimental Setup - 6 models, RQ1-RQ4 defined
- [x] Results - Tables for refusal/erasure rates
- [x] Discussion - Limitations, ethical considerations
- [x] Conclusion - Summary of contributions

### Tables (paper/tables/)
- [x] table_refusal_rates.tex - Model x Attribute refusal matrix
- [x] table_erasure_rates.tex - Model x Attribute erasure matrix
- [x] table_disparity.tex - Disparity summary
- [x] table_human_agreement.tex - Human-VLM agreement

### Figures (paper/figures/)
- [ ] fig_architecture (already in main.tex as TikZ)
- [ ] fig_heatmap_refusal.pdf
- [ ] fig_heatmap_erasure.pdf
- [ ] fig_disparity_bars.pdf
- [ ] fig_domain_analysis.pdf
- [ ] fig_modality_comparison.pdf

### Bibliography
- [x] references.bib complete with all citations
- [ ] Verify all DOIs/URLs are correct
- [ ] Check for duplicate entries
- [ ] Ensure consistent formatting (author names, venues)

---

## Experiment Completion Checklist

### Data Preparation
- [ ] FFHQ-ACRB subset: 500 faces downloaded and verified
- [ ] COCO-ACRB subset: 500 scenes downloaded and verified
- [ ] Base prompts: 100 prompts across 9 domains
- [ ] Expanded prompts: 2,400 attribute-conditioned prompts

### Model Inference
- [ ] GPT Image 1.5 (OpenAI API) - T2I complete
- [ ] Nano Banana Pro (Google API) - T2I complete
- [ ] FLUX.2 [max] (BFL API) - T2I complete
- [ ] Qwen Image Edit 2511 (local/API) - T2I + I2I complete
- [ ] FLUX.2 [dev] (local) - T2I + I2I complete
- [ ] Step1X-Edit (local) - I2I complete

### Evaluation
- [ ] Hard refusal detection (CLIP-based) complete
- [ ] Soft refusal scoring (Qwen3-VL) complete
- [ ] Human evaluation (450 samples, 12 annotators) complete
- [ ] Statistical significance tests (p < 0.05)

---

## File Checklist

### Required Files
```
paper/
├── main.tex              [x] Primary manuscript
├── ijcai26.sty           [x] IJCAI style file
├── named.bst             [x] Bibliography style
├── references.bib        [x] Bibliography
├── tables/
│   ├── table_refusal_rates.tex    [x]
│   ├── table_erasure_rates.tex    [x]
│   ├── table_disparity.tex        [x]
│   └── table_human_agreement.tex  [x]
└── figures/
    ├── fig_heatmap_refusal.pdf    [ ] Generate with scripts/generate_figures.py
    ├── fig_heatmap_erasure.pdf    [ ]
    ├── fig_disparity_bars.pdf     [ ]
    ├── fig_domain_analysis.pdf    [ ]
    └── fig_modality_comparison.pdf [ ]
```

### Supplementary Materials (Optional)
- [ ] Appendix with full prompt examples
- [ ] Extended results tables
- [ ] Code repository link (anonymous during review)

---

## IJCAI-ECAI 2026 Format Requirements

### Page Limits
- Main paper: **7 pages** (excluding references)
- References: No limit
- Appendix: Allowed but reviewers not required to read

### Formatting
- Paper size: US Letter (8.5 x 11 inches)
- Margins: Handled by ijcai26.sty
- Font: Times Roman, 10pt
- Two-column format
- Line spacing: Single

### Anonymization
- [ ] Remove author names and affiliations
- [ ] Remove acknowledgments section
- [ ] Anonymize self-citations ("In our previous work [X]..." -> "In [X]...")
- [ ] Remove funding information
- [ ] Check figures/code for identifying information

### File Submission
- [ ] Single PDF file
- [ ] Filename: Paper_ID.pdf (assigned after submission)
- [ ] PDF/A compliant (recommended)
- [ ] Embedded fonts

---

## 20-Day Sprint Schedule

### Week 1: Dec 30 - Jan 5 (Experimentation)
| Date | Milestone | Status |
|------|-----------|--------|
| Dec 30 | Generate 2,400 prompts, validate quality | [ ] |
| Dec 31 | T2I inference: GPT-Img, Nano Banana | [ ] |
| Jan 1 | T2I inference: FLUX.2 max, Qwen-Edit T2I | [ ] |
| Jan 2 | I2I inference: Qwen-Edit, FLUX.2 dev | [ ] |
| Jan 3 | I2I inference: Step1X-Edit | [ ] |
| Jan 4 | Hard refusal detection (all models) | [ ] |
| Jan 5 | Soft refusal scoring (VLM evaluation) | [ ] |

### Week 2: Jan 6 - Jan 12 (Analysis & Human Eval)
| Date | Milestone | Status |
|------|-----------|--------|
| Jan 6 | Compute disparity metrics | [ ] |
| Jan 7 | Launch human evaluation (annotator recruitment) | [ ] |
| Jan 8 | Human eval: 150 samples | [ ] |
| Jan 9 | Human eval: 300 samples | [ ] |
| Jan 10 | Human eval complete: 450 samples | [ ] |
| Jan 11 | Statistical analysis, significance tests | [ ] |
| Jan 12 | Generate all figures | [ ] |

### Week 3: Jan 13 - Jan 19 (Writing & Polish)
| Date | Milestone | Status |
|------|-----------|--------|
| Jan 13 | Update Results section with real data | [ ] |
| Jan 14 | Revise Discussion, add specific examples | [ ] |
| Jan 15 | Internal review, co-author feedback | [ ] |
| Jan 16 | Address feedback, polish writing | [ ] |
| Jan 17 | Final proofreading, check formatting | [ ] |
| Jan 18 | Buffer day for unexpected issues | [ ] |
| Jan 19 | **SUBMIT BY 23:59 UTC** | [ ] |

---

## Final Pre-Submission Checks (Jan 19)

### 2 Hours Before Deadline
- [ ] Compile final PDF with no errors
- [ ] Verify page count (7 pages + references)
- [ ] Check all figures render correctly
- [ ] Verify anonymization complete
- [ ] Read abstract and conclusion one last time

### 1 Hour Before Deadline
- [ ] Upload to OpenReview/CMT
- [ ] Verify upload successful
- [ ] Download and check uploaded PDF
- [ ] Record confirmation number

### Post-Submission
- [ ] Save local copy of submitted PDF
- [ ] Note confirmation email/number
- [ ] Celebrate! 

---

## Emergency Contacts

- **Paper Chair**: [Check IJCAI website]
- **Technical Support**: [CMT/OpenReview help]
- **LaTeX Issues**: Overleaf support or local TeX installation

---

## Commands Reference

```bash
# Generate figures
python scripts/generate_figures.py --output paper/figures/ --format pdf

# Compile LaTeX
cd paper && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex

# Check page count
pdfinfo main.pdf | grep Pages

# Verify PDF fonts embedded
pdffonts main.pdf
```

---

Last updated: 2025-12-30
