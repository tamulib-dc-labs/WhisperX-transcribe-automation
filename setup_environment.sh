#!/bin/bash
# Step 0: One-time environment setup for WhisperX Automation Pipeline
# This script creates venv, initializes cache paths, and installs requirements

set -e  # Exit on error

echo "================================================"
echo "Step 0: Environment Setup (One-time)"
echo "================================================"
echo ""

# Load Python 3.9+ module (required for pandas 2.x and whisperx)
echo "Loading Python 3.9 module..."
ml GCCcore/10.3.0 Python/3.9

# Verify Python version
PYTHON_VERSION=$(python --version 2>&1)
echo "Python version: $PYTHON_VERSION"
echo ""

# Load configuration
if [ ! -f "config.yaml" ]; then
    echo "Error: config.yaml not found!"
    echo "Please copy config.example.yaml to config.yaml and fill in your settings."
    exit 1
fi

# Parse config.yaml to get paths (simple grep-based parsing)
HF_HOME=$(grep "hf_home:" config.yaml | awk '{print $2}' | tr -d '"' | tr -d "'")
NLTK_DATA=$(grep "nltk_data:" config.yaml | awk '{print $2}' | tr -d '"' | tr -d "'")
TORCH_HOME=$(grep "torch_home:" config.yaml | awk '{print $2}' | tr -d '"' | tr -d "'")
PYTHONPATH_VALUE=$(grep "pythonpath:" config.yaml | awk '{print $2}' | tr -d '"' | tr -d "'")
VENV_ACTIVATE=$(grep "venv_activate:" config.yaml | awk '{print $2}' | tr -d '"' | tr -d "'" | sed 's/\$SCRATCH/$SCRATCH/')
VENV_PATH=$(echo "$VENV_ACTIVATE" | sed 's|/bin/activate||' | sed 's|\\Scripts\\activate||')

# Convert relative venv path to absolute if needed
if [[ "$VENV_PATH" != /* ]] && [[ "$VENV_PATH" != \$* ]]; then
    VENV_PATH="$(pwd)/$VENV_PATH"
    VENV_ACTIVATE="$VENV_PATH/bin/activate"
fi

echo "Configuration loaded from config.yaml"
echo "  HF_HOME: $HF_HOME"
echo "  NLTK_DATA: $NLTK_DATA"
echo "  TORCH_HOME: $TORCH_HOME"
echo "  PYTHONPATH: $PYTHONPATH_VALUE"
echo "  Virtual Environment: $VENV_PATH"
echo ""

# Function to create directory if it doesn't exist
create_dir() {
    if [ ! -d "$1" ]; then
        echo "Creating directory: $1"
        mkdir -p "$1"
    else
        echo "Directory already exists: $1"
    fi
}

# Step 0.1: Create cache directories
echo "================================================"
echo "Step 0.1: Creating cache directories"
echo "================================================"
create_dir "$HF_HOME"
create_dir "$NLTK_DATA"
create_dir "$TORCH_HOME"
create_dir "$PYTHONPATH_VALUE"
echo ""

# Step 0.2: Create virtual environment
echo "================================================"
echo "Step 0.2: Creating virtual environment"
echo "================================================"
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment at: $VENV_PATH"
    python3 -m venv "$VENV_PATH"
    echo "✓ Virtual environment created"
else
    echo "Virtual environment already exists at: $VENV_PATH"
fi
echo ""

# Step 0.3: Activate virtual environment and install requirements
echo "================================================"
echo "Step 0.3: Installing Python dependencies"
echo "================================================"
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Set environment variables for this session
export HF_HOME="$HF_HOME"
export NLTK_DATA="$NLTK_DATA"
export TORCH_HOME="$TORCH_HOME"
export PYTHONPATH="$PYTHONPATH_VALUE${PYTHONPATH:+:$PYTHONPATH}"

echo "Environment variables set:"
echo "  HF_HOME=$HF_HOME"
echo "  NLTK_DATA=$NLTK_DATA"
echo "  TORCH_HOME=$TORCH_HOME"
echo "  PYTHONPATH=$PYTHONPATH"
echo ""

# Upgrade pip first
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "✓ All dependencies installed"
echo ""

# Step 0.4: Create environment activation helper
echo "================================================"
echo "Step 0.4: Creating activation helper script"
echo "================================================"

cat > activate_env.sh << 'EOF'
#!/bin/bash
# Helper script to activate environment with all required variables

# Load configuration
if [ ! -f "config.yaml" ]; then
    echo "Error: config.yaml not found!"
    exit 1
fi

HF_HOME=$(grep "hf_home:" config.yaml | awk '{print $2}' | tr -d '"' | tr -d "'")
NLTK_DATA=$(grep "nltk_data:" config.yaml | awk '{print $2}' | tr -d '"' | tr -d "'")
TORCH_HOME=$(grep "torch_home:" config.yaml | awk '{print $2}' | tr -d '"' | tr -d "'")
PYTHONPATH_VALUE=$(grep "pythonpath:" config.yaml | awk '{print $2}' | tr -d '"' | tr -d "'")
VENV_PATH=$(grep "venv_activate:" config.yaml | awk '{print $2}' | tr -d '"' | tr -d "'" | sed 's|/bin/activate||')

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Set environment variables
export HF_HOME="$HF_HOME"
export NLTK_DATA="$NLTK_DATA"
export TORCH_HOME="$TORCH_HOME"
export PYTHONPATH="$PYTHONPATH_VALUE${PYTHONPATH:+:$PYTHONPATH}"

echo "Environment activated!"
echo "  Virtual env: $VENV_PATH"
echo "  HF_HOME: $HF_HOME"
echo "  NLTK_DATA: $NLTK_DATA"
echo "  TORCH_HOME: $TORCH_HOME"
echo "  PYTHONPATH: $PYTHONPATH"
EOF

chmod +x activate_env.sh
echo "✓ Created activate_env.sh"
echo ""

# Step 0.5: Test imports
echo "================================================"
echo "Step 0.5: Testing Python imports"
echo "================================================"
python -c "import yaml; print('✓ PyYAML')"
python -c "import torch; print('✓ PyTorch')"
python -c "import whisperx; print('✓ WhisperX')"
python -c "import pandas; print('✓ Pandas')"
python -c "from config import load_config; print('✓ Config loader')"
echo ""

echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Your environment is ready to use."
echo ""
echo "To activate the environment in future sessions, run:"
echo "  source activate_env.sh"
echo ""
echo "Next steps:"
echo "  1. (Optional) Download WhisperX models:"
echo "     python d_whisperx.py"
echo ""
echo "  2. Run the full pipeline:"
echo "     python pipeline_2.py"
echo ""
echo "  OR run individual scripts:"
echo "     python download_automation_3.py --help"
echo "     python transcribe.py --help"
echo "     python git_upload.py"
echo ""
