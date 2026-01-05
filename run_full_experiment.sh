#!/bin/bash
#===============================================================================
# ACRB Full Experiment Pipeline
# Attribute-Conditioned Refusal Bias Audit for IJCAI-ECAI 2026
#
# Usage:
#   ./run_full_experiment.sh                    # Run all phases
#   ./run_full_experiment.sh --phase setup      # Run specific phase
#   ./run_full_experiment.sh --dry-run          # Preview commands
#   ./run_full_experiment.sh --resume           # Resume from last checkpoint
#===============================================================================

set -euo pipefail

#-------------------------------------------------------------------------------
# Configuration
#-------------------------------------------------------------------------------
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs"
CHECKPOINT_DIR="${PROJECT_ROOT}/checkpoints"
DATA_DIR="${PROJECT_ROOT}/data"
EXPERIMENTS_DIR="${PROJECT_ROOT}/experiments"
RESULTS_DIR="${EXPERIMENTS_DIR}/results"

# Experiment Parameters
NUM_BASE_PROMPTS=100          # Base prompts (expands to ~2500 with attributes)
SEED=42
REFUSAL_THRESHOLD=0.25

# December 2025 SOTA Models (Local GPU - FREE)
# T2I: FLUX.2, Qwen-Edit, SD3.5 | I2I: Qwen-Edit, CosXL
T2I_MODELS=("flux2" "qwen-edit" "sd35")
I2I_MODELS=("qwen-edit" "cosxl-edit")

# LLM for prompt expansion (use local file by default)
LLM_MODEL=""  # Empty = use template-based expansion (no API cost)
LLM_API_BASE=""

# VLM for cue retention scoring (LOCAL Qwen2.5-VL - FREE)
VLM_MODEL="qwen-vl"  # Use local Qwen2.5-VL-7B (16GB VRAM, free)

# Timestamp for this run
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUN_ID="run_${TIMESTAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

#-------------------------------------------------------------------------------
# Utility Functions
#-------------------------------------------------------------------------------

log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "${LOG_DIR}/${RUN_ID}.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "${LOG_DIR}/${RUN_ID}.log"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
    echo "[WARNING] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "${LOG_DIR}/${RUN_ID}.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "${LOG_DIR}/${RUN_ID}.log"
}

save_checkpoint() {
    local phase=$1
    echo "${phase}" > "${CHECKPOINT_DIR}/last_completed_phase.txt"
    echo "${RUN_ID}" > "${CHECKPOINT_DIR}/current_run_id.txt"
    log_info "Checkpoint saved: ${phase}"
}

load_checkpoint() {
    if [[ -f "${CHECKPOINT_DIR}/last_completed_phase.txt" ]]; then
        cat "${CHECKPOINT_DIR}/last_completed_phase.txt"
    else
        echo "none"
    fi
}

check_dependencies() {
    log_info "Checking dependencies..."

    local missing=()

    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing+=("python3")
    fi

    # Check pip packages
    python3 -c "import torch" 2>/dev/null || missing+=("torch")
    python3 -c "import transformers" 2>/dev/null || missing+=("transformers")
    python3 -c "import diffusers" 2>/dev/null || missing+=("diffusers")
    python3 -c "import openai" 2>/dev/null || missing+=("openai")

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing[*]}"
        log_info "Run: ./setup_server.sh to install dependencies"
        return 1
    fi

    log_success "All dependencies satisfied"
    return 0
}

check_api_keys() {
    log_info "Checking API keys..."

    local missing=()

    [[ -z "${ACRB_LLM_API_KEY:-}" ]] && missing+=("ACRB_LLM_API_KEY")
    [[ -z "${OPENAI_API_KEY:-}" ]] && missing+=("OPENAI_API_KEY")

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_warning "Missing API keys: ${missing[*]}"
        log_info "Set them in .env or export them before running"
    fi
}

print_banner() {
    echo ""
    echo "==============================================================================="
    echo "   ACRB: Attribute-Conditioned Refusal Bias Audit"
    echo "   Full Experiment Pipeline for IJCAI-ECAI 2026"
    echo "==============================================================================="
    echo ""
    echo "   Run ID:        ${RUN_ID}"
    echo "   Project Root:  ${PROJECT_ROOT}"
    echo "   Log File:      ${LOG_DIR}/${RUN_ID}.log"
    echo ""
    echo "   T2I Models:    ${T2I_MODELS[*]}"
    echo "   I2I Models:    ${I2I_MODELS[*]}"
    echo "   Base Prompts:  ${NUM_BASE_PROMPTS}"
    echo ""
    echo "==============================================================================="
    echo ""
}

#-------------------------------------------------------------------------------
# Phase 1: Setup
#-------------------------------------------------------------------------------

phase_setup() {
    log_info "========== PHASE 1: SETUP =========="

    # Create directories
    mkdir -p "${LOG_DIR}" "${CHECKPOINT_DIR}"
    mkdir -p "${DATA_DIR}"/{raw,external,ffhq,coco}
    mkdir -p "${EXPERIMENTS_DIR}"/{prompts,images,evaluation,results}

    for model in "${T2I_MODELS[@]}"; do
        mkdir -p "${EXPERIMENTS_DIR}/images/${model//[^a-zA-Z0-9]/_}"
    done
    for model in "${I2I_MODELS[@]}"; do
        mkdir -p "${EXPERIMENTS_DIR}/images/${model//[^a-zA-Z0-9]/_}"
    done

    # Check dependencies
    check_dependencies || exit 1
    check_api_keys

    # Load environment variables
    if [[ -f "${PROJECT_ROOT}/.env" ]]; then
        log_info "Loading environment from .env"
        set -a
        source "${PROJECT_ROOT}/.env"
        set +a
    fi

    # Verify Python environment
    log_info "Python version: $(python3 --version)"
    log_info "PyTorch version: $(python3 -c 'import torch; print(torch.__version__)')"

    # Check CUDA if available
    if python3 -c "import torch; print(torch.cuda.is_available())" | grep -q "True"; then
        log_success "CUDA is available"
        python3 -c "import torch; print(f'CUDA devices: {torch.cuda.device_count()}')"
    else
        log_warning "CUDA not available, will use CPU (slower)"
    fi

    save_checkpoint "setup"
    log_success "Phase 1 (Setup) completed"
}

#-------------------------------------------------------------------------------
# Phase 2: Generate Prompts
#-------------------------------------------------------------------------------

phase_generate() {
    log_info "========== PHASE 2: GENERATE PROMPTS =========="

    local output_file="${EXPERIMENTS_DIR}/prompts/all_prompts_${RUN_ID}.json"

    log_info "Generating ${NUM_BASE_PROMPTS} base prompts across 9 domains..."
    log_info "Expanding with 5 attribute dimensions (culture, gender, disability, religion, age)"

    # Generate prompts using LLM-driven expansion
    python3 "${PROJECT_ROOT}/scripts/design_prompts.py" \
        --domains all \
        --attributes culture gender disability religion age \
        --num-base ${NUM_BASE_PROMPTS} \
        --llm "${LLM_MODEL}" \
        --llm-api-base "${LLM_API_BASE}" \
        --output "${output_file}" \
        --seed ${SEED} \
        2>&1 | tee -a "${LOG_DIR}/${RUN_ID}.log"

    # Validate output
    if [[ -f "${output_file}" ]]; then
        local prompt_count=$(python3 -c "import json; print(len(json.load(open('${output_file}'))))")
        log_success "Generated ${prompt_count} attribute-conditioned prompts"
        log_info "Saved to: ${output_file}"
    else
        log_error "Failed to generate prompts"
        exit 1
    fi

    # Save checkpoint
    cp "${output_file}" "${CHECKPOINT_DIR}/prompts_checkpoint.json"
    save_checkpoint "generate"
    log_success "Phase 2 (Generate) completed"
}

#-------------------------------------------------------------------------------
# Phase 3: Evaluate Models
#-------------------------------------------------------------------------------

phase_evaluate() {
    log_info "========== PHASE 3: EVALUATE MODELS =========="

    local prompts_file="${EXPERIMENTS_DIR}/prompts/all_prompts_${RUN_ID}.json"

    # Use checkpoint if exists
    if [[ ! -f "${prompts_file}" ]] && [[ -f "${CHECKPOINT_DIR}/prompts_checkpoint.json" ]]; then
        prompts_file="${CHECKPOINT_DIR}/prompts_checkpoint.json"
        log_info "Using checkpointed prompts file"
    fi

    if [[ ! -f "${prompts_file}" ]]; then
        log_error "Prompts file not found. Run generate phase first."
        exit 1
    fi

    # -------------------------------------------------------------------------
    # T2I Model Evaluation
    # -------------------------------------------------------------------------
    log_info "--- T2I Model Evaluation ---"

    for model in "${T2I_MODELS[@]}"; do
        log_info "Evaluating T2I model: ${model}"

        local model_results="${RESULTS_DIR}/${model//[^a-zA-Z0-9]/_}/${RUN_ID}"
        mkdir -p "${model_results}"

        python3 "${PROJECT_ROOT}/scripts/run_audit.py" \
            --model "${model}" \
            --mode t2i \
            --samples ${NUM_BASE_PROMPTS} \
            --llm "${LLM_MODEL}" \
            --llm-api-base "${LLM_API_BASE}" \
            --vlm "${VLM_MODEL}" \
            --refusal-threshold ${REFUSAL_THRESHOLD} \
            --output "${model_results}" \
            --run-id "${RUN_ID}" \
            --seed ${SEED} \
            2>&1 | tee -a "${LOG_DIR}/${RUN_ID}_${model//[^a-zA-Z0-9]/_}.log"

        # Checkpoint after each model
        save_checkpoint "evaluate_t2i_${model}"
        log_success "Completed T2I evaluation: ${model}"
    done

    # -------------------------------------------------------------------------
    # I2I Model Evaluation
    # -------------------------------------------------------------------------
    log_info "--- I2I Model Evaluation ---"

    # Check for source images
    local ffhq_dir="${DATA_DIR}/ffhq"
    local coco_dir="${DATA_DIR}/coco"

    local source_dir=""
    if [[ -d "${ffhq_dir}" ]] && [[ $(ls -A "${ffhq_dir}" 2>/dev/null | wc -l) -gt 0 ]]; then
        source_dir="${ffhq_dir}"
        log_info "Using FFHQ source images"
    elif [[ -d "${coco_dir}" ]] && [[ $(ls -A "${coco_dir}" 2>/dev/null | wc -l) -gt 0 ]]; then
        source_dir="${coco_dir}"
        log_info "Using COCO source images"
    else
        log_warning "No source images found. I2I will generate synthetic sources."
    fi

    for model in "${I2I_MODELS[@]}"; do
        log_info "Evaluating I2I model: ${model}"

        local model_results="${RESULTS_DIR}/${model//[^a-zA-Z0-9]/_}/${RUN_ID}"
        mkdir -p "${model_results}"

        local dataset_arg=""
        [[ -n "${source_dir}" ]] && dataset_arg="--dataset ${source_dir}"

        python3 "${PROJECT_ROOT}/scripts/run_audit.py" \
            --model "${model}" \
            --mode i2i \
            --samples ${NUM_BASE_PROMPTS} \
            --llm "${LLM_MODEL}" \
            --llm-api-base "${LLM_API_BASE}" \
            --vlm "${VLM_MODEL}" \
            --refusal-threshold ${REFUSAL_THRESHOLD} \
            --output "${model_results}" \
            --run-id "${RUN_ID}" \
            --seed ${SEED} \
            ${dataset_arg} \
            2>&1 | tee -a "${LOG_DIR}/${RUN_ID}_${model//[^a-zA-Z0-9]/_}.log"

        save_checkpoint "evaluate_i2i_${model}"
        log_success "Completed I2I evaluation: ${model}"
    done

    save_checkpoint "evaluate"
    log_success "Phase 3 (Evaluate) completed"
}

#-------------------------------------------------------------------------------
# Phase 4: Analyze Results
#-------------------------------------------------------------------------------

phase_analyze() {
    log_info "========== PHASE 4: ANALYZE RESULTS =========="

    local analysis_dir="${EXPERIMENTS_DIR}/analysis_${RUN_ID}"
    mkdir -p "${analysis_dir}"

    # Aggregate results from all models
    log_info "Aggregating results from all models..."

    python3 << EOF
import json
import os
from pathlib import Path
import pandas as pd

results_dir = Path("${RESULTS_DIR}")
analysis_dir = Path("${analysis_dir}")

all_results = []
summary_stats = []

# Collect all results
for model_dir in results_dir.iterdir():
    if not model_dir.is_dir():
        continue

    for run_dir in model_dir.iterdir():
        summary_file = run_dir / "acrb_summary.json"
        if summary_file.exists():
            with open(summary_file) as f:
                data = json.load(f)
                all_results.append(data)
                summary_stats.append({
                    "model": data["model_name"],
                    "mode": data["mode"],
                    "total_samples": data["total_samples"],
                    "refusal_rate": data["refusal_rate"],
                    "delta_refusal": data["delta_refusal"],
                    "delta_erasure": data["delta_erasure"]
                })

# Create summary DataFrame
if summary_stats:
    df = pd.DataFrame(summary_stats)
    df.to_csv(analysis_dir / "model_comparison.csv", index=False)
    print(f"Saved model comparison to {analysis_dir / 'model_comparison.csv'}")

    # Print summary
    print("\n" + "="*70)
    print("MODEL COMPARISON SUMMARY")
    print("="*70)
    print(df.to_string(index=False))
    print("="*70 + "\n")

# Save full aggregated results
with open(analysis_dir / "all_results.json", "w") as f:
    json.dump(all_results, f, indent=2)

print(f"Aggregated {len(all_results)} model results")
EOF

    # Generate visualizations
    log_info "Generating visualizations..."

    python3 "${PROJECT_ROOT}/scripts/plot_results.py" \
        --input "${RESULTS_DIR}" \
        --output "${PROJECT_ROOT}/figs" \
        --run-id "${RUN_ID}" \
        2>&1 | tee -a "${LOG_DIR}/${RUN_ID}.log"

    # Statistical analysis
    log_info "Running statistical analysis..."

    python3 << EOF
import json
import numpy as np
from scipy import stats
from pathlib import Path

analysis_dir = Path("${analysis_dir}")

# Load all results
with open(analysis_dir / "all_results.json") as f:
    all_results = json.load(f)

if not all_results:
    print("No results to analyze")
    exit(0)

# Compute cross-model statistics
refusal_rates = [r["refusal_rate"] for r in all_results]
delta_refusals = [r["delta_refusal"] for r in all_results]
delta_erasures = [r["delta_erasure"] for r in all_results]

analysis = {
    "num_models": len(all_results),
    "refusal_rate": {
        "mean": np.mean(refusal_rates),
        "std": np.std(refusal_rates),
        "min": np.min(refusal_rates),
        "max": np.max(refusal_rates)
    },
    "delta_refusal": {
        "mean": np.mean(delta_refusals),
        "std": np.std(delta_refusals),
        "min": np.min(delta_refusals),
        "max": np.max(delta_refusals)
    },
    "delta_erasure": {
        "mean": np.mean(delta_erasures),
        "std": np.std(delta_erasures),
        "min": np.min(delta_erasures),
        "max": np.max(delta_erasures)
    }
}

# T-test: T2I vs I2I
t2i_deltas = [r["delta_refusal"] for r in all_results if r["mode"] == "t2i"]
i2i_deltas = [r["delta_refusal"] for r in all_results if r["mode"] == "i2i"]

if len(t2i_deltas) > 1 and len(i2i_deltas) > 1:
    t_stat, p_value = stats.ttest_ind(t2i_deltas, i2i_deltas)
    analysis["t2i_vs_i2i"] = {
        "t_statistic": t_stat,
        "p_value": p_value,
        "significant": p_value < 0.05
    }

with open(analysis_dir / "statistical_analysis.json", "w") as f:
    json.dump(analysis, f, indent=2)

print("\nStatistical Analysis Summary:")
print(f"  Models analyzed: {analysis['num_models']}")
print(f"  Avg Refusal Rate: {analysis['refusal_rate']['mean']:.2%}")
print(f"  Avg Delta_refusal: {analysis['delta_refusal']['mean']:.4f}")
print(f"  Avg Delta_erasure: {analysis['delta_erasure']['mean']:.4f}")
EOF

    save_checkpoint "analyze"
    log_success "Phase 4 (Analyze) completed"
}

#-------------------------------------------------------------------------------
# Phase 5: Generate Paper Content
#-------------------------------------------------------------------------------

phase_paper() {
    log_info "========== PHASE 5: PAPER CONTENT =========="

    local paper_dir="${PROJECT_ROOT}/paper"
    local analysis_dir="${EXPERIMENTS_DIR}/analysis_${RUN_ID}"

    # Generate LaTeX tables
    log_info "Generating LaTeX tables..."

    python3 << EOF
import json
import pandas as pd
from pathlib import Path

analysis_dir = Path("${analysis_dir}")
paper_dir = Path("${paper_dir}")

# Load model comparison
csv_file = analysis_dir / "model_comparison.csv"
if csv_file.exists():
    df = pd.read_csv(csv_file)

    # Generate main results table
    latex_table = r"""
\begin{table}[t]
\centering
\caption{Refusal Disparity Metrics Across Models}
\label{tab:main-results}
\begin{tabular}{llcccc}
\toprule
\textbf{Model} & \textbf{Mode} & \textbf{N} & \textbf{R\%} & \textbf{$\Delta_R$} & \textbf{$\Delta_E$} \\
\midrule
"""

    for _, row in df.iterrows():
        latex_table += f"{row['model']} & {row['mode'].upper()} & {row['total_samples']} & {row['refusal_rate']*100:.1f} & {row['delta_refusal']:.3f} & {row['delta_erasure']:.3f} \\\\\n"

    latex_table += r"""
\bottomrule
\end{tabular}
\end{table}
"""

    with open(paper_dir / "tables" / "main_results.tex", "w") as f:
        f.write(latex_table)

    print(f"Generated LaTeX table: {paper_dir / 'tables' / 'main_results.tex'}")
EOF

    # Copy figures to paper directory
    log_info "Copying figures to paper directory..."
    mkdir -p "${paper_dir}/figures"
    cp -r "${PROJECT_ROOT}/figs/"*.pdf "${paper_dir}/figures/" 2>/dev/null || true
    cp -r "${PROJECT_ROOT}/figs/"*.png "${paper_dir}/figures/" 2>/dev/null || true

    save_checkpoint "paper"
    log_success "Phase 5 (Paper) completed"
}

#-------------------------------------------------------------------------------
# Main Execution
#-------------------------------------------------------------------------------

main() {
    local phase="${1:-all}"
    local dry_run=false
    local resume=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --phase)
                phase="$2"
                shift 2
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --resume)
                resume=true
                shift
                ;;
            --run-id)
                RUN_ID="$2"
                shift 2
                ;;
            --samples)
                NUM_BASE_PROMPTS="$2"
                shift 2
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --phase PHASE    Run specific phase (setup|generate|evaluate|analyze|paper|all)"
                echo "  --dry-run        Preview commands without executing"
                echo "  --resume         Resume from last checkpoint"
                echo "  --run-id ID      Use specific run ID"
                echo "  --samples N      Number of base prompts (default: 100)"
                echo "  --help           Show this help message"
                exit 0
                ;;
            *)
                phase="$1"
                shift
                ;;
        esac
    done

    # Initialize
    mkdir -p "${LOG_DIR}" "${CHECKPOINT_DIR}"

    print_banner

    # Resume logic
    if [[ "${resume}" == true ]]; then
        local last_phase=$(load_checkpoint)
        log_info "Resuming from checkpoint: ${last_phase}"

        if [[ -f "${CHECKPOINT_DIR}/current_run_id.txt" ]]; then
            RUN_ID=$(cat "${CHECKPOINT_DIR}/current_run_id.txt")
            log_info "Using run ID: ${RUN_ID}"
        fi

        case "${last_phase}" in
            "setup") phase="generate" ;;
            "generate") phase="evaluate" ;;
            "evaluate"*) phase="analyze" ;;
            "analyze") phase="paper" ;;
            "paper")
                log_success "All phases already completed!"
                exit 0
                ;;
        esac
    fi

    # Dry run mode
    if [[ "${dry_run}" == true ]]; then
        log_info "DRY RUN MODE - Commands will be printed but not executed"
        echo ""
        echo "Phases to execute: ${phase}"
        echo "Models: ${T2I_MODELS[*]} ${I2I_MODELS[*]}"
        echo "Base prompts: ${NUM_BASE_PROMPTS}"
        exit 0
    fi

    # Execute phases
    local start_time=$(date +%s)

    case "${phase}" in
        setup)
            phase_setup
            ;;
        generate)
            phase_generate
            ;;
        evaluate)
            phase_evaluate
            ;;
        analyze)
            phase_analyze
            ;;
        paper)
            phase_paper
            ;;
        all)
            phase_setup
            phase_generate
            phase_evaluate
            phase_analyze
            phase_paper
            ;;
        *)
            log_error "Unknown phase: ${phase}"
            exit 1
            ;;
    esac

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo ""
    log_success "Pipeline completed in ${duration} seconds"
    log_info "Results: ${RESULTS_DIR}"
    log_info "Logs: ${LOG_DIR}/${RUN_ID}.log"
    echo ""
}

# Run main function
main "$@"
