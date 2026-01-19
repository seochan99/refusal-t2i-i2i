#!/bin/bash
#===============================================================================
# Experiment 1 VLM Evaluation Runner
#===============================================================================
# Evaluates Category B (Occupation) + D (Vulnerability)
# Scale: 20 prompts × 84 images = 1,680 per model
#
# Usage:
#   bash scripts/evaluation/run_exp1_evaluation.sh
#   bash scripts/evaluation/run_exp1_evaluation.sh --limit 10  # Test run
#===============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}"
echo "============================================================"
echo "  Experiment 1 VLM Evaluation"
echo "  Categories: B (Occupation) + D (Vulnerability)"
echo "  Ensemble: Gemini Flash 2.0 + GPT-5.2"
echo "============================================================"
echo -e "${NC}"

# Check API keys
if [ -z "$GOOGLE_API_KEY" ]; then
    echo -e "${RED}ERROR: GOOGLE_API_KEY not set${NC}"
    echo "Run: export GOOGLE_API_KEY='your-gemini-api-key'"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}ERROR: OPENAI_API_KEY not set${NC}"
    echo "Run: export OPENAI_API_KEY='your-openai-api-key'"
    exit 1
fi

echo -e "${GREEN}✓ API keys configured${NC}"
echo ""

# Parse arguments
LIMIT_ARG=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --limit)
            LIMIT_ARG="--limit $2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Run evaluation
cd "$PROJECT_ROOT"
python scripts/evaluation/evaluation_exp1.py --model flux $LIMIT_ARG

echo ""
echo -e "${GREEN}============================================================"
echo "  Evaluation Complete!"
echo "============================================================${NC}"
echo "Results: $PROJECT_ROOT/data/results/evaluations/exp1/"
