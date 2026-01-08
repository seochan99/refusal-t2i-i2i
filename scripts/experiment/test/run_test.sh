#!/bin/bash
# Quick Test Runner for I2I Models
# Tests each model with 1 image × 5 prompts (1 per category A-E)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "========================================"
echo "I2I Model Quick Test"
echo "========================================"
echo "Project: $PROJECT_ROOT"
echo ""

# Check arguments
MODEL=${1:-"flux"}
DEVICE=${2:-"cuda"}

if [ "$MODEL" == "--help" ] || [ "$MODEL" == "-h" ]; then
    echo "Usage: ./run_test.sh [model] [device]"
    echo ""
    echo "Models: flux, step1x, qwen, all"
    echo "Device: cuda, cpu, mps"
    echo ""
    echo "Examples:"
    echo "  ./run_test.sh flux cuda    # Test FLUX on GPU"
    echo "  ./run_test.sh all cuda     # Test all models"
    echo "  ./run_test.sh qwen mps     # Test Qwen on Apple Silicon"
    exit 0
fi

cd "$PROJECT_ROOT"

if [ "$MODEL" == "all" ]; then
    python scripts/experiment/test/test_single_prompt.py --all --device "$DEVICE"
else
    python scripts/experiment/test/test_single_prompt.py --model "$MODEL" --device "$DEVICE"
fi

echo ""
echo "Test complete! Check outputs in: scripts/experiment/test/outputs/"
