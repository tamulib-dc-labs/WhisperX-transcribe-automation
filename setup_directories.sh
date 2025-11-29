#!/bin/bash
# Setup script for WhisperX Transcription Automation Pipeline
# Creates required directory structure

echo "================================================"
echo "WhisperX Automation - Directory Setup"
echo "================================================"
echo ""

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Project directory: $PROJECT_ROOT"
echo ""

# Create data folder structure
echo "Creating data directories..."
mkdir -p "$PROJECT_ROOT/data/oral_input"
mkdir -p "$PROJECT_ROOT/data/oral_output"
echo "✓ Created: $PROJECT_ROOT/data/oral_input"
echo "✓ Created: $PROJECT_ROOT/data/oral_output"
echo ""

# Create git_repo as sibling directory
PARENT_DIR="$(dirname "$PROJECT_ROOT")"
GIT_REPO_DIR="$PARENT_DIR/git_repo"

echo "Creating git_repo directory..."
mkdir -p "$GIT_REPO_DIR"
echo "✓ Created: $GIT_REPO_DIR"
echo ""

# Verify structure
echo "Directory structure created:"
echo ""
echo "$PARENT_DIR/"
echo "├── $(basename "$PROJECT_ROOT")/"
echo "│   └── data/"
echo "│       ├── oral_input/"
echo "│       └── oral_output/"
echo "└── git_repo/"
echo ""

echo "================================================"
echo "Setup complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Copy config.example.yaml to config.yaml"
echo "   cp config.example.yaml config.yaml"
echo ""
echo "2. Edit config.yaml with your settings"
echo "   nano config.yaml  # or use your preferred editor"
echo ""
echo "3. Install Python dependencies"
echo "   pip install -r requirements.txt"
echo ""
echo "4. (Optional) Download WhisperX models"
echo "   python d_whisperx.py"
echo ""
