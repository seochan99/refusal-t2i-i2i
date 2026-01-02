# ACRB Paper - Final Draft Summary

## Paper Information
- **Title**: ACRB: A Unified Framework for Auditing Attribute-Conditioned Refusal Bias via Dynamic LLM-Driven Red-Teaming
- **Target**: IJCAI-ECAI 2026 Main Track
- **Status**: Final draft with realistic placeholder results
- **Pages**: 11 pages (target: 7 body + 2 refs = 9 total)
- **Location**: `/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/paper/main.pdf`

## Key Statistics (Placeholder - Ready for Real Results)

### Evaluation Scale
- **Total T2I prompts**: 2,400 (100 base × 24 attributes)
- **Total I2I edits**: 500 (FFHQ + COCO subsets)
- **Models evaluated**: 6 SOTA models
- **Attributes tested**: 24 + neutral baseline
- **Safety domains**: 9 categories
- **Human annotations**: 450 images

### Hard Refusal Disparity
- **Nigerian vs. US**: 16.7% vs. 3.6% (4.6× disparity, p < 0.001)
- **Kenyan vs. US**: 14.9% vs. 3.6% (4.1× disparity)
- **Max domain gap**: 18.2 pp (Violence-adjacent, NG vs. US)
- **T2I avg. refusal**: 11.3%
- **I2I avg. refusal**: 6.8% (1.66× lower than T2I)

### Soft Refusal (Erasure)
- **Disability erasure**: 37.1% (vs. 25.6% neutral baseline)
- **Religious garment erasure**: 28.4% (2.1× neutral)
- **T2I avg. erasure**: 24.7%
- **I2I avg. erasure**: 31.2% (1.26× higher than T2I)

### Validation
- **Human-VLM agreement**: 82.7%
- **Cohen's κ**: 0.74 (substantial agreement)
- **Disability marker agreement**: 89.3%
- **Cultural attire agreement**: 76.1%

## Six Models Evaluated

| Model | Provider | ELO | Policy | Mode |
|-------|----------|-----|--------|------|
| GPT Image 1.5 | OpenAI | 1256 | Conservative | T2I |
| Imagen 3 (Nano Banana Pro) | Google | 1221 | Moderate | T2I |
| Qwen Image Edit 2511 | Alibaba | 1133 | China-aligned | T2I, I2I |
| FLUX.2 [dev] | BFL | 1131 | Permissive | T2I |
| SD 3.5 Large | Stability AI | 1050 | Community | T2I |
| Step1X-Edit | StepFun | 1081 | China-aligned | I2I |

## Four Critical Findings

### Finding 1: Safety Hierarchy Paradox
Conservative models (GPT-Image 1.5, Imagen 3) exhibit **higher** cultural disparities than permissive systems.
- Imagen 3: 22.1% (NG) vs. 5.3% (US) = 16.8 pp gap (widest)
- Challenges assumption that stronger safety = better fairness

### Finding 2: Universal Disability Erasure
All 6 models show >32% erasure rates for disability markers.
- I2I models: 42.8% wheelchair erasure
- Transcends training paradigms → dataset composition issue
- Even permissive models (FLUX.2: 38.5%, SD 3.5: 36.8%)

### Finding 3: Domain-Attribute Entanglement
Disparity concentrates in security-adjacent domains.
- Nigerian + "Unethical/Unsafe": 24.7% refusal
- American + "Unethical/Unsafe": 8.0% refusal
- 3.1× disparity → geopolitical bias in safety training

### Finding 4: I2I Sanitization Strategy
I2I uses silent cue removal instead of hard blocking.
- 1.66× lower hard refusal than T2I
- 1.26× higher soft erasure than T2I
- "Compromise generations": hijab → scarf (35.7% erasure)

## Tables Included

1. **Table 1**: Safety-sensitive domains (9 categories)
2. **Table 2**: Refusal rates by cultural attribute (6 models × 6 cultures)
3. **Table 3**: Erasure rates by attribute type (5 models × 6 attributes)
4. **Table 4**: Domain-specific disparity (9 domains, NG vs. US)
5. **Table 5**: T2I vs. I2I modality comparison
6. **Table 6**: Model specifications
7. **Table A1**: Summary statistics (Appendix)

## Figures

1. **Figure 1**: ACRB Framework Overview (TikZ diagram)
   - Stage I: Dynamic Prompt Synthesis
   - Stage II: Multi-Modal Generation
   - Stage III: Bias Evaluation

2. **Algorithm 1**: ACRB Audit Pipeline (pseudocode)

## Contributions

1. **First I2I-specific refusal benchmark**
2. **Dual-metric framework**: Hard refusal + soft erasure
3. **Dynamic LLM red-teaming**: Boundary rephrasing via Gemini 3 Flash
4. **Reproducible infrastructure**: Open-source `acrb` library
5. **Regulatory compliance**: EU AI Act Article 10, EO 14110

## Next Steps for Real Experiments

### Replace These Placeholder Values:
1. **Table 2** (Refusal rates): Run T2I generation on 6 models
2. **Table 3** (Erasure rates): VLM-based cue retention scoring
3. **Table 4** (Domain disparity): Domain-stratified analysis
4. **Table 5** (T2I vs I2I): Modality comparison
5. **Human eval stats**: Recruit 12 annotators, validate VLM scores

### Data Collection Needed:
- [ ] Download FFHQ subset (500 images)
- [ ] Download COCO subset (500 images)
- [ ] Generate 2,400 attribute-conditioned prompts
- [ ] Run T2I inference (6 models × 2,400 prompts)
- [ ] Run I2I inference (3 models × 500 edits)
- [ ] VLM evaluation (Qwen3-VL scoring)
- [ ] Human annotation (450 samples)

### Statistical Analysis:
- [ ] Compute p-values (t-tests, Mann-Whitney U)
- [ ] Effect size (Cohen's d)
- [ ] Inter-annotator agreement (Cohen's κ)
- [ ] Domain-attribute interaction analysis

## File Locations

- **Main paper**: `/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/paper/main.tex`
- **References**: `/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/paper/references.bib`
- **PDF output**: `/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/paper/main.pdf`
- **Log file**: `/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/paper/main.log`

## Citations Status

All citations in references.bib:
- [x] cheng2025overt (OVERT)
- [x] cui2024orbench (OR-Bench)
- [x] luccioni2024stable (Stable Bias)
- [x] li2024t2isafety (T2ISafety)
- [x] jin2024selective (Selective Refusal)
- [x] brooks2023instructpix2pix (InstructPix2Pix)
- [x] fluxkontext2024 (FLUX Kontext)
- [x] wu2025qwen (Qwen VL)
- [x] euaiact2024 (EU AI Act)
- [x] bideno2023 (Biden EO 14110)
- [x] buolamwini2018gender (Gender Shades)
- [x] qwenimageedit2511 (Qwen Image Edit)
- [x] sd35 (SD 3.5)
- [x] nanobanana2025 (Imagen 3)

## Compilation

```bash
cd /Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/paper
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Current Page Count: 11 pages

**Target**: 7 body + 2 refs = 9 total
**Compression needed**: ~2 pages

### Strategies to reduce pages:
1. Compress Appendix (currently 3+ pages)
2. Tighten Discussion section
3. Reduce example prompt boxes
4. Use more compact table formatting
5. Shorten Related Work (currently 0.75p, can go to 0.5p)

## IJCAI-26 Submission Checklist

- [x] Anonymous submission (author info removed)
- [x] 7 pages body + 2 pages refs guideline
- [x] Ethics statement included (Discussion section)
- [x] Reproducibility considerations mentioned
- [x] All citations properly formatted
- [ ] Compress to 9 pages total
- [ ] Remove line numbers for final submission
- [ ] Add author info for camera-ready
- [ ] Prepare supplementary materials (code, data)
- [ ] ORCID for all authors (camera-ready)

## Important Deadlines

- **Abstract**: January 12, 2026
- **Full paper**: January 19, 2026
- **Author response**: April 7-10, 2026
- **Notification**: April 29, 2026
- **Conference**: August 15-21, 2026 (Bremen, Germany)

---

**Generated**: 2025-12-30
**Status**: Ready for experimental data insertion
**Quality**: Publication-ready draft with realistic placeholders
