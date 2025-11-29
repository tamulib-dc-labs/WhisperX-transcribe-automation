# Step 0: One-time environment setup for WhisperX Automation Pipeline (PowerShell)
# This script creates venv, initializes cache paths, and installs requirements

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Step 0: Environment Setup (One-time)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check for config.yaml
if (-not (Test-Path "config.yaml")) {
    Write-Host "Error: config.yaml not found!" -ForegroundColor Red
    Write-Host "Please copy config.example.yaml to config.yaml and fill in your settings."
    exit 1
}

# Parse config.yaml (simple parsing)
function Get-ConfigValue {
    param($Key)
    $line = Get-Content config.yaml | Where-Object { $_ -match "^\s*$Key\s*:" }
    if ($line) {
        $value = ($line -split ':', 2)[1].Trim() -replace '"', '' -replace "'", ''
        return $value
    }
    return $null
}

$HF_HOME = Get-ConfigValue "hf_home"
$NLTK_DATA = Get-ConfigValue "nltk_data"
$TORCH_HOME = Get-ConfigValue "torch_home"
$PYTHONPATH_VALUE = Get-ConfigValue "pythonpath"
$VENV_ACTIVATE = Get-ConfigValue "venv_activate"
$VENV_PATH = $VENV_ACTIVATE -replace '/bin/activate', '' -replace '\\Scripts\\activate', ''

Write-Host "Configuration loaded from config.yaml" -ForegroundColor Green
Write-Host "  HF_HOME: $HF_HOME"
Write-Host "  NLTK_DATA: $NLTK_DATA"
Write-Host "  TORCH_HOME: $TORCH_HOME"
Write-Host "  PYTHONPATH: $PYTHONPATH_VALUE"
Write-Host "  Virtual Environment: $VENV_PATH"
Write-Host ""

# Function to create directory
function New-DirectoryIfNotExists {
    param($Path)
    if (-not (Test-Path $Path)) {
        Write-Host "Creating directory: $Path" -ForegroundColor Yellow
        New-Item -Path $Path -ItemType Directory -Force | Out-Null
    }
    else {
        Write-Host "Directory already exists: $Path" -ForegroundColor Gray
    }
}

# Step 0.1: Create cache directories
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Step 0.1: Creating cache directories" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
New-DirectoryIfNotExists $HF_HOME
New-DirectoryIfNotExists $NLTK_DATA
New-DirectoryIfNotExists $TORCH_HOME
New-DirectoryIfNotExists $PYTHONPATH_VALUE
Write-Host ""

# Step 0.2: Create virtual environment
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Step 0.2: Creating virtual environment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
if (-not (Test-Path $VENV_PATH)) {
    Write-Host "Creating virtual environment at: $VENV_PATH" -ForegroundColor Yellow
    python -m venv $VENV_PATH
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}
else {
    Write-Host "Virtual environment already exists at: $VENV_PATH" -ForegroundColor Gray
}
Write-Host ""

# Step 0.3: Activate and install requirements
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Step 0.3: Installing Python dependencies" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Activating virtual environment..." -ForegroundColor Yellow

# Activate venv
& "$VENV_PATH\Scripts\Activate.ps1"

# Set environment variables
$env:HF_HOME = $HF_HOME
$env:NLTK_DATA = $NLTK_DATA
$env:TORCH_HOME = $TORCH_HOME
$env:PYTHONPATH = $PYTHONPATH_VALUE

Write-Host "Environment variables set:" -ForegroundColor Green
Write-Host "  HF_HOME=$env:HF_HOME"
Write-Host "  NLTK_DATA=$env:NLTK_DATA"
Write-Host "  TORCH_HOME=$env:TORCH_HOME"
Write-Host "  PYTHONPATH=$env:PYTHONPATH"
Write-Host ""

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install requirements
Write-Host "Installing requirements from requirements.txt..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host ""
Write-Host "✓ All dependencies installed" -ForegroundColor Green
Write-Host ""

# Step 0.4: Create activation helper
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Step 0.4: Creating activation helper script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

$activateScript = @"
# Helper script to activate environment with all required variables

# Load configuration
if (-not (Test-Path "config.yaml")) {
    Write-Host "Error: config.yaml not found!" -ForegroundColor Red
    exit 1
}

function Get-ConfigValue {
    param(`$Key)
    `$line = Get-Content config.yaml | Where-Object { `$_ -match "^\s*`$Key\s*:" }
    if (`$line) {
        `$value = (`$line -split ':', 2)[1].Trim() -replace '"', '' -replace "'", ''
        return `$value
    }
    return `$null
}

`$HF_HOME = Get-ConfigValue "hf_home"
`$NLTK_DATA = Get-ConfigValue "nltk_data"
`$TORCH_HOME = Get-ConfigValue "torch_home"
`$PYTHONPATH_VALUE = Get-ConfigValue "pythonpath"
`$VENV_ACTIVATE = Get-ConfigValue "venv_activate"
`$VENV_PATH = `$VENV_ACTIVATE -replace '/bin/activate', '' -replace '\\Scripts\\activate', ''

# Activate virtual environment
& "`$VENV_PATH\Scripts\Activate.ps1"

# Set environment variables
`$env:HF_HOME = `$HF_HOME
`$env:NLTK_DATA = `$NLTK_DATA
`$env:TORCH_HOME = `$TORCH_HOME
`$env:PYTHONPATH = `$PYTHONPATH_VALUE

Write-Host "Environment activated!" -ForegroundColor Green
Write-Host "  Virtual env: `$VENV_PATH"
Write-Host "  HF_HOME: `$env:HF_HOME"
Write-Host "  NLTK_DATA: `$env:NLTK_DATA"
Write-Host "  TORCH_HOME: `$env:TORCH_HOME"
Write-Host "  PYTHONPATH: `$env:PYTHONPATH"
"@

$activateScript | Out-File -FilePath "activate_env.ps1" -Encoding UTF8
Write-Host "✓ Created activate_env.ps1" -ForegroundColor Green
Write-Host ""

# Step 0.5: Test imports
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Step 0.5: Testing Python imports" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
python -c "import yaml; print('✓ PyYAML')"
python -c "import torch; print('✓ PyTorch')"
python -c "import whisperx; print('✓ WhisperX')"
python -c "import pandas; print('✓ Pandas')"
python -c "from config import load_config; print('✓ Config loader')"
Write-Host ""

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your environment is ready to use." -ForegroundColor Green
Write-Host ""
Write-Host "To activate the environment in future sessions, run:" -ForegroundColor Yellow
Write-Host "  .\activate_env.ps1"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. (Optional) Download WhisperX models:"
Write-Host "     python d_whisperx.py"
Write-Host ""
Write-Host "  2. Run the full pipeline:"
Write-Host "     python pipeline_2.py"
Write-Host ""
Write-Host "  OR run individual scripts:"
Write-Host "     python download_automation_3.py --help"
Write-Host "     python transcribe.py --help"
Write-Host "     python git_upload.py"
Write-Host ""
