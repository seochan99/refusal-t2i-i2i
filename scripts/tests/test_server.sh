#!/bin/bash
# ACRB: Quick Server Test
# Verifies environment setup and runs minimal tests
#
# Usage: ./scripts/test_server.sh [--full]

set -e

FULL_TEST=${1:-""}

echo "========================================"
echo "ACRB Server Verification Test"
echo "========================================"
echo ""

# 1. Check Python
echo "1. Python Environment"
echo "-------------------"
python3 --version
echo ""

# 2. Check dependencies
echo "2. Dependencies"
echo "-------------------"
python3 -c "
import sys
deps = ['torch', 'transformers', 'diffusers', 'mediapipe', 'numpy', 'pandas']
for dep in deps:
    try:
        mod = __import__(dep)
        ver = getattr(mod, '__version__', 'unknown')
        print(f'  {dep}: {ver}')
    except ImportError:
        print(f'  {dep}: NOT INSTALLED')
"
echo ""

# 3. Check ACRB module
echo "3. ACRB Module"
echo "-------------------"
python3 -c "
try:
    from acrb import config
    print(f'  ACRB: OK')
    print(f'  T2I Models: {len(config.MODELS[\"t2i\"])}')
    print(f'  I2I Models: {len(config.MODELS[\"i2i\"])}')
    print(f'  Domains: {len(config.DOMAINS)}')
except Exception as e:
    print(f'  ACRB: ERROR - {e}')
"
echo ""

# 4. Check GPU
echo "4. GPU Status"
echo "-------------------"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
else
    echo "  No NVIDIA GPU detected"
fi
python3 -c "
import torch
print(f'  PyTorch CUDA: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'  Device: {torch.cuda.get_device_name(0)}')
"
echo ""

# 5. Check API Keys
echo "5. API Keys"
echo "-------------------"
[ -n "$OPENAI_API_KEY" ] && echo "  OPENAI_API_KEY: Set" || echo "  OPENAI_API_KEY: NOT SET"
[ -n "$GOOGLE_API_KEY" ] && echo "  GOOGLE_API_KEY: Set" || echo "  GOOGLE_API_KEY: NOT SET"
[ -n "$BYTEPLUS_API_KEY" ] && echo "  BYTEPLUS_API_KEY: Set" || echo "  BYTEPLUS_API_KEY: NOT SET"
echo ""

# 6. Run quick tests if --full
if [ "$FULL_TEST" = "--full" ]; then
    echo "6. Running Quick Tests"
    echo "-------------------"

    # Test with open source model only (no API key needed)
    python scripts/run_test.py \
        --skip-closed \
        --samples 2 \
        --t2i-only \
        --verbose

    echo ""
    echo "Full test completed!"
else
    echo "6. Skip Full Tests"
    echo "-------------------"
    echo "  Run with --full flag to execute model tests"
    echo "  Example: ./scripts/test_server.sh --full"
fi

echo ""
echo "========================================"
echo "Server verification complete!"
echo "========================================"
