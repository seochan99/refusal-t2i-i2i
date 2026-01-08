#!/bin/bash
# FLUX.2-dev Quick Test
# 1 image × 5 prompts (1 per category A-E)

set -e
cd "$(dirname "$0")/../../.."

echo "========================================"
echo "FLUX.2-dev Quick Test"
echo "========================================"

DEVICE=${1:-"cuda"}
echo "Device: $DEVICE"

python scripts/experiment/test/test_single_prompt.py --model flux --device "$DEVICE"

echo ""
echo "Done! Outputs: scripts/experiment/test/outputs/flux/"
