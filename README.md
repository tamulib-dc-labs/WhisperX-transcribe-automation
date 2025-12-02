# WhisperX Transcription Automation Pipeline

An automated batch processing pipeline for transcribing audio files using WhisperX, with integrated Google Sheets tracking, SMB network share downloads, and GitHub upload capabilities.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Pipeline Workflow](#pipeline-workflow)
- [Individual Scripts](#individual-scripts)
- [Troubleshooting](#troubleshooting)

## Overview

This pipeline automates the entire workflow of:
1. Reading incomplete tasks from a Google Sheet
2. Downloading audio files from an SMB network share
3. Transcribing audio files using WhisperX with GPU acceleration
4. Uploading results (JSON and VTT files) to a GitHub repository

The pipeline is designed for high-performance computing (HPC) environments with SLURM job scheduling but can be adapted for other systems.

## Features

- ✅ **Centralized Configuration**: All settings in one place (`pipeline_2.py`)
- ✅ **Google Sheets Integration**: Track processing status and manage queues
- ✅ **SMB Network Share Support**: Direct download from network shares (CIFS)
- ✅ **GPU-Accelerated Transcription**: WhisperX with word-level timestamps
- ✅ **Automated Git Upload**: Creates pull requests with timestamped branches
- ✅ **SLURM Job Management**: Automated job submission and monitoring
- ✅ **External Git Repository**: Git operations happen outside working directory
- ✅ **Modular Architecture**: Each component can be run independently

## System Requirements

### Hardware
- CUDA-capable GPU(s) (recommended: NVIDIA GPUs with 16GB+ VRAM)
- Sufficient storage for audio files and transcriptions

### Software
- Python 3.8+
- CUDA Toolkit (if using GPU)
- Git
- SLURM (for HPC environments)
- Required Python packages (see `requirements.txt`)

### Network Access
- Access to SMB/CIFS network shares
- GitHub repository access with personal access token
- Google Sheets API access (public sheets)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/tamulib-dc-labs/WhisperX-transcribe-automation.git
cd WhisperX-transcribe-automation
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv whisperx_env
source whisperx_env/bin/activate  # On Windows: whisperx_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Install WhisperX
```bash
pip install whisperx
```

### 4. Download Models (Optional - for offline use)
```bash
python d_whisperx.py
```

## Configuration

All configuration is centralized in **`pipeline_2.py`** at the top of the file. Edit these variables according to your setup:

### Automatic Path Configuration (No User Changes Needed)
These paths are **automatically configured** and don't require user modification:

```python
# Automatically set to the directory containing pipeline_2.py
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))

# All scripts automatically reference WORKING_DIR
DOWNLOAD_SCRIPT_PATH = f"{WORKING_DIR}/download_automation_3.py"
MODEL_DOWNLOAD_SCRIPT_PATH = f"{WORKING_DIR}/d_whisperx.py"
TRANSCRIBE_SCRIPT_PATH = f"{WORKING_DIR}/transcribe.py"
GIT_UPLOAD_SCRIPT_PATH = f"{WORKING_DIR}/git_upload.py"
SLURM_JOB_PATH = f"{WORKING_DIR}/run_1.slurm"

# Git repository automatically set to parent directory
GIT_REPO_PATH = os.path.join(os.path.dirname(WORKING_DIR), "edge-grant-json-and-vtts")
```

**Directory Structure:**
```
parent_directory/
├── WhisperX-transcribe-automation/  ← WORKING_DIR (this repo)
│   ├── pipeline_2.py
│   ├── download_automation_3.py
│   ├── transcribe.py
│   ├── git_upload.py
│   ├── d_whisperx.py
│   ├── run_1.slurm
│   ├── requirements.txt
│   └── data/
│       ├── oral_input/
│       └── oral_output/
└── edge-grant-json-and-vtts/        ← GIT_REPO_PATH (output repo)
```

### Data Directories (Automatically Created)
```python
DATA_FOLDER = "data"  # Folder name for data (created under WORKING_DIR)
ORAL_INPUT_FOLDER = "oral_input"   # Input folder (under data/)
ORAL_OUTPUT_FOLDER = "oral_output" # Output folder (under data/)
# Results in: WORKING_DIR/data/oral_input and WORKING_DIR/data/oral_output
```

### SMB Network Share Settings
```python
SMB_SERVER = "your.smb.server.com"
SMB_SHARE = "share_name"
SMB_BASE_PATH = "path/inside/share"
SMB_USERNAME = "your_username"
SMB_PASSWORD = ""  # Leave empty to prompt, or set via environment variable
```

### Google Sheets Settings
```python
SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
MAX_FOLDERS = 20  # Maximum folders to process per run
```

### GitHub Settings
```python
GIT_OWNER = "repository-owner"
GIT_REPO_NAME = "repository-name"
GIT_USERNAME = "your-github-username"
GIT_TOKEN = "your-github-token"  # Personal Access Token with repo permissions
```

### Cache and Model Directories
```python
# You can customize these paths or leave them as default
# These directories store downloaded models and cache data to avoid re-downloading
CACHE_DIR = "/path/to/cache"  # Main cache directory
HF_CACHE = "/path/to/cache/huggingface"  # HuggingFace models cache
NLTK_CACHE = "/path/to/cache/nltk_data"  # NLTK data cache
MODEL_DIR = None  # Optional: specific model directory for offline/local models
```

### Transcription Settings
```python
WHISPER_MODEL = "large-v3"  # Options: tiny, base, small, medium, large-v2, large-v3, turbo
BATCH_SIZE = 16
COMPUTE_TYPE = "float16"    # Options: float16, float32, int8
LANGUAGE = None             # None for auto-detect, or "en", "es", "fr", etc.
ALIGNMENT_LANGUAGES = ["en", "es", "fr", "de"]  # Languages to download alignment models for
MAX_LINE_WIDTH = 42
MAX_LINE_COUNT = 2
HIGHLIGHT_WORDS = False
```

### Model Download Settings
```python
DOWNLOAD_MODELS_BEFORE_SLURM = True  # Download models before SLURM job (required if SLURM has no internet)
```
**Important:** If your SLURM nodes don't have internet access, keep this `True` to download models before job submission.

### Environment Variables (Alternative Configuration)
You can also set sensitive information via environment variables:
```bash
export SMB_PASSWORD="your_password"
export GIT_TOKEN="your_github_token"
```

## Usage

### Running the Complete Pipeline
```bash
python pipeline_2.py
```

The pipeline will:
1. Load all modules (GCCcore, FFmpeg, CUDA, Python)
2. Activate virtual environment
3. Clear previous input/output directories
4. Download audio files from Google Sheets
5. Submit SLURM job for transcription
6. Monitor job status
7. Upload results to GitHub

### Running Individual Scripts

#### Download Only
```bash
python download_automation_3.py \
  --sheet-url "YOUR_SHEET_URL" \
  --username "YOUR_USERNAME" \
  --password "YOUR_PASSWORD" \
  --server "SMB_SERVER" \
  --share "SHARE_NAME" \
  --base-path "PATH/IN/SHARE" \
  --local-path "/path/to/download" \
  --max-folders 20
```

#### Transcribe Only
```bash
python transcribe.py \
  /path/to/input/audio \
  /path/to/output \
  --model large-v3 \
  --batch-size 16 \
  --compute-type float16 \
  --language en \
  --parallel \
  --num-gpus 2
```

#### Git Upload Only
```bash
python git_upload.py \
  --source-path "/path/to/transcriptions" \
  --repo-path "/path/to/git/repo" \
  --owner "OWNER" \
  --repo-name "REPO_NAME" \
  --username "USERNAME" \
  --token "TOKEN"
```

## Pipeline Workflow

The pipeline executes these steps in order:

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Load Environment Modules                                │
│    Command: ml GCCcore/10.3.0 Python FFmpeg CUDA               │
│    Purpose: Loads base Python interpreter and system libraries │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Export PYTHONPATH                                       │
│    Purpose: Sets Python package search paths                    │
│    Required: Must run BEFORE venv creation                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Check/Create Virtual Environment                        │
│    - Checks if venv/ exists in working directory                │
│    - Creates if missing: python -m venv venv                    │
│    - Installs requirements.txt (includes WhisperX PACKAGE)      │
│    - All subsequent Python commands use venv/bin/python         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Prepare Data Directories                                │
│    - Clears data/oral_input/ directory                          │
│    - Clears data/oral_output/ directory                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Download Audio Files (download_automation_3.py)         │
│    - Reads Google Sheet for incomplete tasks                    │
│    - Downloads audio from SMB network share                     │
│    - Saves to data/oral_input/                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: Download WhisperX Model FILES (d_whisperx.py)           │
│    - Downloads AI model FILES (large-v3, alignment models)      │
│    - Saves to cache/models/ directory                           │
│    - Enables offline SLURM execution (no internet needed)       │
│    - Note: This downloads MODEL FILES, NOT the WhisperX        │
│      package (package already installed via requirements.txt)   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 7: Submit SLURM Job                                        │
│    - Updates cache paths in run_1.slurm                         │
│    - Submits batch job: sbatch run_1.slurm                      │
│    - Captures job ID for monitoring                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 8: Monitor SLURM Job Status                                │
│    - Checks status every N minutes (configurable)               │
│    - Waits until job completes                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 9: Upload Results to GitHub (git_upload.py)                │
│    - Syncs to OUTPUT repo (edge-grant-json-and-vtts)           │
│    - Creates timestamped branch                                 │
│    - Uploads JSON + VTT files from data/oral_output/            │
│    - Pushes to GitHub                                           │
└─────────────────────────────────────────────────────────────────┘

**Important Notes:**
- WORKING_DIR is automatically set to the repo directory (WhisperX-transcribe-automation)
- GIT_REPO_PATH is automatically set to `../edge-grant-json-and-vtts` (one level above WORKING_DIR)
- All script paths are automatically configured - no manual path updates needed
- Steps 1-2 MUST run before Step 3 (venv creation)
- WhisperX PACKAGE (Python library) → installed in Step 3 via requirements.txt
- WhisperX MODEL FILES (AI models) → downloaded in Step 6 via d_whisperx.py
```

## Individual Scripts

### `pipeline_2.py`
**Main orchestration script** that runs the entire workflow. All configuration variables are defined at the top of this file.

**Key Functions:**
- `run_command()`: Execute system commands with logging
- `clear_directory()`: Clean directories before processing
- `submit_slurm_job()`: Submit batch jobs and capture job ID
- `monitor_job_status()`: Track SLURM job completion

### `download_automation_3.py`
Downloads audio files from SMB network shares based on Google Sheets data.

**Features:**
- Google Sheets integration for task tracking
- SMB/CIFS network share support
- Folder name parsing and mapping
- Progress tracking and error handling

**Command Line Arguments:**
- `--sheet-url`: Google Sheets URL
- `--username`: SMB username
- `--password`: SMB password
- `--server`: SMB server address
- `--share`: Share name
- `--base-path`: Path inside share
- `--local-path`: Local download destination
- `--max-folders`: Maximum folders to process

### `transcribe.py`
WhisperX-based transcription with word-level timestamps.

**Features:**
- Multiple GPU support with parallel processing
- Word-level timestamp alignment
- JSON and VTT output formats
- Automatic language detection
- Customizable subtitle formatting

**Command Line Arguments:**
- `input_dir`: Input directory with audio files
- `output_dir`: Output directory for transcriptions
- `--model`: WhisperX model size
- `--batch-size`: Batch size for processing
- `--compute-type`: Computation precision
- `--language`: Language code (or auto-detect)
- `--parallel`: Enable multi-GPU processing
- `--num-gpus`: Number of GPUs to use
- `--max-line-width`: VTT line width
- `--max-line-count`: VTT lines per subtitle

### `git_upload.py`
Uploads transcription results to GitHub repository.

**Features:**
- Automatic repository cloning/updating
- Timestamped branch creation
- Rsync-based file synchronization
- Token-based authentication
- Pull request URL generation

**Command Line Arguments:**
- `--source-path`: Source folder with files
- `--repo-path`: Git repository path (OUTSIDE working dir)
- `--owner`: Repository owner
- `--repo-name`: Repository name
- `--username`: GitHub username
- `--token`: GitHub personal access token
- `--branch-prefix`: Branch name prefix (optional)

### `d_whisperx.py`
Downloads WhisperX **model files** (not the package) for offline use.

**Important:** WhisperX Python package is installed via `requirements.txt` in your venv. This script only downloads the **model files** to cache so SLURM jobs can run offline.

**Features:**
- Download any WhisperX model files (tiny to turbo)
- Download alignment model files for multiple languages
- Configurable cache directory
- Automatic directory creation
- Integrated into pipeline (runs before SLURM job)

**Command Line Arguments:**
- `--model`: WhisperX model size (default: large-v3)
- `--cache-dir`: Directory to cache model files
- `--languages`: Language codes for alignment models
- `--compute-type`: Computation precision

**Standalone Usage:**
```bash
python d_whisperx.py \
  --model large-v3 \
  --cache-dir /path/to/cache \
  --languages en es fr de \
  --compute-type float16
```

**Pipeline Integration:**
The pipeline automatically runs this before SLURM job submission if `DOWNLOAD_MODELS_BEFORE_SLURM = True`.

**Note:** Ensure WhisperX package is already installed in your venv via:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### `run_1.slurm`
SLURM batch script for GPU transcription jobs.

**Configuration is automatically updated by pipeline_2.py** with correct cache paths.

## Troubleshooting

### Common Issues

#### 1. Authentication Failed (Git)
**Problem:** Git push fails with authentication error.

**Solution:**
- Verify GitHub token has correct permissions (repo or Contents: Write)
- Check token hasn't expired
- Ensure token is correctly set in `GIT_TOKEN` variable

#### 2. SMB Connection Failed
**Problem:** Cannot connect to network share.

**Solutions:**
- Verify SMB credentials
- Check network connectivity
- Confirm share name and path are correct
- Try setting password via environment variable:
  ```bash
  export SMB_PASSWORD="your_password"
  ```

#### 3. CUDA Out of Memory
**Problem:** GPU runs out of memory during transcription.

**Solutions:**
- Reduce `BATCH_SIZE` (try 8 or 4)
- Use smaller model (`medium` or `small` instead of `large-v3`)
- Use `--compute-type int8` for lower memory usage

#### 4. Model Download Fails
**Problem:** Cannot download WhisperX models.

**Solutions:**
- Check internet connectivity
- Verify `HF_CACHE` directory is writable
- Pre-download models using `d_whisperx.py`
- Set `MODEL_DIR` to local model path

#### 5. Git Repository Not Outside Working Directory
**Problem:** Git operations interfering with source files.

**Solution:**
- Ensure `GIT_REPO_PATH` points to a location OUTSIDE your working directory
- Example: `/scratch/user/git_repositories/repo-name` instead of `/scratch/user/libraries/speech_text/git_repo`

#### 6. Google Sheets Access Denied
**Problem:** Cannot read Google Sheets.

**Solutions:**
- Ensure sheet is publicly accessible or shared with your account
- Verify sheet URL is correct
- Check internet connectivity

### Debug Mode

For detailed logging, you can modify the pipeline to add verbose output:

```python
# In pipeline_2.py, modify run_command():
result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, 
                       stderr=subprocess.STDOUT, text=True)
print(result.stdout)  # This shows all output
```

### Log Files

Check SLURM job output files for transcription errors:
```bash
cat slurm-<job_id>.out
```

## Security Considerations

⚠️ **Important Security Notes:**

1. **Never commit tokens or passwords to Git**
   - Use environment variables for sensitive data
   - Add `.env` files to `.gitignore`

2. **Token Permissions**
   - Use minimal required permissions
   - For Classic tokens: only `repo` scope
   - For Fine-grained tokens: only `Contents: Write`

3. **Rotate Tokens Regularly**
   - GitHub tokens should be rotated periodically
   - Update `GIT_TOKEN` when rotating

4. **SMB Credentials**
   - Never hardcode passwords
   - Use `getpass` for interactive input
   - Or set `SMB_PASSWORD` environment variable

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Specify your license here]

## Support

For issues or questions:
- Open an issue on GitHub
- Contact: [Your contact information]

## Acknowledgments

- [WhisperX](https://github.com/m-bain/whisperX) - Fast automatic speech recognition
- OpenAI Whisper - Base ASR model
- Texas A&M University Libraries - Digital Collections Lab

---

**Last Updated:** December 2025
