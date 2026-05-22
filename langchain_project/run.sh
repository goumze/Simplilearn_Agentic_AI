#!/usr/bin/env bash
# run.sh — Install dependencies and run the LangChain Q&A Agent
# Usage: bash run.sh
#        OPENAI_API_KEY=sk-... bash run.sh   (inline key)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── 0. Load shared .env from repo root (if present) ─────────────────────────
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"
if [[ -f "$ENV_FILE" ]]; then
  echo "── Loading environment from $(basename "$(dirname "$SCRIPT_DIR")")/.env ──"
  # Export only lines that look like KEY=VALUE, skip comments and blank lines
  set -a
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +a
fi

# ── 1. Check for OPENAI_API_KEY ─────────────────────────────────────────────
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo ""
  echo "  ERROR: OPENAI_API_KEY is not set."
  echo ""
  echo "  Please export your OpenAI API key first:"
  echo "    export OPENAI_API_KEY='sk-...'"
  echo ""
  exit 1
fi

# ── 2. Create virtual environment (if it doesn't exist) ─────────────────────
VENV_DIR="$SCRIPT_DIR/.venv"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "── Creating virtual environment at .venv/ ──────────────────────────"
  python3 -m venv "$VENV_DIR"
fi

# ── 3. Activate virtual environment ─────────────────────────────────────────
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

# ── 4. Install dependencies ──────────────────────────────────────────────────
echo "── Installing dependencies from requirements.txt ───────────────────"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "── Dependencies installed ──────────────────────────────────────────"

# ── 5. Run the agent ─────────────────────────────────────────────────────────
echo ""
echo "── Running LangChain Agent ─────────────────────────────────────────"
echo ""
python agent.py
