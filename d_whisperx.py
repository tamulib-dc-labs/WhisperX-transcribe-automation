import os
import whisperx
import torch
import yaml

# Load cache paths from config.yaml
config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Set HuggingFace cache
hf_cache = config.get("cache", {}).get("huggingface_cache", "./hf_cache")
os.environ['HF_HOME'] = hf_cache

# Set model cache (if needed by your workflow)
model_cache = config.get("cache", {}).get("model_cache", "./model_cache")
os.environ['MODEL_CACHE'] = model_cache

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