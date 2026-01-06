# ACRB Scripts

Organized collection of scripts for the ACRB (Attribute-Conditioned Refusal Bias) project.

## 📁 Directory Structure

### `cli/` - User CLI Interfaces
High-level commands that users invoke directly.

- `prompt_engine.py` - Prompt generation engine (main)
- `generate_all.py` - Image generation (main)
- `design_prompts.py` - Prompt design
- `validate_prompt_constraints.py` - Prompt validation
- `run_audit.py` - Audit execution
- Model-specific runner scripts

### `utils/` - Internal Utilities
Tools used by other scripts internally.

- `evaluate_all.py` - Evaluation pipeline
- `compute_disparity.py` - Disparity metric calculation
- `compute_results.py` - Result computation
- `plot_results.py` - Result visualization

### `tests/` - Tests and Experiments
Scripts for testing and experimental analysis.

- `test_pipeline.py` - Pipeline testing
- `ablation_study.py` - Ablation studies
- `intersectionality_analysis.py` - Intersectionality analysis

## 🔄 Execution Flow

```
Prompt Generation → Validation → Image Generation → Evaluation → Analysis
      ↓                ↓            ↓              ↓            ↓
prompt_engine      validate     generate      evaluate      analyze
```

## 📋 Key Script Usage

### Prompt Generation
```bash
python scripts/cli/prompt_engine.py --num-base 100 --output data/prompts/final.json
```

### Image Generation
```bash
python scripts/generate_all.py --models flux2 sd35 --prompts data/prompts/final.json --output experiments/images
```

### Evaluation
```bash
python scripts/utils/evaluate_all.py --images experiments/images --output experiments/results
```

## 🏗️ Architecture Principles

1. **Single Responsibility**: Each script has one clear responsibility
2. **Thin Wrapper**: CLI scripts are thin wrappers around `acrb/` package
3. **Modularization**: Logic in `acrb/` package, interfaces in `scripts/`
4. **No Duplication**: Same functionality implemented in only one place

## 🔧 Development Guidelines

- Implement new features in `acrb/` package
- Add CLI interfaces as thin wrappers in `scripts/cli/`
- Put internal utilities in `scripts/utils/`
- Put tests in `scripts/tests/`
