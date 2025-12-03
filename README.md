# WhisperX Transcription Automation Pipeline

An automated batch processing pipeline for transcribing audio files using WhisperX, with integrated Google Sheets tracking, SMB network share downloads, and GitHub upload capabilities.

**Version 2.0** - Refactored with professional software architecture following best practices.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Pipeline Workflow](#pipeline-workflow)
- [Module Documentation](#module-documentation)
- [Troubleshooting](#troubleshooting)

## Overview

This pipeline automates the entire workflow of:
1. Reading incomplete tasks from a Google Sheet
2. Downloading audio files from an SMB network share
3. Transcribing audio files using WhisperX with GPU acceleration
4. Uploading results (JSON and VTT files) to a GitHub repository

The pipeline is designed for high-performance computing (HPC) environments with SLURM job scheduling but can be adapted for other systems.

## Features

- ✅ **Professional Architecture**: Modular class-based design with dataclass configuration
- ✅ **Centralized Configuration**: All settings in `src/config.py` with derived paths
- ✅ **Google Sheets Integration**: Track processing status and manage queues
- ✅ **SMB Network Share Support**: Direct download from network shares (CIFS)
- ✅ **GPU-Accelerated Transcription**: WhisperX with word-level timestamps
- ✅ **Automated Git Upload**: Creates pull requests with timestamped branches
- ✅ **SLURM Job Management**: Automated job submission and monitoring
- ✅ **External Git Repository**: Git operations happen outside working directory
- ✅ **Modular Components**: Utilities, git, transcription modules separated
- ✅ **PyTorch 2.6+ Compatible**: Automatic compatibility patches applied

## Architecture

The pipeline follows modern Python software development practices:

### Design Principles
- **Dataclass Configuration**: Centralized settings with derived properties
- **Class-Based Utilities**: FileManager, CommandRunner, Logger classes
- **Separation of Concerns**: Distinct modules for git, transcription, utilities
- **Single Responsibility**: Each class has one clear purpose
- **Automatic Path Resolution**: Working directory auto-detected

### Module Structure
```
src/
├── config.py              # PipelineConfig dataclass
├── pipeline.py            # TranscriptionPipeline orchestrator
├── utils/                 # Utility classes
│   ├── file_manager.py    # FileManager, CommandRunner
│   └── logger.py          # Logger
├── git/                   # Git operations
│   └── uploader.py        # GitUploader
└── transcription/         # Transcription components
    └── model_downloader.py # ModelDownloader
```

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

### 2. Load Required Modules (HPC/SLURM environments only)
```bash
# Load GCC and Python modules
ml GCCcore/10.3.0 Python
```

### 3. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Settings
Edit `src/config.py` to set your SMB, Google Sheets, and GitHub credentials.

### 5. Download Models (Optional - for offline use)
The pipeline will download models automatically, or you can pre-download:
```bash
python scripts/run_pipeline.py  # Will download models in Step 5
```

## Configuration

All configuration is centralized in **`src/config.py`** using a dataclass. Edit the `PipelineConfig` class with your settings:

### Path Configuration (Automatic)
Paths are automatically derived from the working directory - no manual configuration needed:

```python
@property
def working_dir(self) -> str:
    """Auto-detected from __file__ location"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@property
def venv_path(self) -> str:
    """Virtual environment path"""
    return os.path.join(self.working_dir, "venv")

@property
def git_repo_path(self) -> str:
    """External git repository (outside working directory)"""
    return os.path.join(os.path.dirname(self.working_dir), 
                       "edge-grant-json-and-vtts")
```

**Directory Structure:**
```
parent_directory/
├── WhisperX-transcribe-automation/  ← Auto-detected working_dir
│   ├── src/
│   │   ├── config.py               ← Configuration here
│   │   ├── pipeline.py
│   │   └── ...
│   ├── legacy/                     ← Deprecated v1.0 scripts
│   │   └── ...
│   ├── scripts/
│   │   ├── run_pipeline.py         ← Entry point
│   │   └── transcribe.py
│   ├── config/
│   │   └── run.slurm
│   └── data/
│       ├── oral_input/
│       └── oral_output/
└── edge-grant-json-and-vtts/        ← Auto-located git repo
```

### Required User Configuration
Edit these fields in `PipelineConfig` dataclass:

```python
@dataclass
class PipelineConfig:
    # SMB Network Share
    smb_server: str = "your.smb.server.com"
    smb_share: str = "share_name"
    smb_base_path: str = "path/inside/share"
    smb_username: str = "your_username"
    smb_password: str = ""  # Leave empty to prompt
    
    # Google Sheets
    sheet_url: str = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
    max_folders: int = 20
    
    # GitHub
    git_owner: str = "repository-owner"
    git_repo_name: str = "repository-name"
    git_username: str = "your-github-username"
    git_token: str = "your-github-token"
    
    # WhisperX Model
    whisper_model: str = "large-v3"
    batch_size: int = 16
    compute_type: str = "float16"
    language: str = "en"  # or None for auto-detect
```

### Environment Variables (Alternative)
You can set sensitive data via environment variables instead:
```bash
export SMB_PASSWORD="your_password"
export GIT_TOKEN="your_github_token"
```

## Usage

### Running the Complete Pipeline
```bash
# Activate virtual environment (if not already active)
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the pipeline
python scripts/run_pipeline.py
```

The pipeline will automatically:
1. Load environment modules (GCCcore, FFmpeg, CUDA, Python)
2. Set up/verify virtual environment
3. Install requirements if venv was just created
4. Prepare data directories
5. Download audio files from Google Sheets
6. Download WhisperX models
7. Download NLTK data
8. Submit SLURM transcription job
9. Monitor job status
10. Upload results to GitHub

### Using the Legacy Pipeline (Deprecated)
The old `pipeline_2.py` script is still available but deprecated:
```bash
python pipeline_2.py  # Not recommended - use scripts/run_pipeline.py instead
```

## Project Structure

```
WhisperX-transcribe-automation/
├── src/                           # Source code (modular architecture)
│   ├── __init__.py
│   ├── config.py                  # PipelineConfig dataclass
│   ├── pipeline.py                # TranscriptionPipeline orchestrator
│   ├── utils/                     # Utility classes
│   │   ├── __init__.py
│   │   ├── file_manager.py        # FileManager, CommandRunner
│   │   └── logger.py              # Logger
│   ├── git/                       # Git operations
│   │   ├── __init__.py
│   │   └── uploader.py            # GitUploader class
│   └── transcription/             # Transcription components
│       ├── __init__.py
│       └── model_downloader.py    # ModelDownloader class
│
├── scripts/                       # Executable scripts
│   ├── run_pipeline.py            # Main entry point (NEW)
│   └── transcribe.py              # SLURM transcription script
│
├── config/                        # Configuration templates
│   └── run.slurm                  # SLURM job template
│
├── data/                          # Data directories (created at runtime)
│   ├── oral_input/                # Downloaded audio files
│   └── oral_output/               # Transcription results (JSON, VTT)
│
├── cache/                         # Model and data cache (created at runtime)
│   ├── huggingface/               # WhisperX models
│   └── nltk_data/                 # NLTK data (punkt_tab)
│
├── venv/                          # Python virtual environment
│
├── requirements.txt               # Python dependencies
├── README.md                      # This file
│
└── legacy/                        # ⚠️ DEPRECATED v1.0 scripts (see legacy/README.md)
    ├── pipeline_2.py              # Old pipeline (use scripts/run_pipeline.py)
    ├── git_upload.py              # Old git script (now src/git/uploader.py)
    ├── d_whisperx.py              # Old downloader (now src/transcription/)
    ├── download_automation_3.py   # Integrated into pipeline
    ├── transcribe.py              # Old script (now scripts/transcribe.py)
    └── run_1.slurm                # Old template (now config/run.slurm)
```

## Pipeline Workflow

The TranscriptionPipeline orchestrates these steps:

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Load Environment Modules                                │
│    Module: TranscriptionPipeline._load_modules()                │
│    Command: ml GCCcore/10.3.0 Python FFmpeg CUDA               │
│    Purpose: Loads system libraries and base Python             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Setup Python Environment                                │
│    Module: TranscriptionPipeline._setup_python_environment()    │
│    Actions:                                                      │
│      - Check if venv exists                                      │
│      - Create venv if missing: python -m venv venv               │
│      - Install requirements.txt (if new venv)                    │
│      - Includes: WhisperX, torch, nltk, etc.                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Prepare Data Directories                                │
│    Module: TranscriptionPipeline._prepare_directories()         │
│    Actions:                                                      │
│      - Clear data/oral_input/                                    │
│      - Clear data/oral_output/                                   │
│      - Ensure cache directories exist                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Download Audio Files                                    │
│    Module: TranscriptionPipeline._download_audio_files()        │
│    Script: download_automation_3.py (integrated)                │
│    Actions:                                                      │
│      - Read Google Sheet for incomplete tasks                   │
│      - Download audio from SMB share                            │
│      - Save to data/oral_input/                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Download WhisperX Models                                │
│    Module: TranscriptionPipeline._download_models()             │
│    Class: ModelDownloader                                        │
│    Actions:                                                      │
│      - Download AI model files (large-v3, alignment models)     │
│      - Apply PyTorch 2.6+ compatibility patch                   │
│      - Save to cache/huggingface/                                │
│      - Enables offline SLURM execution                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: Download NLTK Data                                      │
│    Module: TranscriptionPipeline._download_nltk_data()          │
│    Actions:                                                      │
│      - Download punkt_tab tokenizer                             │
│      - Save to cache/nltk_data/                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 7: Submit SLURM Job                                        │
│    Module: TranscriptionPipeline._submit_slurm_job()            │
│    Class: CommandRunner                                          │
│    Actions:                                                      │
│      - Update config/run.slurm with cache paths                 │
│      - Submit: sbatch config/run.slurm                           │
│      - Capture job ID for monitoring                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 8: Monitor SLURM Job                                       │
│    Module: TranscriptionPipeline._monitor_slurm_job()           │
│    Class: CommandRunner                                          │
│    Actions:                                                      │
│      - Check status every 2 minutes                              │
│      - Wait until job completes or fails                         │
│      - Display progress updates                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 9: Upload to GitHub                                        │
│    Module: TranscriptionPipeline._upload_to_github()            │
│    Class: GitUploader                                            │
│    Actions:                                                      │
│      - Sync to edge-grant-json-and-vtts repo                    │
│      - Create timestamped branch                                 │
│      - Upload JSON + VTT files from data/oral_output/           │
│      - Push to GitHub (additions only, no deletions)            │
└─────────────────────────────────────────────────────────────────┘

**Architecture Notes:**
- All paths automatically derived from working_dir
- Configuration centralized in PipelineConfig dataclass
- Each step is a method in TranscriptionPipeline class
- Utilities (FileManager, Logger, CommandRunner) shared across steps
- PyTorch compatibility patches applied automatically
- Git operations use --ignore-removal flag (no deletions)
```

## Module Documentation

### Core Classes

#### `PipelineConfig` (src/config.py)
Centralized configuration using Python dataclass.

**Key Properties:**
- `working_dir`: Auto-detected project root
- `venv_path`: Virtual environment location
- `data_input_path` / `data_output_path`: Audio and transcription directories
- `hf_cache` / `nltk_cache`: Model and data cache locations
- `git_repo_path`: External git repository location

**Usage:**
```python
from src.config import get_config

config = get_config()
print(config.working_dir)  # Auto-detected path
print(config.hf_cache)     # Derived cache path
```

#### `TranscriptionPipeline` (src/pipeline.py)
Main orchestrator coordinating all pipeline steps.

**Methods:**
- `run()`: Execute complete pipeline (Steps 1-9)
- `_load_modules()`: Load HPC environment modules
- `_setup_python_environment()`: Create/verify venv
- `_prepare_directories()`: Clear and prepare data directories
- `_download_audio_files()`: Download from SMB share
- `_download_models()`: Download WhisperX models
- `_download_nltk_data()`: Download NLTK tokenizers
- `_submit_slurm_job()`: Submit transcription job
- `_monitor_slurm_job()`: Wait for job completion
- `_upload_to_github()`: Upload results to repository

**Usage:**
```python
from src.pipeline import TranscriptionPipeline

pipeline = TranscriptionPipeline()
pipeline.run()
```

#### `FileManager` (src/utils/file_manager.py)
File and directory operations.

**Static Methods:**
- `clear_directory(path)`: Remove all files from directory
- `ensure_directory(path)`: Create directory if missing
- `count_files(path, pattern)`: Count files matching pattern
- `get_file_list(path, pattern)`: List files matching pattern

#### `CommandRunner` (src/utils/file_manager.py)
Execute system commands and SLURM operations.

**Static Methods:**
- `run(command, cwd)`: Execute shell command
- `submit_slurm_job(script_path)`: Submit SLURM job, return job ID
- `check_slurm_job_status(job_id)`: Get job status

#### `Logger` (src/utils/logger.py)
Standardized logging for pipeline operations.

**Static Methods:**
- `log_step(step_number, message)`: Log pipeline step
- `log_info(message)`: Log informational message
- `log_warning(message)`: Log warning message
- `log_error(message)`: Log error message

#### `GitUploader` (src/git/uploader.py)
GitHub repository operations.

**Methods:**
- `upload()`: Complete upload workflow
- `setup_repository()`: Clone or verify repository
- `create_branch(name)`: Create timestamped branch
- `sync_files(source_path)`: Sync files to repository
- `commit_and_push(message)`: Commit and push changes

**Key Feature:** Uses `git add --all --ignore-removal` to prevent deletions.

#### `ModelDownloader` (src/transcription/model_downloader.py)
WhisperX model downloading with PyTorch compatibility.

**Methods:**
- `download_models()`: Download WhisperX and alignment models

**Key Feature:** Applies PyTorch 2.6+ compatibility patch automatically.

### Legacy Scripts (Deprecated)

⚠️ **The following files have been moved to the `legacy/` folder**. Use the new modular structure instead:

- `legacy/pipeline_2.py` → Use `scripts/run_pipeline.py`
- `legacy/git_upload.py` → Now `src/git/uploader.py`
- `legacy/d_whisperx.py` → Now `src/transcription/model_downloader.py`
- `legacy/download_automation_3.py` → Integrated into `TranscriptionPipeline`
- `legacy/transcribe.py` → Now `scripts/transcribe.py`
- `legacy/run_1.slurm` → Now `config/run.slurm`

**See `legacy/README.md` for details and migration guide.**

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
