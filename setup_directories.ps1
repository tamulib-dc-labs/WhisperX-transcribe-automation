# PowerShell Setup Script for WhisperX Transcription Automation Pipeline
# Creates required directory structure

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "WhisperX Automation - Directory Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get the project root directory
$ProjectRoot = $PSScriptRoot
Write-Host "Project directory: $ProjectRoot" -ForegroundColor Yellow
Write-Host ""

# Create data folder structure
Write-Host "Creating data directories..." -ForegroundColor Green
New-Item -Path "$ProjectRoot\data\oral_input" -ItemType Directory -Force | Out-Null
New-Item -Path "$ProjectRoot\data\oral_output" -ItemType Directory -Force | Out-Null
Write-Host "✓ Created: $ProjectRoot\data\oral_input" -ForegroundColor Green
Write-Host "✓ Created: $ProjectRoot\data\oral_output" -ForegroundColor Green
Write-Host ""

# Create git_repo as sibling directory
$ParentDir = Split-Path -Parent $ProjectRoot
$GitRepoDir = Join-Path $ParentDir "git_repo"

Write-Host "Creating git_repo directory..." -ForegroundColor Green
New-Item -Path $GitRepoDir -ItemType Directory -Force | Out-Null
Write-Host "✓ Created: $GitRepoDir" -ForegroundColor Green
Write-Host ""

# Verify structure
Write-Host "Directory structure created:" -ForegroundColor Cyan
Write-Host ""
Write-Host "$ParentDir\"
Write-Host "├── $(Split-Path -Leaf $ProjectRoot)\"
Write-Host "│   └── data\"
Write-Host "│       ├── oral_input\"
Write-Host "│       └── oral_output\"
Write-Host "└── git_repo\"
Write-Host ""

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Copy config.example.yaml to config.yaml"
Write-Host "   Copy-Item config.example.yaml config.yaml"
Write-Host ""
Write-Host "2. Edit config.yaml with your settings"
Write-Host "   notepad config.yaml  # or use your preferred editor"
Write-Host ""
Write-Host "3. Install Python dependencies"
Write-Host "   pip install -r requirements.txt"
Write-Host ""
Write-Host "4. (Optional) Download WhisperX models"
Write-Host "   python d_whisperx.py"
Write-Host ""
