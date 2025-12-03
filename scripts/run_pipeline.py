#!/usr/bin/env python3
"""
WhisperX Transcription Automation Pipeline - Entry Point

This is the main entry point for running the transcription pipeline.
All configuration is managed in src/config.py
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from src.pipeline import TranscriptionPipeline
from src.utils.logger import Logger


def main():
    """Main entry point for the pipeline."""
    try:
        pipeline = TranscriptionPipeline()
        pipeline.run()
    except KeyboardInterrupt:
        Logger.log_warning("\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        Logger.log_error(f"Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
