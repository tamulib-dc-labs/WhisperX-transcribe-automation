#!/bin/bash
##NECESSARY JOB SPECIFICATIONS
#SBATCH --job-name=speech_transcribe       #Set the job name to "JobExample4"
#SBATCH --time=3:00:00              #Set the wall clock limit to 1hr and 30min
#SBATCH --ntasks=2                   #Request 1 task
#SBATCH --mem=40G                  #Request 2560MB (2.5GB) per task
#SBATCH --output=transcribe_Out.%j      #Send stdout/err to "Example4Out.[jobID]"
#SBATCH --gres=gpu:a100:2                 #Request 1 GPU per node can be 1 or 2
#SBATCH --partition=gpu              #Request the GPU partition/queue

# modules needed for running DL jobs. Module restore will also work
#module restore dl
ml GCCcore/10.3.0 FFmpeg CUDA Python

# Python venv - PATH WILL BE INJECTED BY PIPELINE
source {{VENV_ACTIVATE_PATH}}

#specify package paths - PATHS WILL BE INJECTED BY PIPELINE
export PYTHONPATH={{PYTHON_CACHE}}:$PYTHONPATH

# Set HuggingFace cache directory
export HF_HOME={{HF_CACHE}}

# Set cuDNN library path - use pip-installed cuDNN (nvidia-cudnn-cu12)
# Must be BEFORE $LD_LIBRARY_PATH to take priority
export LD_LIBRARY_PATH={{PYTHON_CACHE}}/nvidia/cudnn/lib:$LD_LIBRARY_PATH

export NLTK_DATA={{NLTK_CACHE}}

mkdir -p $NLTK_DATA


# scripts or executables

# IMPORTANT: Enable offline mode to prevent internet access attempts
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

# PATHS WILL BE INJECTED BY PIPELINE
python {{TRANSCRIBE_SCRIPT}} \
    --model "{{WHISPER_MODEL}}" \
    --parallel \
    "{{ORAL_INPUT_PATH}}/" \
    "{{ORAL_OUTPUT_PATH}}/"