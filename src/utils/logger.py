"""
Logging utilities for the transcription pipeline.
"""

from datetime import datetime


class Logger:
    """Handles logging for the pipeline."""
    
    @staticmethod
    def log_step(step_num, description: str, status: str = "STARTED"):
        """
        Print formatted log message with timestamp.
        
        Args:
            step_num: Step number (can be int or string like "3.5")
            description: Description of the step
            status: Status (STARTED, COMPLETED, FAILED, etc.)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{'='*80}")
        print(f"[{timestamp}] Step {step_num}: {description} - {status}")
        print(f"{'='*80}\n")
    
    @staticmethod
    def log_info(message: str):
        """Log an info message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] INFO: {message}")
    
    @staticmethod
    def log_warning(message: str):
        """Log a warning message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] WARNING: {message}")
    
    @staticmethod
    def log_error(message: str):
        """Log an error message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] ERROR: {message}")
