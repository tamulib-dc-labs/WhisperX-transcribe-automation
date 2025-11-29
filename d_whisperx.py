import os
import whisperx
import torch
import yaml

# Load cache paths from config.yaml
config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Set HuggingFace cache
hf_cache = config.get("cache", {}).get("huggingface_cache", "/absolute/path/to/hf_cache")
os.environ['HF_HOME'] = hf_cache

# Set Python cache
python_cache = config.get("cache", {}).get("python_cache", "/absolute/path/to/pycache")
os.environ['PYTHONPATH'] = python_cache

# Set NLTK data cache
nltk_data = config.get("cache", {}).get("nltk_data", "/absolute/path/to/nltk_data")
os.environ['NLTK_DATA'] = nltk_data

# Set model cache
model_cache = config.get("cache", {}).get("model_cache", "/absolute/path/to/model_cache")
os.environ['MODEL_CACHE'] = model_cache

# Set offline mode to False for downloading
os.environ['HF_HUB_OFFLINE'] = '0'

device = "cuda" if torch.cuda.is_available() else "cpu"

# Use model_dir from config if specified
model_dir = config.get("model", {}).get("model_dir", None)

print("Downloading Whisper model...")
if model_dir:
    model = whisperx.load_model("large-v3", device, compute_type="float16", model_dir=model_dir)
else:
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