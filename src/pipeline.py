"""
Main pipeline orchestrator for WhisperX Transcription Automation.

This module coordinates all pipeline steps including:
- Environment setup
- File downloads
- Model preparation
- SLURM job submission
- Git upload
"""

import os
import sys
import time
import subprocess
from pathlib import Path

from src.config import get_config
from src.utils.file_manager import FileManager, CommandRunner
from src.utils.logger import Logger
from src.git.uploader import GitUploader
from src.transcription.model_downloader import ModelDownloader


class TranscriptionPipeline:
    """Main pipeline orchestrator."""
    
    def __init__(self):
        """Initialize the pipeline with configuration."""
        self.config = get_config()
        self.file_manager = FileManager()
        self.command_runner = CommandRunner()
    
    def run(self):
        """Execute the complete pipeline."""
        Logger.log_info("Starting Transcription Automation Pipeline")
        Logger.log_info(f"Working directory: {self.config.working_dir}")
        
        # Step 1: Load environment modules
        self._load_modules()
        
        # Step 2: Setup Python environment
        self._setup_python_environment()
        
        # Step 3: Prepare directories
        self._prepare_directories()
        
        # Step 4: Download audio files
        self._download_audio_files()
        
        # Step 5: Download models
        if self.config.download_models_before_slurm:
            self._download_models()
        
        # Step 6: Download NLTK data
        self._download_nltk_data()
        
        # Step 7: Submit SLURM job
        job_id = self._submit_slurm_job()
        
        if job_id:
            # Step 8: Monitor job
            self._monitor_slurm_job(job_id)
            
            # Step 9: Upload results to GitHub
            self._upload_to_github()
        
        Logger.log_info("Pipeline execution completed")
    
    def _load_modules(self):
        """Load required environment modules."""
        Logger.log_step(1, "Load environment modules", "STARTED")
        try:
            subprocess.run(
                self.config.module_load_command,
                shell=True,
                check=True,
                executable='/bin/bash'
            )
            Logger.log_step(1, "Load environment modules", "COMPLETED")
        except Exception as e:
            Logger.log_warning(f"Failed to load modules: {e}. Continuing anyway...")
    
    def _setup_python_environment(self):
        """Setup or verify Python virtual environment."""
        venv_exists = os.path.exists(self.config.venv_python)
        
        if not venv_exists:
            # Create venv
            if not self.command_runner.run(
                f"python -m venv {self.config.venv_path}",
                3,
                f"Create virtual environment at {self.config.venv_path}",
                shell=True
            ):
                sys.exit(1)
            
            # Install requirements
            if os.path.exists(self.config.requirements_path):
                Logger.log_step("3.5", "Install Python dependencies", "STARTED")
                if not self.command_runner.run(
                    f"{self.config.venv_pip} install -r {self.config.requirements_path}",
                    "3.5",
                    "Install dependencies from requirements.txt",
                    shell=True
                ):
                    Logger.log_warning("Failed to install some dependencies")
        else:
            Logger.log_step(3, "Using existing virtual environment", "COMPLETED")
    
    def _prepare_directories(self):
        """Clear and prepare input/output directories."""
        # Clear input directory
        self.file_manager.clear_directory(self.config.oral_input_path)
        Logger.log_step(4, f"Cleared {self.config.oral_input_path}", "COMPLETED")
        
        # Clear output directory
        self.file_manager.clear_directory(self.config.oral_output_path)
        Logger.log_step(5, f"Cleared {self.config.oral_output_path}", "COMPLETED")
    
    def _download_audio_files(self):
        """Download audio files using download script."""
        Logger.log_step(6, "Download audio files from network share", "STARTED")
        
        password = self.config.get_smb_password()
        
        download_cmd = [
            self.config.venv_python,
            self.config.download_script_path,
            "--server", self.config.smb_server,
            "--share", self.config.smb_share,
            "--username", self.config.smb_username,
            "--password", password,
            "--base-path", self.config.smb_base_path,
            "--local-path", self.config.oral_input_path,
            "--sheet-url", self.config.sheet_url,
            "--max-folders", str(self.config.max_folders)
        ]
        
        if not self.command_runner.run(download_cmd, 6, "Download audio files"):
            sys.exit(1)
    
    def _download_models(self):
        """Download WhisperX models for offline use."""
        Logger.log_step(7, "Download WhisperX models", "STARTED")
        
        downloader = ModelDownloader(cache_dir=self.config.hf_cache)
        if not downloader.download_models(
            model_name=self.config.whisper_model,
            languages=self.config.alignment_languages,
            compute_type="int8"  # Use int8 for CPU download
        ):
            Logger.log_warning("Model download failed")
    
    def _download_nltk_data(self):
        """Download NLTK punkt_tab data."""
        Logger.log_step("7.5", "Download NLTK data", "STARTED")
        
        nltk_script = f"""
import nltk
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

nltk.download('punkt_tab', download_dir='{self.config.nltk_cache}', quiet=False)
print("✓ NLTK punkt_tab downloaded successfully")
"""
        
        nltk_cmd = [self.config.venv_python, "-c", nltk_script]
        self.command_runner.run(nltk_cmd, "7.5", "Download NLTK punkt_tab data")
    
    def _submit_slurm_job(self) -> str:
        """Inject paths and submit SLURM job."""
        Logger.log_step(8, "Update and submit SLURM job", "STARTED")
        
        # Read SLURM template
        with open(self.config.slurm_job_path, "r") as f:
            slurm_content = f.read()
        
        # Inject paths
        slurm_content = slurm_content.replace("{{VENV_ACTIVATE_PATH}}", f"{self.config.venv_path}/bin/activate")
        slurm_content = slurm_content.replace("{{HF_CACHE}}", self.config.hf_cache)
        slurm_content = slurm_content.replace("{{NLTK_CACHE}}", self.config.nltk_cache)
        slurm_content = slurm_content.replace("{{TRANSCRIBE_SCRIPT}}", self.config.transcribe_script_path)
        slurm_content = slurm_content.replace("{{WHISPER_MODEL}}", self.config.whisper_model)
        slurm_content = slurm_content.replace("{{ORAL_INPUT_PATH}}", self.config.oral_input_path)
        slurm_content = slurm_content.replace("{{ORAL_OUTPUT_PATH}}", self.config.oral_output_path)
        
        # Write updated SLURM file
        updated_slurm = os.path.join(self.config.working_dir, "run_job.slurm")
        with open(updated_slurm, "w") as f:
            f.write(slurm_content)
        
        # Submit job
        job_id = self.command_runner.submit_slurm_job(updated_slurm)
        return job_id
    
    def _monitor_slurm_job(self, job_id: str):
        """Monitor SLURM job until completion."""
        Logger.log_step(9, f"Monitor SLURM job {job_id}", "STARTED")
        
        while True:
            status = self.command_runner.check_slurm_job_status(job_id)
            
            if status in ["COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"]:
                Logger.log_info(f"Job {job_id} finished with status: {status}")
                break
            
            Logger.log_info(f"Job {job_id} status: {status}")
            time.sleep(self.config.check_interval_mins * 60)
    
    def _upload_to_github(self):
        """Upload transcription results to GitHub."""
        Logger.log_step(10, "Upload results to GitHub", "STARTED")
        
        token = self.config.get_git_token()
        
        uploader = GitUploader(
            source_folder=self.config.oral_output_path,
            repo_folder=self.config.git_repo_path,
            owner=self.config.git_owner,
            repo_name=self.config.git_repo_name,
            username=self.config.git_username,
            token=token
        )
        
        if uploader.upload():
            Logger.log_step(10, "Upload results to GitHub", "COMPLETED")
        else:
            Logger.log_error("GitHub upload failed")
