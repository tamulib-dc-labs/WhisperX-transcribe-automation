# Setup Guide - First Time Installation

This guide walks you through the **one-time setup** process. After this, you can simply run `python pipeline_2.py` without any manual intervention.

## 🚀 One-Time Setup (Steps 1-5)

### Step 1: Clone the Repository
```bash
cd /scratch/user/your_username/
git clone https://github.com/tamulib-dc-labs/WhisperX-transcribe-automation.git
cd WhisperX-transcribe-automation
```

### Step 2: Load Python Module
```bash
ml GCCcore/10.3.0 Python
```
This loads the base Python environment needed for creating the virtual environment.

### Step 3: Export PYTHONPATH
```bash
export PYTHONPATH=/scratch/user/your_username/cache/python_packages
```
This tells Python where to find installed packages.

### Step 4: Create Virtual Environment
```bash
python -m venv venv
```
This creates a virtual environment in the `venv` folder inside your working directory.

**Note:** You can also let the pipeline create the venv automatically on first run (it will detect if venv doesn't exist).

### Step 5: Configure `pipeline_2.py`

Edit the **CONFIGURATION SECTION** at the top of `pipeline_2.py`:

```python
# --- Working Directory ---
WORKING_DIR = "/scratch/user/YOUR_USERNAME/WhisperX-transcribe-automation"

# --- Virtual Environment ---
VENV_NAME = "venv"  # This should match the venv you created in Step 4

# --- Environment Modules ---
MODULE_LOAD_COMMAND = "ml GCCcore/10.3.0 Python FFmpeg CUDA"

# --- File Paths (Scripts) ---
DOWNLOAD_SCRIPT_PATH = f"{WORKING_DIR}/download_automation_3.py"
MODEL_DOWNLOAD_SCRIPT_PATH = f"{WORKING_DIR}/d_whisperx.py"
TRANSCRIBE_SCRIPT_PATH = f"{WORKING_DIR}/transcribe.py"
GIT_UPLOAD_SCRIPT_PATH = f"{WORKING_DIR}/git_upload.py"
SLURM_JOB_PATH = f"{WORKING_DIR}/run_1.slurm"

# --- Cache Directories ---
CACHE_DIR = "/scratch/user/YOUR_USERNAME/cache"

# --- Git Repository (OUTSIDE working directory) ---
GIT_REPO_PATH = "/scratch/user/YOUR_USERNAME/git_repositories/edge-grant-json-and-vtts"

# --- SMB Network Share Settings ---
SMB_USERNAME = "your_netid"
SMB_PASSWORD = ""  # Leave empty for secure prompt

# --- Google Sheets Settings ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"

# --- GitHub Settings ---
GIT_OWNER = "tamulib-dc-labs"
GIT_REPO_NAME = "edge-grant-json-and-vtts"
GIT_USERNAME = "your_github_username"
GIT_TOKEN = "your_github_token"

# --- Transcription Settings ---
WHISPER_MODEL = "large-v3"
ALIGNMENT_LANGUAGES = ["en", "es", "fr", "de"]
```

### Step 6: Install Dependencies (First Time Only)
```bash
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

## ✅ Setup Complete!

From now on, you can simply run:
```bash
python pipeline_2.py
```

The pipeline will automatically:
- ✅ Load required modules (`ml GCCcore/10.3.0 Python FFmpeg CUDA`)
- ✅ Set PYTHONPATH
- ✅ Use the virtual environment
- ✅ Create necessary directories
- ✅ Run the entire workflow

## 📋 What the Pipeline Does Automatically

### On Every Run:
1. **Load Environment Modules** - Executes `MODULE_LOAD_COMMAND`
2. **Check Virtual Environment** - Uses existing venv or creates if missing
3. **Set Environment Variables** - PYTHONPATH, HF_HOME, etc.
4. **Create Directories** - data/, cache/ subdirectories
5. **Run Workflow**:
   - Download audio files from SMB
   - Download WhisperX models (if needed)
   - Submit SLURM job
   - Monitor job
   - Upload to GitHub

### Virtual Environment Handling:
- **First run:** Creates venv if it doesn't exist
- **Subsequent runs:** Detects and uses existing venv
- **All Python commands:** Use venv's Python automatically

## 🔧 Workflow After Setup

```bash
# Simply run the pipeline (from any location)
cd /scratch/user/your_username/WhisperX-transcribe-automation
python pipeline_2.py
```

Or create a convenient alias:
```bash
# Add to your ~/.bashrc
alias run-pipeline='cd /scratch/user/your_username/WhisperX-transcribe-automation && python pipeline_2.py'

# Then just run:
run-pipeline
```

## 📝 Configuration Changes

To change settings later, just edit `pipeline_2.py` - no need to reconfigure anything else!

**Common changes:**
- Different model: Change `WHISPER_MODEL`
- More/fewer folders: Change `MAX_FOLDERS`
- Different languages: Update `ALIGNMENT_LANGUAGES`
- New Google Sheet: Update `SHEET_URL`

## 🔍 Verify Setup

After setup, verify everything is configured correctly:

```bash
# Check venv exists
ls -la venv/bin/python

# Check configuration
grep "WORKING_DIR" pipeline_2.py
grep "VENV_PATH" pipeline_2.py

# Test module loading
ml GCCcore/10.3.0 Python
python --version
```

## 🆘 Troubleshooting

### Problem: "venv not found"
**Solution:** The pipeline will create it automatically on first run, or manually:
```bash
python -m venv venv
```

### Problem: "Module not found"
**Solution:** Check `MODULE_LOAD_COMMAND` matches your HPC environment:
```bash
# List available modules
module avail
```

### Problem: "Permission denied"
**Solution:** Ensure all paths are in your scratch directory with write permissions

### Problem: "Package not installed"
**Solution:** Install dependencies in venv:
```bash
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

## 🎯 Directory Structure After Setup

```
/scratch/user/your_username/
├── WhisperX-transcribe-automation/     ← Working directory
│   ├── pipeline_2.py                   ← Main script
│   ├── download_automation_3.py
│   ├── transcribe.py
│   ├── git_upload.py
│   ├── d_whisperx.py
│   ├── run_1.slurm
│   ├── venv/                           ← Virtual environment (auto-created)
│   └── data/                           ← Data folder (auto-created)
│       ├── oral_input/
│       └── oral_output/
│           ├── json/
│           └── vtts/
├── cache/                              ← Cache directory (auto-created)
│   ├── huggingface/                    ← Models cached here
│   ├── python_packages/
│   ├── nltk_data/
│   └── models/
└── git_repositories/                   ← Git repos (auto-created)
    └── edge-grant-json-and-vtts/
```

## ✨ Key Benefits

- 🎯 **One-time setup** - Configure once, run forever
- 🚀 **Zero intervention** - Pipeline handles everything
- 🔄 **Automatic venv** - Creates/uses venv automatically
- 📦 **Module loading** - Loads required modules on every run
- 🛡️ **Safe** - No hardcoded passwords, secure prompts
- 📁 **Organized** - Clean directory structure
- 🔧 **Flexible** - Easy to change settings

---

**Happy transcribing! 🎉**
