# Migration Guide: Version 1.0 → 2.0

This guide helps you transition from the old script-based structure to the new modular architecture.

## What Changed?

### Architecture
- **Before**: Single-file scripts (pipeline_2.py, git_upload.py, d_whisperx.py)
- **After**: Modular class-based design with src/ directory structure

### Configuration
- **Before**: Variables at top of pipeline_2.py
- **After**: Centralized PipelineConfig dataclass in src/config.py

### Entry Point
- **Before**: `python pipeline_2.py`
- **After**: `python scripts/run_pipeline.py`

## File Mapping

### Old → New

| Old Location | New Location | Notes |
|-------------|--------------|-------|
| `pipeline_2.py` | `scripts/run_pipeline.py` + `src/pipeline.py` | Split into entry point + orchestrator |
| `git_upload.py` | `src/git/uploader.py` | Now GitUploader class |
| `d_whisperx.py` | `src/transcription/model_downloader.py` | Now ModelDownloader class |
| `download_automation_3.py` | Integrated into `src/pipeline.py` | Called by _download_audio_files() |
| `transcribe.py` | `scripts/transcribe.py` | Moved to scripts/ directory |
| `run_1.slurm` | `config/run.slurm` | Moved to config/ directory |

### Configuration Migration

**Before (pipeline_2.py):**
```python
# At top of file
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
SMB_SERVER = "your.server.com"
WHISPER_MODEL = "large-v3"
# ... 50+ variables
```

**After (src/config.py):**
```python
from src.config import get_config

config = get_config()
print(config.working_dir)     # Auto-detected
print(config.smb_server)      # From dataclass field
print(config.whisper_model)   # From dataclass field
```

### Code Migration Examples

#### Running the Pipeline

**Before:**
```python
# pipeline_2.py - monolithic script
def main():
    # Step 1: Load modules
    run_command("ml GCCcore/10.3.0 Python")
    # Step 2: Setup venv
    if not os.path.exists(venv_path):
        run_command(f"python -m venv {venv_path}")
    # ... 200+ more lines
```

**After:**
```python
# scripts/run_pipeline.py - clean entry point
from src.pipeline import TranscriptionPipeline

def main():
    pipeline = TranscriptionPipeline()
    pipeline.run()  # Handles all steps internally
```

#### Git Operations

**Before:**
```python
# git_upload.py - script with argparse
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--owner", required=True)
# ... many arguments
args = parser.parse_args()

# Clone repo
subprocess.run(["git", "clone", repo_url, args.repo_path])
# ... many subprocess calls
```

**After:**
```python
# src/git/uploader.py - class-based
from src.git.uploader import GitUploader
from src.config import get_config

config = get_config()
uploader = GitUploader(
    source_path=config.data_output_path,
    repo_path=config.git_repo_path,
    owner=config.git_owner,
    repo_name=config.git_repo_name,
    username=config.git_username,
    token=config.git_token
)
uploader.upload()  # Handles all git operations
```

#### Model Downloading

**Before:**
```python
# d_whisperx.py - standalone script
import whisperx
model = whisperx.load_model(model_name, ...)
# Download alignment models
for lang in languages:
    whisperx.load_align_model(language_code=lang, ...)
```

**After:**
```python
# src/transcription/model_downloader.py - class with PyTorch patch
from src.transcription.model_downloader import ModelDownloader
from src.config import get_config

config = get_config()
downloader = ModelDownloader(config)
downloader.download_models()  # Handles all downloads + PyTorch patch
```

## Breaking Changes

### 1. Import Paths
If you have custom scripts importing from old files:

**Before:**
```python
from pipeline_2 import run_command, clear_directory
from git_upload import upload_to_github
```

**After:**
```python
from src.utils.file_manager import CommandRunner, FileManager
from src.git.uploader import GitUploader
```

### 2. Configuration Access
**Before:**
```python
import pipeline_2
print(pipeline_2.WORKING_DIR)
print(pipeline_2.WHISPER_MODEL)
```

**After:**
```python
from src.config import get_config
config = get_config()
print(config.working_dir)
print(config.whisper_model)
```

### 3. Path References
All paths now derived from config:

**Before:**
```python
input_path = f"{WORKING_DIR}/data/oral_input"
output_path = f"{WORKING_DIR}/data/oral_output"
slurm_script = f"{WORKING_DIR}/run_1.slurm"
```

**After:**
```python
from src.config import get_config
config = get_config()
input_path = config.data_input_path      # Property
output_path = config.data_output_path    # Property
slurm_script = config.slurm_script_path  # Property
```

## Migration Steps

### For Users (No Code Changes)

1. **Update configuration:**
   ```bash
   # Edit src/config.py instead of pipeline_2.py
   nano src/config.py
   ```

2. **Use new entry point:**
   ```bash
   # Old way (still works but deprecated)
   python pipeline_2.py
   
   # New way (recommended)
   python scripts/run_pipeline.py
   ```

3. **Everything else stays the same:**
   - Same virtual environment
   - Same SLURM submission
   - Same output format
   - Same functionality

### For Developers (Custom Scripts)

1. **Update imports:**
   ```python
   # Replace old imports
   from src.config import get_config
   from src.utils.logger import Logger
   from src.utils.file_manager import FileManager, CommandRunner
   from src.git.uploader import GitUploader
   from src.transcription.model_downloader import ModelDownloader
   ```

2. **Use configuration object:**
   ```python
   config = get_config()
   # Access all settings via config object
   ```

3. **Use utility classes:**
   ```python
   # Instead of custom functions
   FileManager.clear_directory(path)
   CommandRunner.run(command)
   Logger.log_info(message)
   ```

## Backward Compatibility

### Old Scripts Still Work
The old scripts (pipeline_2.py, git_upload.py, etc.) are still present and functional, but **deprecated**:

- ✅ Still work as before
- ⚠️ Not recommended for new usage
- 📅 May be removed in future version
- 🔄 Use new structure for better maintainability

### Transition Period
You can gradually migrate:

1. **Phase 1**: Use new entry point, keep old config
   - Run `python scripts/run_pipeline.py` but don't modify config yet
   
2. **Phase 2**: Migrate configuration
   - Move settings from pipeline_2.py to src/config.py
   
3. **Phase 3**: Clean up old files
   - Once confident, remove deprecated scripts

## Benefits of New Structure

### 1. **Separation of Concerns**
- Configuration: `src/config.py`
- Orchestration: `src/pipeline.py`
- Utilities: `src/utils/`
- Git operations: `src/git/`
- Transcription: `src/transcription/`

### 2. **Reusability**
Each class can be used independently:
```python
# Just upload files
from src.git.uploader import GitUploader
uploader = GitUploader(...)
uploader.upload()

# Just download models
from src.transcription.model_downloader import ModelDownloader
downloader = ModelDownloader(config)
downloader.download_models()
```

### 3. **Testability**
Classes are easier to unit test:
```python
import unittest
from src.utils.file_manager import FileManager

class TestFileManager(unittest.TestCase):
    def test_clear_directory(self):
        # Test logic here
        pass
```

### 4. **Maintainability**
- Single responsibility per class
- Clear module boundaries
- Type hints throughout
- Docstrings for all classes/methods

### 5. **Auto-Configuration**
Paths automatically derived:
```python
@property
def hf_cache(self) -> str:
    return os.path.join(self.cache_dir, "huggingface")

@property  
def nltk_cache(self) -> str:
    return os.path.join(self.cache_dir, "nltk_data")
```

## Troubleshooting Migration

### Issue: "ModuleNotFoundError: No module named 'src'"

**Cause**: Python can't find src/ directory

**Solution**: Run from project root or update PYTHONPATH:
```bash
# Option 1: Run from project root
cd WhisperX-transcribe-automation
python scripts/run_pipeline.py

# Option 2: Add to PYTHONPATH (entry point handles this automatically)
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: "Configuration file not found"

**Cause**: Looking for old pipeline_2.py variables

**Solution**: Update code to use new config:
```python
from src.config import get_config
config = get_config()
```

### Issue: "Old scripts not working"

**Cause**: Dependencies between old and new code

**Solution**: Use either old OR new structure consistently:
- **Option A**: Use only old scripts (pipeline_2.py, git_upload.py, etc.)
- **Option B**: Use only new structure (scripts/run_pipeline.py)
- Don't mix old and new in same run

## Getting Help

If you encounter issues during migration:

1. **Check this guide** for common patterns
2. **Review examples** in Module Documentation section of README
3. **Compare old vs new** file side-by-side
4. **Open an issue** on GitHub with:
   - What you're trying to do
   - Old code snippet
   - Error message (if any)

## Timeline

- **v1.0**: Original script-based structure (deprecated)
- **v2.0**: New modular architecture (current)
- **v2.1**: Deprecation warnings added to old scripts (planned)
- **v3.0**: Old scripts removed (future)

## Quick Reference

### Common Tasks

| Task | Old Way | New Way |
|------|---------|---------|
| Run pipeline | `python pipeline_2.py` | `python scripts/run_pipeline.py` |
| Configure settings | Edit `pipeline_2.py` | Edit `src/config.py` |
| Upload to git | `python git_upload.py --args` | Integrated in pipeline |
| Download models | `python d_whisperx.py --args` | Integrated in pipeline |
| Check logs | Read subprocess output | `Logger.log_info()` messages |
| Clear directories | `clear_directory()` function | `FileManager.clear_directory()` |
| Run commands | `run_command()` function | `CommandRunner.run()` |

### Import Quick Reference

```python
# Configuration
from src.config import get_config, PipelineConfig

# Pipeline
from src.pipeline import TranscriptionPipeline

# Utilities
from src.utils.logger import Logger
from src.utils.file_manager import FileManager, CommandRunner

# Git
from src.git.uploader import GitUploader

# Transcription
from src.transcription.model_downloader import ModelDownloader
```

---

**Questions?** Open an issue or contact the development team.
