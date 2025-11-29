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

# Python venv
source $SCRATCH/libraries/dlvenv/bin/activate

#specify package paths
export PYTHONPATH=/scratch/user/jvk_chaitanya/python_packages:$PYTHONPATH

# Set HuggingFace cache directory to your scratch space
export HF_HOME=/scratch/user/jvk_chaitanya/hf_cache

export LD_LIBRARY_PATH=/scratch/user/jvk_chaitanya/python_packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH

export NLTK_DATA=/scratch/user/jvk_chaitanya/nltk_data

mkdir -p $NLTK_DATA


# scripts or executables

# IMPORTANT: Enable offline mode to prevent internet access attempts
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

python /scratch/user/jvk_chaitanya/libraries/speech_text/transcribe.py \
    --model "large-v3" \
    --model-dir "/scratch/user/jvk_chaitanya/hf_cache/hub/models--Systran--faster-whisper-large-v3/snapshots/edaa852ec7e145841d8ffdb056a99866b5f0a478" \
    --language "en" \
    --parallel \
    "/scratch/user/jvk_chaitanya/libraries/speech_text/oral_input/" \
    "/scratch/user/jvk_chaitanya/libraries/speech_text/oral_output/"