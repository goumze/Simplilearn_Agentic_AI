#!/usr/bin/env bash
# run.sh — Install dependencies, start the Sidekick app, and run sample tests.
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

# ── 3. Free port 7860 if already in use ─────────────────────────────────────
if lsof -ti:7860 > /dev/null 2>&1; then
    warn "Port 7860 is busy — freeing it..."
    fuser -k 7860/tcp 2>/dev/null || true
    sleep 1
fi

# ── 4. Start app in background ───────────────────────────────────────────────
log "Starting Sidekick app (http://0.0.0.0:7860)..."
python main.py &
APP_PID=$!

# Kill app on script exit unless we explicitly clear the trap
cleanup() { kill "$APP_PID" 2>/dev/null || true; }
trap cleanup INT TERM EXIT

# ── 5. Wait for Gradio to be ready ───────────────────────────────────────────
log "Waiting for Gradio to become ready..."
MAX_WAIT=60
WAITED=0
until curl -sf http://localhost:7860/gradio_api/info > /dev/null 2>&1; do
    sleep 1
    WAITED=$((WAITED + 1))
    [[ $WAITED -ge $MAX_WAIT ]] && fail "App did not start within ${MAX_WAIT}s. Check for errors above."
done
log "App is ready!"

# ── 6. Sample tests via Gradio client API ────────────────────────────────────
log "Running sample tests..."

python - <<'PYEOF'
from gradio_client import Client
import uuid, sys

client = Client("http://localhost:7860", verbose=False)

TESTS = [
    {
        "name": "London Weather",
        "message": "What is the current weather in London?",
        "criteria": "The current temperature and weather condition in London is provided",
    },
    {
        "name": "BBC Top Headline",
        "message": "What is the top headline on BBC News today?",
        "criteria": "The actual current top headline from BBC News is provided",
    },
    {
        "name": "Bitcoin Price",
        "message": "What is the current price of Bitcoin in USD?",
        "criteria": "The current Bitcoin price in USD is provided",
    },
]

passed = 0
for i, test in enumerate(TESTS, 1):
    print(f"\n{'='*65}")
    print(f"  Test {i}/{len(TESTS)}: {test['name']}")
    print(f"  Query   : {test['message']}")
    print(f"  Criteria: {test['criteria']}")
    print(f"{'='*65}")
    try:
        result = client.predict(
            test["message"],
            test["criteria"],
            [],
            str(uuid.uuid4()),
            api_name="/process_message",
        )
        for msg in result:
            role = msg["role"].upper()
            content = msg["content"]
            text = content[0]["text"] if isinstance(content, list) else str(content)
            print(f"  [{role}] {text}\n")
        passed += 1
        print(f"  PASSED")
    except Exception as e:
        print(f"  FAILED — {e}")

print(f"\n{'='*65}")
print(f"  Results: {passed}/{len(TESTS)} tests passed")
print(f"{'='*65}\n")
sys.exit(0 if passed == len(TESTS) else 1)
PYEOF

TEST_EXIT=$?

# ── 7. Keep app running after tests ─────────────────────────────────────────
trap - EXIT INT TERM   # Remove auto-kill so app stays up
log "Tests complete. App is still running at http://0.0.0.0:7860 (PID: $APP_PID)"
log "Press Ctrl+C to stop the app."
wait "$APP_PID"
