#!/usr/bin/env python3
"""
Download WhisperX models and alignment models for offline use.
This should be run before submitting SLURM jobs that don't have internet access.
"""

import os
import sys
import argparse
import whisperx
import torch

def download_models(model_name="large-v3", cache_dir=None, languages=None, compute_type="float16"):
    """
    Download WhisperX models and alignment models.
    
    Args:
        model_name: WhisperX model to download (tiny, base, small, medium, large-v2, large-v3, turbo)
        cache_dir: Directory to cache models (uses HF_HOME if not specified)
        languages: List of language codes for alignment models (default: ["en", "es", "fr", "de"])
        compute_type: Compute type for the model (float16, float32, int8)
    """
    # Set HF cache if provided
    if cache_dir:
        os.environ['HF_HOME'] = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        print(f"Using cache directory: {cache_dir}")
    
    # Set offline mode to False for downloading
    os.environ['HF_HUB_OFFLINE'] = '0'
    
    # Auto-detect device (GPU if available, else CPU)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Adjust compute type based on device
    if device == "cpu" and compute_type == "float16":
        print("Warning: CPU detected, float16 not supported. Using int8 instead.")
        compute_type = "int8"
    
    print(f"Using device: {device}, compute_type: {compute_type}")
    
    if languages is None:
        languages = ["en", "es", "fr", "de"]
    
    print(f"Downloading WhisperX model: {model_name}...")
    print("This may take several minutes for large models...")
    print(f"Model will be cached at: {os.environ.get('HF_HOME', 'default cache')}")
    sys.stdout.flush()  # Force output to show immediately
    
    try:
        model = whisperx.load_model(model_name, device, compute_type=compute_type)
        print(f"✓ WhisperX model '{model_name}' downloaded successfully!")
        sys.stdout.flush()
        del model
    except Exception as e:
        print(f"✗ Error downloading WhisperX model: {e}")
        sys.stdout.flush()
        return False
    
    print(f"\nDownloading alignment models for languages: {', '.join(languages)}...")
    sys.stdout.flush()
    for lang in languages:
        try:
            print(f"  Downloading alignment model for '{lang}'...")
            sys.stdout.flush()
            align_model, metadata = whisperx.load_align_model(language_code=lang, device=device)
            print(f"  ✓ Alignment model for '{lang}' downloaded!")
            sys.stdout.flush()
            del align_model
        except Exception as e:
            print(f"  ✗ Could not download alignment for '{lang}': {e}")
            sys.stdout.flush()
    
    cache_location = os.environ.get('HF_HOME', 'default HuggingFace cache')
    print(f"\n{'='*60}")
    print(f"All models downloaded to: {cache_location}")
    print(f"{'='*60}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download WhisperX models and alignment models for offline use"
    )
    parser.add_argument(
        "--model",
        default="large-v3",
        choices=['tiny', 'base', 'small', 'medium', 'large-v2', 'large-v3', 'turbo'],
        help="WhisperX model to download (default: large-v3)"
    )
    parser.add_argument(
        "--cache-dir",
        help="Directory to cache models (default: uses HF_HOME environment variable)"
    )
    parser.add_argument(
        "--languages",
        nargs="+",
        default=["en", "es", "fr", "de"],
        help="Language codes for alignment models (default: en es fr de)"
    )
    parser.add_argument(
        "--compute-type",
        default="float16",
        choices=['float16', 'float32', 'int8'],
        help="Compute type for the model (default: float16)"
    )
    
    args = parser.parse_args()
    
    success = download_models(
        model_name=args.model,
        cache_dir=args.cache_dir,
        languages=args.languages,
        compute_type=args.compute_type
    )
    
    sys.exit(0 if success else 1)