# ACRB: Attribute-Conditioned Refusal Bias Framework

## Project Overview

**Goal**: IJCAI-ECAI 2026 submission (AI4Good Track)
**Deadline**: January 19, 2026
**Paper Title**: "ACRB: A Unified Framework for Auditing Attribute-Conditioned Refusal Bias via Dynamic LLM-Driven Red-Teaming"

## Research Question

Do T2I/I2I models exhibit differential refusal behavior based on demographic/cultural attributes?

## Key Innovation

1. **First I2I-specific refusal benchmark**
2. **Dual-metric evaluation**: Hard Refusal (explicit blocking) + Soft Refusal (cue erasure)
3. **Dynamic LLM red-teaming**: Boundary rephrasing via LLM instead of static templates

## Available Agents

| Agent | Model | Purpose | Command |
|-------|-------|---------|---------|
| `research-lead` | opus | Strategic planning, paper coordination | `/agent research-lead` |
| `ml-experimenter` | sonnet | Experiment execution, metric computation | `/agent ml-experimenter` |
| `prompt-designer` | sonnet | LLM red-teaming, prompt generation | `/agent prompt-designer` |
| `paper-writer` | sonnet | LaTeX writing, formatting | `/agent paper-writer` |

## Project Structure

```
I2I-T2I-Bias-Refusal/
├── acrb/                    # Core library
│   ├── evaluation/          # Pipeline orchestration
│   ├── metrics/             # Refusal & Erasure scorers
│   ├── models/              # T2I/I2I model wrappers
│   ├── prompt_generation/   # LLM-driven expansion
│   └── vlm/                  # VLM-based evaluation
├── data/
│   ├── raw/                 # Base prompts (OVERT-aligned)
│   └── external/            # FFHQ & COCO hooks
├── experiments/             # Result cache
├── paper/                   # LaTeX source
│   ├── main.tex
│   ├── references.bib
│   └── figures/
├── scripts/
│   ├── run_audit.py        # Main entry point
│   ├── design_prompts.py   # Prompt generation
│   └── survey_app/          # Human evaluation UI
└── OVERT-main/              # Reference benchmark
```

## 3-Week Sprint Plan

### Week 1: Data & Prompts
- [ ] Download FFHQ/COCO subsets (500 each)
- [ ] Generate 2,400 attribute-conditioned prompts
- [ ] Validate prompt quality (benign but triggering)

### Week 2: Experiments
- [ ] Run T2I generation (6 models × 2,500 prompts)
- [ ] Run I2I editing (3 models × 500 source images)
- [ ] Compute refusal rates and cue retention scores
- [ ] VLM-based automated evaluation

### Week 3: Analysis & Writing
- [ ] Statistical analysis of disparity metrics
- [ ] Human evaluation (100-150 samples)
- [ ] Finalize paper (7 pages + refs)
- [ ] Generate publication-ready figures

## Key Metrics

```
Δ_refusal = max_a R(a) - min_a R(a)
Δ_erasure = max_a E(a) - min_a E(a)
```

## Reference Materials

- Research notes: `/Users/chan/IJCAI26/R-bias/i2i-refusal-research.md`
- Resource list: `/Users/chan/IJCAI26/R-bias/reference.txt`
- OVERT benchmark: `/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal/OVERT-main/`

## Commands

```bash
# Run full audit
python scripts/run_audit.py --model flux-2-dev --mode t2i --samples 100

# Generate prompts
python scripts/design_prompts.py --domains all --attributes all

# Plot results
python scripts/plot_results.py --input experiments/ --output figs/
```

## Budget Estimate

- API calls (T2I/I2I): ~$100-150
- Human annotation: ~$75-225
- Total: ~$200-400
