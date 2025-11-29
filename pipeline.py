#!/usr/bin/env python3
"""
Batch job pipeline for processing speech data
Executes steps sequentially with logging after each completion
Updated to use refactored whisperx_automation package with new CLI tools.
Configuration is loaded from config/config.yaml - NO HARDCODED VALUES!
"""

import subprocess
import sys
import os
import re
import time
import getpass
from datetime import datetime
from pathlib import Path

# =================CONFIGURATION=================
# Pipeline Settings
CHECK_INTERVAL_MINS = 5

# Project paths (relative to this script)
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR
VENV_DIR = PROJECT_ROOT / "venv"
CONFIG_FILE = PROJECT_ROOT / "config" / "config.yaml"

# All other configuration is loaded from config.yaml in main()
# ===============================================

def log_step(step_num, description, status="STARTED"):
    """Print formatted log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*80}")
    print(f"[{timestamp}] Step {step_num}: {description} - {status}")
    print(f"{'='*80}\n")

def run_command(cmd, step_num, description, shell=False, env=None, cwd=None):
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
                                   text=True, executable='/bin/bash', env=run_env, cwd=cwd)
        else:
            result = subprocess.run(cmd, check=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                   text=True, env=run_env, cwd=cwd)
        
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

def check_create_venv(venv_path, step_num, description):
    """Check if venv exists, create if not, and ensure dependencies are installed"""
    log_step(step_num, description, "STARTED")
    
    pip_path = venv_path / "bin" / "pip" if os.name != 'nt' else venv_path / "Scripts" / "pip.exe"
    
    try:
        # Create venv if it doesn't exist
        if not venv_path.exists():
            print(f"Creating virtual environment at: {venv_path}")
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(f"Virtual environment created successfully")
        else:
            print(f"Virtual environment found at: {venv_path}")
        
        # Always ensure dependencies are installed (whether venv is new or existing)
        print("Checking and installing dependencies...")
        
        # Upgrade pip first
        print("Upgrading pip...")
        subprocess.run(
            [str(pip_path), "install", "--upgrade", "pip"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT)
        )
        
        # Install requirements
        print("Installing dependencies from requirements.txt...")
        subprocess.run(
            [str(pip_path), "install", "-r", "requirements.txt"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT)
        )
        
        # Install package in editable mode
        print("Installing whisperx_automation package in editable mode...")
        subprocess.run(
            [str(pip_path), "install", "-e", "."],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT)
        )
        
        print("✓ All dependencies installed successfully")
        log_step(step_num, description, "COMPLETED")
        return True
            
    except Exception as e:
        log_step(step_num, description, "FAILED")
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

def submit_slurm_job(sbatch_path, step_num, description):
    """Submits sbatch job, parses output for Job ID."""
    log_step(step_num, description, "STARTED")
    cmd = ["sbatch", str(sbatch_path)]
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
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Config File: {CONFIG_FILE}")
    print("="*80)

    # Step 1: Load modules FIRST (cluster needs this for Python)
    if not run_command(
        "ml GCCcore/10.3.0 FFmpeg CUDA Python",
        1,
        "Load modules (GCCcore/10.3.0 FFmpeg CUDA Python)",
        shell=True
    ):
        print("Warning: Module loading failed (ignore if not on cluster)")
    
    # Step 2: Check/Create Virtual Environment (now that Python is available)
    if not check_create_venv(VENV_DIR, 2, "Check/Create virtual environment"):
        sys.exit(1)
    
    # Determine python path
    if os.name == 'nt':  # Windows
        python_path = VENV_DIR / "Scripts" / "python.exe"
    else:  # Linux/Mac
        python_path = VENV_DIR / "bin" / "python"
    
    # Step 3: Load Configuration from config.yaml
    log_step(3, "Load configuration from config.yaml", "STARTED")
    
    # Add src to path for importing
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    
    try:
        # Try to import ConfigManager
        from whisperx_automation.utils.config import ConfigManager
    except ImportError as e:
        # If import fails due to missing dependencies, reinstall the package
        print(f"⚠ Package dependencies not fully installed: {e}")
        print("Reinstalling package with dependencies...")
        
        pip_path = VENV_DIR / "bin" / "pip" if os.name != 'nt' else VENV_DIR / "Scripts" / "pip.exe"
        
        try:
            subprocess.run(
                [str(pip_path), "install", "-e", str(PROJECT_ROOT)],
                check=True,
                cwd=str(PROJECT_ROOT)
            )
            print("✓ Package reinstalled successfully")
            
            # Try importing again
            from whisperx_automation.utils.config import ConfigManager
        except Exception as install_error:
            print(f"✗ Failed to install dependencies: {install_error}")
            print("Falling back to defaults...")
            # Set a flag to skip config loading
            ConfigManager = None
    
    if ConfigManager is not None:
        try:
            config = ConfigManager(str(CONFIG_FILE))
            print(f"✓ Configuration loaded from: {CONFIG_FILE}")
            
            # Extract configuration values
            ORAL_INPUT_PATH = PROJECT_ROOT / "data" / "oral_input"
            ORAL_OUTPUT_PATH = PROJECT_ROOT / "data" / "oral_output"
            GIT_REPO_PATH = PROJECT_ROOT.parent / "git_repo"
            
            SMB_SERVER = config.get('smb.server', 'cifs.library.tamu.edu')
            SMB_SHARE = config.get('smb.share', 'digital_project_management')
            SMB_BASE_PATH = config.get('smb.base_path', 'edge-grant/GB_38253_MP3s')
            NETID_USERNAME = config.get('smb.username', os.environ.get('SMB_USERNAME', 'jvk_chaitanya'))
            
            SHEET_URL = config.get('google_sheets.url', os.environ.get('SHEET_URL', ''))
            MAX_FOLDERS = config.get('google_sheets.max_folders', 20)
            
            GIT_OWNER = config.get('git.owner', 'tamulib-dc-labs')
            GIT_REPO = config.get('git.repo', 'edge-grant-json-and-vtts')
            GIT_USERNAME = config.get('git.username', os.environ.get('GIT_USERNAME', NETID_USERNAME))
            GIT_TOKEN = config.get('git.token', '')  # Read token from config
            
            SLURM_JOB_PATH = PROJECT_ROOT / "run_1.slurm"
            
            print(f"✓ Paths: input={ORAL_INPUT_PATH.name}, output={ORAL_OUTPUT_PATH.name}")
            print(f"✓ SMB: {SMB_SERVER}/{SMB_SHARE}/{SMB_BASE_PATH}")
            print(f"✓ Git: {GIT_OWNER}/{GIT_REPO}")
            
            log_step(3, "Load configuration from config.yaml", "COMPLETED")
        except Exception as e:
            print(f"⚠ Warning: Could not load config.yaml: {e}")
            print("Using default fallback values...")
            ConfigManager = None  # Trigger fallback
    
    if ConfigManager is None:
        # Fallback to defaults (config loading failed)
        ORAL_INPUT_PATH = PROJECT_ROOT / "data" / "oral_input"
        ORAL_OUTPUT_PATH = PROJECT_ROOT / "data" / "oral_output"
        GIT_REPO_PATH = PROJECT_ROOT.parent / "git_repo"
        SMB_SERVER = "cifs.library.tamu.edu"
        SMB_SHARE = "digital_project_management"
        SMB_BASE_PATH = "edge-grant/GB_38253_MP3s"
        NETID_USERNAME = "jvk_chaitanya"
        SHEET_URL = os.environ.get('SHEET_URL', '')
        MAX_FOLDERS = 20
        GIT_OWNER = "tamulib-dc-labs"
        GIT_REPO = "edge-grant-json-and-vtts"
        GIT_USERNAME = NETID_USERNAME
        GIT_TOKEN = ''  # Will check env var and prompt if needed
        SLURM_JOB_PATH = PROJECT_ROOT / "run_1.slurm"
    
    # ---GET Passwords/Tokens ---
    smb_password = os.environ.get('SMB_PASSWORD')
    if not smb_password:
        print("\n[INPUT REQUIRED] Please enter password for Network Share access:")
        try:
            smb_password = getpass.getpass(f"Password for {NETID_USERNAME}: ")
        except Exception as e:
            print(f"Error getting password: {e}")
            sys.exit(1)
    
    if not smb_password:
        print("Error: SMB password cannot be empty.")
        sys.exit(1)
    
    # Git Token: Priority: config.yaml > environment variable > prompt
    if not GIT_TOKEN:
        GIT_TOKEN = os.environ.get('GIT_TOKEN', '')
    else:
        print(f"✓ Git token loaded from config.yaml")
    
    if not GIT_TOKEN:
        print("\n[INPUT REQUIRED] Please enter GitHub personal access token:")
        try:
            GIT_TOKEN = getpass.getpass("GitHub Token: ")
        except Exception as e:
            print(f"Error getting token: {e}")
            sys.exit(1)
    
    if not GIT_TOKEN:
        print("Error: GitHub token cannot be empty.")
        sys.exit(1)
    
    # Step 4: Set environment variables
    log_step(4, "Set environment variables", "STARTED")
    pythonpath_value = str(PROJECT_ROOT / "src")
    existing_pythonpath = os.environ.get('PYTHONPATH', '')
    if existing_pythonpath:
        os.environ['PYTHONPATH'] = f"{pythonpath_value}:{existing_pythonpath}"
    else:
        os.environ['PYTHONPATH'] = pythonpath_value
    print(f"PYTHONPATH={os.environ['PYTHONPATH']}")
    log_step(4, "Set environment variables", "COMPLETED")
    
    # Step 5: Clear files in oral_input/
    if not clear_directory(str(ORAL_INPUT_PATH), 5, f"Clear files in {ORAL_INPUT_PATH}"):
        sys.exit(1)
    
    # Step 6: Clear files in oral_output/
    if not clear_directory(str(ORAL_OUTPUT_PATH), 6, f"Clear files in {ORAL_OUTPUT_PATH}"):
        sys.exit(1)
    
    # Step 7: Run Download Script
    print(f"\n{'='*80}")
    print("Running whisperx-download CLI")
    print(f"{'='*80}\n")
    
    download_cmd = [
        str(python_path), "-m", "whisperx_automation.cli.download_cli",
        "--sheet-url", SHEET_URL,
        "--username", NETID_USERNAME,
        "--password", smb_password,
        "--server", SMB_SERVER,
        "--share", SMB_SHARE,
        "--base-path", SMB_BASE_PATH,
        "--local-path", str(ORAL_INPUT_PATH),
        "--max-folders", str(MAX_FOLDERS)
    ]
    
    if not run_command(download_cmd, 7, "Run Download Script"):
        sys.exit(1)
    
    # Step 8: Run sbatch run_1.slurm AND Monitor
    if SLURM_JOB_PATH.exists():
        job_id = submit_slurm_job(SLURM_JOB_PATH, 8, "Submit batch job (run_1.slurm)")
        
        if not job_id:
            print("Failed to submit batch job. Exiting.")
            sys.exit(1)

        # Step 9: Monitor the job
        monitor_job_status(job_id, CHECK_INTERVAL_MINS)
    else:
        print(f"\n⚠ Warning: Slurm job file not found at {SLURM_JOB_PATH}")
        print("Skipping Slurm job submission")
    
    # Step 10: Run Git Upload
    print(f"\n{'='*80}")
    print("Running whisperx-upload CLI")
    print(f"{'='*80}\n")
    
    git_upload_cmd = [
        str(python_path), "-m", "whisperx_automation.cli.upload_cli",
        "--source-path", str(ORAL_OUTPUT_PATH),
        "--repo-path", str(GIT_REPO_PATH),
        "--owner", GIT_OWNER,
        "--repo", GIT_REPO,
        "--username", GIT_USERNAME,
        "--token", GIT_TOKEN
    ]

    if not run_command(git_upload_cmd, 10, "Run Git Upload"):
        sys.exit(1)
    
    # Final Completion
    log_step(11, "All steps completed successfully", "COMPLETED")
    
    print("\n" + "="*80)
    print("BATCH JOB PIPELINE - FINISHED")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
