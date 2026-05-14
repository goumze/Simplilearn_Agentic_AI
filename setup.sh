#!/bin/bash

# Banking Customer Support AI Agent - Setup Script
# This script installs all required Python dependencies and initializes the project.

set -e

echo "=============================================="
echo " Banking Customer Support AI Agent - Setup"
echo "=============================================="

# Check Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is not installed. Please install Python 3.9+."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Found Python $PYTHON_VERSION"

# Check pip is available
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip3 is not installed. Please install pip."
    exit 1
fi

# Upgrade pip
echo ""
echo "[1/4] Upgrading pip..."
pip3 install --upgrade pip

# Install dependencies from requirements.txt
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "ERROR: requirements.txt not found at $REQUIREMENTS_FILE"
    exit 1
fi

echo ""
echo "[2/4] Installing Python dependencies from requirements.txt..."
pip3 install -r "$REQUIREMENTS_FILE"

# Create .env file if it does not exist
ENV_FILE="$SCRIPT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo ""
    echo "[3/4] Creating .env template..."
    cat > "$ENV_FILE" <<EOF
# OpenAI API Key - replace with your actual key
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Model name (default: gpt-4o-mini)
OPENAI_MODEL=gpt-4o-mini

# Database path (default: support_tickets.db in project root)
DB_PATH=support_tickets.db
EOF
    echo ".env file created at $ENV_FILE"
    echo "IMPORTANT: Edit .env and set your OPENAI_API_KEY before running the app."
else
    echo ""
    echo "[3/4] .env file already exists, skipping."
fi

# Initialize the SQLite database
echo ""
echo "[4/4] Initializing SQLite database..."
python3 "$SCRIPT_DIR/src/database.py"

echo ""
echo "=============================================="
echo " Setup complete!"
echo ""
echo " Next steps:"
echo "   1. Edit .env and set your OPENAI_API_KEY"
echo "   2. Run the Streamlit UI:"
echo "      streamlit run src/app.py"
echo "   3. Or run the CLI demo:"
echo "      python3 src/main.py"
echo "=============================================="
