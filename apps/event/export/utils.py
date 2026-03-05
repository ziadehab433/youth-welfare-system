import os
import base64
import asyncio
import logging
import concurrent.futures
from django.conf import settings
from django.core.cache import cache
from rest_framework.renderers import BaseRenderer
from playwright.async_api import async_playwright
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=os.cpu_count() or 4
)

_playwright = None
_browser = None
_browser_lock = asyncio.Lock()

async def get_browser():
    global _playwright, _browser

    async with _browser_lock:
        try:
            if _browser and not _browser.is_connected():
                logger.warning("Browser disconnected, creating new one")
                _browser = None
        except Exception:
            _browser = None

        if _browser is None:
            logger.info("Launching persistent Playwright browser...")

            if _playwright:
                try:
                    await _playwright.stop()
                except Exception:
                    pass

            _playwright = await async_playwright().start()

            _browser = await _playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                    "--disable-background-networking",
                    "--disable-sync",
                    "--metrics-recording-only",
                    "--mute-audio",
                ],
            )

            logger.info("Persistent browser launched")

        return _browser


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
        logger.debug("Assets loaded from cache")
        return assets

    assets = {"logo": "", "font": ""}

    logo_path = os.path.join(settings.BASE_DIR, "static", "logo", "logo.png")
    font_path = os.path.join(settings.BASE_DIR, "static", "fonts", "Amiri-Regular.ttf")

    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as f:
                assets["logo"] = base64.b64encode(f.read()).decode("ascii")
        except Exception as e:
            logger.warning(f"Logo loading error: {e}")

    if os.path.exists(font_path):
        try:
            with open(font_path, "rb") as f:
                assets["font"] = base64.b64encode(f.read()).decode("ascii")
        except Exception as e:
            logger.warning(f"Font loading error: {e}")

    cache.set(CACHE_KEY, assets, timeout=60 * 60 * 24)

    return assets

async def _run_playwright_core(html_content, output_path=None, margins=None):

    if len(html_content) > 10_000_000:
        raise ValueError("HTML content too large")

    for attempt in range(2):
        page = None
        context = None

        try:
            async with asyncio.timeout(60):

                browser = await get_browser()

                context = await browser.new_context(
                    viewport={"width": 794, "height": 1123}
                )

                page = await context.new_page()

                await page.emulate_media(media="print")

                await page.set_content(
                    html_content,
                    wait_until="networkidle",
                    timeout=45000,
                )

                pdf_margins = margins or {
                    "top": "0px",
                    "right": "0px",
                    "bottom": "0px",
                    "left": "0px",
                }

                pdf_params = {
                    "format": "A4",
                    "print_background": True,
                    "margin": pdf_margins,
                    "display_header_footer": False,
                }

                if output_path:
                    pdf_params["path"] = output_path

                pdf_bytes = await page.pdf(**pdf_params)

                return pdf_bytes

        except asyncio.TimeoutError:
            logger.error("PDF generation timed out")

            if attempt == 1:
                raise

        except Exception as e:
            logger.exception(
                f"Playwright error attempt {attempt + 1}: {str(e)}"
            )

            if attempt == 1:
                raise

            global _browser
            _browser = None

            await asyncio.sleep(1)

        finally:
            if page:
                await page.close()

            if context:
                await context.close()

    raise Exception("Failed to generate PDF after retries")

def generate_pdf_from_html(html_content, output_path, margins=None):
    try:
        async_to_sync(_run_playwright_core)(
            html_content,
            output_path=output_path,
            margins=margins,
        )
        return True
    except Exception:
        return False

def generate_pdf_sync(html_content, margins=None):
    future = _EXECUTOR.submit(_run_playwright_sync, html_content, margins)
    return future.result()


def _run_playwright_sync(html_content, margins=None):
    return async_to_sync(_run_playwright_core)(
        html_content,
        margins=margins,
    )