#!/bin/bash
# ACRB: Run all closed source models
# Usage: ./scripts/run_closed_models.sh [t2i|i2i|all] [samples]

set -e

MODE=${1:-"all"}
SAMPLES=${2:-100}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "========================================"
echo "ACRB Closed Source Models Runner"
echo "Mode: $MODE | Samples: $SAMPLES"
echo "========================================"

# Check API keys
if [ -z "$OPENAI_API_KEY" ]; then
    echo "WARNING: OPENAI_API_KEY not set (required for GPT Image 1.5)"
fi
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "WARNING: GOOGLE_API_KEY not set (required for Imagen 3)"
fi
if [ -z "$BYTEPLUS_API_KEY" ]; then
    echo "WARNING: BYTEPLUS_API_KEY not set (required for Seedream 4.5)"
fi

# T2I Experiments
if [ "$MODE" = "t2i" ] || [ "$MODE" = "all" ]; then
    echo ""
    echo ">>> Running T2I closed source models..."
    python scripts/run_t2i_all.py \
        --closed-only \
        --samples $SAMPLES \
        --output "experiments/results/t2i_closed_$TIMESTAMP"
fi

# I2I Experiments
if [ "$MODE" = "i2i" ] || [ "$MODE" = "all" ]; then
    if [ -z "$FFHQ_PATH" ]; then
        echo ""
        echo "WARNING: FFHQ_PATH not set. Skipping I2I experiments."
        echo "Set FFHQ_PATH to your FFHQ dataset directory."
    else
        echo ""
        echo ">>> Running I2I closed source models..."
        python scripts/run_i2i_all.py \
            --closed-only \
            --dataset "$FFHQ_PATH" \
            --samples $SAMPLES \
            --output "experiments/results/i2i_closed_$TIMESTAMP"
    fi
fi

echo ""
echo "========================================"
echo "Closed source experiments complete!"
echo "========================================"
