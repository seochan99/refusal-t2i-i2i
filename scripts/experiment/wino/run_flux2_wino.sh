#!/bin/bash
#
# Run WinoBias experiment with FLUX.2-dev
#
# Usage:
#   bash scripts/experiment/run_flux2_wino.sh [GPU_ID] [START_ID] [END_ID]
#
# Examples:
#   bash scripts/experiment/run_flux2_wino.sh 0 1 50    # Full experiment on GPU 0
#   bash scripts/experiment/run_flux2_wino.sh 0 1 25    # First 25 prompts (male-centered)
#   bash scripts/experiment/run_flux2_wino.sh 1 26 50   # Last 25 prompts (female-centered)

set -e

# Configuration
GPU_ID=${1:-0}
START_ID=${2:-1}
END_ID=${3:-50}

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

OUTPUT_DIR="data/results/experiments/winobias/flux2"
PROMPTS_FILE="data/prompts/winobias_50_prompts.json"
BASE_DIR="data/source_images/final"

# Model parameters
STEPS=50
SEED=42

echo "========================================"
echo "WinoBias Experiment: FLUX.2-dev"
echo "========================================"
echo "GPU: $GPU_ID"
echo "Prompts: $START_ID to $END_ID"
echo "Output: $OUTPUT_DIR"
echo "========================================"
echo ""

# Run experiment
CUDA_VISIBLE_DEVICES=$GPU_ID python3 scripts/experiment/run_winobias_experiment.py \
    --model flux2 \
    --prompts-file "$PROMPTS_FILE" \
    --base-dir "$BASE_DIR" \
    --output-dir "$OUTPUT_DIR" \
    --start-id $START_ID \
    --end-id $END_ID \
    --device cuda \
    --steps $STEPS \
    --seed $SEED

echo ""
echo "✓ FLUX.2 experiment complete!"
echo "Results saved to: $OUTPUT_DIR"
