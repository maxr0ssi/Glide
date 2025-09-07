#!/bin/bash
# Setup script for Glide - Downloads models and prepares environment

set -e  # Exit on error

echo "🚀 Setting up Glide..."
echo

# Check Python version
if ! command -v python3.10 &> /dev/null; then
    echo "❌ Error: Python 3.10 is required but not found"
    echo "Please install Python 3.10 or later"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3.10 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Download MediaPipe models
echo "📥 Downloading MediaPipe models..."
python setup_models.py

echo
echo "✅ Setup complete!"
echo
echo "To activate the environment, run:"
echo "  source venv/bin/activate"
echo
echo "To run Glide:"
echo "  make run        # Run with HUD"
echo "  make run-backend # Run backend only"
