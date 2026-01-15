#!/bin/bash
#
# Quick test: Run single prompt on all 3 models
# 
# Usage:
#   bash scripts/experiment/test_wino_single.sh [PROMPT_ID] [GPU_ID]
#
# Example:
#   bash scripts/experiment/test_wino_single.sh 1 0

set -e

PROMPT_ID=${1:-1}
GPU_ID=${2:-0}

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "========================================================================"
echo "WinoBias Test: Single Prompt on All Models"
echo "========================================================================"
echo "Prompt ID: $PROMPT_ID"
echo "GPU: $GPU_ID"
echo "========================================================================"
echo ""

# Test FLUX.2
echo "→ [1/3] Testing FLUX.2-dev..."
bash scripts/experiment/run_flux2_wino.sh $GPU_ID $PROMPT_ID $PROMPT_ID
echo ""

# Test Qwen
echo "→ [2/3] Testing Qwen-Image-Edit-2511..."
bash scripts/experiment/run_qwen_wino.sh $GPU_ID $PROMPT_ID $PROMPT_ID
echo ""

# Test Step1X
echo "→ [3/3] Testing Step1X-Edit-v1p2..."
bash scripts/experiment/run_step1x_wino.sh $GPU_ID $PROMPT_ID $PROMPT_ID
echo ""

echo "========================================================================"
echo "✓ Test Complete!"
echo "========================================================================"
echo "Check results in:"
echo "  - data/results/winobias/flux2/"
echo "  - data/results/winobias/qwen/"
echo "  - data/results/winobias/step1x/"
echo "========================================================================"
