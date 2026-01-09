#!/bin/bash
# Step1X-Edit-v1p2 Environment Setup Script
# Model: https://huggingface.co/stepfun-ai/Step1X-Edit-v1p2
#
# Usage:
#   chmod +x setup_step1x.sh
#   ./setup_step1x.sh
#
# Requirements:
#   - NVIDIA GPU with CUDA support (24GB+ VRAM recommended)
#   - Conda (Miniconda or Anaconda)
#   - ~50GB disk space for model weights

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Step1X-Edit-v1p2 Environment Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Configuration
ENV_NAME="step1x"
PYTHON_VERSION="3.11"
CUDA_VERSION="cu124"
TORCH_VERSION="2.5.1"
DIFFUSERS_DIR="diffusers-step1x"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for conda
if ! command -v conda &> /dev/null; then
    echo -e "${RED}Error: conda not found. Please install Miniconda or Anaconda first.${NC}"
    echo "  Download: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Check for NVIDIA GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${YELLOW}Warning: nvidia-smi not found. GPU may not be available.${NC}"
fi

# Step 1: Create conda environment
echo -e "\n${GREEN}[1/5] Creating conda environment '${ENV_NAME}'...${NC}"
if conda env list | grep -q "^${ENV_NAME} "; then
    echo -e "${YELLOW}Environment '${ENV_NAME}' already exists.${NC}"
    read -p "Do you want to remove and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        conda env remove -n ${ENV_NAME} -y
        conda create -n ${ENV_NAME} python=${PYTHON_VERSION} -y
    fi
else
    conda create -n ${ENV_NAME} python=${PYTHON_VERSION} -y
fi

# Activate environment
echo -e "\n${GREEN}[2/5] Activating environment...${NC}"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate ${ENV_NAME}

# Step 3: Install PyTorch with CUDA
echo -e "\n${GREEN}[3/5] Installing PyTorch ${TORCH_VERSION} with CUDA ${CUDA_VERSION}...${NC}"
pip install torch==${TORCH_VERSION} torchvision==0.20.1 --index-url https://download.pytorch.org/whl/${CUDA_VERSION}

# Verify PyTorch installation
python -c "import torch; print(f'PyTorch {torch.__version__} installed, CUDA available: {torch.cuda.is_available()}')"

# Step 4: Install dependencies
echo -e "\n${GREEN}[4/5] Installing dependencies...${NC}"
pip install -r "${SCRIPT_DIR}/requirements-step1x.txt"

# Step 5: Install custom diffusers
echo -e "\n${GREEN}[5/5] Installing custom diffusers branch (step1xedit_v1p2)...${NC}"
if [ -d "${SCRIPT_DIR}/${DIFFUSERS_DIR}" ]; then
    echo -e "${YELLOW}Directory '${DIFFUSERS_DIR}' already exists.${NC}"
    read -p "Do you want to update it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "${SCRIPT_DIR}/${DIFFUSERS_DIR}"
        git pull
        pip install -e .
        cd "${SCRIPT_DIR}"
    else
        cd "${SCRIPT_DIR}/${DIFFUSERS_DIR}"
        pip install -e .
        cd "${SCRIPT_DIR}"
    fi
else
    git clone -b step1xedit_v1p2 https://github.com/Peyton-Chen/diffusers.git "${SCRIPT_DIR}/${DIFFUSERS_DIR}"
    cd "${SCRIPT_DIR}/${DIFFUSERS_DIR}"
    pip install -e .
    cd "${SCRIPT_DIR}"
fi

# Verify diffusers installation
echo -e "\n${GREEN}Verifying diffusers installation...${NC}"
python -c "from diffusers import Step1XEditPipelineV1P2; print('Step1XEditPipelineV1P2 imported successfully!')"

# Optional: Install RegionE
echo ""
read -p "Do you want to install RegionE for faster inference? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${GREEN}Installing RegionE...${NC}"
    pip install RegionE
fi

# Success message
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "To use Step1X, activate the environment:"
echo -e "  ${YELLOW}conda activate ${ENV_NAME}${NC}"
echo ""
echo -e "Test the installation:"
echo -e "  ${YELLOW}python test_step1x_minimal.py${NC}"
echo ""
echo -e "Note: The first run will download ~50GB of model weights."
echo -e "GPU Memory: 24GB+ VRAM recommended (uses CPU offload)"
echo ""
