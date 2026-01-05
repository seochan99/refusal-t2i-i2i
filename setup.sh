#!/bin/bash
#===============================================================================
# ACRB One-Click Setup Script
#
# Usage:
#   ./setup.sh           # Full setup
#   ./setup.sh --test    # Setup + run test
#   ./setup.sh --help    # Show help
#===============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Parse arguments
RUN_TEST=false
SKIP_VENV=false

for arg in "$@"; do
    case $arg in
        --test)
            RUN_TEST=true
            shift
            ;;
        --skip-venv)
            SKIP_VENV=true
            shift
            ;;
        --help)
            echo "ACRB Setup Script"
            echo ""
            echo "Usage: ./setup.sh [options]"
            echo ""
            echo "Options:"
            echo "  --test       Run test after setup"
            echo "  --skip-venv  Skip virtual environment creation"
            echo "  --help       Show this help message"
            echo ""
            echo "Environment Variables (optional):"
            echo "  OPENAI_API_KEY     For GPT Image 1.5"
            echo "  GOOGLE_API_KEY     For Imagen 3 & Gemini"
            echo "  BYTEPLUS_API_KEY   For Seedream 4.5"
            exit 0
            ;;
    esac
done

print_header "ACRB Setup - IJCAI-ECAI 2026"

#-------------------------------------------------------------------------------
# 1. Check Python
#-------------------------------------------------------------------------------
echo "1. Checking Python..."

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python $PYTHON_VERSION found"
else
    print_error "Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# Check Python version >= 3.10
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    print_warning "Python 3.10+ recommended (found $PYTHON_VERSION)"
fi

#-------------------------------------------------------------------------------
# 2. Create Virtual Environment
#-------------------------------------------------------------------------------
echo ""
echo "2. Setting up virtual environment..."

if [ "$SKIP_VENV" = false ]; then
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi

    # Activate
    source venv/bin/activate
    print_success "Virtual environment activated"
else
    print_warning "Skipping virtual environment (--skip-venv)"
fi

#-------------------------------------------------------------------------------
# 3. Upgrade pip
#-------------------------------------------------------------------------------
echo ""
echo "3. Upgrading pip..."

pip install --upgrade pip -q
print_success "pip upgraded"

#-------------------------------------------------------------------------------
# 4. Install dependencies
#-------------------------------------------------------------------------------
echo ""
echo "4. Installing dependencies..."

# Core dependencies first
pip install numpy pandas scipy tqdm pillow requests -q
print_success "Core dependencies installed"

# PyTorch (check if CUDA available)
if command -v nvidia-smi &> /dev/null; then
    print_success "NVIDIA GPU detected"
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121 -q 2>/dev/null || \
    pip install torch torchvision -q
else
    print_warning "No NVIDIA GPU detected, installing CPU version"
    pip install torch torchvision -q
fi
print_success "PyTorch installed"

# ML dependencies
pip install transformers accelerate diffusers safetensors -q
print_success "ML dependencies installed"

# Full requirements
pip install -r requirements.txt -q 2>/dev/null || {
    print_warning "Some optional dependencies failed, continuing..."
}
print_success "Requirements installed"

#-------------------------------------------------------------------------------
# 5. Check GPU
#-------------------------------------------------------------------------------
echo ""
echo "5. Checking GPU..."

python3 -c "
import torch
if torch.cuda.is_available():
    print(f'  GPU: {torch.cuda.get_device_name(0)}')
    print(f'  Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
else:
    print('  No CUDA GPU available (CPU mode)')
"

#-------------------------------------------------------------------------------
# 6. Verify ACRB module
#-------------------------------------------------------------------------------
echo ""
echo "6. Verifying ACRB module..."

python3 -c "
try:
    from acrb.config import MODELS, DOMAINS, ATTRIBUTES
    print(f'  Models: {len(MODELS[\"t2i\"])} T2I, {len(MODELS[\"i2i\"])} I2I')
    print(f'  Domains: {len(DOMAINS)}')
    print(f'  Attribute types: {len(ATTRIBUTES)}')
except Exception as e:
    print(f'  Warning: {e}')
" 2>/dev/null && print_success "ACRB module OK" || print_warning "ACRB module check failed"

#-------------------------------------------------------------------------------
# 7. Setup API Keys (Interactive)
#-------------------------------------------------------------------------------
echo ""
echo "7. Setting up API keys..."

# Load existing .env if exists
if [ -f ".env" ]; then
    source .env 2>/dev/null || true
fi

# Function to prompt for API key
prompt_api_key() {
    local key_name=$1
    local key_desc=$2
    local current_value=${!key_name}

    if [ -n "$current_value" ]; then
        print_success "$key_name already set"
        return
    fi

    echo ""
    echo -e "${YELLOW}$key_desc${NC}"
    echo -n "  Enter $key_name (or press Enter to skip): "
    read -r input_key

    if [ -n "$input_key" ]; then
        export $key_name="$input_key"
        echo "$key_name=$input_key" >> .env
        print_success "$key_name saved to .env"
    else
        print_warning "$key_name skipped (can add later to .env)"
    fi
}

# Create .env if not exists
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# ACRB Environment Configuration
# API keys for closed-source models

EOF
fi

echo ""
echo "API keys are optional. You can skip and add later to .env file."
echo "Press Enter to skip any key you don't have."

prompt_api_key "GOOGLE_API_KEY" "Google API Key (for Imagen 3 & Gemini - get from https://aistudio.google.com)"
prompt_api_key "OPENAI_API_KEY" "OpenAI API Key (for GPT Image 1.5 - get from https://platform.openai.com)"

echo ""
echo -e "  ${BLUE}Tip: Open source models (FLUX, SD, Qwen) don't need API keys!${NC}"

#-------------------------------------------------------------------------------
# 9. Make scripts executable
#-------------------------------------------------------------------------------
echo ""
echo "9. Making scripts executable..."

chmod +x scripts/*.sh scripts/*.py 2>/dev/null || true
print_success "Scripts are executable"

#-------------------------------------------------------------------------------
# 10. Run test (optional)
#-------------------------------------------------------------------------------
if [ "$RUN_TEST" = true ]; then
    echo ""
    print_header "Running Test"

    python scripts/run_test.py --skip-closed --samples 2 --t2i-only || {
        print_warning "Test had issues, check output above"
    }
fi

#-------------------------------------------------------------------------------
# Done!
#-------------------------------------------------------------------------------
print_header "Setup Complete!"

echo -e "Next steps:"
echo -e "  1. ${YELLOW}source venv/bin/activate${NC}  # Activate environment"
echo -e "  2. ${YELLOW}./scripts/test_server.sh${NC}   # Check setup"
echo -e "  3. ${YELLOW}python scripts/run_test.py${NC} # Run test"
echo ""
echo -e "For API-based models, set environment variables:"
echo -e "  ${YELLOW}export OPENAI_API_KEY='...'${NC}"
echo -e "  ${YELLOW}export GOOGLE_API_KEY='...'${NC}"
echo ""
echo -e "Full experiment:"
echo -e "  ${YELLOW}python scripts/run_t2i_all.py --samples 100${NC}"
echo ""
