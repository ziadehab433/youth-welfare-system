import os
import base64
import asyncio
import logging
import atexit
from django.conf import settings
from django.core.cache import cache
from rest_framework.renderers import BaseRenderer
from playwright.async_api import async_playwright
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

class PlaywrightPDFService:
    def __init__(self):
        self._playwright = None
        self._browser = None
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(6)

    async def _launch_browser(self):
        logger.info("Launching Playwright browser")

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-sync",
                "--disable-default-apps",
                "--disable-translate",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--metrics-recording-only",
                "--mute-audio",
                "--single-process",
                "--no-zygote",
            ],
        )
        logger.info("Playwright browser ready")

    async def get_browser(self):
        async with self._lock:
            if self._browser:
                try:
                    if self._browser.is_connected():
                        return self._browser
                except Exception:
                    pass
            if self._browser:
                try:
                    await self._browser.close()
                except Exception:
                    pass
            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception:
                    pass
            await self._launch_browser()
            return self._browser

    async def generate_pdf(self, html_content, margins=None):
        if not html_content:
            raise ValueError("Empty HTML")
        if len(html_content) > 10_000_000:
            raise ValueError("HTML too large")

        async with self._semaphore:

            browser = await self.get_browser()

            for attempt in range(2):

                context = None
                page = None

                try:

                    async with asyncio.timeout(60):

                        context = await browser.new_context(
                            java_script_enabled=False
                        )

                        page = await context.new_page()

                        async def block_heavy(route):

                            resource = route.request.resource_type

                            if resource in ["media"]:
                                await route.abort()
                            else:
                                await route.continue_()

                        await page.route("**/*", block_heavy)

                        await page.emulate_media(media="print")

                        await page.set_content(
                            html_content,
                            wait_until="domcontentloaded",
                            timeout=20000,
                        )

                        pdf_margins = margins or {
                            "top": "0px",
                            "right": "0px",
                            "bottom": "0px",
                            "left": "0px",
                        }

                        pdf = await page.pdf(
                            format="A4",
                            print_background=True,
                            margin=pdf_margins,
                            display_header_footer=False,
                        )

                        return pdf

                except asyncio.TimeoutError:

                    logger.error("PDF generation timeout")

                    if attempt == 1:
                        raise

                except Exception as e:

                    logger.exception(f"PDF generation error: {e}")

                    if attempt == 1:
                        raise

                    await self.restart_browser()

                    browser = await self.get_browser()

                finally:
                    try:
                        if page:
                            await page.close()
                    except Exception:
                        pass

                    try:
                        if context:
                            await context.close()
                    except Exception:
                        pass

        raise RuntimeError("PDF generation failed")

    async def restart_browser(self):
        logger.warning("Restarting browser")
        try:
            if self._browser:
                await self._browser.close()
        except Exception:
            pass
        self._browser = None

    async def shutdown(self):
        logger.info("Shutting down Playwright")
        try:
            if self._browser:
                await self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass

pdf_service = PlaywrightPDFService()

def generate_pdf_sync(html, margins=None):
    return async_to_sync(pdf_service.generate_pdf)(html, margins)

class PDFRenderer(BaseRenderer):
    media_type = "application/pdf"
    format = "pdf"
    charset = None
    render_style = "binary"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data

def get_report_assets():
    CACHE_KEY = "report_assets_v1"
    assets = cache.get(CACHE_KEY)
    if assets:
        return assets

    assets = {"logo": "", "font": ""}

    logo_path = os.path.join(settings.BASE_DIR, "static/logo/logo.png")
    font_path = os.path.join(settings.BASE_DIR, "static/fonts/Amiri-Regular.ttf")

    try:
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                assets["logo"] = base64.b64encode(f.read()).decode()

        if os.path.exists(font_path):
            with open(font_path, "rb") as f:
                assets["font"] = base64.b64encode(f.read()).decode()

    except Exception as e:
        logger.warning(f"Asset loading error: {e}")

    cache.set(CACHE_KEY, assets, 60 * 60 * 24)

    return assets

def shutdown_playwright():
    try:
        async_to_sync(pdf_service.shutdown)()
    except Exception:
        pass

atexit.register(shutdown_playwright)