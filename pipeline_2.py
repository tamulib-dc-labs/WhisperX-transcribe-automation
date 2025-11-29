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
import yaml

# =================CONFIGURATION=================
# Pipeline Settings
CHECK_INTERVAL_MINS = 5

# Network Share Settings
# CHANGE THIS to the actual name of your script file
DOWNLOAD_SCRIPT_PATH = "/scratch/user/jvk_chaitanya/libraries/speech_text/download_automation_3.py" 

# SMB Connection Details
SMB_SERVER = "cifs.library.tamu.edu"
SMB_SHARE = "digital_project_management"  # <--- UPDATE THIS (e.g., 'projects', 'reserves', 'staff')
SMB_BASE_PATH = "edge-grant/GB_38253_MP3s" # Path inside the share
NETID_USERNAME = "jvk_chaitanya"

# Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/16cHa57n7rJmS744nMH2dY2H4IKLP5fMeHJ0iY8w85EM/edit?usp=sharing"
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

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    print("\n" + "="*80)
    print("BATCH JOB PIPELINE - STARTING")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)


    # Load config
    config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
    config = load_config(config_path)

    # --- Set environment variables for all cache paths and model_dir ---
    cache = config.get("cache", {})
    model_dir = config.get("model", {}).get("model_dir", None)
    if cache.get("huggingface_cache"): os.environ['HF_HOME'] = cache["huggingface_cache"]
    if cache.get("python_cache"): os.environ['PYTHONPATH'] = cache["python_cache"]
    if cache.get("nltk_data"): os.environ['NLTK_DATA'] = cache["nltk_data"]
    if cache.get("model_cache"): os.environ['MODEL_CACHE'] = cache["model_cache"]
    if model_dir: os.environ['MODEL_DIR'] = model_dir

    # Step 3.5: Inject model_dir into download and slurm job commands if needed
    # Update download_cmd if model_dir is required
    if model_dir:
        download_cmd.extend(["--model-dir", model_dir])

    # --- PRE-CHECK: Get Password ---
    smb_password = config["smb"].get("password")
    if not smb_password:
        smb_password = os.environ.get('SMB_PASSWORD')
        if not smb_password:
            print("\n[INPUT REQUIRED] Please enter password for Network Share access:")
            try:
                smb_password = getpass.getpass(f"Password for {config['smb'].get('username', 'username')}: ")
            except Exception as e:
                print(f"Error getting password: {e}")
                sys.exit(1)
    if not smb_password:
        print("Error: Password cannot be empty.")
        sys.exit(1)

    # Step 1: Run ml GCCcore/10.3.0 FFmpeg CUDA Python
    if not run_command(
        "ml GCCcore/10.3.0 FFmpeg CUDA Python",
        1,
        "Load modules (GCCcore/10.3.0 FFmpeg CUDA Python)",
        shell=True
    ):
        sys.exit(1)

    # Step 2: Activate Python virtual environment
    if not run_command(
        "source $SCRATCH/libraries/dlvenv/bin/activate",
        2,
        "Activate Python virtual environment",
        shell=True
    ):
        sys.exit(1)

    # Step 3: Set PYTHONPATH
    pythonpath_value = '/scratch/user/jvk_chaitanya/python_packages'
    existing_pythonpath = os.environ.get('PYTHONPATH', '')
    if existing_pythonpath:
        os.environ['PYTHONPATH'] = f"{pythonpath_value}:{existing_pythonpath}"
    else:
        os.environ['PYTHONPATH'] = pythonpath_value

    log_step(3, "Set PYTHONPATH environment variable", "STARTED")
    print(f"PYTHONPATH={os.environ['PYTHONPATH']}")
    log_step(3, "Set PYTHONPATH environment variable", "COMPLETED")

    # Step 4: Clear files in data/oral_input/
    oral_input_path = os.path.abspath(config["paths"]["oral_input"])
    if not clear_directory(oral_input_path, 4, f"Clear files in {oral_input_path}"):
        sys.exit(1)

    # Step 5: Clear files in data/oral_output/
    oral_output_path = os.path.abspath(config["paths"]["oral_output"])
    if not clear_directory(oral_output_path, 5, f"Clear files in {oral_output_path}"):
        sys.exit(1)

    # Step 6: Run Network Download Script (Replaces Dropbox)
    download_cmd = [
        "python",
        config.get("download_script_path", "download_automation_3.py"),
        "--sheet-url", config["google_sheets"]["url"],
        "--username", config["smb"]["username"],
        "--password", smb_password,
        "--server", config["smb"]["server"],
        "--share", config["smb"]["share"],
        "--base-path", config["smb"].get("base_path", ""),
        "--local-path", oral_input_path,
        "--max-folders", str(config["google_sheets"].get("max_folders", 20))
    ]

    log_cmd_display = download_cmd.copy()
    log_cmd_display[5] = "********"

    if not run_command(
        download_cmd,
        6,
        "Run Network Download Script"
    ):
        sys.exit(1)



    # Step 7: Update cache paths in slurm job file before submission
    slurm_job_path = os.path.abspath(config.get("slurm_job_path", "run_1.slurm"))
    # Read slurm job file
    with open(slurm_job_path, "r") as f:
        slurm_content = f.read()

    # Replace cache paths and model_dir using config values
    cache = config.get("cache", {})
    slurm_content = slurm_content.replace("/scratch/user/jvk_chaitanya/hf_cache", cache.get("huggingface_cache", "./hf_cache"))
    slurm_content = slurm_content.replace("/scratch/user/jvk_chaitanya/python_packages", cache.get("python_cache", "./.pycache"))
    slurm_content = slurm_content.replace("/scratch/user/jvk_chaitanya/nltk_data", cache.get("nltk_data", "./nltk_data"))
    slurm_content = slurm_content.replace("/scratch/user/jvk_chaitanya/hf_cache/hub/models--Systran--faster-whisper-large-v3/snapshots/edaa852ec7e145841d8ffdb056a99866b5f0a478", cache.get("model_cache", "./model_cache"))
    if model_dir:
        # Replace any model-dir argument or path in slurm job file
        slurm_content = re.sub(r'(--model-dir\s+)("[^"]*"|\S+)', f'\1"{model_dir}"', slurm_content)

    # Overwrite the main slurm job file with updated content
    with open(slurm_job_path, "w") as f:
        f.write(slurm_content)

    job_id = submit_slurm_job(
        slurm_job_path,
        7,
        f"Submit batch job ({slurm_job_path})"
    )

    if not job_id:
        print("Failed to submit batch job. Exiting.")
        sys.exit(1)

    # Step 8: Monitor the job
    monitor_job_status(job_id, CHECK_INTERVAL_MINS)

    # Step 9: Trigger Git Upload (Only runs after monitor finishes)
    git_repo_path = os.path.abspath(config["paths"]["git_repo"])
    git_upload_cmd = [
        "python",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "git_upload.py")),
        "--repo-path", git_repo_path
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