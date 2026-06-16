import os
import json
import logging
from pathlib import Path
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Engine.Session")

# Local cache directory path to store authenticated session cookies
COOKIE_DIR = Path(__file__).resolve().parent.parent / "database" / "cookies"
os.makedirs(COOKIE_DIR, exist_ok=True)

def _get_cookie_path(account_id: int) -> Path:
    return COOKIE_DIR / f"account_{account_id}_cookies.json"

async def save_session_cookies(account_id: int, context) -> None:
    """Serializes browser context cookies and saves them to a local JSON file."""
    cookies = await context.cookies()
    cookie_path = _get_cookie_path(account_id)
    with open(cookie_path, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=4)
    logger.info(f"Saved active session cookies for account validation footprint: {account_id}")

async def load_session_cookies(account_id: int, context) -> bool:
    """Injects saved session cookies back into the active browser context."""
    cookie_path = _get_cookie_path(account_id)
    if not cookie_path.exists():
        return False
    
    try:
        with open(cookie_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)
        logger.info(f"Loaded active session cookies for account: {account_id}")
        return True
    except Exception as e:
        logger.error(f"Error loading cookies for account {account_id}: {str(e)}")
        return False

async def remove_session_cookies(account_id: int) -> None:
    """Deletes the stored cookie footprint when an account is cleared or updated."""
    cookie_path = _get_cookie_path(account_id)
    if cookie_path.exists():
        os.remove(cookie_path)