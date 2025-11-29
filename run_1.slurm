#!/bin/bash
##NECESSARY JOB SPECIFICATIONS
#SBATCH --job-name=whisperx_transcribe
#SBATCH --time=3:00:00              # Wall clock limit
#SBATCH --ntasks=2                  # Number of tasks
#SBATCH --mem=40G                   # Memory per node
#SBATCH --output=transcribe_Out.%j  # Output file
#SBATCH --gres=gpu:a100:2           # Request 2 A100 GPUs
#SBATCH --partition=gpu             # GPU partition/queue

##############################################################################
# WhisperX Transcription Job - Uses centralized config.yaml
##############################################################################

echo "================================================"
echo "WhisperX Transcription Job Started"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "GPUs: $CUDA_VISIBLE_DEVICES"
echo "================================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load Python from config (simple parsing)
if [ -f "config.yaml" ]; then
    HF_HOME=$(grep "hf_home:" config.yaml | awk '{print $2}' | tr -d '"' | tr -d "'")
    NLTK_DATA=$(grep "nltk_data:" config.yaml | awk '{print $2}' | tr -d '"' | tr -d "'")
    TORCH_HOME=$(grep "torch_home:" config.yaml | awk '{print $2}' | tr -d '"' | tr -d "'")
    PYTHONPATH_VALUE=$(grep "pythonpath:" config.yaml | awk '{print $2}' | tr -d '"' | tr -d "'")
    VENV_ACTIVATE=$(grep "venv_activate:" config.yaml | awk '{print $2}' | tr -d '"' | tr -d "'")
    MODULE_LOAD=$(grep "module_load_cmd:" config.yaml | awk '{print $2}' | tr -d '"' | tr -d "'" | sed 's/^"\(.*\)"$/\1/')
    ORAL_INPUT=$(grep "oral_input:" config.yaml | awk '{print $2}' | tr -d '"' | tr -d "'")
    ORAL_OUTPUT=$(grep "oral_output:" config.yaml | awk '{print $2}' | tr -d '"' | tr -d "'")
else
    echo "ERROR: config.yaml not found!"
    exit 1
fi

# Load modules
echo "Loading modules..."
# modules needed for running DL jobs. Module restore will also work
#module restore dl
ml GCCcore/10.3.0 FFmpeg CUDA Python/3.9

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_ACTIVATE"

# Set environment variables from config
export HF_HOME="$HF_HOME"
export NLTK_DATA="$NLTK_DATA"
export TORCH_HOME="$TORCH_HOME"
export PYTHONPATH="$PYTHONPATH_VALUE${PYTHONPATH:+:$PYTHONPATH}"

# Create NLTK data directory if it doesn't exist
mkdir -p "$NLTK_DATA"

echo "Environment variables:"
echo "  HF_HOME=$HF_HOME"
echo "  NLTK_DATA=$NLTK_DATA"
echo "  TORCH_HOME=$TORCH_HOME"
echo "  PYTHONPATH=$PYTHONPATH"
echo ""

# IMPORTANT: Enable offline mode to prevent internet access attempts
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

# Make CUDA_VISIBLE_DEVICES dynamic based on allocated GPUs
# This ensures compatibility whether 1 or 2 GPUs are allocated
if [ -n "$SLURM_JOB_GPUS" ]; then
    # Use Slurm's GPU allocation
    export CUDA_VISIBLE_DEVICES=$SLURM_JOB_GPUS
    echo "Using GPUs: $CUDA_VISIBLE_DEVICES"
else
    # Fallback if SLURM_JOB_GPUS not set
    echo "Warning: SLURM_JOB_GPUS not set, using default GPU configuration"
fi

# Convert relative paths to absolute if needed
if [[ "$ORAL_INPUT" != /* ]]; then
    ORAL_INPUT="$SCRIPT_DIR/$ORAL_INPUT"
fi
if [[ "$ORAL_OUTPUT" != /* ]]; then
    ORAL_OUTPUT="$SCRIPT_DIR/$ORAL_OUTPUT"
fi

echo "Input directory: $ORAL_INPUT"
echo "Output directory: $ORAL_OUTPUT"
echo ""

# Run transcription
echo "Starting transcription..."
python "$SCRIPT_DIR/transcribe.py" \
    --model "large-v3" \
    --language "en" \
    --parallel \
    --num-gpus 2 \
    "$ORAL_INPUT" \
    "$ORAL_OUTPUT"

EXIT_CODE=$?

echo ""
echo "================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "Transcription completed successfully!"
else
    echo "Transcription failed with exit code: $EXIT_CODE"
fi
echo "Job ID: $SLURM_JOB_ID"
echo "================================================"

exit $EXIT_CODE