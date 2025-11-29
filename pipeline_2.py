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
from config import load_config

# Load configuration
config = load_config()

# =================CONFIGURATION=================
# Extract from config
CHECK_INTERVAL_MINS = config['pipeline']['check_interval_mins']

# Network Share Settings
DOWNLOAD_SCRIPT_PATH = config['paths']['download_script']

# SMB Connection Details
SMB_SERVER = config['smb']['server']
SMB_SHARE = config['smb']['share']
SMB_BASE_PATH = config['smb']['base_path']
NETID_USERNAME = config['credentials']['netid_username']

# Google Sheet
SHEET_URL = config['google_sheets']['sheet_url']

# Paths
ORAL_INPUT_PATH = config['paths']['oral_input']
ORAL_OUTPUT_PATH = config['paths']['oral_output']
SLURM_SCRIPT_PATH = config['paths']['slurm_script']
GIT_UPLOAD_SCRIPT = config['paths']['git_upload_script']
PYTHONPATH_VALUE = config['paths']['pythonpath']
VENV_ACTIVATE = config['pipeline']['venv_activate']
MODULE_LOAD_CMD = config['pipeline']['module_load_cmd']
MAX_FOLDERS = str(config['pipeline']['max_folders'])
# ===============================================

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

    # --- PRE-CHECK: Get Password ---
    # Try to get password from environment variable first (good for automation)
    smb_password = os.environ.get('SMB_PASSWORD')
    
    if not smb_password:
        # If not in environment, ask interactively
        print("\n[INPUT REQUIRED] Please enter password for Network Share access:")
        try:
            smb_password = getpass.getpass(f"Password for {NETID_USERNAME}: ")
        except Exception as e:
            print(f"Error getting password: {e}")
            sys.exit(1)
    
    if not smb_password:
        print("Error: Password cannot be empty.")
        sys.exit(1)

    # Step 1: Run module load command
    if not run_command(
        MODULE_LOAD_CMD,
        1,
        f"Load modules ({MODULE_LOAD_CMD})",
        shell=True
    ):
        sys.exit(1)
    
    # Step 2: Activate Python virtual environment
    if not run_command(
        f"source {VENV_ACTIVATE}",
        2,
        "Activate Python virtual environment",
        shell=True
    ):
        sys.exit(1)
    
    # Step 3: Set PYTHONPATH
    existing_pythonpath = os.environ.get('PYTHONPATH', '')
    if existing_pythonpath:
        os.environ['PYTHONPATH'] = f"{PYTHONPATH_VALUE}:{existing_pythonpath}"
    else:
        os.environ['PYTHONPATH'] = PYTHONPATH_VALUE
    
    log_step(3, "Set PYTHONPATH environment variable", "STARTED")
    print(f"PYTHONPATH={os.environ['PYTHONPATH']}")
    log_step(3, "Set PYTHONPATH environment variable", "COMPLETED")
    
    # Step 4: Clear files in oral_input/
    if not clear_directory(ORAL_INPUT_PATH, 4, f"Clear files in {ORAL_INPUT_PATH}"):
        sys.exit(1)
    
    # Step 5: Clear files in oral_output/
    if not clear_directory(ORAL_OUTPUT_PATH, 5, f"Clear files in {ORAL_OUTPUT_PATH}"):
        sys.exit(1)
    
    # Step 6: Run Network Download Script (Replaces Dropbox)
    download_cmd = [
        "python",
        DOWNLOAD_SCRIPT_PATH,
        "--sheet-url", SHEET_URL,
        "--username", NETID_USERNAME,
        "--password", smb_password,  # Passed safely from variable
        "--server", SMB_SERVER,
        "--share", SMB_SHARE,
        "--base-path", SMB_BASE_PATH,
        "--local-path", ORAL_INPUT_PATH,
        "--max-folders", MAX_FOLDERS
    ]
    
    # Mask password in logs just in case
    log_cmd_display = download_cmd.copy()
    log_cmd_display[5] = "********" 
    
    if not run_command(
        download_cmd,
        6,
        "Run Network Download Script"
    ):
        sys.exit(1)
    
    # Step 7: Run sbatch script AND Monitor
    job_id = submit_slurm_job(
        SLURM_SCRIPT_PATH,
        7,
        f"Submit batch job ({SLURM_SCRIPT_PATH})"
    )
    
    if not job_id:
        print("Failed to submit batch job. Exiting.")
        sys.exit(1)

    # Step 8: Monitor the job
    monitor_job_status(job_id, CHECK_INTERVAL_MINS)

    # Step 9: Trigger Git Upload (Only runs after monitor finishes)
    git_upload_cmd = [
        "python",
        GIT_UPLOAD_SCRIPT
    ]

    if not run_command(
        git_upload_cmd,
        9,
        "Run Git_upload.py to upload files to github"
    ):
        sys.exit(1)
    
    # Final Completion
    log_step(10, "All steps completed successfully", "COMPLETED")
    
    print("\n" + "="*80)
    print("BATCH JOB PIPELINE - FINISHED")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()