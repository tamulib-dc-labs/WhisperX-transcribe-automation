# Quick Start Guide

## ⚡ Getting Started in 5 Minutes

### Step 1: Edit Configuration
Open `pipeline_2.py` and find the **CONFIGURATION SECTION** at the top (around line 17). Update these key values:

```python
# --- Working Directory ---
WORKING_DIR = "/your/path/to/working/directory"  # Main working directory
DATA_FOLDER = "data"  # Data folder name (auto-created under WORKING_DIR)
ORAL_INPUT_FOLDER = "oral_input"   # Input folder (under data/)
ORAL_OUTPUT_FOLDER = "oral_output" # Output folder (under data/)
# This creates: WORKING_DIR/data/oral_input and WORKING_DIR/data/oral_output

GIT_REPO_PATH = "/your/path/OUTSIDE/working/dir/git_repo"  # ⚠️ Must be OUTSIDE working directory

# --- SMB Network Share Settings ---
SMB_SERVER = "your.server.com"
SMB_SHARE = "your_share_name"
SMB_BASE_PATH = "path/inside/share"
SMB_USERNAME = "your_username"
SMB_PASSWORD = ""  # Leave empty for secure prompt

# --- Google Sheets Settings ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"

# --- GitHub Settings ---
GIT_OWNER = "your-github-org"
GIT_REPO_NAME = "your-repo-name"
GIT_USERNAME = "your-github-username"
GIT_TOKEN = "ghp_YourTokenHere"
```

### Step 2: Run the Pipeline
```bash
python pipeline_2.py
```

That's it! The pipeline will:
1. ✅ Download audio files from Google Sheets
2. ✅ Transcribe using WhisperX
3. ✅ Upload results to GitHub

---

## 📝 Configuration Cheat Sheet

### Essential Settings (Must Configure)

| Setting | Example | Description |
|---------|---------|-------------|
| `WORKING_DIR` | `/scratch/user/me/speech_text` | Main working directory |
| `DATA_FOLDER` | `data` | Data folder name (under WORKING_DIR) |
| `ORAL_INPUT_FOLDER` | `oral_input` | Input folder (under data/) |
| `ORAL_OUTPUT_FOLDER` | `oral_output` | Output folder (under data/) |
| `GIT_REPO_PATH` | `/scratch/user/git_repos/my-repo` | Git repo location (OUTSIDE working dir) |
| `SMB_USERNAME` | `myusername` | Network share username |
| `SMB_SERVER` | `files.example.com` | SMB server address |
| `SMB_SHARE` | `projects` | Share name |
| `SHEET_URL` | `https://docs.google...` | Google Sheets URL |
| `GIT_TOKEN` | `ghp_...` | GitHub personal access token |

### Optional Settings (Can Keep Defaults)

| Setting | Default | Options |
|---------|---------|---------|
| `WHISPER_MODEL` | `large-v3` | `tiny`, `base`, `small`, `medium`, `large-v2`, `large-v3`, `turbo` |
| `BATCH_SIZE` | `16` | Smaller = less memory, slower |
| `COMPUTE_TYPE` | `float16` | `float16`, `float32`, `int8` |
| `LANGUAGE` | `None` | `None` (auto), `"en"`, `"es"`, `"fr"`, etc. |
| `MAX_FOLDERS` | `20` | Max folders to download per run |
| `CHECK_INTERVAL_MINS` | `5` | How often to check job status |

---

## 🚀 Usage Examples

### Full Pipeline
```bash
python pipeline_2.py
```

### Download Only
```bash
python download_automation_3.py \
  --sheet-url "YOUR_URL" \
  --username "USERNAME" \
  --password "PASSWORD" \
  --server "SERVER" \
  --share "SHARE" \
  --base-path "PATH" \
  --local-path "/path/to/save" \
  --max-folders 20
```

### Transcribe Only (Single GPU)
```bash
python transcribe.py /input/path /output/path --model large-v3
```

### Transcribe with Multiple GPUs
```bash
python transcribe.py /input/path /output/path \
  --model large-v3 \
  --parallel \
  --num-gpus 4
```

### Upload to GitHub Only
```bash
python git_upload.py \
  --source-path "/path/to/files" \
  --repo-path "/path/to/git/repo" \
  --owner "OWNER" \
  --repo-name "REPO" \
  --username "USER" \
  --token "TOKEN"
```

---

## 🔧 Common Customizations

### Use Different Model
```python
WHISPER_MODEL = "medium"  # Faster, less accurate
WHISPER_MODEL = "large-v3"  # Slower, more accurate
```

### Process More/Fewer Folders
```python
MAX_FOLDERS = 50  # Process up to 50 folders per run
```

### Change Subtitle Format
```python
MAX_LINE_WIDTH = 30  # Shorter lines
MAX_LINE_COUNT = 3   # More lines per subtitle
HIGHLIGHT_WORDS = True  # Enable word highlighting
```

### Use Specific Language (No Auto-Detect)
```python
LANGUAGE = "en"  # Force English
LANGUAGE = "es"  # Force Spanish
```

### Reduce GPU Memory Usage
```python
BATCH_SIZE = 8  # Reduce from 16
COMPUTE_TYPE = "int8"  # Use lower precision
```

---

## 🔒 Security Tips

### Secure Password Entry
Leave password empty for interactive prompt:
```python
SMB_PASSWORD = ""  # Will prompt securely
```

Or use environment variable:
```bash
export SMB_PASSWORD="your_password"
```

### Secure Token Storage
Use environment variable instead of hardcoding:
```bash
export GIT_TOKEN="ghp_your_token"
```

Then in pipeline_2.py:
```python
GIT_TOKEN = os.environ.get("GIT_TOKEN", "")
```

### Never Commit Secrets
Add to `.gitignore`:
```
.env
config.yaml
*_secret.py
```

---

## ❓ Troubleshooting Quick Fixes

### Problem: "Authentication failed" (Git)
**Fix:** Check your `GIT_TOKEN` in `pipeline_2.py` - ensure it has `repo` permissions

### Problem: "Cannot connect to SMB share"
**Fix:** Verify `SMB_SERVER`, `SMB_SHARE`, and credentials are correct

### Problem: "CUDA out of memory"
**Fix:** Reduce `BATCH_SIZE` to `8` or `4`, or use smaller model

### Problem: "Google Sheet access denied"
**Fix:** Make sure sheet is publicly accessible or shared with you

### Problem: "Git repo conflicts with working dir"
**Fix:** Ensure `GIT_REPO_PATH` is OUTSIDE your working directory:
```python
# ❌ Bad - inside working dir
GIT_REPO_PATH = "/scratch/user/me/speech_text/git_repo"

# ✅ Good - outside working dir  
GIT_REPO_PATH = "/scratch/user/me/git_repositories/my-repo"
```

---

## 📂 Directory Structure

```
WhisperX-transcribe-automation/
├── pipeline_2.py          ← 🎯 EDIT THIS FILE (main config)
├── download_automation_3.py
├── transcribe.py
├── git_upload.py
├── d_whisperx.py
├── run_1.slurm
├── requirements.txt
├── README.md              ← Full documentation
├── CHANGES.md             ← What changed in this version
└── QUICK_START.md         ← This file

Working Directories (configured in pipeline_2.py):
WORKING_DIR/
└── data/                     ← Auto-created data folder
    ├── oral_input/           ← Audio files downloaded here
    └── oral_output/          ← Transcriptions saved here
        ├── json/             ← JSON transcriptions
        └── vtts/             ← VTT subtitle files

Cache Directories (auto-created):
CACHE_DIR/
├── huggingface/
├── python_packages/
├── nltk_data/
└── models/

Git Repository (OUTSIDE working directory):
/your/path/to/git_repositories/
└── your-repo-name/           ← Git operations happen here
```

---

## 📞 Getting Help

1. **Read the full docs:** `README.md`
2. **Check what changed:** `CHANGES.md`
3. **Common issues:** See "Troubleshooting" in README.md
4. **Still stuck?** Open an issue on GitHub

---

**Quick Tip:** All configuration is in ONE place - the top of `pipeline_2.py`. No other config files needed! 🎉
