"""
Captures screenshots of all Streamlit UI tabs and saves them to screenshots/
Uses Playwright running inside the container (localhost access, no auth required).
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_URL  = "http://localhost:8502"
SAVE_DIR  = Path(__file__).parent.parent / "screenshots"
SAVE_DIR.mkdir(exist_ok=True)

TABS = [
    ("chat",       "💬 Chat",        None),
    ("tickets",    "🎫 Tickets",     None),
    ("logs",       "📋 Logs",        None),
    ("rag_store",  "🧠 RAG Store",   None),
    ("evaluation", "📊 Evaluation",  None),
]


async def wait_for_streamlit(page, timeout=45_000):
    """Wait until Streamlit has fully rendered content."""
    await page.wait_for_load_state("domcontentloaded", timeout=timeout)
    # Wait for Streamlit app container
    await page.wait_for_selector('[data-testid="stApp"]', timeout=timeout)
    # Wait for any Streamlit spinner to disappear
    try:
        await page.wait_for_selector('.stSpinner', state='detached', timeout=8_000)
    except Exception:
        pass
    # Wait until there is visible text content in the app
    await page.wait_for_function(
        "() => document.querySelector('[data-testid=\"stApp\"]')?.innerText?.trim().length > 20",
        timeout=timeout,
    )
    await asyncio.sleep(2.0)  # final render settle


async def click_tab(page, tab_label: str):
    """Click a tab by its visible text and wait for content to settle."""
    # Use partial text match for tab button
    label_word = tab_label.split()[-1]  # e.g. "Chat", "Tickets"
    await page.click(f'button[role="tab"]:has-text("{label_word}")')
    await asyncio.sleep(2.0)


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page(viewport={"width": 1280, "height": 900})

        print(f"Opening {BASE_URL} ...")
        await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)
        await wait_for_streamlit(page)
        print("  Streamlit loaded.")

        # ── 1. Full app screenshot (Chat tab default) ──────────────────────
        path = SAVE_DIR / "01_chat_tab.png"
        await page.screenshot(path=str(path), full_page=False)
        print(f"  Saved: {path.name}")

        # ── 2. Tickets tab ─────────────────────────────────────────────────
        await click_tab(page, "🎫 Tickets")
        path = SAVE_DIR / "02_tickets_tab.png"
        await page.screenshot(path=str(path), full_page=False)
        print(f"  Saved: {path.name}")

        # ── 3. Logs tab ────────────────────────────────────────────────────
        await click_tab(page, "📋 Logs")
        path = SAVE_DIR / "03_logs_tab.png"
        await page.screenshot(path=str(path), full_page=False)
        print(f"  Saved: {path.name}")

        # ── 4. RAG Store tab ───────────────────────────────────────────────
        await click_tab(page, "🧠 RAG Store")
        path = SAVE_DIR / "04_rag_store_tab.png"
        await page.screenshot(path=str(path), full_page=False)
        print(f"  Saved: {path.name}")

        # ── 5. Evaluation tab ──────────────────────────────────────────────
        await click_tab(page, "📊 Evaluation")
        path = SAVE_DIR / "05_evaluation_tab.png"
        await page.screenshot(path=str(path), full_page=False)
        print(f"  Saved: {path.name}")

        # ── 6. Full page scrolled screenshot of Chat tab ───────────────────
        await click_tab(page, "💬 Chat")
        await asyncio.sleep(0.8)
        path = SAVE_DIR / "06_full_page.png"
        await page.screenshot(path=str(path), full_page=True)
        print(f"  Saved: {path.name}")

        await browser.close()
        print("\nAll screenshots saved to screenshots/")


if __name__ == "__main__":
    asyncio.run(main())
