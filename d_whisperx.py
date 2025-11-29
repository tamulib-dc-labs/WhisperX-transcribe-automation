import os
import whisperx
import torch
from config import load_config

# Load configuration
config = load_config()

# Set HF cache from config
os.environ['HF_HOME'] = config['paths']['hf_home']

# Set offline mode to False for downloading
os.environ['HF_HUB_OFFLINE'] = '0'

device = "cuda" if torch.cuda.is_available() else "cpu"

# Get model settings from config
model_name = config['whisperx']['model_name']
compute_type = config['whisperx']['compute_type']

print(f"Downloading Whisper model: {model_name}...")
model = whisperx.load_model(model_name, device, compute_type=compute_type)
print("Whisper model downloaded!")

print("\nDownloading alignment models for configured languages...")
languages = config['model_download']['alignment_languages']

for lang in languages:
    try:
        print(f"Downloading alignment model for {lang}...")
        align_model, metadata = whisperx.load_align_model(language_code=lang, device=device)
        print(f"Alignment model for {lang} downloaded!")
        del align_model
    except Exception as e:
        print(f"Could not download alignment for {lang}: {e}")

print("\nAll models downloaded to:", os.environ['HF_HOME'])