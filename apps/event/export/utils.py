import os
import base64
import asyncio
import logging
import atexit
import threading
from django.conf import settings
from django.core.cache import cache
from rest_framework.renderers import BaseRenderer
from playwright.async_api import async_playwright
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)
_CONCURRENCY = 6
_BROWSER_MAX_USES = 200
_BLOCKED_RESOURCES = frozenset({"media"})  
_INIT_LOCK = threading.Lock()
_WAIT_FOR_IMAGES_JS = """
async () => {
    const imgs = [...document.images];
    await Promise.all(imgs.map(img =>
        img.complete
            ? null
            : new Promise(r => { img.onload = r; img.onerror = r; })
    ));
}
"""

_CHROMIUM_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-extensions",
    "--disable-sync",
    "--disable-default-apps",
    "--disable-translate",
    "--disable-background-timer-throttling",
    "--disable-renderer-backgrounding",
    "--metrics-recording-only",
    "--mute-audio",
]

_ASSET_PATHS: dict[str, str] = {
    "logo": os.path.join(settings.BASE_DIR, "static/logo/logo.png"),
    "font": os.path.join(settings.BASE_DIR, "static/fonts/Amiri-Regular.ttf"),
}

_ASSET_CACHE_KEY = "report_assets_v1"
_ASSET_CACHE_TTL = 60 * 60 * 24


class PlaywrightPDFService:
    def __init__(self):
        self._playwright = None
        self._browser = None
        self._browser_uses = 0
        self.__lock = None
        self.__semaphore = None

    @property
    def _lock(self) -> asyncio.Lock:
        if self.__lock is None:
            with _INIT_LOCK:
                if self.__lock is None:
                    self.__lock = asyncio.Lock()
        return self.__lock

    @property
    def _semaphore(self) -> asyncio.Semaphore:
        if self.__semaphore is None:
            with _INIT_LOCK:
                if self.__semaphore is None:
                    self.__semaphore = asyncio.Semaphore(_CONCURRENCY)
        return self.__semaphore

    async def _launch_browser(self) -> None:
        logger.info("Launching Playwright browser")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=_CHROMIUM_ARGS,
        )
        self._browser_uses = 0
        logger.info("Playwright browser launched successfully")

    async def get_browser(self):
        async with self._lock:
            needs_restart = (
                self._browser is None
                or not self._browser.is_connected()
                or self._browser_uses >= _BROWSER_MAX_USES
            )
            if needs_restart:
                logger.info(
                    "Browser restart triggered (uses=%d, connected=%s)",
                    self._browser_uses,
                    self._browser.is_connected() if self._browser else False,
                )
                await self._close_browser_unsafe()
                await self._launch_browser()
            return self._browser

    async def _close_browser_unsafe(self) -> None:
        try:
            if self._browser:
                await self._browser.close()
        except Exception:
            pass
        finally:
            self._browser = None

        try:
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass
        finally:
            self._playwright = None

    async def generate_pdf(self, html_content: str, margins: dict | None = None) -> bytes:
        if not html_content:
            raise ValueError("Empty HTML")
        if len(html_content) > 10_000_000:
            raise ValueError("HTML too large (max 10 MB)")

        pdf_margins = margins or {
            "top": "0px",
            "right": "0px",
            "bottom": "0px",
            "left": "0px",
        }

        async def block_heavy(route):
            if route.request.resource_type in _BLOCKED_RESOURCES:
                await route.abort()
            else:
                await route.continue_()

        async with self._semaphore:
            browser = await self.get_browser()

            for attempt in range(2):
                is_last_attempt = attempt == 1
                context = None
                page = None

                try:
                    async with asyncio.timeout(60):
                        context = await browser.new_context()
                        page = await context.new_page()

                        await page.route("**/*", block_heavy)
                        await page.emulate_media(media="print")
                        await page.set_content(
                            html_content,
                            wait_until="domcontentloaded",
                            timeout=20000,
                        )
                        try:
                            await page.wait_for_function(_WAIT_FOR_IMAGES_JS, timeout=10000)
                        except Exception:
                            logger.warning(
                                "Image wait timed out or failed on attempt %d; proceeding anyway",
                                attempt + 1,
                            )

                        pdf = await page.pdf(
                            format="A4",
                            print_background=True,
                            margin=pdf_margins,
                            display_header_footer=False,
                        )
                    async with self._lock:
                        self._browser_uses += 1

                    return pdf

                except asyncio.TimeoutError:
                    logger.error("PDF generation timed out (attempt %d/2)", attempt + 1)
                    if is_last_attempt:
                        raise
                    await self.restart_browser()
                    browser = await self.get_browser()

                except Exception as e:
                    logger.exception("PDF generation error (attempt %d/2): %s", attempt + 1, e)
                    if is_last_attempt:
                        raise
                    await self.restart_browser()
                    browser = await self.get_browser()

                finally:
                    for obj, name in [(page, "page"), (context, "context")]:
                        if obj:
                            try:
                                await obj.close()
                            except Exception:
                                logger.debug("Failed to close %s cleanly", name)

        raise RuntimeError("PDF generation failed after all retries")

    async def restart_browser(self) -> None:
        logger.warning("Restarting Playwright browser")
        async with self._lock:
            await self._close_browser_unsafe()

    async def shutdown(self) -> None:
        logger.info("Shutting down Playwright service")
        async with self._lock:
            await self._close_browser_unsafe()


pdf_service = PlaywrightPDFService()


def generate_pdf_sync(html: str, margins: dict | None = None) -> bytes:
    return async_to_sync(pdf_service.generate_pdf)(html, margins)


class PDFRenderer(BaseRenderer):
    media_type = "application/pdf"
    format = "pdf"
    charset = None
    render_style = "binary"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data

def get_report_assets() -> dict:
    assets = cache.get(_ASSET_CACHE_KEY)
    if assets:
        return assets

    assets = {}
    for key, path in _ASSET_PATHS.items():
        if not os.path.exists(path):
            logger.warning("Report asset not found: %s", path)
            assets[key] = ""
            continue
        try:
            with open(path, "rb") as f:
                assets[key] = base64.b64encode(f.read()).decode()
        except Exception as e:
            logger.warning("Failed to load asset %s: %s", path, e)
            assets[key] = ""

    cache.set(_ASSET_CACHE_KEY, assets, _ASSET_CACHE_TTL)
    return assets

def _shutdown_playwright() -> None:
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(pdf_service.shutdown())
        loop.close()
    except Exception:
        pass

atexit.register(_shutdown_playwright)