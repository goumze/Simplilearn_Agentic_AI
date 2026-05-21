#!/usr/bin/env bash
# run.sh — Install dependencies, start the Sidekick Flask server, and run integration tests.
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[sidekick]${NC} $*"; }
warn() { echo -e "${YELLOW}[sidekick]${NC} $*"; }
fail() { echo -e "${RED}[sidekick]${NC} $*"; exit 1; }

# ── 1. Python dependencies ───────────────────────────────────────────────────
log "Installing Python dependencies..."
pip install -r requirements.txt -q

# ── 2. Playwright Chromium ───────────────────────────────────────────────────
log "Installing Playwright Chromium browser..."
python -m playwright install chromium --quiet
log "Installing Playwright system dependencies..."
python -m playwright install-deps chromium

# ── 3. Free port 8080 if already in use ─────────────────────────────────────
if lsof -ti:8080 > /dev/null 2>&1; then
    warn "Port 8080 is busy — freeing it..."
    fuser -k 8080/tcp 2>/dev/null || true
    sleep 1
fi

# ── 4. Start Flask server in background ─────────────────────────────────────
log "Starting Sidekick Flask server (http://0.0.0.0:8080)..."
python main.py &
APP_PID=$!

cleanup() { kill "$APP_PID" 2>/dev/null || true; }
trap cleanup INT TERM EXIT

# ── 5. Wait for Flask to be ready ────────────────────────────────────────────
log "Waiting for server to become ready..."
MAX_WAIT=60
WAITED=0
until curl -sf http://localhost:8080/health > /dev/null 2>&1; do
    sleep 1
    WAITED=$((WAITED + 1))
    [[ $WAITED -ge $MAX_WAIT ]] && fail "Server did not start within ${MAX_WAIT}s. Check for errors above."
done
log "Server is ready at http://localhost:8080"

# ── 6. Run integration tests ─────────────────────────────────────────────────
log "Running integration tests (test_app.py)..."
python test_app.py http://localhost:8080
TEST_EXIT=$?

# ── 7. Keep server running after tests ──────────────────────────────────────
trap - EXIT INT TERM   # Remove auto-kill so server stays up
if [[ $TEST_EXIT -eq 0 ]]; then
    log "All tests passed. Server still running at http://0.0.0.0:8080 (PID: $APP_PID)"
else
    warn "Some tests failed (exit $TEST_EXIT). Server still running at http://0.0.0.0:8080 (PID: $APP_PID)"
fi
log "Press Ctrl+C to stop the server."
wait "$APP_PID"
