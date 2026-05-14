"""
Captures screenshots of all Streamlit UI tabs and saves them to screenshots/.
Uses Playwright running inside the container (localhost access, no auth required).

Tabs captured: Chat, Tickets, Evaluation (Logs and RAG Store removed from UI).
Also pre-fills each sample message button to show the test-case scenarios.
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:8502"
SAVE_DIR = Path(__file__).parent.parent / "screenshots"
SAVE_DIR.mkdir(exist_ok=True)


async def wait_for_streamlit(page, timeout=45_000):
    """Wait until Streamlit has fully rendered content."""
    await page.wait_for_load_state("domcontentloaded", timeout=timeout)
    await page.wait_for_selector('[data-testid="stApp"]', timeout=timeout)
    try:
        await page.wait_for_selector(".stSpinner", state="detached", timeout=8_000)
    except Exception:
        pass
    await page.wait_for_function(
        "() => document.querySelector('[data-testid=\"stApp\"]')?.innerText?.trim().length > 20",
        timeout=timeout,
    )
    await asyncio.sleep(2.0)


async def click_tab(page, label_word: str):
    """Click a tab button by a word in its label and wait for content."""
    await page.click(f'button[role="tab"]:has-text("{label_word}")')
    await asyncio.sleep(2.0)


async def fill_and_screenshot(page, message: str, filename: str, label: str):
    """Type a message into the textarea and screenshot (without sending — no API key)."""
    await click_tab(page, "Chat")
    # Clear the textarea and type the test message
    textarea = page.locator("textarea").first
    await textarea.click()
    await textarea.fill(message)
    await asyncio.sleep(1.0)
    path = SAVE_DIR / filename
    await page.screenshot(path=str(path), full_page=False)
    print(f"  Saved: {path.name}  ({label})")


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page(viewport={"width": 1280, "height": 900})

        print(f"Opening {BASE_URL} ...")
        await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)
        await wait_for_streamlit(page)
        print("  Streamlit loaded.\n")

        # ── 01. Chat tab — empty (default state) ──────────────────────────
        path = SAVE_DIR / "01_chat_tab_default.png"
        await page.screenshot(path=str(path), full_page=False)
        print(f"  Saved: {path.name}  (Chat — default state)")

        # ── 02–04. Chat tab — test-case messages pre-filled ────────────────
        test_messages = [
            ("Thanks for sorting out my net banking login issue.",
             "02_chat_positive_feedback.png",
             "Test case: Positive Feedback (Alice)"),
            ("My debit card replacement still hasn't arrived after 3 weeks.",
             "03_chat_negative_feedback.png",
             "Test case: Negative Feedback (Carol)"),
            ("Could you check the status of ticket 650932?",
             "04_chat_ticket_query.png",
             "Test case: Ticket Query (Eve)"),
        ]
        for msg, fname, lbl in test_messages:
            await fill_and_screenshot(page, msg, fname, lbl)

        # ── 05. Tickets tab ────────────────────────────────────────────────
        await click_tab(page, "Tickets")
        path = SAVE_DIR / "05_tickets_tab.png"
        await page.screenshot(path=str(path), full_page=False)
        print(f"  Saved: {path.name}  (Tickets)")

        # ── 06. Evaluation tab ─────────────────────────────────────────────
        await click_tab(page, "Evaluation")
        path = SAVE_DIR / "06_evaluation_tab.png"
        await page.screenshot(path=str(path), full_page=False)
        print(f"  Saved: {path.name}  (Evaluation)")

        # ── 07. Full-page Chat tab ─────────────────────────────────────────
        await click_tab(page, "Chat")
        await asyncio.sleep(0.5)
        path = SAVE_DIR / "07_full_page.png"
        await page.screenshot(path=str(path), full_page=True)
        print(f"  Saved: {path.name}  (full-page scroll)")

        await browser.close()
        print("\nAll screenshots saved to screenshots/")


if __name__ == "__main__":
    asyncio.run(main())
