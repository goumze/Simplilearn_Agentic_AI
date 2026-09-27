#!/bin/bash
# ============================================================
# FastAPI RAG Application Startup Script
# ============================================================

echo "Starting Enterprise Agentic RAG API..."

# Set Python path to include current directory
export PYTHONPATH="."

# Run uvicorn with auto-reload enabled
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative without reload (for production):
# python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
