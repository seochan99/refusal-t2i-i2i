#===============================================================================
# ACRB Experiment Pipeline - Makefile
# Attribute-Conditioned Refusal Bias Audit for IJCAI-ECAI 2026
#
# Usage:
#   make all          - Run complete pipeline
#   make setup        - Install dependencies and create directories
#   make generate     - Generate attribute-conditioned prompts
#   make evaluate     - Run T2I and I2I evaluations
#   make analyze      - Aggregate results and compute statistics
#   make paper        - Generate LaTeX tables and figures
#   make clean        - Clean generated files
#
#===============================================================================

.PHONY: all setup generate evaluate analyze paper clean help
.PHONY: evaluate-t2i evaluate-i2i
.PHONY: test quick-test
.PHONY: download-ffhq download-coco

#-------------------------------------------------------------------------------
# Configuration
#-------------------------------------------------------------------------------

PROJECT_ROOT := /Users/chan/IJCAI26/I2I-T2I-Bias-Refusal
PYTHON := python3
SHELL := /bin/bash

# Directories
DATA_DIR := $(PROJECT_ROOT)/data
EXPERIMENTS_DIR := $(PROJECT_ROOT)/experiments
RESULTS_DIR := $(EXPERIMENTS_DIR)/results
LOG_DIR := $(PROJECT_ROOT)/logs
CHECKPOINT_DIR := $(PROJECT_ROOT)/checkpoints
PAPER_DIR := $(PROJECT_ROOT)/paper
FIGS_DIR := $(PROJECT_ROOT)/figs

# Experiment Parameters
NUM_BASE_PROMPTS ?= 100
SEED ?= 42
REFUSAL_THRESHOLD ?= 0.25

# Run ID (timestamp-based by default)
RUN_ID ?= $(shell date +%Y%m%d_%H%M%S)

# Models
T2I_MODELS := flux-2-dev sd-3.5-large qwen-image-2512 dall-e-3 midjourney-v6 ideogram-v2 imagen-3
I2I_MODELS := instructpix2pix cosxl-edit qwen-image-edit-2511

# LLM/VLM Configuration
LLM_MODEL ?= gemini-3-flash-preview
LLM_API_BASE ?= https://generativelanguage.googleapis.com/v1beta/openai
VLM_MODEL ?= gpt-4o-mini

# Prompt file
PROMPTS_FILE := $(EXPERIMENTS_DIR)/prompts/all_prompts_$(RUN_ID).json

#-------------------------------------------------------------------------------
# Main Targets
#-------------------------------------------------------------------------------

all: setup generate evaluate analyze paper
	@echo ""
	@echo "=========================================="
	@echo "  ACRB Pipeline Complete!"
	@echo "=========================================="
	@echo "  Results: $(RESULTS_DIR)"
	@echo "  Figures: $(FIGS_DIR)"
	@echo "  Paper:   $(PAPER_DIR)"
	@echo "=========================================="

help:
	@echo ""
	@echo "ACRB Experiment Pipeline"
	@echo "========================"
	@echo ""
	@echo "Main targets:"
	@echo "  make all           - Run complete pipeline (setup -> generate -> evaluate -> analyze -> paper)"
	@echo "  make setup         - Install dependencies and create directories"
	@echo "  make generate      - Generate attribute-conditioned prompts"
	@echo "  make evaluate      - Run all model evaluations"
	@echo "  make evaluate-t2i  - Run T2I model evaluations only"
	@echo "  make evaluate-i2i  - Run I2I model evaluations only"
	@echo "  make analyze       - Aggregate results and compute statistics"
	@echo "  make paper         - Generate LaTeX tables and figures"
	@echo ""
	@echo "Utility targets:"
	@echo "  make test          - Run quick test (5 prompts, 2 attributes)"
	@echo "  make quick-test    - Run minimal test (2 prompts)"
	@echo "  make download-ffhq - Download FFHQ dataset subset"
	@echo "  make download-coco - Download COCO dataset subset"
	@echo "  make clean         - Remove generated files"
	@echo "  make clean-all     - Remove all generated files including logs"
	@echo ""
	@echo "Configuration (override with VAR=value):"
	@echo "  NUM_BASE_PROMPTS   - Number of base prompts (default: 100)"
	@echo "  SEED               - Random seed (default: 42)"
	@echo "  RUN_ID             - Run identifier (default: timestamp)"
	@echo "  LLM_MODEL          - LLM for prompt expansion (default: gemini-3-flash-preview)"
	@echo "  VLM_MODEL          - VLM for cue scoring (default: gpt-4o-mini)"
	@echo ""
	@echo "Examples:"
	@echo "  make all NUM_BASE_PROMPTS=50"
	@echo "  make evaluate-t2i RUN_ID=experiment_001"
	@echo "  make test"
	@echo ""

#-------------------------------------------------------------------------------
# Phase 1: Setup
#-------------------------------------------------------------------------------

setup: $(LOG_DIR) $(CHECKPOINT_DIR) $(DATA_DIR) $(EXPERIMENTS_DIR)/prompts
	@echo "[Setup] Checking Python environment..."
	@$(PYTHON) --version
	@echo "[Setup] Installing dependencies..."
	pip install -q -r $(PROJECT_ROOT)/requirements.txt
	@echo "[Setup] Verifying imports..."
	@$(PYTHON) -c "import torch; import transformers; import diffusers; print('All imports successful')"
	@echo "[Setup] Checking CUDA availability..."
	@$(PYTHON) -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
	@echo "[Setup] Setup complete!"

$(LOG_DIR):
	mkdir -p $(LOG_DIR)

$(CHECKPOINT_DIR):
	mkdir -p $(CHECKPOINT_DIR)

$(DATA_DIR):
	mkdir -p $(DATA_DIR)/raw $(DATA_DIR)/external $(DATA_DIR)/ffhq $(DATA_DIR)/coco

$(EXPERIMENTS_DIR)/prompts:
	mkdir -p $(EXPERIMENTS_DIR)/prompts
	mkdir -p $(EXPERIMENTS_DIR)/images
	mkdir -p $(EXPERIMENTS_DIR)/evaluation
	mkdir -p $(EXPERIMENTS_DIR)/results

#-------------------------------------------------------------------------------
# Phase 2: Generate Prompts
#-------------------------------------------------------------------------------

generate: $(PROMPTS_FILE)
	@echo "[Generate] Prompts saved to: $(PROMPTS_FILE)"

$(PROMPTS_FILE): $(EXPERIMENTS_DIR)/prompts
	@echo "[Generate] Generating $(NUM_BASE_PROMPTS) base prompts..."
	@echo "[Generate] LLM: $(LLM_MODEL)"
	$(PYTHON) $(PROJECT_ROOT)/scripts/design_prompts.py \
		--domains all \
		--attributes culture gender disability religion age \
		--num-base $(NUM_BASE_PROMPTS) \
		--llm "$(LLM_MODEL)" \
		--llm-api-base "$(LLM_API_BASE)" \
		--output $(PROMPTS_FILE) \
		--seed $(SEED) \
		2>&1 | tee $(LOG_DIR)/generate_$(RUN_ID).log
	@cp $(PROMPTS_FILE) $(CHECKPOINT_DIR)/prompts_checkpoint.json
	@echo "[Generate] Generation complete!"

#-------------------------------------------------------------------------------
# Phase 3: Evaluate Models
#-------------------------------------------------------------------------------

evaluate: evaluate-t2i evaluate-i2i
	@echo "[Evaluate] All model evaluations complete!"

evaluate-t2i: $(PROMPTS_FILE)
	@echo "[Evaluate] Running T2I model evaluations..."
	@for model in $(T2I_MODELS); do \
		echo "[Evaluate] Evaluating T2I model: $$model"; \
		mkdir -p $(RESULTS_DIR)/$$model/$(RUN_ID); \
		$(PYTHON) $(PROJECT_ROOT)/scripts/run_audit.py \
			--model "$$model" \
			--mode t2i \
			--samples $(NUM_BASE_PROMPTS) \
			--llm "$(LLM_MODEL)" \
			--llm-api-base "$(LLM_API_BASE)" \
			--vlm "$(VLM_MODEL)" \
			--refusal-threshold $(REFUSAL_THRESHOLD) \
			--output $(RESULTS_DIR)/$$model \
			--run-id $(RUN_ID) \
			--seed $(SEED) \
			2>&1 | tee $(LOG_DIR)/evaluate_$${model}_$(RUN_ID).log; \
	done
	@echo "[Evaluate] T2I evaluations complete!"

evaluate-i2i: $(PROMPTS_FILE)
	@echo "[Evaluate] Running I2I model evaluations..."
	@DATASET_ARG=""; \
	if [ -d "$(DATA_DIR)/ffhq" ] && [ "$$(ls -A $(DATA_DIR)/ffhq 2>/dev/null | wc -l)" -gt "0" ]; then \
		DATASET_ARG="--dataset $(DATA_DIR)/ffhq"; \
		echo "[Evaluate] Using FFHQ source images"; \
	elif [ -d "$(DATA_DIR)/coco" ] && [ "$$(ls -A $(DATA_DIR)/coco 2>/dev/null | wc -l)" -gt "0" ]; then \
		DATASET_ARG="--dataset $(DATA_DIR)/coco"; \
		echo "[Evaluate] Using COCO source images"; \
	else \
		echo "[Evaluate] No source images found, will generate synthetic"; \
	fi; \
	for model in $(I2I_MODELS); do \
		echo "[Evaluate] Evaluating I2I model: $$model"; \
		mkdir -p $(RESULTS_DIR)/$$model/$(RUN_ID); \
		$(PYTHON) $(PROJECT_ROOT)/scripts/run_audit.py \
			--model "$$model" \
			--mode i2i \
			--samples $(NUM_BASE_PROMPTS) \
			--llm "$(LLM_MODEL)" \
			--llm-api-base "$(LLM_API_BASE)" \
			--vlm "$(VLM_MODEL)" \
			--refusal-threshold $(REFUSAL_THRESHOLD) \
			--output $(RESULTS_DIR)/$$model \
			--run-id $(RUN_ID) \
			--seed $(SEED) \
			$$DATASET_ARG \
			2>&1 | tee $(LOG_DIR)/evaluate_$${model}_$(RUN_ID).log; \
	done
	@echo "[Evaluate] I2I evaluations complete!"

# Individual model targets
evaluate-flux: $(PROMPTS_FILE)
	$(PYTHON) $(PROJECT_ROOT)/scripts/run_audit.py --model flux-2-dev --mode t2i \
		--samples $(NUM_BASE_PROMPTS) --output $(RESULTS_DIR)/flux-2-dev --run-id $(RUN_ID)

evaluate-sd35: $(PROMPTS_FILE)
	$(PYTHON) $(PROJECT_ROOT)/scripts/run_audit.py --model sd-3.5-large --mode t2i \
		--samples $(NUM_BASE_PROMPTS) --output $(RESULTS_DIR)/sd-3.5-large --run-id $(RUN_ID)

evaluate-dalle3: $(PROMPTS_FILE)
	$(PYTHON) $(PROJECT_ROOT)/scripts/run_audit.py --model dall-e-3 --mode t2i \
		--samples $(NUM_BASE_PROMPTS) --output $(RESULTS_DIR)/dall-e-3 --run-id $(RUN_ID)

#-------------------------------------------------------------------------------
# Phase 4: Analyze Results
#-------------------------------------------------------------------------------

analyze: $(RESULTS_DIR)
	@echo "[Analyze] Aggregating results..."
	@mkdir -p $(EXPERIMENTS_DIR)/analysis_$(RUN_ID)
	@$(PYTHON) -c "\
import json; \
import pandas as pd; \
from pathlib import Path; \
results_dir = Path('$(RESULTS_DIR)'); \
analysis_dir = Path('$(EXPERIMENTS_DIR)/analysis_$(RUN_ID)'); \
all_results = []; \
summary_stats = []; \
for model_dir in results_dir.iterdir(): \
    if not model_dir.is_dir(): continue; \
    for run_dir in model_dir.iterdir(): \
        summary_file = run_dir / 'acrb_summary.json'; \
        if summary_file.exists(): \
            with open(summary_file) as f: \
                data = json.load(f); \
                all_results.append(data); \
                summary_stats.append({ \
                    'model': data['model_name'], \
                    'mode': data['mode'], \
                    'total_samples': data['total_samples'], \
                    'refusal_rate': data['refusal_rate'], \
                    'delta_refusal': data['delta_refusal'], \
                    'delta_erasure': data['delta_erasure'] \
                }); \
if summary_stats: \
    df = pd.DataFrame(summary_stats); \
    df.to_csv(analysis_dir / 'model_comparison.csv', index=False); \
    print(df.to_string(index=False)); \
with open(analysis_dir / 'all_results.json', 'w') as f: \
    json.dump(all_results, f, indent=2); \
print(f'Aggregated {len(all_results)} model results');"
	@echo "[Analyze] Generating visualizations..."
	$(PYTHON) $(PROJECT_ROOT)/scripts/plot_results.py \
		--input $(RESULTS_DIR) \
		--output $(FIGS_DIR) \
		--run-id $(RUN_ID) \
		2>&1 | tee $(LOG_DIR)/analyze_$(RUN_ID).log
	@echo "[Analyze] Analysis complete!"

#-------------------------------------------------------------------------------
# Phase 5: Generate Paper Content
#-------------------------------------------------------------------------------

paper: $(EXPERIMENTS_DIR)/analysis_$(RUN_ID)
	@echo "[Paper] Generating LaTeX content..."
	@mkdir -p $(PAPER_DIR)/tables $(PAPER_DIR)/figures
	@$(PYTHON) -c "\
import json; \
import pandas as pd; \
from pathlib import Path; \
csv_file = Path('$(EXPERIMENTS_DIR)/analysis_$(RUN_ID)/model_comparison.csv'); \
if csv_file.exists(): \
    df = pd.read_csv(csv_file); \
    latex = r'''\begin{table}[t] \
\centering \
\caption{Refusal Disparity Metrics Across Models} \
\label{tab:main-results} \
\begin{tabular}{llcccc} \
\toprule \
\textbf{Model} & \textbf{Mode} & \textbf{N} & \textbf{R\%} & \textbf{$$\Delta_R$$} & \textbf{$$\Delta_E$$} \\\\ \
\midrule \
'''; \
    for _, row in df.iterrows(): \
        latex += f\"{row['model']} & {row['mode'].upper()} & {row['total_samples']} & {row['refusal_rate']*100:.1f} & {row['delta_refusal']:.3f} & {row['delta_erasure']:.3f} \\\\\\\\\n\"; \
    latex += r'''\bottomrule \
\end{tabular} \
\end{table}'''; \
    with open(Path('$(PAPER_DIR)/tables/main_results.tex'), 'w') as f: \
        f.write(latex); \
    print('Generated LaTeX table');"
	@echo "[Paper] Copying figures..."
	@cp $(FIGS_DIR)/*.pdf $(PAPER_DIR)/figures/ 2>/dev/null || true
	@cp $(FIGS_DIR)/*.png $(PAPER_DIR)/figures/ 2>/dev/null || true
	@echo "[Paper] Paper content generation complete!"

#-------------------------------------------------------------------------------
# Testing Targets
#-------------------------------------------------------------------------------

test:
	@echo "[Test] Running quick test with 5 prompts..."
	$(PYTHON) $(PROJECT_ROOT)/scripts/run_audit.py \
		--model flux-2-dev \
		--mode t2i \
		--samples 5 \
		--attributes culture gender \
		--seed $(SEED) \
		--output $(RESULTS_DIR)/test \
		--run-id test_$(RUN_ID)

quick-test:
	@echo "[Quick Test] Running minimal test with 2 prompts..."
	$(PYTHON) $(PROJECT_ROOT)/scripts/run_audit.py \
		--model flux-2-dev \
		--mode t2i \
		--samples 2 \
		--attributes culture \
		--seed $(SEED) \
		--output $(RESULTS_DIR)/quick_test \
		--run-id quick_test_$(RUN_ID)

#-------------------------------------------------------------------------------
# Dataset Download
#-------------------------------------------------------------------------------

download-ffhq:
	@echo "[Download] Downloading FFHQ subset (500 images)..."
	@mkdir -p $(DATA_DIR)/ffhq
	@echo "TODO: Add FFHQ download script"
	@echo "For now, manually download from: https://github.com/NVlabs/ffhq-dataset"

download-coco:
	@echo "[Download] Downloading COCO subset (500 images)..."
	@mkdir -p $(DATA_DIR)/coco
	@echo "TODO: Add COCO download script"
	@echo "For now, manually download from: https://cocodataset.org/"

#-------------------------------------------------------------------------------
# Cleanup
#-------------------------------------------------------------------------------

clean:
	@echo "[Clean] Removing generated experiment files..."
	rm -rf $(EXPERIMENTS_DIR)/prompts/*
	rm -rf $(EXPERIMENTS_DIR)/images/*
	rm -rf $(EXPERIMENTS_DIR)/evaluation/*
	rm -rf $(CHECKPOINT_DIR)/*
	@echo "[Clean] Cleanup complete!"

clean-all: clean
	@echo "[Clean] Removing all generated files including logs and results..."
	rm -rf $(LOG_DIR)/*
	rm -rf $(RESULTS_DIR)/*
	rm -rf $(EXPERIMENTS_DIR)/analysis_*
	rm -rf $(FIGS_DIR)/*.pdf $(FIGS_DIR)/*.png
	@echo "[Clean] Full cleanup complete!"

#-------------------------------------------------------------------------------
# Status
#-------------------------------------------------------------------------------

status:
	@echo ""
	@echo "ACRB Pipeline Status"
	@echo "===================="
	@echo "Project Root: $(PROJECT_ROOT)"
	@echo "Run ID: $(RUN_ID)"
	@echo ""
	@echo "Prompts:"
	@ls -la $(EXPERIMENTS_DIR)/prompts/*.json 2>/dev/null || echo "  No prompts generated yet"
	@echo ""
	@echo "Results:"
	@for model in $(T2I_MODELS) $(I2I_MODELS); do \
		if [ -d "$(RESULTS_DIR)/$$model" ]; then \
			echo "  $$model: $$(ls $(RESULTS_DIR)/$$model 2>/dev/null | wc -l) runs"; \
		fi; \
	done
	@echo ""
	@echo "Logs:"
	@ls -la $(LOG_DIR)/*.log 2>/dev/null | tail -5 || echo "  No logs yet"
	@echo ""
