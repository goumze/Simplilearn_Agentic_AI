# ============================================================
# FastAPI RAG Application Startup Script
# ============================================================

# Ensure we're in the project root directory
Write-Host "Starting Enterprise Agentic RAG API..." -ForegroundColor Green

# Set Python path to include current directory
$env:PYTHONPATH = "."

# Run uvicorn with auto-reload enabled
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative without reload (for production):
# python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
