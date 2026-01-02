#!/bin/bash
#===============================================================================
# ACRB Server Setup Script
# Sets up the complete environment for running ACRB experiments
#
# Usage:
#   ./setup_server.sh                # Full setup
#   ./setup_server.sh --check        # Check environment only
#   ./setup_server.sh --models       # Download models only
#   ./setup_server.sh --data         # Download datasets only
#===============================================================================

set -euo pipefail

#-------------------------------------------------------------------------------
# Configuration
#-------------------------------------------------------------------------------

PROJECT_ROOT="/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal"
PYTHON_VERSION="3.10"
VENV_NAME="acrb_env"
VENV_PATH="${PROJECT_ROOT}/${VENV_NAME}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

#-------------------------------------------------------------------------------
# Utility Functions
#-------------------------------------------------------------------------------

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_banner() {
    echo ""
    echo "==============================================================================="
    echo "   ACRB Server Setup"
    echo "   Attribute-Conditioned Refusal Bias Framework"
    echo "==============================================================================="
    echo ""
}

#-------------------------------------------------------------------------------
# System Checks
#-------------------------------------------------------------------------------

check_system() {
    log_info "Checking system requirements..."

    # OS detection
    OS="unknown"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    fi
    log_info "Operating System: ${OS} (${OSTYPE})"

    # Python check
    if command -v python3 &> /dev/null; then
        PYTHON_INSTALLED=$(python3 --version 2>&1)
        log_success "Python: ${PYTHON_INSTALLED}"
    else
        log_error "Python3 not found. Please install Python ${PYTHON_VERSION}+"
        exit 1
    fi

    # pip check
    if command -v pip3 &> /dev/null; then
        log_success "pip3: $(pip3 --version | head -1)"
    else
        log_error "pip3 not found"
        exit 1
    fi

    # git check
    if command -v git &> /dev/null; then
        log_success "git: $(git --version)"
    else
        log_warning "git not found (optional)"
    fi
}

#-------------------------------------------------------------------------------
# CUDA Check
#-------------------------------------------------------------------------------

check_cuda() {
    log_info "Checking CUDA environment..."

    # NVIDIA driver check
    if command -v nvidia-smi &> /dev/null; then
        log_success "NVIDIA driver found"
        echo ""
        nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
        echo ""

        # CUDA version
        if nvidia-smi --query-gpu=driver_version --format=csv,noheader &> /dev/null; then
            DRIVER_VERSION=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)
            log_info "NVIDIA Driver Version: ${DRIVER_VERSION}"
        fi
    else
        log_warning "nvidia-smi not found - CUDA may not be available"
        log_info "Will fall back to CPU (slower)"
    fi

    # nvcc check
    if command -v nvcc &> /dev/null; then
        NVCC_VERSION=$(nvcc --version | grep release | awk '{print $5}' | tr -d ',')
        log_success "CUDA Compiler (nvcc): ${NVCC_VERSION}"
    else
        log_warning "nvcc not found - CUDA toolkit may not be installed"
    fi

    # Check CUDA in Python
    python3 << 'EOF'
try:
    import torch
    if torch.cuda.is_available():
        print(f"[OK] PyTorch CUDA: {torch.version.cuda}")
        print(f"[OK] CUDA devices: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            print(f"     GPU {i}: {props.name} ({props.total_memory / 1e9:.1f} GB)")
    else:
        print("[WARN] PyTorch CUDA not available")
except ImportError:
    print("[INFO] PyTorch not installed yet")
EOF
}

#-------------------------------------------------------------------------------
# Python Environment Setup
#-------------------------------------------------------------------------------

setup_python_env() {
    log_info "Setting up Python environment..."

    # Check if virtual environment exists
    if [[ -d "${VENV_PATH}" ]]; then
        log_info "Virtual environment already exists at ${VENV_PATH}"
        read -p "Recreate? (y/N): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "${VENV_PATH}"
        else
            log_info "Using existing environment"
            source "${VENV_PATH}/bin/activate"
            return
        fi
    fi

    # Create virtual environment
    log_info "Creating virtual environment..."
    python3 -m venv "${VENV_PATH}"

    # Activate
    source "${VENV_PATH}/bin/activate"
    log_success "Virtual environment created and activated"

    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel
}

#-------------------------------------------------------------------------------
# Install Dependencies
#-------------------------------------------------------------------------------

install_dependencies() {
    log_info "Installing Python dependencies..."

    # Activate virtual environment if not already active
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        source "${VENV_PATH}/bin/activate"
    fi

    # Install PyTorch with CUDA support
    log_info "Installing PyTorch..."
    if nvidia-smi &> /dev/null; then
        # CUDA available - install with CUDA support
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    else
        # CPU only
        pip install torch torchvision torchaudio
    fi

    # Install project requirements
    log_info "Installing project requirements..."
    pip install -r "${PROJECT_ROOT}/requirements.txt"

    # Install additional dependencies
    log_info "Installing additional dependencies..."
    pip install \
        accelerate \
        bitsandbytes \
        sentencepiece \
        protobuf \
        huggingface_hub \
        datasets

    # Verify installations
    log_info "Verifying installations..."
    python3 << 'EOF'
import sys
packages = [
    "torch",
    "transformers",
    "diffusers",
    "PIL",
    "numpy",
    "pandas",
    "openai",
    "tqdm"
]
missing = []
for pkg in packages:
    try:
        __import__(pkg.replace("PIL", "PIL.Image").split(".")[0])
        print(f"  [OK] {pkg}")
    except ImportError:
        print(f"  [MISSING] {pkg}")
        missing.append(pkg)
if missing:
    print(f"\nMissing packages: {', '.join(missing)}")
    sys.exit(1)
print("\nAll packages installed successfully!")
EOF

    log_success "Dependencies installed successfully"
}

#-------------------------------------------------------------------------------
# Download Models
#-------------------------------------------------------------------------------

download_models() {
    log_info "Downloading pre-trained models..."

    # Activate virtual environment if not already active
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        source "${VENV_PATH}/bin/activate"
    fi

    python3 << 'EOF'
from huggingface_hub import snapshot_download
import os

models_dir = os.path.expanduser("~/.cache/huggingface/hub")
os.makedirs(models_dir, exist_ok=True)

models_to_download = [
    # CLIP for refusal detection
    ("openai/clip-vit-large-patch14", "CLIP (refusal detection)"),

    # T2I Models (optional - these are large)
    # ("black-forest-labs/FLUX.1-dev", "FLUX.1-dev"),
    # ("stabilityai/stable-diffusion-3.5-large", "SD 3.5 Large"),

    # I2I Models
    ("timbrooks/instruct-pix2pix", "InstructPix2Pix"),

    # VLM for cue retention
    ("Qwen/Qwen2-VL-7B-Instruct", "Qwen2-VL"),
]

print("Downloading essential models...")
for model_id, name in models_to_download:
    try:
        print(f"  Downloading {name}...")
        snapshot_download(
            model_id,
            local_files_only=False,
            resume_download=True
        )
        print(f"  [OK] {name}")
    except Exception as e:
        print(f"  [SKIP] {name}: {e}")

print("\nModel download complete!")
print("Note: Large T2I models (FLUX, SD3.5) will be downloaded on first use.")
EOF

    log_success "Models downloaded"
}

#-------------------------------------------------------------------------------
# Download Datasets
#-------------------------------------------------------------------------------

download_datasets() {
    log_info "Setting up datasets..."

    local data_dir="${PROJECT_ROOT}/data"
    mkdir -p "${data_dir}/ffhq" "${data_dir}/coco"

    # FFHQ download instructions
    cat << 'EOF'

FFHQ Dataset Setup
==================
FFHQ (Flickr-Faces-HQ) is used for I2I source images.

Option 1: Download subset (recommended)
  1. Visit: https://github.com/NVlabs/ffhq-dataset
  2. Download thumbnails (128x128 or 256x256)
  3. Extract ~500 random images to: data/ffhq/

Option 2: Use HuggingFace datasets
  pip install datasets
  python -c "
  from datasets import load_dataset
  ds = load_dataset('nielsr/FFHQ-128', split='train[:500]')
  for i, example in enumerate(ds):
      example['image'].save(f'data/ffhq/ffhq_{i:05d}.png')
  "

EOF

    # COCO download instructions
    cat << 'EOF'

COCO Dataset Setup
==================
COCO is used for I2I source images with diverse scenes.

Option 1: Download subset
  1. Visit: https://cocodataset.org/#download
  2. Download val2017 images
  3. Extract ~500 random images to: data/coco/

Option 2: Use wget
  cd data/coco
  wget http://images.cocodataset.org/zips/val2017.zip
  unzip val2017.zip
  mv val2017/* .
  rmdir val2017
  rm val2017.zip

EOF

    log_info "Dataset directories created at:"
    log_info "  ${data_dir}/ffhq"
    log_info "  ${data_dir}/coco"
}

#-------------------------------------------------------------------------------
# Create Project Structure
#-------------------------------------------------------------------------------

create_structure() {
    log_info "Creating project structure..."

    mkdir -p "${PROJECT_ROOT}"/{logs,checkpoints}
    mkdir -p "${PROJECT_ROOT}/data"/{raw,external,ffhq,coco}
    mkdir -p "${PROJECT_ROOT}/experiments"/{prompts,images,evaluation,results}
    mkdir -p "${PROJECT_ROOT}/paper"/{tables,figures}
    mkdir -p "${PROJECT_ROOT}/figs"

    # Create .env template if not exists
    if [[ ! -f "${PROJECT_ROOT}/.env" ]]; then
        cat > "${PROJECT_ROOT}/.env" << 'EOF'
# ACRB Environment Variables
# Copy this file to .env and fill in your API keys

# LLM API (for prompt expansion)
ACRB_LLM_API_KEY=your_gemini_or_openai_key

# OpenAI API (for VLM cue scoring and DALL-E)
OPENAI_API_KEY=your_openai_key

# HuggingFace API (for downloading gated models)
HF_TOKEN=your_huggingface_token

# Optional: API keys for other services
REPLICATE_API_TOKEN=
FAL_API_KEY=
STABILITY_API_KEY=
EOF
        log_info "Created .env template at ${PROJECT_ROOT}/.env"
        log_warning "Please fill in your API keys in .env"
    fi

    log_success "Project structure created"
}

#-------------------------------------------------------------------------------
# Create Activation Script
#-------------------------------------------------------------------------------

create_activation_script() {
    cat > "${PROJECT_ROOT}/activate.sh" << EOF
#!/bin/bash
# Activate ACRB environment
source "${VENV_PATH}/bin/activate"

# Load environment variables
if [[ -f "${PROJECT_ROOT}/.env" ]]; then
    set -a
    source "${PROJECT_ROOT}/.env"
    set +a
fi

# Add project to PYTHONPATH
export PYTHONPATH="${PROJECT_ROOT}:\${PYTHONPATH:-}"

echo "ACRB environment activated!"
echo "  Python: \$(which python)"
echo "  Project: ${PROJECT_ROOT}"
EOF

    chmod +x "${PROJECT_ROOT}/activate.sh"
    log_success "Created activation script: ${PROJECT_ROOT}/activate.sh"
    log_info "Run 'source activate.sh' to activate the environment"
}

#-------------------------------------------------------------------------------
# Final Check
#-------------------------------------------------------------------------------

final_check() {
    log_info "Running final verification..."

    # Activate environment
    source "${VENV_PATH}/bin/activate"

    # Run verification script
    python3 << 'EOF'
import sys
print("\n" + "="*60)
print("ACRB Environment Verification")
print("="*60 + "\n")

checks_passed = 0
checks_failed = 0

# Check 1: PyTorch
try:
    import torch
    cuda_status = "CUDA" if torch.cuda.is_available() else "CPU"
    print(f"[OK] PyTorch {torch.__version__} ({cuda_status})")
    checks_passed += 1
except Exception as e:
    print(f"[FAIL] PyTorch: {e}")
    checks_failed += 1

# Check 2: Transformers
try:
    import transformers
    print(f"[OK] Transformers {transformers.__version__}")
    checks_passed += 1
except Exception as e:
    print(f"[FAIL] Transformers: {e}")
    checks_failed += 1

# Check 3: Diffusers
try:
    import diffusers
    print(f"[OK] Diffusers {diffusers.__version__}")
    checks_passed += 1
except Exception as e:
    print(f"[FAIL] Diffusers: {e}")
    checks_failed += 1

# Check 4: OpenAI
try:
    import openai
    print(f"[OK] OpenAI {openai.__version__}")
    checks_passed += 1
except Exception as e:
    print(f"[FAIL] OpenAI: {e}")
    checks_failed += 1

# Check 5: ACRB package
try:
    sys.path.insert(0, "/Users/chan/IJCAI26/I2I-T2I-Bias-Refusal")
    import acrb
    print(f"[OK] ACRB package")
    checks_passed += 1
except Exception as e:
    print(f"[FAIL] ACRB package: {e}")
    checks_failed += 1

print("\n" + "-"*60)
print(f"Checks: {checks_passed} passed, {checks_failed} failed")
print("="*60 + "\n")

if checks_failed > 0:
    sys.exit(1)
EOF

    if [[ $? -eq 0 ]]; then
        log_success "All checks passed!"
    else
        log_error "Some checks failed. Please review the output above."
        exit 1
    fi
}

#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------

main() {
    local action="${1:-full}"

    print_banner

    case "${action}" in
        --check)
            check_system
            check_cuda
            ;;
        --models)
            download_models
            ;;
        --data)
            download_datasets
            ;;
        --deps)
            setup_python_env
            install_dependencies
            ;;
        full|--full)
            check_system
            check_cuda
            create_structure
            setup_python_env
            install_dependencies
            download_models
            download_datasets
            create_activation_script
            final_check
            ;;
        --help|-h)
            echo "Usage: $0 [OPTION]"
            echo ""
            echo "Options:"
            echo "  --check     Check system and CUDA environment only"
            echo "  --deps      Install Python dependencies only"
            echo "  --models    Download models only"
            echo "  --data      Setup datasets only"
            echo "  --full      Full setup (default)"
            echo "  --help      Show this help"
            ;;
        *)
            log_error "Unknown option: ${action}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac

    echo ""
    log_success "Setup complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Activate environment:  source activate.sh"
    echo "  2. Configure API keys:    Edit .env"
    echo "  3. Run experiments:       make all"
    echo ""
}

main "$@"
