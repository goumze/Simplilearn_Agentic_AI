"""
test_ui.py — Playwright-driven UI tests for the Sidekick chat interface.
Run after the server is up: python test_ui.py [base_url]

Tests interact with the actual browser UI at / rather than the REST API
directly, exercising the full stack: browser → Flask → LangGraph → Playwright agent.
"""
import sys
from playwright.sync_api import sync_playwright, Page, expect

BASE_URL  = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8080"
NAV_WAIT  = 5_000    # ms — page-level waits
CHAT_WAIT = 180_000  # ms — LLM + browser-agent round trip can be slow

PASS = "\033[32mPASSED\033[0m"
FAIL = "\033[31mFAILED\033[0m"

passed = 0
failed = 0


# ── Helpers ───────────────────────────────────────────────────────────────────

def run_test(name: str, fn):
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


def fresh_page(browser) -> Page:
    """Return a new page navigated to BASE_URL."""
    page = browser.new_page()
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=NAV_WAIT)
    return page


def send_chat(page: Page, message: str, criteria: str = "") -> None:
    """Fill in the inputs and click Go, then wait for the typing indicator to appear."""
    page.fill("#msgInput", message)
    if criteria:
        page.fill("#criteriaInput", criteria)
    page.click("#goBtn")


def wait_for_response(page: Page) -> None:
    """Block until the typing indicator disappears (agent has replied)."""
    # Wait for typing indicator to appear first (proves request was sent)
    page.wait_for_selector("#typing", timeout=10_000)
    # Then wait for it to disappear (proves reply arrived)
    page.wait_for_selector("#typing", state="detached", timeout=CHAT_WAIT)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_page_load(browser):
    """The UI renders with the correct title, header, and empty state."""
    page = fresh_page(browser)

    # Title
    assert "Sidekick" in page.title(), f"Unexpected title: {page.title()}"
    print(f"  Title: {page.title()}")

    # Header
    header_text = page.locator("header h1").inner_text()
    assert "Sidekick" in header_text, f"Unexpected header: {header_text}"
    print(f"  Header: {header_text}")

    # Empty-state placeholder is visible before any message
    empty = page.locator("#emptyState")
    expect(empty).to_be_visible()
    print(f"  Empty state visible: ✓")

    # Input elements present and enabled
    expect(page.locator("#msgInput")).to_be_visible()
    expect(page.locator("#criteriaInput")).to_be_visible()
    expect(page.locator("#goBtn")).to_be_enabled()
    expect(page.locator("#resetBtn")).to_be_enabled()
    print(f"  Input controls present and enabled: ✓")

    page.close()


def test_go_button_disabled_while_busy(browser):
    """The Go button is disabled while the agent is processing a request."""
    page = fresh_page(browser)

    send_chat(page, "What is 2 + 2?", criteria="The answer 4 is given")

    # Immediately after clicking, Go should be disabled
    expect(page.locator("#goBtn")).to_be_disabled()
    print(f"  Go button disabled during request: ✓")

    wait_for_response(page)

    # After reply, Go should be re-enabled
    expect(page.locator("#goBtn")).to_be_enabled()
    print(f"  Go button re-enabled after response: ✓")

    page.close()


def test_user_bubble_appears(browser):
    """A user message bubble is rendered immediately after submitting."""
    page = fresh_page(browser)

    msg = "Hello Sidekick!"
    page.fill("#msgInput", msg)
    page.click("#goBtn")

    # User bubble should appear right away (before the LLM replies)
    user_bubble = page.locator(".msg.user .bubble").first
    expect(user_bubble).to_be_visible(timeout=3_000)
    assert msg in user_bubble.inner_text(), "User message text missing from bubble"
    print(f"  User bubble content: {user_bubble.inner_text()[:60]!r}")

    # Input should be cleared
    assert page.input_value("#msgInput") == "", "msgInput was not cleared after send"
    print(f"  Input cleared after send: ✓")

    # Empty state removed
    expect(page.locator("#emptyState")).not_to_be_visible()
    print(f"  Empty state hidden after first message: ✓")

    wait_for_response(page)
    page.close()


def test_assistant_and_evaluator_bubbles(browser):
    """After a full round-trip the assistant reply and evaluator feedback both appear."""
    page = fresh_page(browser)

    send_chat(
        page,
        "What is the current weather in Paris?",
        criteria="The temperature in Paris is stated",
    )
    wait_for_response(page)

    # Assistant bubble
    assistant_bubbles = page.locator(".msg.assistant .bubble")
    assert assistant_bubbles.count() >= 1, "No assistant bubble found"
    reply_text = assistant_bubbles.first.inner_text()
    print(f"  Assistant reply (first 120 chars): {reply_text[:120]!r}")

    # Evaluator bubble
    eval_bubbles = page.locator(".msg.evaluator .bubble")
    assert eval_bubbles.count() >= 1, "No evaluator bubble found"
    eval_text = eval_bubbles.first.inner_text()
    print(f"  Evaluator feedback (first 120 chars): {eval_text[:120]!r}")

    page.close()


def test_enter_key_submits(browser):
    """Pressing Enter (without Shift) in the message box submits the form."""
    page = fresh_page(browser)

    page.fill("#msgInput", "Ping")
    page.keyboard.press("Enter")

    # Typing indicator should appear shortly after
    page.wait_for_selector("#typing", timeout=10_000)
    print(f"  Enter key triggered submission: ✓")

    wait_for_response(page)
    page.close()


def test_reset_clears_chat(browser):
    """Clicking Reset clears the chat and restores the empty state."""
    page = fresh_page(browser)

    send_chat(page, "Quick reset test")
    wait_for_response(page)

    # Confirm messages are present
    assert page.locator(".msg").count() > 0, "Expected messages before reset"

    page.click("#resetBtn")

    # Chat should be cleared and empty-state restored
    expect(page.locator("#emptyState")).to_be_visible(timeout=3_000)
    assert page.locator(".msg").count() == 0, "Messages remain after reset"
    assert page.input_value("#msgInput") == "", "msgInput not cleared on reset"
    assert page.input_value("#criteriaInput") == "", "criteriaInput not cleared on reset"
    print(f"  Chat cleared and empty state restored: ✓")

    page.close()


def test_shift_enter_newline(browser):
    """Shift+Enter inserts a newline instead of submitting."""
    page = fresh_page(browser)

    page.fill("#msgInput", "Line one")
    page.keyboard.press("Shift+Enter")
    page.keyboard.type("Line two")

    value = page.input_value("#msgInput")
    assert "\n" in value, "Shift+Enter did not insert a newline"
    print(f"  Shift+Enter inserted newline: ✓")

    # No submission happened (no typing indicator, no user bubble)
    assert page.locator("#typing").count() == 0, "Unexpected submission on Shift+Enter"
    print(f"  No accidental submission on Shift+Enter: ✓")

    page.close()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\nSidekick UI Tests (Playwright)")
    print(f"Target: {BASE_URL}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=False,   # visible browser so you can watch actions live
            slow_mo=800,      # 800 ms pause between each action for visibility
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
                # Prevent Chromium from throttling timers/JS when the
                # window is occluded on the Xvfb virtual display
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
            ],
        )

        run_test("UI-1. Page load & structure",           lambda: test_page_load(browser))
        run_test("UI-2. Go button disables while busy",   lambda: test_go_button_disabled_while_busy(browser))
        run_test("UI-3. User bubble appears immediately", lambda: test_user_bubble_appears(browser))
        run_test("UI-4. Assistant & evaluator bubbles",   lambda: test_assistant_and_evaluator_bubbles(browser))
        run_test("UI-5. Enter key submits message",       lambda: test_enter_key_submits(browser))
        run_test("UI-6. Reset clears the chat",           lambda: test_reset_clears_chat(browser))
        run_test("UI-7. Shift+Enter inserts newline",     lambda: test_shift_enter_newline(browser))

        browser.close()

    print(f"\n{'='*65}")
    print(f"  UI Results: {passed}/{passed + failed} tests passed")
    print(f"{'='*65}\n")
    sys.exit(0 if failed == 0 else 1)
