#!/bin/bash
# ACRB: Run all open source models
# Usage: ./scripts/run_open_models.sh [t2i|i2i|all] [samples]

set -e

MODE=${1:-"all"}
SAMPLES=${2:-100}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "========================================"
echo "ACRB Open Source Models Runner"
echo "Mode: $MODE | Samples: $SAMPLES"
echo "========================================"

# Check GPU
if command -v nvidia-smi &> /dev/null; then
    echo "GPU Status:"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
else
    echo "WARNING: No NVIDIA GPU detected. Open source models require GPU."
fi

# T2I Experiments
if [ "$MODE" = "t2i" ] || [ "$MODE" = "all" ]; then
    echo ""
    echo ">>> Running T2I open source models..."
    python scripts/run_t2i_all.py \
        --open-only \
        --samples $SAMPLES \
        --output "experiments/results/t2i_open_$TIMESTAMP"
fi

# I2I Experiments
if [ "$MODE" = "i2i" ] || [ "$MODE" = "all" ]; then
    if [ -z "$FFHQ_PATH" ]; then
        echo ""
        echo "WARNING: FFHQ_PATH not set. Skipping I2I experiments."
        echo "Set FFHQ_PATH to your FFHQ dataset directory."
    else
        echo ""
        echo ">>> Running I2I open source models..."
        python scripts/run_i2i_all.py \
            --open-only \
            --dataset "$FFHQ_PATH" \
            --samples $SAMPLES \
            --output "experiments/results/i2i_open_$TIMESTAMP"
    fi
fi

echo ""
echo "========================================"
echo "Open source experiments complete!"
echo "========================================"
