#!/bin/bash
#
# Run Step1X WinoBias experiment in parallel across 2 GPUs
# GPU 0: prompts 1-25
# GPU 1: prompts 26-50
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Configuration
MODEL="step1x"
PROMPTS_FILE="$PROJECT_ROOT/data/prompts/winobias_prompts.json"
BASE_DIR="$PROJECT_ROOT/data/source_images/final"
OUTPUT_BASE="$PROJECT_ROOT/data/results/experiments/winobias_step1x"

# Inference parameters
STEPS=50
SEED=42
THINKING="--thinking"    # Enable thinking mode
REFLECTION=""            # Optional: add --reflection to enable

# Create base output directory
mkdir -p "$OUTPUT_BASE"

# Timestamp for this run
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Output directories for each GPU
OUTPUT_DIR_GPU0="$OUTPUT_BASE/gpu0_${TIMESTAMP}"
OUTPUT_DIR_GPU1="$OUTPUT_BASE/gpu1_${TIMESTAMP}"

echo "========================================================================"
echo "Step1X WinoBias Experiment - Parallel GPU Execution"
echo "========================================================================"
echo "Model: $MODEL"
echo "Total Prompts: 50"
echo "GPU 0: Prompts 1-25 → $OUTPUT_DIR_GPU0"
echo "GPU 1: Prompts 26-50 → $OUTPUT_DIR_GPU1"
echo "Thinking Mode: Enabled"
echo "========================================================================"
echo ""

# Run on GPU 0 (prompts 1-25) in background
echo "[GPU 0] Starting prompts 1-25..."
CUDA_VISIBLE_DEVICES=0 python3 "$SCRIPT_DIR/run_winobias_experiment.py" \
    --model "$MODEL" \
    --prompts-file "$PROMPTS_FILE" \
    --base-dir "$BASE_DIR" \
    --output-dir "$OUTPUT_DIR_GPU0" \
    --device cuda:0 \
    --start-id 1 \
    --end-id 25 \
    --steps "$STEPS" \
    --seed "$SEED" \
    $THINKING \
    $REFLECTION \
    > "$OUTPUT_DIR_GPU0/console.log" 2>&1 &

GPU0_PID=$!
echo "  → Process started (PID: $GPU0_PID)"
echo "  → Log: $OUTPUT_DIR_GPU0/console.log"

# Small delay to avoid race conditions
sleep 2

# Run on GPU 1 (prompts 26-50) in background
echo "[GPU 1] Starting prompts 26-50..."
CUDA_VISIBLE_DEVICES=1 python3 "$SCRIPT_DIR/run_winobias_experiment.py" \
    --model "$MODEL" \
    --prompts-file "$PROMPTS_FILE" \
    --base-dir "$BASE_DIR" \
    --output-dir "$OUTPUT_DIR_GPU1" \
    --device cuda:0 \
    --start-id 26 \
    --end-id 50 \
    --steps "$STEPS" \
    --seed "$SEED" \
    $THINKING \
    $REFLECTION \
    > "$OUTPUT_DIR_GPU1/console.log" 2>&1 &

GPU1_PID=$!
echo "  → Process started (PID: $GPU1_PID)"
echo "  → Log: $OUTPUT_DIR_GPU1/console.log"

echo ""
echo "========================================================================"
echo "Both processes started!"
echo "========================================================================"
echo "GPU 0 PID: $GPU0_PID (prompts 1-25)"
echo "GPU 1 PID: $GPU1_PID (prompts 26-50)"
echo ""
echo "Monitor progress:"
echo "  tail -f $OUTPUT_DIR_GPU0/console.log"
echo "  tail -f $OUTPUT_DIR_GPU1/console.log"
echo ""
echo "Waiting for both processes to complete..."
echo "========================================================================"

# Wait for both processes to complete
wait $GPU0_PID
GPU0_EXIT=$?
echo "[GPU 0] Process completed (exit code: $GPU0_EXIT)"

wait $GPU1_PID
GPU1_EXIT=$?
echo "[GPU 1] Process completed (exit code: $GPU1_EXIT)"

echo ""
echo "========================================================================"
echo "PARALLEL EXECUTION COMPLETE"
echo "========================================================================"

if [ $GPU0_EXIT -eq 0 ] && [ $GPU1_EXIT -eq 0 ]; then
    echo "✓ Both GPUs completed successfully"
    
    # Count generated images
    GPU0_IMAGES=$(find "$OUTPUT_DIR_GPU0" -name "prompt_*.png" | wc -l)
    GPU1_IMAGES=$(find "$OUTPUT_DIR_GPU1" -name "prompt_*.png" | wc -l)
    TOTAL_IMAGES=$((GPU0_IMAGES + GPU1_IMAGES))
    
    echo ""
    echo "Generated Images:"
    echo "  GPU 0: $GPU0_IMAGES images"
    echo "  GPU 1: $GPU1_IMAGES images"
    echo "  Total: $TOTAL_IMAGES / 50"
    echo ""
    echo "Results:"
    echo "  GPU 0: $OUTPUT_DIR_GPU0"
    echo "  GPU 1: $OUTPUT_DIR_GPU1"
    
    # Optional: Merge results
    echo ""
    echo "To merge results into a single directory:"
    echo "  mkdir -p $OUTPUT_BASE/merged_${TIMESTAMP}"
    echo "  cp $OUTPUT_DIR_GPU0/*.png $OUTPUT_BASE/merged_${TIMESTAMP}/"
    echo "  cp $OUTPUT_DIR_GPU1/*.png $OUTPUT_BASE/merged_${TIMESTAMP}/"
    echo "  # Merge JSON results manually or with jq"
    
else
    echo "✗ One or more processes failed"
    echo "  GPU 0 exit code: $GPU0_EXIT"
    echo "  GPU 1 exit code: $GPU1_EXIT"
    echo ""
    echo "Check logs for details:"
    echo "  GPU 0: $OUTPUT_DIR_GPU0/console.log"
    echo "  GPU 1: $OUTPUT_DIR_GPU1/console.log"
    exit 1
fi

echo "========================================================================"
