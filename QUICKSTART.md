# Quick Start Guide

Get up and running with the WhisperX transcription pipeline in 5 minutes.

## Prerequisites

- Python 3.9+ installed
- Access to HPC cluster with SLURM (for GPU transcription)
- Git installed
- SMB network share credentials
- GitHub personal access token

## Installation (5 minutes)

### 1. Clone and Navigate
```bash
git clone https://github.com/tamulib-dc-labs/WhisperX-transcribe-automation.git
cd WhisperX-transcribe-automation
```

### 2. Load Modules (HPC only)
```bash
ml GCCcore/10.3.0 Python
```

### 3. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

## Configuration (2 minutes)

Edit `src/config.py` and update these fields in the `PipelineConfig` dataclass:

```python
@dataclass
class PipelineConfig:
    # SMB Settings - Update these
    smb_server: str = "your.smb.server.com"
    smb_share: str = "your_share_name"
    smb_base_path: str = "path/inside/share"
    smb_username: str = "your_username"
    smb_password: str = ""  # Leave empty to be prompted
    
    # Google Sheets - Update this
    sheet_url: str = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
    
    # GitHub - Update these
    git_owner: str = "your-github-org"
    git_repo_name: str = "your-repo-name"
    git_username: str = "your-username"
    git_token: str = "your_github_token"
    
    # Model Settings - Keep defaults or customize
    whisper_model: str = "large-v3"  # Options: tiny, base, small, medium, large-v2, large-v3, turbo
    batch_size: int = 16
    compute_type: str = "float16"
    language: str = "en"  # or None for auto-detect
```

**Pro Tip**: Use environment variables for sensitive data:
```bash
export SMB_PASSWORD="your_password"
export GIT_TOKEN="your_token"
```

## Usage

### Run the Complete Pipeline
```bash
python scripts/run_pipeline.py
```

That's it! The pipeline will:
1. ✅ Load environment modules
2. ✅ Set up virtual environment
3. ✅ Download audio files from Google Sheets
4. ✅ Download WhisperX models
5. ✅ Download NLTK data
6. ✅ Submit SLURM job for GPU transcription
7. ✅ Monitor job status
8. ✅ Upload results to GitHub

## What Gets Created

### Data Directories
```
data/
├── oral_input/          # Downloaded audio files
└── oral_output/         # Transcription results (JSON + VTT)
```

### Cache Directories
```
cache/
├── huggingface/         # WhisperX models
└── nltk_data/           # NLTK tokenizers
```

### Output Files
For each audio file (e.g., `interview_001.mp3`):
- `interview_001.json` - Full transcription with word-level timestamps
- `interview_001.vtt` - WebVTT subtitle file (42 chars/line, 2 lines max)

## Expected Timeline

| Step | Duration | Notes |
|------|----------|-------|
| 1. Load modules | < 1 min | HPC module loading |
| 2. Setup venv | 1-2 min | Only first run |
| 3. Prepare directories | < 1 min | Clear old data |
| 4. Download audio | 5-30 min | Depends on file count/size |
| 5. Download models | 10-20 min | Only first run, ~10GB |
| 6. Download NLTK | < 1 min | Only first run |
| 7. Submit SLURM | < 1 min | Job submission |
| 8. Transcription | 1-6 hours | Depends on audio length |
| 9. Upload to GitHub | 5-15 min | Depends on file count |

**First run**: 1.5-8 hours (includes model downloads)  
**Subsequent runs**: 1-6.5 hours (models cached)

## Monitoring Progress

### Check Pipeline Status
The pipeline displays progress messages:
```
================================================================================
Step 1: Loading environment modules
================================================================================
[INFO] Loading modules: GCCcore/10.3.0 Python FFmpeg CUDA
[INFO] Modules loaded successfully

================================================================================
Step 2: Setting up Python environment
================================================================================
[INFO] Virtual environment exists at: /path/to/venv
...
```

### Check SLURM Job
```bash
# View job status
squeue -u $USER

# View job output (while running)
tail -f slurm-<job_id>.out

# View completed job output
cat slurm-<job_id>.out
```

### Check Output Files
```bash
# Count transcribed files
ls data/oral_output/*.json | wc -l

# View a transcription
cat data/oral_output/interview_001.json | jq '.'
```

## Troubleshooting

### "No module named 'src'"
**Solution**: Run from project root:
```bash
cd WhisperX-transcribe-automation
python scripts/run_pipeline.py
```

### "Authentication failed" (Git)
**Solution**: Check your GitHub token:
```bash
# Test token
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

# Update token in src/config.py
```

### "CUDA out of memory"
**Solution**: Reduce batch size in `src/config.py`:
```python
batch_size: int = 8  # Reduced from 16
```

### "SMB connection failed"
**Solution**: Verify credentials and network:
```bash
# Test SMB connection
smbclient //server/share -U username

# Or set password via environment variable
export SMB_PASSWORD="your_password"
```

### "Models not found"
**Solution**: Manually download models:
```python
# The pipeline will do this automatically, but you can trigger manually:
from src.transcription.model_downloader import ModelDownloader
from src.config import get_config

downloader = ModelDownloader(get_config())
downloader.download_models()
```

## Common Customizations

### Change Model Size
For faster (less accurate) transcription:
```python
# In src/config.py
whisper_model: str = "medium"  # Instead of large-v3
```

### Change Language
For non-English audio:
```python
# In src/config.py
language: str = "es"  # Spanish
# or
language: str = None  # Auto-detect
```

### Change VTT Formatting
```python
# In src/config.py
max_line_width: int = 50  # Wider lines
max_line_count: int = 1   # Single-line subtitles
```

### Process Fewer Files
```python
# In src/config.py
max_folders: int = 5  # Process only 5 folders
```

## Next Steps

Once the pipeline is running successfully:

1. **Review output**: Check JSON and VTT files in `data/oral_output/`
2. **Check GitHub**: Verify files uploaded to your repository
3. **Customize**: Adjust settings in `src/config.py` as needed
4. **Schedule**: Set up cron job or scheduled task for automation
5. **Monitor**: Set up alerts for job completion/failure

## Getting Help

- **Documentation**: See [README.md](README.md) for full details
- **Migration**: See [MIGRATION.md](MIGRATION.md) if upgrading from v1.0
- **Architecture**: See [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) for technical details
- **Issues**: Open an issue on GitHub with error messages and logs

## Example: First Run

```bash
# 1. Clone repository
git clone https://github.com/tamulib-dc-labs/WhisperX-transcribe-automation.git
cd WhisperX-transcribe-automation

# 2. Load modules (HPC)
ml GCCcore/10.3.0 Python

# 3. Create venv
python -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure (edit src/config.py with your credentials)
nano src/config.py

# 6. Run pipeline
python scripts/run_pipeline.py

# Output:
# ================================================================================
# Step 1: Loading environment modules
# ================================================================================
# [INFO] Loading modules: GCCcore/10.3.0 Python FFmpeg CUDA
# [INFO] Modules loaded successfully
# 
# ================================================================================
# Step 2: Setting up Python environment
# ================================================================================
# [INFO] Virtual environment exists at: /path/to/venv
# 
# ... (pipeline continues)
```

## Resources

- **WhisperX Documentation**: https://github.com/m-bain/whisperX
- **SLURM Documentation**: https://slurm.schedmd.com/
- **GitHub API**: https://docs.github.com/en/rest
- **NLTK Documentation**: https://www.nltk.org/

---

**Need more help?** Contact the development team or open an issue on GitHub.
