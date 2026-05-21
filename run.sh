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
python -m playwright install chromium
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

XVFB_PID=""; NOVNC_PID=""
cleanup() {
    kill "$APP_PID"    2>/dev/null || true
    kill "$XVFB_PID"   2>/dev/null || true
    kill "$NOVNC_PID"  2>/dev/null || true
}
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

# ── 6. Run API integration tests ─────────────────────────────────────────────
log "Running API integration tests (test_app.py)..."
set +e   # allow tests to fail without aborting the script
python test_app.py http://localhost:8080
API_EXIT=$?
set -e

# ── 7. Virtual display + VNC for live Playwright observation ────────────────
log "Installing x11vnc and novnc for live browser preview..."
sudo apt-get install -y -q x11vnc novnc 2>/dev/null || warn "VNC install failed — falling back to headless"

log "Starting virtual display (Xvfb :99, 1280×900)..."
pkill -f "Xvfb :99" 2>/dev/null || true; sleep 0.3
Xvfb :99 -screen 0 1280x900x24 -ac +extension GLX +render -noreset &
XVFB_PID=$!
export DISPLAY=:99
sleep 1

log "Starting VNC server (x11vnc → display :99)..."
pkill -f x11vnc 2>/dev/null || true; sleep 0.3
x11vnc -display :99 -nopw -listen localhost -xkb -forever -bg -quiet || warn "x11vnc failed to start"
sleep 1

log "Starting noVNC WebSocket proxy (port 6080 → VNC 5900)..."
pkill -f "novnc_proxy\|websockify.*6080" 2>/dev/null || true; sleep 0.3
/usr/share/novnc/utils/novnc_proxy --vnc localhost:5900 --listen 6080 &
NOVNC_PID=$!
sleep 1

log "===> Open http://localhost:6080/vnc.html in the PORTS panel to watch Playwright LIVE <=="

# ── 8. Run Playwright UI tests (headed, 800 ms slow-motion) ──────────────────
log "Running Playwright UI tests (test_ui.py) — browser visible on the virtual display..."
set +e
DISPLAY=:99 python test_ui.py http://localhost:8080
UI_EXIT=$?
set -e

TEST_EXIT=$(( API_EXIT || UI_EXIT ))

# ── 9. Keep server running after tests ──────────────────────────────────────
trap - EXIT INT TERM   # Remove auto-kill so server stays up
if [[ $TEST_EXIT -eq 0 ]]; then
    log "All tests passed. Server still running at http://0.0.0.0:8080 (PID: $APP_PID)"
else
    warn "Some tests failed (API exit: $API_EXIT, UI exit: $UI_EXIT). Server still running at http://0.0.0.0:8080 (PID: $APP_PID)"
fi
log "Press Ctrl+C to stop the server."
wait "$APP_PID"
