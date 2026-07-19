#!/bin/bash

# Report Generator - Setup and Execution Script
# This script installs dependencies and runs the report generator

set -e  # Exit on any error

echo "=================================="
echo "Report Generator Setup & Execution"
echo "=================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed"
    exit 1
fi

echo "✓ Python3 found: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

echo ""

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source "$VENV_DIR/bin/activate"
echo "✓ Virtual environment activated"

echo ""

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ Pip upgraded"

echo ""

# Install requirements
echo "📦 Installing dependencies from requirements.txt..."
if [ -f "requirements.txt" ]; then
    # Install with --no-cache-dir to ensure fresh packages
    # Use --upgrade-strategy eager to resolve dependency conflicts
    pip install --no-cache-dir --upgrade-strategy eager -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo "✓ All dependencies installed successfully"
    else
        echo "❌ Error installing dependencies"
        echo ""
        echo "Trying alternative installation method..."
        pip install --no-cache-dir -r requirements.txt
        if [ $? -eq 0 ]; then
            echo "✓ Dependencies installed"
        else
            echo "❌ Failed to install dependencies"
            exit 1
        fi
    fi
else
    echo "❌ requirements.txt not found"
    exit 1
fi

echo ""
echo "=================================="
echo "Dependencies Ready - Running Report"
echo "=================================="
echo ""

# Check for .env file
if [ ! -f "Reporter_Generator/.env" ]; then
    echo "⚠️  Note: .env file not found"
    echo "   If you need to configure OPENROUTER_API_KEY, create:"
    echo "   Reporter_Generator/.env"
    echo ""
fi

# Run the report generator
echo "🚀 Executing report_generator.py..."
echo ""
python3 Reporter_Generator/report_generator.py

echo ""
echo "=================================="
echo "✅ Execution complete!"
echo "=================================="
