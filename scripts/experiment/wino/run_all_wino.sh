#!/bin/bash
#
# Run WinoBias experiment on ALL 3 models (Flux2, Qwen, Step1X)
#
# Usage:
#   bash scripts/experiment/run_all_wino.sh [GPU_ID]
#
# This will run all 50 prompts on all 3 models sequentially
# Total: 150 images (50 prompts × 3 models)

set -e

GPU_ID=${1:-0}

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "========================================================================"
echo "WinoBias Experiment: ALL 3 MODELS"
echo "========================================================================"
echo "GPU: $GPU_ID"
echo "Models: FLUX.2, Qwen-Image-Edit-2511, Step1X-Edit-v1p2"
echo "Prompts: 50 total (25 male-centered, 25 female-centered)"
echo "Output: 150 images (50 × 3)"
echo "========================================================================"
echo ""

# Run each model
echo "→ [1/3] Running FLUX.2-dev..."
bash scripts/experiment/run_flux2_wino.sh $GPU_ID 1 50
echo ""

echo "→ [2/3] Running Qwen-Image-Edit-2511..."
bash scripts/experiment/run_qwen_wino.sh $GPU_ID 1 50
echo ""

echo "→ [3/3] Running Step1X-Edit-v1p2..."
bash scripts/experiment/run_step1x_wino.sh $GPU_ID 1 50
echo ""

echo "========================================================================"
echo "✓ ALL EXPERIMENTS COMPLETE!"
echo "========================================================================"
echo "Results:"
echo "  - FLUX.2:  data/results/experiments/winobias/flux2/"
echo "  - Qwen:    data/results/experiments/winobias/qwen/"
echo "  - Step1X:  data/results/experiments/winobias/step1x/"
echo "========================================================================"
