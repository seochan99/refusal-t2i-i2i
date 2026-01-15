#!/bin/bash
#
# Run WinoBias experiment with Step1X-Edit-v1p2
#
# Usage:
#   bash scripts/experiment/run_step1x_wino.sh [GPU_ID] [START_ID] [END_ID]
#
# Examples:
#   bash scripts/experiment/wino/run_step1x_wino.sh 0 1 50    # Full experiment on GPU 0
#   bash scripts/experiment/wino/run_step1x_wino.sh 0 1 25    # First 25 prompts
#   bash scripts/experiment/wino/run_step1x_wino.sh 1 26 50   # Last 25 prompts

set -e

# Configuration
GPU_ID=${1:-0}
START_ID=${2:-1}
END_ID=${3:-50}

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

OUTPUT_DIR="data/results/experiments/winobias/step1x"
PROMPTS_FILE="data/prompts/winobias_prompts.json"
BASE_DIR="data/source_images/final"

# Model parameters
STEPS=50
SEED=42

# Step1X reasoning modes (optional)
ENABLE_THINKING=${ENABLE_THINKING:-false}
ENABLE_REFLECTION=${ENABLE_REFLECTION:-false}

echo "========================================"
echo "WinoBias Experiment: Step1X-Edit-v1p2"
echo "========================================"
echo "GPU: $GPU_ID"
echo "Prompts: $START_ID to $END_ID"
echo "Output: $OUTPUT_DIR"
echo "Thinking: $ENABLE_THINKING"
echo "Reflection: $ENABLE_REFLECTION"
echo "========================================"
echo ""

# Build command
CMD="CUDA_VISIBLE_DEVICES=$GPU_ID python3 scripts/experiment/run_winobias_experiment.py \
    --model step1x \
    --prompts-file $PROMPTS_FILE \
    --base-dir $BASE_DIR \
    --output-dir $OUTPUT_DIR \
    --start-id $START_ID \
    --end-id $END_ID \
    --device cuda \
    --steps $STEPS \
    --seed $SEED"

# Add reasoning modes if enabled
if [ "$ENABLE_THINKING" = "true" ]; then
    CMD="$CMD --thinking"
fi

if [ "$ENABLE_REFLECTION" = "true" ]; then
    CMD="$CMD --reflection"
fi

# Run experiment
eval $CMD

echo ""
echo "✓ Step1X experiment complete!"
echo "Results saved to: $OUTPUT_DIR"
