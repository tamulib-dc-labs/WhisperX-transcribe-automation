import os
import whisperx
import torch

# Set HF cache
os.environ['HF_HOME'] = '/scratch/user/jvk_chaitanya/hf_cache'

# Set offline mode to False for downloading
os.environ['HF_HUB_OFFLINE'] = '0'

device = "cuda" if torch.cuda.is_available() else "cpu"

print("Downloading Whisper model...")
model = whisperx.load_model("large-v3", device, compute_type="float16")
print("Whisper model downloaded!")

print("\nDownloading alignment models for common languages...")
languages = ["en", "es", "fr", "de"]  # Add languages you need

for lang in languages:
    try:
        print(f"Downloading alignment model for {lang}...")
        align_model, metadata = whisperx.load_align_model(language_code=lang, device=device)
        print(f"Alignment model for {lang} downloaded!")
        del align_model
    except Exception as e:
        print(f"Could not download alignment for {lang}: {e}")

print("\nAll models downloaded to:", os.environ['HF_HOME'])