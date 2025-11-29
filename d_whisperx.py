import os
import whisperx
import torch
from config import load_config
import functools
import warnings

# Monkey patch torch.load to fix "weights_only" error in PyTorch 2.6+
original_torch_load = torch.load
torch.load = functools.partial(original_torch_load, weights_only=False)

warnings.filterwarnings('ignore')

# Load configuration
config = load_config()

# Set HF cache from config
os.environ['HF_HOME'] = config['paths']['hf_home']

# Set offline mode to False for downloading
os.environ['HF_HUB_OFFLINE'] = '0'

# Detect device
device = "cuda" if torch.cuda.is_available() else "cpu"

# Use appropriate compute type based on device
# CPU requires float32, GPU can use int8 or float16
if device == "cpu":
    compute_type = "float32"
    print("No GPU detected, using CPU with float32")
else:
    compute_type = "int8"  # int8 works on all GPUs, float16 needs newer GPUs
    print(f"GPU detected, using {device} with {compute_type}")

# Get model name from config
model_name = config.get('whisperx', {}).get('model_name', 'large-v3')

print(f"\nDownloading Whisper model: {model_name}...")
model = whisperx.load_model(model_name, device, compute_type=compute_type)
print("Whisper model downloaded!")

print("\nDownloading alignment models for common languages...")
languages = config.get('model_download', {}).get('alignment_languages', ['en', 'es', 'fr', 'de'])

for lang in languages:
    try:
        print(f"Downloading alignment model for {lang}...")
        align_model, metadata = whisperx.load_align_model(language_code=lang, device=device)
        print(f"Alignment model for {lang} downloaded!")
        del align_model
    except Exception as e:
        print(f"Could not download alignment for {lang}: {e}")

print("\nAll models downloaded to:", os.environ['HF_HOME'])