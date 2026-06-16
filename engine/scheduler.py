import asyncio
import logging
import datetime
from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models import Account, UpdateLog
from database.crypto import decrypt_password
from engine.browser_session import load_session_cookies, save_session_cookies
from engine.parser import detect_delta_changes
from playwright.async_api import async_playwright
from config.settings import BACKGROUND_CHECK_INTERVAL_SECONDS, HTTP_REQUEST_TIMEOUT_SECONDS

logger = logging.getLogger("Engine.Scheduler")

async def process_account_check(account_id: int) -> None:
    """Launches an isolated headless browser instance to check a single account for updates."""
    db: Session = SessionLocal()
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        db.close()
        return

    logger.info(f"Starting scheduled lookups for platform: {account.platform_name} ({account.username})")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        
        # Try utilizing session serialization tokens
        has_cookies = await load_session_cookies(account.id, context)
        page = await context.new_page()
        page.set_default_timeout(HTTP_REQUEST_TIMEOUT_SECONDS * 1000)
        
        try:
            # Navigate directly to target data layer URL
            await page.goto(account.target_url, wait_until="networkidle")
            
            # Simple heuristic detection mechanism checking if we were dropped back at a login screen
            current_url = page.url.lower()
            needs_login = not has_cookies or "login" in current_url or "signin" in current_url
            
            if needs_login:
                logger.info(f"Session cookies invalid or expired for account {account.id}. Re-authenticating...")
                # Decrypt password payload directly in active volatile memory segments
                plain_password = decrypt_password(account.encrypted_password)
                
                # --- HEURISTIC GENERIC LOGIN ROUTINE ---
                # Locates standard username and password fields on typical login pages
                inputs = await page.query_selector_all("input[type='text'], input[type='email'], input[type='username']")
                if inputs:
                    await inputs[0].fill(account.username)
                    
                password_inputs = await page.query_selector_all("input[type='password']")
                if password_inputs:
                    await password_inputs[0].fill(plain_password)
                    await password_inputs[0].press("Enter")
                    
                # Await operational stability buffers
                await page.wait_for_load_state("networkidle")
                
                # Double check to ensure we navigated back to the target view after logging in
                if page.url != account.target_url:
                    await page.goto(account.target_url, wait_until="networkidle")
                    
                # Cache newly established authentication token signatures
                await save_session_cookies(account.id, context)
            
            # Extract raw DOM body frames
            html_content = await page.content()
            
            # Run delta evaluations
            has_changes, new_snapshot = detect_delta_changes(html_content, account.last_update_summary)
            
            # Commit update changes to database state models
            account.last_checked = datetime.datetime.utcnow()
            account.last_update_summary = new_snapshot
            
            status_flag = "SUCCESS"
            log_detail = "Content checked, state unchanged."
            
            if has_changes:
                account.has_update = True
                status_flag = "CHANGED"
                log_detail = f"New modification delta detected at: {datetime.datetime.utcnow()}"
                logger.info(f"Update detected for account {account.id} on {account.platform_name}!")

            # Write event directly to historical log tier
            log_entry = UpdateLog(account_id=account.id, status=status_flag, details=log_detail)
            db.add(log_entry)
            db.commit()

        except Exception as err:
            logger.error(f"Execution boundary error during validation for account {account.id}: {str(err)}")
            log_entry = UpdateLog(account_id=account.id, status="FETCH_FAILED", details=str(err))
            db.add(log_entry)
            db.commit()
        finally:
            await context.close()
            await browser.close()
            db.close()

async def scheduler_loop() -> None:
    """Infinite core background thread loop coordinating your polling queues."""
    logger.info("Initializing background update checking scheduler...")
    while True:
        db = SessionLocal()
        accounts = db.query(Account).all()
        db.close()
        
        if accounts:
            # Process accounts concurrently using async tasks
            tasks = [process_account_check(acc.id) for acc in accounts]
            await asyncio.gather(*tasks)
            
        logger.info(f"Polling loop completed. Sleeping for {BACKGROUND_CHECK_INTERVAL_SECONDS} seconds.")
        await asyncio.sleep(BACKGROUND_CHECK_INTERVAL_SECONDS)