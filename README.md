# WhisperX Transcription Automation Pipeline

Automated pipeline for transcribing audio files using WhisperX, with support for batch processing, multi-GPU parallel execution, and automated upload to GitHub.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Directory Structure](#directory-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Individual Scripts](#individual-scripts)
  - [Full Pipeline](#full-pipeline)
- [Scripts Description](#scripts-description)
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
- **VTT Formatting**: Customizable subtitle formatting (line width, line count)
- **Batch Processing**: Process multiple folders automatically

## Directory Structure

The project uses the following directory organization:

```
parent-directory/
├── WhisperX-transcribe-automation/    # Main project directory
│   ├── venv/                          # Python virtual environment (gitignored)
│   ├── data/                          # Data folder (created during setup)
│   │   ├── oral_input/                # Input audio files
│   │   └── oral_output/               # Transcription outputs
│   │       ├── json/                  # JSON transcriptions
│   │       └── vtts/                  # VTT subtitle files
│   ├── config.py                      # Configuration loader
│   ├── config.yaml                    # Your configuration (gitignored)
│   ├── config.example.yaml            # Configuration template
│   ├── transcribe.py                  # Transcription script
│   ├── download_automation_3.py       # Download script
│   ├── git_upload.py                  # Upload script
│   ├── pipeline_2.py                  # Full pipeline
│   ├── d_whisperx.py                  # Model downloader
│   ├── setup_environment.sh           # Step 0 setup script
│   ├── setup_directories.sh           # Directory creation script
│   ├── activate_env.sh                # Environment activation helper
│   ├── run_1.slurm                    # Slurm job script
│   ├── requirements.txt               # Python dependencies
│   └── README.md                      # This file
│
└── git_repo/                          # Git repository (sibling to project)
    └── (cloned repository for uploads)
```

**Key Points:**
- `data/` folder keeps all input/output organized in one place
- `git_repo/` is outside the project to avoid conflicts
- Both folders are created automatically during setup
- Paths in `config.yaml` use relative paths for portability

## Prerequisites

### System Requirements
- Python 3.8+
- CUDA-capable GPU (recommended for faster processing)
- Access to TAMU network shares (for download functionality)
- GitHub account with repository access

### HPC Cluster (Optional)
If running on an HPC cluster like TAMU Terra:
- Slurm job scheduler
- Module system (for loading dependencies)
- Scratch storage space

## Installation

### Step 0: One-Time Environment Setup (Run Once)

**This step sets up your Python environment, cache directories, and installs all dependencies. Run this only once during initial setup.**

#### Prerequisites for Step 0:
- Python 3.8+ installed and in PATH
- Git installed (to clone the repository)

#### 0.1: Clone the Repository

```bash
cd /path/to/your/workspace
git clone <repository-url>
cd WhisperX-transcribe-automation
```

#### 0.2: Configure Settings

```bash
# Copy the example config
cp config.example.yaml config.yaml

# Edit config.yaml with your paths and credentials
nano config.yaml  # or use your preferred editor
```

**Important**: Make sure to fill in at least these required fields in `config.yaml`:
- `paths.hf_home` - HuggingFace cache directory
- `paths.nltk_data` - NLTK data directory
- `paths.torch_home` - PyTorch cache directory
- `paths.pythonpath` - Python packages directory
- `pipeline.venv_activate` - Virtual environment path (default: `venv/bin/activate` for local venv)

#### 0.3: Run Environment Setup Script

This script will automatically:
- Create all cache directories (HF_HOME, NLTK_DATA, TORCH_HOME, PYTHONPATH)
- Create a Python virtual environment
- Activate the environment with proper environment variables
- Install all dependencies from requirements.txt
- Test that all imports work correctly
- Create an `activate_env.sh` helper script for future use

```bash
# Linux/Mac/HPC Cluster
bash setup_environment.sh

# Windows (PowerShell - Run as Administrator may be needed)
.\setup_environment.ps1
```

**What this does:**
```
Step 0.1: Creating cache directories
  ✓ Creates HF_HOME, NLTK_DATA, TORCH_HOME, PYTHONPATH
  
Step 0.2: Creating virtual environment
  ✓ Creates venv at specified location
  
Step 0.3: Installing Python dependencies
  ✓ Activates venv
  ✓ Sets environment variables
  ✓ Upgrades pip
  ✓ Installs requirements.txt
  
Step 0.4: Creating activation helper
  ✓ Creates activate_env.sh for future sessions
  
Step 0.5: Testing imports
  ✓ Verifies all packages installed correctly
```

---

### Step 1: Create Directory Structure (Automated)

**Quick Setup Option:**

Run the automated setup script to create data and git_repo directories:

```bash
# Linux/Mac/HPC
bash setup_directories.sh

# Windows (PowerShell)
.\setup_directories.ps1
```

This will create the `data/` folder and `../git_repo/` directory automatically.

---

### Alternative: Manual Installation (If you prefer manual setup)

If you don't want to use the automated `setup_environment.sh`, follow these steps:

```bash
cd /path/to/your/workspace
git clone <repository-url>
cd WhisperX-transcribe-automation
```

**Quick Setup Option:**

Run the automated setup script to create directories:

```bash
# Linux/Mac/HPC
bash setup_directories.sh

# Windows (PowerShell)
.\setup_directories.ps1
```

This will create the `data/` folder and `../git_repo/` directory automatically.

#### Option A: Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Option B: On HPC Cluster

```bash
# Load required modules
ml GCCcore/10.3.0 FFmpeg CUDA Python

# Create virtual environment in scratch
python -m venv $SCRATCH/libraries/dlvenv

# Activate
source $SCRATCH/libraries/dlvenv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### Step 2: Activate Environment (For Future Sessions)

After the one-time Step 0 setup, for all future sessions, activate your environment using:

```bash
# Linux/Mac/HPC
source activate_env.sh

# Windows (PowerShell)
.\activate_env.ps1
```

This automatically:
- Activates the virtual environment
- Sets HF_HOME, NLTK_DATA, TORCH_HOME environment variables
- Sets PYTHONPATH

---

### Step 3: Download WhisperX Models (Optional - for offline use)

```bash
# Run the model download script
python d_whisperx.py
```


This will download:
- WhisperX transcription model (configured in config.yaml)
- Alignment models for specified languages

## Configuration

Configuration was already done in **Step 0.2** above. If you need to make changes:

### 1. Edit Configuration File

Open `config.yaml` and update fields as needed:

#### Paths
```yaml
paths:
  hf_home: "/your/path/to/hf_cache"              # HuggingFace cache
  pythonpath: "/your/path/to/python_packages"    # Python packages
  
  # Data directories (relative or absolute paths)
  oral_input: "data/oral_input"                  # Input audio directory
  oral_output: "data/oral_output"                # Output directory
  
  # Git repo (sibling to project directory)
  git_repo: "../git_repo"                        # Git repo clone location
  
  # Script paths (can be relative or absolute)
  download_script: "download_automation_3.py"
  slurm_script: "/full/path/to/run_1.slurm"      # If using Slurm
  git_upload_script: "git_upload.py"
```

**Note:** You can use relative paths (like `data/oral_input`) or absolute paths. Relative paths are resolved from the project directory.

#### Credentials (⚠️ IMPORTANT)
```yaml
credentials:
  github_token: "ghp_YOUR_ACTUAL_TOKEN_HERE"     # Get from GitHub Settings
  netid_username: "your_netid"                   # Your NetID
  smb_password: ""                               # Leave empty to prompt
```

To create a GitHub token:
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select `repo` scope
4. Copy the token and paste it in `config.yaml`

#### GitHub Repository
```yaml
github:
  owner: "repository-owner"                      # GitHub username/org
  repo_name: "repository-name"                   # Repository name
  auth_username: "your-github-username"
```

#### Other Settings
Review and adjust as needed:
- WhisperX model settings
- SMB server details
- Google Sheets URL
- Pipeline settings

### 2. Re-test Configuration (if changed)

If you modified `config.yaml` after Step 0, verify it still works:

```bash
# Activate environment first
source activate_env.sh  # or .\activate_env.ps1 on Windows

# Test config loading
python -c "from config import load_config; cfg = load_config(); print('Config loaded successfully!')"
```

## Usage

### Individual Scripts

#### 1. Download Audio Files

Download audio files from network share based on Google Sheets:

```bash
python download_automation_3.py \
  --sheet-url "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit" \
  --local-path ./oral_input \
  --max-folders 20
```

If credentials are in `config.yaml`, they'll be used automatically. Otherwise, provide them:

```bash
python download_automation_3.py \
  --sheet-url "URL" \
  --local-path ./oral_input \
  --username your_netid \
  --password your_password \
  --server cifs.library.tamu.edu \
  --share digital_project_management \
  --base-path "edge-grant/GB_38253_MP3s"
```

#### 2. Transcribe Audio Files

Transcribe all audio files in a directory:

```bash
python transcribe.py input_directory output_directory
```

**With options:**

```bash
python transcribe.py ./oral_input ./oral_output \
  --model large-v3 \
  --batch-size 16 \
  --language en \
  --max-line-width 42 \
  --max-line-count 2
```

**Multi-GPU parallel processing:**

```bash
python transcribe.py ./oral_input ./oral_output \
  --parallel \
  --num-gpus 4 \
  --model large-v3
```

#### 3. Upload to GitHub

Upload transcribed files to GitHub:

```bash
python git_upload.py
```

This will:
- Create a new branch with timestamp
- Copy files from `oral_output` to `git_repo`
- Commit and push changes
- Provide a pull request URL

#### 4. Download Models Only

Download WhisperX models for offline use:

```bash
python d_whisperx.py
```

### Full Pipeline

Run the complete automated pipeline (download → transcribe → upload):

```bash
python pipeline_2.py
```

**What the pipeline does:**
1. Loads modules and activates virtual environment
2. Sets up Python environment variables
3. Clears input/output directories
4. Downloads audio files from network share
5. Submits Slurm job for transcription (or runs locally)
6. Monitors job status
7. Uploads results to GitHub

**For Slurm clusters:**

You may need to update `run_1.slurm` with your job configuration:
- Number of GPUs
- Memory requirements
- Time limit
- Module loads

## Scripts Description

### Core Scripts

| Script | Purpose |
|--------|---------|
| `config.py` | Configuration loader (loads `config.yaml`) |
| `download_automation_3.py` | Downloads audio files from network share |
| `transcribe.py` | Transcribes audio using WhisperX |
| `git_upload.py` | Uploads results to GitHub |
| `pipeline_2.py` | Orchestrates the full pipeline |
| `d_whisperx.py` | Downloads WhisperX models |

### Configuration Files

| File | Purpose |
|------|---------|
| `config.yaml` | **Your actual configuration** (gitignored) |
| `config.example.yaml` | Template with documentation |
| `.gitignore` | Prevents committing sensitive data |
| `requirements.txt` | Python dependencies |

## Output Structure

After transcription, files are organized as:

```
data/
├── oral_input/                # Input audio files
│   ├── folder1/
│   │   ├── audio1.mp3
│   │   └── audio2.mp3
│   └── folder2/
│       └── audio3.wav
│
└── oral_output/               # Generated transcriptions
    ├── json/
    │   ├── audio1.json
    │   ├── audio2.json
    │   └── audio3.json
    └── vtts/
        ├── audio1.vtt
        ├── audio2.vtt
        └── audio3.vtt
```

### JSON Format

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

## Troubleshooting

### Common Issues

#### 1. **Config file not found**
```
FileNotFoundError: config.yaml not found
```
**Solution**: Copy `config.example.yaml` to `config.yaml` and fill in your values.

#### 2. **GitHub authentication failed**
```
Authentication failed
```
**Solution**: 
- Verify your `github_token` in `config.yaml`
- Ensure the token has `repo` permissions
- Check that the token hasn't expired

#### 3. **CUDA out of memory**
```
RuntimeError: CUDA out of memory
```
**Solution**: 
- Reduce `batch_size` in config or command-line
- Use smaller model (`medium` instead of `large-v3`)
- Process fewer files at once

#### 4. **SMB connection failed**
```
Folder not found on Network
```
**Solution**:
- Verify you're on TAMU network or VPN
- Check `smb` settings in `config.yaml`
- Verify your NetID credentials

#### 5. **Module not found (HPC)**
```
ModuleNotFoundError: No module named 'whisperx'
```
**Solution**:
- Activate virtual environment: `source $SCRATCH/libraries/dlvenv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`
- Check `PYTHONPATH` is set correctly

### Environment Variables

You can override config values with environment variables:

```bash
export GITHUB_TOKEN="your-token"
export SMB_PASSWORD="your-password"
export HF_HOME="/path/to/cache"

python script.py
```

### Getting Help

For more information on individual scripts:

```bash
python transcribe.py --help
python download_automation_3.py --help
```

## Security Notes

⚠️ **IMPORTANT**:
- Never commit `config.yaml` to version control
- Keep your GitHub token secure
- Use environment variables for sensitive data in production
- Regularly rotate your GitHub tokens

## License

[Add your license information here]

## Support

For issues or questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review script-specific help with `--help` flag
- Consult the configuration examples in `config.example.yaml`
