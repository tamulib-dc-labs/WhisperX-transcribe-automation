#!/usr/bin/env python3
"""
Batch job pipeline for processing speech data
Executes steps sequentially with logging after each completion
Updated to use SMB/CIFS Network Share for downloads.
"""


import subprocess
import sys
import os
import re
import time
import getpass
from datetime import datetime

# ======================== CONFIGURATION SECTION ========================
# All configurable parameters are defined here for easy modification

# --- Pipeline Settings ---
CHECK_INTERVAL_MINS = 5  # How often to check SLURM job status (in minutes)

# --- Working Directory ---
# Main working directory - automatically set to this script's directory (the repo root)
# This is your local clone of WhisperX-transcribe-automation repo
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Virtual Environment ---
# Virtual environment will be created inside WORKING_DIR
VENV_NAME = "venv"  # Name of virtual environment folder
VENV_PATH = f"{WORKING_DIR}/{VENV_NAME}"  # Full path to virtual environment

# --- Environment Modules ---
# Modules to load before running (for HPC environments)
MODULE_LOAD_COMMAND = "ml GCCcore/10.3.0 Python FFmpeg CUDA"  # Customize as needed

# --- File Paths (Scripts) ---
# All scripts are in the WORKING_DIR (local git repo)
DOWNLOAD_SCRIPT_PATH = f"{WORKING_DIR}/download_automation_3.py"
MODEL_DOWNLOAD_SCRIPT_PATH = f"{WORKING_DIR}/d_whisperx.py"
TRANSCRIBE_SCRIPT_PATH = f"{WORKING_DIR}/transcribe.py"
GIT_UPLOAD_SCRIPT_PATH = f"{WORKING_DIR}/git_upload.py"
SLURM_JOB_PATH = f"{WORKING_DIR}/run_1.slurm"

# --- Data Directories (relative to WORKING_DIR) ---
# Data folder structure: WORKING_DIR/data/oral_input and WORKING_DIR/data/oral_output
DATA_FOLDER = "data"  # Folder name for data (will be created under WORKING_DIR)
ORAL_INPUT_FOLDER = "oral_input"   # Input folder name (under data/)
ORAL_OUTPUT_FOLDER = "oral_output" # Output folder name (under data/)

# --- Git Repository for Output (OUTSIDE working directory) ---
# This is where transcription OUTPUT will be pushed (edge-grant-json-and-vtts repo)
# This is DIFFERENT from WORKING_DIR (which is the WhisperX-transcribe-automation repo)
GIT_REPO_PATH = "/scratch/user/jvk_chaitanya/git_repositories/edge-grant-json-and-vtts"

# --- SMB Network Share Settings ---
SMB_SERVER = "cifs.library.tamu.edu"
SMB_SHARE = "digital_project_management"
SMB_BASE_PATH = "edge-grant/GB_38253_MP3s"
SMB_USERNAME = "jvk_chaitanya"
SMB_PASSWORD = ""  # Leave empty to prompt, or set via environment variable SMB_PASSWORD

# --- Google Sheets Settings ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/16cHa57n7rJmS744nMH2dY2H4IKLP5fMeHJ0iY8w85EM/edit?usp=sharing"
MAX_FOLDERS = 20  # Maximum number of folders to download from Google Sheets

# --- GitHub Settings ---
GIT_OWNER = "tamulib-dc-labs"
GIT_REPO_NAME = "edge-grant-json-and-vtts"
GIT_USERNAME = "JvkChaitanya"
GIT_TOKEN = ""  # Set your token here or use environment variable GIT_TOKEN

# --- Cache and Model Directories ---
# You can customize these paths or leave them as default
# These directories store downloaded models and cache data to avoid re-downloading
CACHE_DIR = "/scratch/user/jvk_chaitanya/cache"  # Main cache directory
# All cache subdirectories are automatically created under CACHE_DIR:
HF_CACHE = f"{CACHE_DIR}/huggingface"  # HuggingFace models cache
PYTHON_CACHE = f"{CACHE_DIR}/python_packages"  # Python packages cache
NLTK_CACHE = f"{CACHE_DIR}/nltk_data"  # NLTK data cache
MODEL_CACHE = f"{CACHE_DIR}/models"  # WhisperX models cache
MODEL_DIR = None  # Set to specific model directory if using offline/local models

# --- Transcription Settings ---
WHISPER_MODEL = "large-v3"
BATCH_SIZE = 16
COMPUTE_TYPE = "float16"
LANGUAGE = None  # Set to specific language code (e.g., "en") or None for auto-detect
ALIGNMENT_LANGUAGES = ["en", "es", "fr", "de"]  # Languages to download alignment models for
MAX_LINE_WIDTH = 42
MAX_LINE_COUNT = 2
HIGHLIGHT_WORDS = False

# --- Model Download Settings ---
DOWNLOAD_MODELS_BEFORE_SLURM = True  # Download models before SLURM job (required if SLURM has no internet)

# ====================================================================

def log_step(step_num, description, status="STARTED"):
    """Print formatted log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*80}")
    print(f"[{timestamp}] Step {step_num}: {description} - {status}")
    print(f"{'='*80}\n")

def run_command(cmd, step_num, description, shell=False, env=None):
    """Execute a command and log its completion"""
    log_step(step_num, description, "STARTED")
    
    # Merge current environment with passed env if needed
    run_env = os.environ.copy()
    if env:
        run_env.update(env)

    try:
        if shell:
            result = subprocess.run(cmd, shell=True, check=True, 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                   text=True, executable='/bin/bash', env=run_env)
        else:
            result = subprocess.run(cmd, check=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                   text=True, env=run_env)
        
        if result.stdout:
            print(result.stdout)
        
        log_step(step_num, description, "COMPLETED")
        return True
        
    except subprocess.CalledProcessError as e:
        log_step(step_num, description, "FAILED")
        print(f"Error output: {e.stderr}", file=sys.stderr)
        print(f"Return code: {e.returncode}", file=sys.stderr)
        return False

def clear_directory(path, step_num, description):
    """Clear all files and folders in a directory"""
    import shutil
    log_step(step_num, description, "STARTED")
    try:
        if os.path.exists(path):
            files_removed = 0
            folders_removed = 0
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    print(f"Removed file: {item_path}")
                    files_removed += 1
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"Removed folder: {item_path}")
                    folders_removed += 1
            print(f"Total files removed: {files_removed}")
            print(f"Total folders removed: {folders_removed}")
        else:
            print(f"Directory does not exist: {path}")
        log_step(step_num, description, "COMPLETED")
        return True
    except Exception as e:
        log_step(step_num, description, "FAILED")
        print(f"Error: {e}", file=sys.stderr)
        return False

def submit_slurm_job(sbatch_path, step_num, description):
    """Submits sbatch job, parses output for Job ID."""
    log_step(step_num, description, "STARTED")
    cmd = ["sbatch", sbatch_path]
    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(result.stdout)
        match = re.search(r"Submitted batch job (\d+)", result.stdout)
        
        if match:
            job_id = match.group(1)
            print(f"\nSUCCESS: Job submitted. Detected Job ID: {job_id}")
            log_step(step_num, description, "COMPLETED")
            return job_id
        else:
            print("ERROR: Could not parse Job ID from sbatch output.")
            log_step(step_num, description, "FAILED")
            return None
    except subprocess.CalledProcessError as e:
        log_step(step_num, description, "FAILED")
        print(f"Error output: {e.stderr}", file=sys.stderr)
        return None

def monitor_job_status(job_id, check_interval_mins=5):
    """Monitors a Slurm job ID using squeue."""
    print(f"\nMonitoring Job {job_id} every {check_interval_mins} minutes...")
    print("-" * 40)
    while True:
        cmd = ["squeue", "--job", job_id]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if job_id in result.stdout:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Job {job_id} is currently in queue/running.")
            time.sleep(check_interval_mins * 60)
        else:
            print(f"\nJob {job_id} is no longer in squeue. Assuming completion.")
            return True

def main():
    print("\n" + "="*80)
    print("BATCH JOB PIPELINE - STARTING")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # --- Ensure working directory exists ---
    os.makedirs(WORKING_DIR, exist_ok=True)
    
    # --- Build full paths for data directories ---
    data_dir = os.path.join(WORKING_DIR, DATA_FOLDER)
    oral_input_path = os.path.join(data_dir, ORAL_INPUT_FOLDER)
    oral_output_path = os.path.join(data_dir, ORAL_OUTPUT_FOLDER)
    
    # Create data directory structure if it doesn't exist
    os.makedirs(oral_input_path, exist_ok=True)
    os.makedirs(oral_output_path, exist_ok=True)
    print(f"Working directory: {WORKING_DIR}")
    print(f"Data directory: {data_dir}")
    print(f"Input path: {oral_input_path}")
    print(f"Output path: {oral_output_path}")

    # --- Create cache directory structure ---
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # --- Set environment variables for all cache paths and model_dir ---
    if HF_CACHE: 
        os.environ['HF_HOME'] = HF_CACHE
        os.makedirs(HF_CACHE, exist_ok=True)
    if PYTHON_CACHE: 
        os.makedirs(PYTHON_CACHE, exist_ok=True)
    if NLTK_CACHE: 
        os.environ['NLTK_DATA'] = NLTK_CACHE
        os.makedirs(NLTK_CACHE, exist_ok=True)
    if MODEL_CACHE: 
        os.environ['MODEL_CACHE'] = MODEL_CACHE
        os.makedirs(MODEL_CACHE, exist_ok=True)
    if MODEL_DIR: 
        os.environ['MODEL_DIR'] = MODEL_DIR
        os.makedirs(MODEL_DIR, exist_ok=True)
    
    # --- Create git repository parent directory ---
    git_repo_parent = os.path.dirname(GIT_REPO_PATH)
    if git_repo_parent:
        os.makedirs(git_repo_parent, exist_ok=True)
        print(f"Git repository parent directory: {git_repo_parent}")

    # Set PYTHONPATH for Python packages
    pythonpath_value = PYTHON_CACHE if PYTHON_CACHE else '/scratch/user/jvk_chaitanya/python_packages'
    existing_pythonpath = os.environ.get('PYTHONPATH', '')
    if existing_pythonpath:
        os.environ['PYTHONPATH'] = f"{pythonpath_value}:{existing_pythonpath}"
    else:
        os.environ['PYTHONPATH'] = pythonpath_value
    print(f"PYTHONPATH set to: {os.environ['PYTHONPATH']}")

    # --- PRE-CHECK: Get Password ---
    smb_password = SMB_PASSWORD
    if not smb_password:
        smb_password = os.environ.get('SMB_PASSWORD')
        if not smb_password:
            print("\n[INPUT REQUIRED] Please enter password for Network Share access:")
            try:
                smb_password = getpass.getpass(f"Password for {SMB_USERNAME}: ")
            except Exception as e:
                print(f"Error getting password: {e}")
                sys.exit(1)
    if not smb_password:
        print("Error: Password cannot be empty.")
        sys.exit(1)

    # --- PRE-CHECK: Get Git Token ---
    git_token = GIT_TOKEN
    if not git_token:
        git_token = os.environ.get('GIT_TOKEN')
        if not git_token:
            print("\n[INPUT REQUIRED] Please enter GitHub personal access token:")
            try:
                git_token = getpass.getpass(f"GitHub token for {GIT_USERNAME}: ")
            except Exception as e:
                print(f"Error getting token: {e}")
                sys.exit(1)
    if not git_token:
        print("Error: GitHub token cannot be empty.")
        sys.exit(1)

    # Step 1: Load Environment Modules (for HPC) - BEFORE creating venv
    log_step(1, "Load environment modules", "STARTED")
    print(f"Loading modules: {MODULE_LOAD_COMMAND}")
    if not run_command(
        MODULE_LOAD_COMMAND,
        1,
        f"Load environment modules ({MODULE_LOAD_COMMAND})",
        shell=True
    ):
        sys.exit(1)

    # Step 2: Export PYTHONPATH - BEFORE creating venv
    log_step(2, "Export PYTHONPATH environment variable", "STARTED")
    # PYTHONPATH is already set above, just confirm it
    export_cmd = f"export PYTHONPATH={os.environ['PYTHONPATH']}"
    print(f"Exporting: {export_cmd}")
    if not run_command(
        export_cmd,
        2,
        "Export PYTHONPATH for module access",
        shell=True
    ):
        print("Warning: Could not export PYTHONPATH (may already be set)")
    
    # Step 3: Check/Create Virtual Environment
    venv_python = os.path.join(VENV_PATH, "bin", "python")
    if not os.path.exists(venv_python):
        log_step(3, "Create Python virtual environment", "STARTED")
        print(f"Virtual environment not found at {VENV_PATH}")
        print("Creating new virtual environment...")
        if not run_command(
            f"python -m venv {VENV_PATH}",
            3,
            f"Create virtual environment at {VENV_PATH}",
            shell=True
        ):
            sys.exit(1)
    else:
        log_step(3, "Virtual environment already exists", "STARTED")
        print(f"Using existing virtual environment at {VENV_PATH}")
        log_step(3, "Virtual environment already exists", "COMPLETED")

    # Step 4: Use virtual environment Python for all subsequent commands
    python_cmd = venv_python
    print(f"Using Python: {python_cmd}")

    # Step 5: Clear files in data/oral_input/
    if not clear_directory(oral_input_path, 5, f"Clear files in {oral_input_path}"):
        sys.exit(1)

    # Step 6: Clear files in data/oral_output/
    if not clear_directory(oral_output_path, 6, f"Clear files in {oral_output_path}"):
        sys.exit(1)

    # Step 7: Run Network Download Script
    download_cmd = [
        python_cmd,
        DOWNLOAD_SCRIPT_PATH,
        "--sheet-url", SHEET_URL,
        "--username", SMB_USERNAME,
        "--password", smb_password,
        "--server", SMB_SERVER,
        "--share", SMB_SHARE,
        "--base-path", SMB_BASE_PATH,
        "--local-path", oral_input_path,
        "--max-folders", str(MAX_FOLDERS)
    ]

    log_cmd_display = download_cmd.copy()
    log_cmd_display[5] = "********"

    if not run_command(
        download_cmd,
        7,
        "Run Network Download Script"
    ):
        sys.exit(1)

    # Step 8: Download WhisperX models (if enabled and not already cached)
    # Note: WhisperX is installed via requirements.txt in venv
    # This step only downloads the model files for offline use
    if DOWNLOAD_MODELS_BEFORE_SLURM:
        log_step(8, "Checking/Downloading WhisperX model files", "STARTED")
        print("This ensures SLURM job can run offline without internet access.")
        print("Note: WhisperX package should already be installed in venv via requirements.txt")
        
        model_download_cmd = [
            python_cmd,
            MODEL_DOWNLOAD_SCRIPT_PATH,
            "--model", WHISPER_MODEL,
            "--cache-dir", HF_CACHE,
            "--compute-type", COMPUTE_TYPE,
            "--languages"
        ] + ALIGNMENT_LANGUAGES
        
        if not run_command(
            model_download_cmd,
            8,
            "Download WhisperX model files for offline use"
        ):
            print("Warning: Model download failed. SLURM job may fail if it needs to download models.")
            # Don't exit - let user decide if they want to continue

    # Step 9: Update cache paths in slurm job file before submission
    slurm_job_path = os.path.abspath(SLURM_JOB_PATH)
    # Read slurm job file
    with open(slurm_job_path, "r") as f:
        slurm_content = f.read()

    # Replace cache paths and model_dir using config values
    # Note: Update these old paths if your SLURM file contains them
    if HF_CACHE:
        slurm_content = slurm_content.replace("/scratch/user/jvk_chaitanya/hf_cache", HF_CACHE)
    if PYTHON_CACHE:
        slurm_content = slurm_content.replace("/scratch/user/jvk_chaitanya/python_packages", PYTHON_CACHE)
    if NLTK_CACHE:
        slurm_content = slurm_content.replace("/scratch/user/jvk_chaitanya/nltk_data", NLTK_CACHE)
    if MODEL_CACHE:
        slurm_content = slurm_content.replace("/scratch/user/jvk_chaitanya/hf_cache/hub/models--Systran--faster-whisper-large-v3/snapshots/edaa852ec7e145841d8ffdb056a99866b5f0a478", MODEL_CACHE)
    if MODEL_DIR:
        # Replace any model-dir argument or path in slurm job file
        slurm_content = re.sub(r'(--model-dir\s+)("[^"]*"|\S+)', f'\\1"{MODEL_DIR}"', slurm_content)

    # Overwrite the main slurm job file with updated content
    with open(slurm_job_path, "w") as f:
        f.write(slurm_content)

    job_id = submit_slurm_job(
        slurm_job_path,
        9,
        f"Submit batch job ({slurm_job_path})"
    )

    if not job_id:
        print("Failed to submit batch job. Exiting.")
        sys.exit(1)

    # Step 10: Monitor the job
    monitor_job_status(job_id, CHECK_INTERVAL_MINS)

    # Step 11: Trigger Git Upload (Only runs after monitor finishes)
    git_repo_path = os.path.abspath(GIT_REPO_PATH)
    git_upload_cmd = [
        python_cmd,
        GIT_UPLOAD_SCRIPT_PATH,
        "--source-path", oral_output_path,
        "--repo-path", git_repo_path,
        "--owner", GIT_OWNER,
        "--repo-name", GIT_REPO_NAME,
        "--username", GIT_USERNAME,
        "--token", git_token
    ]

    if not run_command(
        git_upload_cmd,
        11,
        "Run Git_upload.py to upload files to github"
    ):
        sys.exit(1)

    # Final Completion
    log_step(12, "All steps completed successfully", "COMPLETED")

    print("\n" + "="*80)
    print("BATCH JOB PIPELINE - FINISHED")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()