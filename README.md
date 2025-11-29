# WhisperX Transcription Automation Pipeline

Automated pipeline for transcribing audio files using WhisperX, with support for batch processing, multi-GPU parallel execution, and automated upload to GitHub.

**Platform**: Linux / HPC Clusters (e.g., TAMU Terra)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Directory Structure](#directory-structure)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Usage](#usage)
- [Configuration Reference](#configuration-reference)
- [Troubleshooting](#troubleshooting)

## Overview

This pipeline automates the process of:
1. Downloading audio files from a network share based on Google Sheets tracking
2. Transcribing audio files using WhisperX with word-level timestamps
3. Generating JSON and VTT subtitle files
4. Uploading results to GitHub

## Features

- **Centralized Configuration**: All paths and credentials in one `config.yaml` file
- **WhisperX Integration**: High-quality transcription with word-level timestamps
- **Multi-GPU Support**: Parallel processing across multiple GPUs
- **Automated Downloads**: Fetch files from SMB/CIFS network shares
- **Google Sheets Integration**: Track processing status via spreadsheet
- **GitHub Integration**: Automated upload to repository via pull requests
- **Slurm Support**: Built-in support for HPC cluster job submission

## Directory Structure

```
parent-directory/
├── WhisperX-transcribe-automation/
│   ├── venv/                    #  Python virtual environment (auto-created, gitignored)
│   ├── data/                    # ← Data folder (auto-created)
│   │   ├── oral_input/          #    Input audio files
│   │   └── oral_output/         #    Transcription outputs (json/ and vtts/)
│   ├── config.yaml              # ← Your configuration (gitignored, YOU create this)
│   ├── config.example.yaml      #    Configuration template
│   ├── transcribe.py            #    Core transcription script
│   ├── download_automation_3.py #    Download from network share
│   ├── git_upload.py            #    Upload to GitHub
│   ├── pipeline_2.py            #    Full automated pipeline
│   ├── run_1.slurm              #    Slurm job script
│   ├── setup_environment.sh     # ← Run ONCE for initial setup
│   ├── activate_env.sh          #    Generated activation helper
│   └── requirements.txt         #    Python dependencies
│
└── git_repo/                    # ← Git repository (sibling, auto-created)
```

## Quick Start

For first-time setup, run these commands:

```bash
# 1. Clone the repository
git clone https://github.com/tamulib-dc-labs/WhisperX-transcribe-automation.git
cd WhisperX-transcribe-automation

# 2. Create and configure config.yaml
cp config.example.yaml config.yaml
nano config.yaml  # Edit with your paths and credentials

# 3. Run one-time environment setup (creates venv, installs dependencies)
bash setup_environment.sh

# 4. (Optional) Download WhisperX models for offline use
python d_whisperx.py
```

**That's it!** You're ready to use the pipeline.

For subsequent sessions:
```bash
cd WhisperX-transcribe-automation
source activate_env.sh  # Activates venv and sets environment variables
python pipeline_2.py    # Run the full pipeline
```

---

## Detailed Setup

### Prerequisites

- **System**: Linux or HPC cluster with Slurm
- **Python**: 3.9 or higher (required for pandas 2.x and whisperx)
- **GPU**: CUDA-capable GPU (recommended)
- **Access**: TAMU network or VPN (for file downloads)
- **GitHub**: Account with repository access

### Step-by-Step Installation

#### Step 1: Clone Repository

```bash
cd /path/to/your/workspace
git clone https://github.com/tamulib-dc-labs/WhisperX-transcribe-automation.git
cd WhisperX-transcribe-automation
```

#### Step 2: Create Configuration File

```bash
# Copy the example configuration
cp config.example.yaml config.yaml

# Edit with your settings
nano config.yaml
```

**Required fields** to fill in:
- `paths.hf_home` - HuggingFace cache directory
- `paths.nltk_data` - NLTK data directory  
- `paths.torch_home` - PyTorch cache directory
- `credentials.github_token` - Your GitHub Personal Access Token
bash setup_environment.sh
```

**Output**:
```
Step 0.1: Creating cache directories
  ✓ Creates HF_HOME, NLTK_DATA, TORCH_HOME, PYTHONPATH
Step 0.2: Creating virtual environment
  ✓ Creates venv/
Step 0.3: Installing Python dependencies
  ✓ Installs all requirements
Step 0.4: Creating activation helper
  ✓ Creates activate_env.sh
Step 0.5: Testing imports
  ✓ Verifies installation
```

#### Step 4: Create Data Directories

```bash
bash setup_directories.sh
```

This creates:
- `data/oral_input/` - for input audio files
- `data/oral_output/` - for transcription outputs
- `../git_repo/` - for GitHub repository clone (outside project)

#### Step 5: Download Models (Optional but Recommended)

For offline use, download WhisperX models:

```bash
python d_whisperx.py
```

This will download the model specified in `config.yaml` and alignment models for configured languages.

---

## Usage

### Daily Workflow

**Every time you start a new session:**

```bash
# Navigate to project
cd WhisperX-transcribe-automation

# Activate environment (loads venv + environment variables)
source activate_env.sh
```

### Running the Full Pipeline

```bash
python pipeline_2.py
```

This runs the complete workflow:
1. Clears input/output directories
2. Downloads audio files from network share

3. Submits Slurm job for transcription
4. Monitors job until completion
5. Uploads results to GitHub

### Running Individual Scripts

#### Download Files

```bash
python download_automation_3.py \
  --sheet-url "https://docs.google.com/spreadsheets/d/YOUR_ID/edit" \
  --local-path data/oral_input \
  --max-folders 20
```

#### Transcribe Audio

```bash
# Basic transcription
python transcribe.py data/oral_input data/oral_output

# With options
python transcribe.py data/oral_input data/oral_output \
  --model large-v3 \
  --language en \
  --batch-size 16

# Multi-GPU parallel
python transcribe.py data/oral_input data/oral_output \
  --parallel \
  --num-gpus 2
```

#### Upload to GitHub

```bash
python git_upload.py
```

This creates a new branch, commits files, and provides a pull request URL.

### Slurm Job Submission

The pipeline uses `run_1.slurm` for job submission. To customize:

```bash
nano run_1.slurm
```

Adjust:
- `#SBATCH --gres=gpu:a100:2` - Number of GPUs
- `#SBATCH --time=3:00:00` - Time limit
- `#SBATCH --mem=40G` - Memory allocation

---

## Configuration Reference

### Paths Section

```yaml
paths:
  # Cache directories (use absolute paths)
  hf_home: "/scratch/user/YOUR_NETID/hf_cache"
  nltk_data: "/scratch/user/YOUR_NETID/nltk_data"
  torch_home: "/scratch/user/YOUR_NETID/torch_cache"
  
  # Data directories (relative to project root)
  oral_input: "data/oral_input"
  oral_output: "data/oral_output"
  
  # Git repo (sibling to project)
  git_repo: "../git_repo"
  
  # Scripts (relative or absolute)
  download_script: "download_automation_3.py"
  git_upload_script: "git_upload.py"
  slurm_script: "run_1.slurm"
```

### Credentials Section

```yaml
credentials:
  github_token: "ghp_YOUR_TOKEN_HERE"  # Get from GitHub Settings > Developer Settings > Tokens
  netid_username: "your_netid"
  smb_password: ""  # Leave empty to be prompted
```

**Creating a GitHub Token:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select `repo` scope
4. Copy token and paste in config.yaml

### WhisperX Settings

```yaml
whisperx:
  model_name: "large-v3"  # Options: tiny, base, small, medium, large-v2, large-v3, turbo
  batch_size: 16          # Adjust based on GPU memory
  compute_type: "float16" # float16 (GPU) or float32 (CPU)
  language: null          # e.g., "en", "es", or null for auto-detect
  
  vtt:
    max_line_width: 42
    max_line_count: 2
    highlight_words: false
  
  parallel:
    enabled: false
    num_gpus: null  # null = use all available
```

### Pipeline Settings

```yaml
pipeline:
  check_interval_mins: 5
  max_folders: 20
  module_load_cmd: "ml GCCcore/10.3.0 FFmpeg CUDA Python"
  venv_activate: "venv/bin/activate"
```

---

## Troubleshooting

### Config file not found
```
FileNotFoundError: config.yaml not found
```
**Solution**: `cp config.example.yaml config.yaml` and edit with your settings

### Pandas dependency conflict
```
ERROR: Cannot install pandas and whisperx because of conflicting dependencies
```
**Solution**: Already fixed in `requirements.txt` with `pandas>=2.2.3,<2.3.0`

### Pandas dependency conflict
```
ERROR: No matching distribution found for pandas<2.3.0,>=2.2.3
```
**Solution**: 
```bash
# Your Python version is too old. Load Python 3.9+
ml GCCcore/10.3.0 Python/3.9

# Remove old venv and recreate
rm -rf venv
bash setup_environment.sh
```

### GitHub authentication failed
```
Authentication failed
```
**Solution**: 
- Check `github_token` in `config.yaml`
- Ensure token has `repo` scope
- Verify token hasn't expired

### CUDA out of memory
```
RuntimeError: CUDA out of memory
```
**Solution**:
- Reduce `batch_size` in config.yaml
- Use smaller model (e.g., `medium` instead of `large-v3`)
- Use `--parallel` with fewer GPUs per worker

### Module not found
```
ModuleNotFoundError: No module named 'whisperx'
```
**Solution**:
```bash
source activate_env.sh  # Activate environment first
pip install -r requirements.txt  # Reinstall if needed
```

### SMB connection failed
```
Folder not found on Network
```
**Solution**:
- Verify you're on TAMU network or connected via VPN
- Check SMB settings in `config.yaml`
- Verify NetID credentials are correct

---

## Output Structure

After transcription:

```
data/
├── oral_input/
│   ├── folder1/
│   │   └── audio1.mp3
│   └── folder2/
│       └── audio2.wav
│
└── oral_output/
    ├── json/
    │   ├── audio1.json  ← Word-level timestamps
    │   └── audio2.json
    └── vtts/
        ├── audio1.vtt   ← Formatted subtitles
        └── audio2.vtt
```

**JSON format** (with word-level timestamps):
```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "Hello world",
      "words": [
        {"word": "Hello", "start": 0.0, "end": 0.5, "score": 0.99},
        {"word": "world", "start": 0.6, "end": 2.5, "score": 0.98}
      ]
    }
  ]
}
```

---

## Environment Variables

Override config values with environment variables:

```bash
export HF_HOME="/custom/path/to/cache"
export GITHUB_TOKEN="your-token"
export SMB_PASSWORD="your-password"

python script.py
```

---

## Security

⚠️ **IMPORTANT**:
- Never commit `config.yaml` to version control (already in `.gitignore`)
- Keep your GitHub token secure
- Regularly rotate your GitHub tokens
- Use environment variables for sensitive data in production

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `setup_environment.sh` | One-time setup: creates venv, installs dependencies |
| `activate_env.sh` | Activate environment (run at start of each session) |
| `pipeline_2.py` | Full automated pipeline |
| `transcribe.py` | Core transcription using WhisperX |
| `download_automation_3.py` | Download files from network share |
| `git_upload.py` | Upload results to GitHub |
| `d_whisperx.py` | Download WhisperX models for offline use |
| `run_1.slurm` | Slurm job script for HPC clusters |
| `config.py` | Configuration loader (used by all scripts) |

---

## Getting Help

```bash
# Script-specific help
python transcribe.py --help
python download_automation_3.py --help

# Check configuration
python -c "from config import load_config; load_config()"
```

---

## License

[Add your license information here]
