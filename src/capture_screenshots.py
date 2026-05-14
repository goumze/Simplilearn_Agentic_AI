"""
Captures screenshots of all Streamlit UI tabs and every test-case interaction.
Uses Playwright running inside the container (localhost access, no auth required).

Test cases mirror evaluation.py TEST_CASES so each run documents real agent output.
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:8502"
SAVE_DIR = Path(__file__).parent.parent / "screenshots"
SAVE_DIR.mkdir(exist_ok=True)

# Mirror of evaluation.py TEST_CASES
TEST_CASES = [
    {"name": "Alice",  "msg": "Thanks for sorting out my net banking login issue.",           "tag": "01_positive_alice"},
    {"name": "Bob",    "msg": "Your service is amazing! The loan approval was so fast.",       "tag": "02_positive_bob"},
    {"name": "Carol",  "msg": "My debit card replacement still hasn't arrived after 3 weeks.", "tag": "03_negative_carol"},
    {"name": "David",  "msg": "I was charged twice for the same transaction. This is unacceptable.", "tag": "04_negative_david"},
    {"name": "Eve",    "msg": "Could you check the status of ticket 650932?",                  "tag": "05_query_eve"},
    {"name": "Frank",  "msg": "What is the current status of my complaint number 123456?",     "tag": "06_query_frank"},
    {"name": "Grace",  "msg": "I'm extremely disappointed with the ATM service.",              "tag": "07_negative_grace"},
    {"name": "Henry",  "msg": "The mobile app works perfectly now. Great job!",                "tag": "08_positive_henry"},
]


async def wait_for_app(page, timeout=45_000):
    await page.wait_for_load_state("domcontentloaded", timeout=timeout)
    await page.wait_for_selector('[data-testid="stApp"]', timeout=timeout)
    try:
        await page.wait_for_selector(".stSpinner", state="detached", timeout=8_000)
    except Exception:
        pass
    await page.wait_for_function(
        "() => (document.querySelector('[data-testid=\"stApp\"]')?.innerText?.trim().length ?? 0) > 20",
        timeout=timeout,
    )
    await asyncio.sleep(1.5)


async def click_tab(page, label: str):
    await page.click(f'button[role="tab"]:has-text("{label}")')
    await asyncio.sleep(1.5)


async def run_test_case(page, customer_name: str, message: str) -> None:
    """Fill customer name + message, click Send, wait for agent response."""
    # Set customer name in sidebar (fill replaces existing content)
    name_input = page.locator('[data-testid="stTextInput"] input').first
    await name_input.click()
    await name_input.fill(customer_name)

    # Set message in textarea
    textarea = page.locator("textarea").first
    await textarea.click()
    await textarea.fill(message)

    # Click Send
    await page.click('button:has-text("Send")')

    # Wait: spinner appears then disappears, then result renders
    try:
        await page.wait_for_selector(".stSpinner", timeout=5_000)
    except Exception:
        pass
    try:
        await page.wait_for_selector(".stSpinner", state="detached", timeout=60_000)
    except Exception:
        pass
    await asyncio.sleep(2.0)


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page(viewport={"width": 1280, "height": 900})

        print(f"Opening {BASE_URL} ...")
        await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)
        await wait_for_app(page)
        print("  App loaded.")

        # ── 0. Default Chat tab ────────────────────────────────────────────
        path = SAVE_DIR / "00_chat_tab_default.png"
        await page.screenshot(path=str(path), full_page=False)
        print(f"  Saved: {path.name}")

        # ── 1-8. Run each test case ────────────────────────────────────────
        for tc in TEST_CASES:
            await click_tab(page, "Chat")
            await run_test_case(page, tc["name"], tc["msg"])
            path = SAVE_DIR / f"{tc['tag']}_result.png"
            await page.screenshot(path=str(path), full_page=False)
            print(f"  Saved: {path.name}  ({tc['name']} — {tc['msg'][:50]})")

        # ── 9. Tickets tab (after all interactions) ───────────────────────
        await click_tab(page, "Tickets")
        await asyncio.sleep(1.0)
        path = SAVE_DIR / "09_tickets_tab.png"
        await page.screenshot(path=str(path), full_page=False)
        print(f"  Saved: {path.name}")

        # ── 10. Evaluation tab – run evaluation ───────────────────────────
        await click_tab(page, "Evaluation")
        await asyncio.sleep(1.0)
        # Click "Run Evaluation"
        await page.click('button:has-text("Run Evaluation")')
        print("  Evaluation running (this may take ~30s)...")
        try:
            await page.wait_for_selector(".stSpinner", timeout=5_000)
        except Exception:
            pass
        try:
            await page.wait_for_selector(".stSpinner", state="detached", timeout=120_000)
        except Exception:
            pass
        await asyncio.sleep(2.0)
        path = SAVE_DIR / "10_evaluation_results.png"
        await page.screenshot(path=str(path), full_page=True)
        print(f"  Saved: {path.name}")

        await browser.close()
        print(f"\nAll screenshots saved to {SAVE_DIR}/")


if __name__ == "__main__":
    asyncio.run(main())
