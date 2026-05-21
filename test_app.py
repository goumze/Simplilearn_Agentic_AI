"""
test_app.py — Integration tests for the Sidekick Flask REST API.
Run after the server is up: python test_app.py [base_url]
"""
import sys
import uuid
import requests

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:7860"
TIMEOUT  = 180  # seconds per request (browser + LLM can be slow)

PASS = "\033[32mPASSED\033[0m"
FAIL = "\033[31mFAILED\033[0m"

passed = 0
failed = 0


def run_test(name, fn):
    global passed, failed
    print(f"\n{'─'*65}")
    print(f"  {name}")
    print(f"{'─'*65}")
    try:
        fn()
        print(f"  {PASS}")
        passed += 1
    except Exception as e:
        print(f"  {FAIL} — {e}")
        failed += 1


# ── Helpers ──────────────────────────────────────────────────────────────────

def chat(message, criteria="", history=None, thread_id=None):
    r = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": message,
            "success_criteria": criteria,
            "history": history or [],
            "thread_id": thread_id or str(uuid.uuid4()),
        },
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def print_messages(messages, indent="  "):
    for msg in messages:
        content = msg.get("content", "")
        print(f"{indent}[{msg['role'].upper()}] {str(content)[:300]}")


# ── Tests ────────────────────────────────────────────────────────────────────

def test_health():
    r = requests.get(f"{BASE_URL}/health", timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data.get("status") == "ok", f"Unexpected body: {data}"
    print(f"  Response: {data}")


def test_reset():
    r = requests.post(f"{BASE_URL}/api/reset", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert "thread_id" in data and len(data["thread_id"]) > 0
    print(f"  New thread_id: {data['thread_id']}")


def test_missing_message():
    r = requests.post(f"{BASE_URL}/api/chat", json={}, timeout=10)
    assert r.status_code == 400, f"Expected 400, got {r.status_code}"
    assert "error" in r.json()
    print(f"  Correctly rejected empty request: {r.json()}")


def test_weather():
    data = chat(
        message="What is the current weather in London?",
        criteria="The current temperature and weather condition in London is provided",
    )
    assert "messages" in data and len(data["messages"]) >= 3
    print_messages(data["messages"])


def test_bbc_headline():
    data = chat(
        message="What is the top headline on BBC News right now?",
        criteria="The actual current top headline from BBC News is provided",
    )
    assert "messages" in data and len(data["messages"]) >= 3
    print_messages(data["messages"])


def test_bitcoin_price():
    data = chat(
        message="What is the current price of Bitcoin in USD?",
        criteria="A specific Bitcoin price in USD is stated",
    )
    assert "messages" in data and len(data["messages"]) >= 3
    print_messages(data["messages"])


def test_multiturn():
    thread_id = str(uuid.uuid4())

    # Turn 1
    r1 = chat(
        message="What is the current price of Ethereum in USD?",
        criteria="A specific Ethereum price in USD is stated",
        thread_id=thread_id,
    )
    assert "messages" in r1 and len(r1["messages"]) >= 3
    print(f"  Turn 1 — {len(r1['messages'])} messages")
    print_messages(r1["messages"][-2:])

    # Turn 2 — reference previous exchange
    r2 = chat(
        message="Based on what you just found, is that higher or lower than Bitcoin's price?",
        criteria="A comparison between Ethereum and Bitcoin prices is provided",
        history=r1["messages"],
        thread_id=thread_id,
    )
    assert "messages" in r2 and len(r2["messages"]) > len(r1["messages"])
    print(f"  Turn 2 — {len(r2['messages'])} messages")
    print_messages(r2["messages"][-2:])


# ── Run all tests ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\nSidekick API Integration Tests")
    print(f"Target: {BASE_URL}")

    run_test("1. Health check",             test_health)
    run_test("2. Reset endpoint",           test_reset)
    run_test("3. Missing message → 400",    test_missing_message)
    run_test("4. London weather query",     test_weather)
    run_test("5. BBC News headline",        test_bbc_headline)
    run_test("6. Bitcoin price",            test_bitcoin_price)
    run_test("7. Multi-turn conversation",  test_multiturn)

    print(f"\n{'='*65}")
    print(f"  Results: {passed}/{passed + failed} tests passed")
    print(f"{'='*65}\n")
    sys.exit(0 if failed == 0 else 1)
