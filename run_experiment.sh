#!/bin/bash
#===============================================================================
# ACRB I2I Experiment Runner
#
# Runs I2I refusal bias evaluation experiments.
#
# Supported I2I Models:
#   - flux-2-dev (Black Forest Labs) - Permissive
#   - gpt-image-1.5 (OpenAI) - Conservative
#   - imagen-3 (Google) - Moderate
#   - step1x-edit (StepFun) - I2I specialist
#   - qwen-image-edit-2511 (Alibaba) - Regional
#   - seedream-4.5 (ByteDance) - Regional
#
# Usage:
#   ./run_experiment.sh                         # Default: flux-2-dev, 100 samples
#   ./run_experiment.sh --model step1x-edit     # Specific model
#   ./run_experiment.sh --samples 500           # Custom sample count
#   ./run_experiment.sh --help                  # Show help
#===============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "${PROJECT_ROOT}"

# Default parameters
MODEL="flux-2-dev"
SAMPLES=100
SOURCE_DIR="data/raw/ffhq"
OUTPUT_DIR="experiments/results"
PROMPTS_FILE=""
SEED=42

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --samples)
            SAMPLES="$2"
            shift 2
            ;;
        --source-dir)
            SOURCE_DIR="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --prompts)
            PROMPTS_FILE="$2"
            shift 2
            ;;
        --seed)
            SEED="$2"
            shift 2
            ;;
        --help|-h)
            echo "ACRB I2I Experiment Runner"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --model MODEL       I2I model to use (default: flux-2-dev)"
            echo "  --samples N         Number of samples (default: 100)"
            echo "  --source-dir DIR    Source images directory (default: data/raw/ffhq)"
            echo "  --output DIR        Output directory (default: experiments/results)"
            echo "  --prompts FILE      Prompts JSON file (optional)"
            echo "  --seed N            Random seed (default: 42)"
            echo "  --help, -h          Show this help"
            echo ""
            echo "Supported I2I models:"
            echo "  flux-2-dev          Black Forest Labs (open, permissive)"
            echo "  gpt-image-1.5       OpenAI (closed, conservative)"
            echo "  imagen-3            Google (closed, moderate)"
            echo "  step1x-edit         StepFun (open, I2I specialist)"
            echo "  qwen-image-edit-2511 Alibaba (open, regional)"
            echo "  seedream-4.5        ByteDance (closed, regional)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "========================================"
echo "ACRB I2I Experiment Runner"
echo "========================================"
echo "Model:         $MODEL"
echo "Samples:       $SAMPLES"
echo "Source Images: $SOURCE_DIR"
echo "Output:        $OUTPUT_DIR"
echo "Seed:          $SEED"
echo "========================================"

# Check if source images exist
if [ ! -d "$SOURCE_DIR" ]; then
    echo ""
    echo "Warning: Source images directory not found: $SOURCE_DIR"
    echo "Please download FFHQ or COCO images first."
    echo ""
    echo "For FFHQ: https://github.com/NVlabs/ffhq-dataset"
    echo "For COCO: https://cocodataset.org/"
    echo ""
fi

# Check Python environment
if ! python -c "import acrb" 2>/dev/null; then
    echo "Error: acrb package not found. Please install dependencies:"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Build prompts argument
PROMPTS_ARG=""
if [ -n "$PROMPTS_FILE" ] && [ -f "$PROMPTS_FILE" ]; then
    PROMPTS_ARG="prompts_file='$PROMPTS_FILE',"
fi

# Run experiment
echo ""
echo "Starting I2I experiment..."
echo ""

python -c "
from acrb import ACRBPipeline, ACRBConfig

config = ACRBConfig(
    model_name='$MODEL',
    max_base_prompts=$SAMPLES,
    i2i_source_images_dir='$SOURCE_DIR',
    output_dir='$OUTPUT_DIR',
    seed=$SEED,
)

pipeline = ACRBPipeline(config)
prompts_file = '$PROMPTS_FILE' if '$PROMPTS_FILE' else None
result = pipeline.run(prompts_file)

print()
print('=' * 50)
print('EXPERIMENT RESULTS')
print('=' * 50)
print(f'Model:          {result.model_name}')
print(f'Total Samples:  {result.total_samples}')
print(f'Total Refused:  {result.total_refused}')
print(f'Total Failed:   {result.total_failed}')
print()
print(f'Refusal Rate:   {result.refusal_rate:.2%}')
print(f'Failure Rate:   {result.failure_rate:.2%}')
print()
print(f'Delta Refusal:  {result.delta_refusal:.4f}')
print(f'Delta Erasure:  {result.delta_erasure:.4f}')
print('=' * 50)
"

echo ""
echo "Experiment completed!"
echo "Results saved to: $OUTPUT_DIR/$MODEL/"
