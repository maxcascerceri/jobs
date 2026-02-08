"""
Headless browser fetcher using Playwright.
Use only for sources that block simple HTTP (403). Lazy-loaded so API-only runs don't need it.
Runs async Playwright in a fresh event loop per call to avoid conflicts with other async code.
"""
import os
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def _fetch_html_async(url: str, timeout_ms: int = 30000) -> Optional[str]:
    """Fetch a URL with a headless browser. Returns page HTML or None."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning(
            "Playwright not installed. Run: pip install playwright && python -m playwright install chromium"
        )
        return None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 720},
                )
                page = await context.new_page()
                response = await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                if not response or response.status >= 400:
                    logger.warning("Headless fetch got status %s for %s", getattr(response, "status", None), url)
                    return None
                await page.wait_for_timeout(500)
                html = await page.content()
                await context.close()
                return html
            finally:
                await browser.close()
    except Exception as e:
        logger.warning("Headless fetch failed for %s: %s", url, e)
        return None


def fetch_html(url: str, timeout_ms: int = 30000) -> Optional[str]:
    """
    Fetch a URL with a headless browser. Returns page HTML or None.
    Call this only when requests get 403 or when the page is JS-rendered.
    """
    try:
        return asyncio.run(_fetch_html_async(url, timeout_ms))
    except RuntimeError as e:
        if "event loop" in str(e).lower() or "asyncio" in str(e).lower():
            # Already inside an event loop — run in a new thread with its own loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, _fetch_html_async(url, timeout_ms))
                return future.result(timeout=(timeout_ms / 1000) + 30)
        raise


async def _fetch_html_with_scroll_async(
    url: str,
    scroll_cycles: int = 15,
    scroll_pause_ms: int = 800,
    timeout_ms: int = 60000,
) -> Optional[str]:
    """
    Load URL in headless browser, scroll to bottom and optionally click "Load more"
    to trigger lazy-loaded content, then return final page HTML.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("Playwright not installed.")
        return None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 720},
                )
                page = await context.new_page()
                response = await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                if not response or response.status >= 400:
                    logger.warning("Headless scroll fetch got status %s for %s", getattr(response, "status", None), url)
                    return None
                await page.wait_for_timeout(1500)

                load_more_texts = ["Load more", "Load more jobs", "Show more", "See more jobs", "More jobs"]
                for _ in range(scroll_cycles):
                    # Try to click a "Load more" style button if present
                    clicked = False
                    for text in load_more_texts:
                        try:
                            for loc in [
                                page.get_by_role("button", name=text),
                                page.locator(f'button:has-text("{text}")'),
                                page.locator(f'a:has-text("{text}")'),
                            ]:
                                if await loc.count() > 0:
                                    first = loc.first
                                    if await first.is_visible():
                                        await first.click()
                                        await page.wait_for_timeout(scroll_pause_ms)
                                        clicked = True
                                        break
                            if clicked:
                                break
                        except Exception:
                            pass

                    # Scroll to bottom to trigger infinite scroll
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(scroll_pause_ms)

                html = await page.content()
                await context.close()
                return html
            finally:
                await browser.close()
    except Exception as e:
        logger.warning("Headless scroll fetch failed for %s: %s", url, e)
        return None


def fetch_html_with_scroll(
    url: str,
    scroll_cycles: int = 15,
    scroll_pause_ms: int = 800,
    timeout_ms: int = 60000,
) -> Optional[str]:
    """
    Load URL, scroll and click "Load more" as needed, return final HTML.
    Use for pages that lazy-load or paginate with a button.
    """
    try:
        return asyncio.run(_fetch_html_with_scroll_async(url, scroll_cycles, scroll_pause_ms, timeout_ms))
    except RuntimeError as e:
        if "event loop" in str(e).lower() or "asyncio" in str(e).lower():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(
                    asyncio.run,
                    _fetch_html_with_scroll_async(url, scroll_cycles, scroll_pause_ms, timeout_ms),
                )
                return future.result(timeout=(timeout_ms / 1000) + 60)
        raise


async def _with_logged_in_session_async(
    login_url: str,
    email: str,
    password: str,
    async_callback,
    timeout_ms: int = 30000,
):
    """
    Start browser, log in at login_url with email/password, then call async_callback(page).
    async_callback must be async and accept one argument (page). Return value is passed through.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("Playwright not installed.")
        return None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
        )
        page = await context.new_page()
        try:
            await page.goto(login_url, wait_until="networkidle", timeout=timeout_ms)
            await page.wait_for_timeout(3000)
            # If no email field yet, try clicking "Log in" / "Sign in" (for SPAs with modal or lazy form)
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[id="email"]',
                'input[placeholder*="mail" i]',
                'input[placeholder*="email" i]',
                'input[name="username"]',
                'input[autocomplete="email"]',
            ]
            email_loc = None
            for sel in email_selectors:
                try:
                    loc = page.locator(sel)
                    if await loc.count() > 0:
                        await loc.first.wait_for(state="visible", timeout=5000)
                        email_loc = loc.first
                        break
                except Exception:
                    continue
            if not email_loc:
                # Open login popup: header has "Log in" button (or link) that opens a modal
                for role, name in [("button", "Log in"), ("button", "Log In"), ("link", "Log in")]:
                    try:
                        loc = page.get_by_role(role, name=name).first
                        if await loc.count() > 0:
                            await loc.click()
                            await page.wait_for_timeout(2000)
                            break
                    except Exception:
                        continue
                # In popup: choose "Sign in" to show email/password form (tab or link)
                for role in ["link", "button"]:
                    try:
                        sign_in = page.get_by_role(role, name="Sign in").first
                        if await sign_in.count() > 0:
                            await sign_in.click()
                            await page.wait_for_timeout(2000)
                            break
                    except Exception:
                        continue
                for sel in email_selectors:
                    try:
                        loc = page.locator(sel)
                        if await loc.count() > 0:
                            await loc.first.wait_for(state="visible", timeout=10000)
                            email_loc = loc.first
                            break
                    except Exception:
                        continue
            if not email_loc:
                logger.warning("Login form fill/click failed: no email/username input found")
                # Save page HTML for debugging (find correct selectors from this file)
                try:
                    _debug_path = os.path.join(os.path.dirname(__file__), "remotesource_debug.html")
                    with open(_debug_path, "w", encoding="utf-8") as f:
                        f.write(await page.content())
                    logger.info("Saved page HTML to %s — open it to find the correct input selectors", _debug_path)
                except Exception as e:
                    logger.debug("Could not save debug HTML: %s", e)
                await context.close()
                await browser.close()
                return None
            await email_loc.fill(email)
            pass_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[id="password"]',
                'input[autocomplete="current-password"]',
            ]
            pass_loc = None
            for sel in pass_selectors:
                try:
                    loc = page.locator(sel)
                    if await loc.count() > 0:
                        pass_loc = loc.first
                        break
                except Exception:
                    continue
            if not pass_loc:
                logger.warning("Login form fill/click failed: no password input found")
                await context.close()
                await browser.close()
                return None
            await pass_loc.fill(password)
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Log in")',
                'button:has-text("Sign in")',
                'button:has-text("Log In")',
                '[type="submit"]',
            ]
            for sel in submit_selectors:
                try:
                    btn = page.locator(sel)
                    if await btn.count() > 0:
                        await btn.first.click()
                        break
                except Exception:
                    continue
            await page.wait_for_load_state("networkidle", timeout=15000)
            await page.wait_for_timeout(2000)
            result = await async_callback(page)
            return result
        finally:
            await context.close()
            await browser.close()


def with_logged_in_session(login_url: str, email: str, password: str, async_callback, timeout_ms: int = 30000):
    """Sync wrapper: log in at login_url, then run async_callback(page). Returns callback result."""
    try:
        return asyncio.run(_with_logged_in_session_async(login_url, email, password, async_callback, timeout_ms))
    except RuntimeError as e:
        if "event loop" in str(e).lower() or "asyncio" in str(e).lower():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(
                    asyncio.run,
                    _with_logged_in_session_async(login_url, email, password, async_callback, timeout_ms),
                )
                return future.result(timeout=120)
        raise


class HeadlessResponse:
    """Minimal response-like object so callers can use .text and .json() like requests.Response."""

    def __init__(self, text: str, status_code: int = 200, url: str = ""):
        self.text = text
        self.status_code = status_code
        self.url = url

    def raise_for_status(self):
        if self.status_code >= 400:
            raise OSError(f"HTTP {self.status_code}")

    def json(self):
        import json
        return json.loads(self.text)
