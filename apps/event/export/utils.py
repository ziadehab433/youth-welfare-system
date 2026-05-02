import os
import base64
import asyncio
import logging
import atexit
import threading
import concurrent.futures
from django.conf import settings
from django.core.cache import cache
from rest_framework.renderers import BaseRenderer
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)
_PDF_CONCURRENCY = 4
_BROWSER_MAX_USES = 250

_HTML_MAX_BYTES = 15_000_000

_RENDER_TIMEOUT_SECONDS = 45
_SET_CONTENT_TIMEOUT_MS = 15_000
_IMAGE_WAIT_TIMEOUT_SECONDS = 10
_SYNC_WAIT_TIMEOUT_SECONDS = 60

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
    "--no-first-run",
    "--no-default-browser-check",
]

_ASSET_PATHS: dict[str, str] = {
    "logo": os.path.join(settings.BASE_DIR, "static/logo/logo.png"),
    "font": os.path.join(settings.BASE_DIR, "static/fonts/Amiri-Regular.ttf"),
}

_ASSET_CACHE_TTL = 60 * 60 * 24
_IMAGE_BASE64_CACHE_TTL = 60 * 60 * 24


_WAIT_FOR_IMAGES_AND_FONTS_JS = """
async () => {
    const imgs = Array.from(document.images || []);

    await Promise.all(imgs.map(img => {
        if (img.complete) {
            return Promise.resolve();
        }

        return new Promise(resolve => {
            const done = () => resolve();
            img.addEventListener("load", done, { once: true });
            img.addEventListener("error", done, { once: true });
        });
    }));

    if (document.fonts && document.fonts.ready) {
        try {
            await document.fonts.ready;
        } catch (_) {}
    }

    return true;
}
"""


# ============================================================
# Asset helpers
# ============================================================

def _file_signature(path: str) -> str:
    try:
        stat = os.stat(path)
        return f"{int(stat.st_mtime)}:{stat.st_size}"
    except FileNotFoundError:
        return "missing"


def _assets_cache_key() -> str:
    parts = ["report_assets_fast_v1"]

    for key, path in sorted(_ASSET_PATHS.items()):
        parts.append(f"{key}:{_file_signature(path)}")

    return "|".join(parts)


def get_report_assets() -> dict:
    cache_key = _assets_cache_key()
    assets = cache.get(cache_key)

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
                assets[key] = base64.b64encode(f.read()).decode("ascii")
        except Exception as exc:
            logger.warning("Failed to load report asset %s: %s", path, exc)
            assets[key] = ""

    cache.set(cache_key, assets, _ASSET_CACHE_TTL)
    return assets


def get_image_base64(image_path: str | None) -> str | None:
    if not image_path:
        return None

    try:
        image_path = str(image_path)

        if os.path.isabs(image_path):
            full_path = image_path
        else:
            full_path = os.path.join(settings.MEDIA_ROOT, image_path)

        if not os.path.exists(full_path):
            logger.warning("Image not found for PDF: %s", full_path)
            return None

        stat = os.stat(full_path)
        cache_key = f"pdf_image_b64:{full_path}:{int(stat.st_mtime)}:{stat.st_size}"

        cached = cache.get(cache_key)
        if cached:
            return cached

        with open(full_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("ascii")

        cache.set(cache_key, encoded, _IMAGE_BASE64_CACHE_TTL)
        return encoded

    except Exception as exc:
        logger.warning("Failed to load image for PDF %s: %s", image_path, exc)
        return None


# ============================================================
# Async Playwright core
# ============================================================

class PlaywrightPDFAsyncCore:
    def __init__(self):
        self._playwright = None
        self._browser = None

        self._browser_uses = 0
        self._active_jobs = 0
        self._restart_requested = False

        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition(self._lock)
        self._semaphore = asyncio.Semaphore(_PDF_CONCURRENCY)

    async def startup(self) -> None:
        async with self._condition:
            if not self._browser:
                await self._launch_browser_unsafe()

    async def _launch_browser_unsafe(self) -> None:
        logger.info("Launching Playwright Chromium browser")

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=_CHROMIUM_ARGS,
        )

        self._browser_uses = 0

        logger.info("Playwright Chromium browser launched")

    async def _close_browser_unsafe(self) -> None:
        try:
            if self._browser:
                await self._browser.close()
        except Exception:
            logger.exception("Failed to close Chromium browser")
        finally:
            self._browser = None

        try:
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            logger.exception("Failed to stop Playwright")
        finally:
            self._playwright = None

    def _browser_is_healthy_unlocked(self) -> bool:
        return bool(
            self._browser
            and self._browser.is_connected()
            and self._browser_uses < _BROWSER_MAX_USES
            and not self._restart_requested
        )

    async def _acquire_browser(self):
        async with self._condition:
            while True:
                if self._browser_is_healthy_unlocked():
                    self._active_jobs += 1
                    return self._browser

                if self._active_jobs == 0:
                    await self._close_browser_unsafe()
                    await self._launch_browser_unsafe()

                    self._restart_requested = False
                    self._active_jobs += 1
                    return self._browser

                self._restart_requested = True
                await self._condition.wait()

    async def _release_browser(
        self,
        *,
        success: bool,
        request_restart: bool = False,
    ) -> None:
        async with self._condition:
            if success:
                self._browser_uses += 1

                if self._browser_uses >= _BROWSER_MAX_USES:
                    self._restart_requested = True

            if request_restart:
                self._restart_requested = True

            self._active_jobs = max(0, self._active_jobs - 1)
            self._condition.notify_all()

    async def _restart_when_idle(self) -> None:
        async with self._condition:
            self._restart_requested = True

            while self._active_jobs > 0:
                await self._condition.wait()

            await self._close_browser_unsafe()
            await self._launch_browser_unsafe()

            self._restart_requested = False
            self._condition.notify_all()

    async def _block_external_request(self, route) -> None:
        try:
            await route.abort()
        except Exception:
            pass

    async def generate_pdf(self, html_content: str, margins: dict | None = None) -> bytes:
        if not html_content:
            raise ValueError("Empty HTML")

        html_size = len(html_content.encode("utf-8", errors="ignore"))
        if html_size > _HTML_MAX_BYTES:
            raise ValueError(f"HTML too large. Max allowed size is {_HTML_MAX_BYTES} bytes")

        pdf_margins = margins or {
            "top": "0px",
            "right": "0px",
            "bottom": "0px",
            "left": "0px",
        }

        async with self._semaphore:
            last_error: Exception | None = None

            for attempt in range(2):
                browser = None
                context = None
                page = None
                acquired = False
                success = False
                request_restart = False

                try:
                    browser = await self._acquire_browser()
                    acquired = True

                    async with asyncio.timeout(_RENDER_TIMEOUT_SECONDS):
                        context = await browser.new_context(
                            java_script_enabled=False,
                        )

                        await context.route("http://*/*", self._block_external_request)
                        await context.route("https://*/*", self._block_external_request)

                        page = await context.new_page()
                        page.set_default_timeout(_SET_CONTENT_TIMEOUT_MS)

                        await page.emulate_media(media="print")

                        await page.set_content(
                            html_content,
                            wait_until="domcontentloaded",
                            timeout=_SET_CONTENT_TIMEOUT_MS,
                        )

                        try:
                            await asyncio.wait_for(
                                page.evaluate(_WAIT_FOR_IMAGES_AND_FONTS_JS),
                                timeout=_IMAGE_WAIT_TIMEOUT_SECONDS,
                            )
                        except Exception:
                            logger.warning(
                                "Image/font wait timed out on PDF attempt %d; continuing",
                                attempt + 1,
                            )

                        pdf = await page.pdf(
                            format="A4",
                            print_background=True,
                            margin=pdf_margins,
                            display_header_footer=False,
                            prefer_css_page_size=True,
                        )

                    success = True
                    return pdf

                except Exception as exc:
                    last_error = exc
                    request_restart = True

                    logger.exception(
                        "PDF generation failed on attempt %d/2: %s",
                        attempt + 1,
                        exc,
                    )

                finally:
                    if page:
                        try:
                            await page.close()
                        except Exception:
                            pass

                    if context:
                        try:
                            await context.close()
                        except Exception:
                            pass

                    if acquired:
                        await self._release_browser(
                            success=success,
                            request_restart=request_restart,
                        )

                if attempt == 0:
                    await self._restart_when_idle()

            if last_error:
                raise last_error

            raise RuntimeError("PDF generation failed after all retries")

    async def shutdown(self) -> None:
        logger.info("Shutting down Playwright PDF service")

        async with self._condition:
            self._restart_requested = True

            while self._active_jobs > 0:
                await self._condition.wait()

            await self._close_browser_unsafe()
            self._condition.notify_all()


# ============================================================
# Dedicated loop thread sync service
# ============================================================

class PlaywrightPDFService:
    def __init__(self):
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._core: PlaywrightPDFAsyncCore | None = None

        self._ready = threading.Event()
        self._start_lock = threading.Lock()
        self._startup_error: BaseException | None = None
        self._closed = False

    def _thread_main(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        self._loop = loop
        self._core = PlaywrightPDFAsyncCore()

        try:
            loop.run_until_complete(self._core.startup())
        except BaseException as exc:
            self._startup_error = exc
            logger.exception("Failed to start Playwright PDF service")
            self._ready.set()

            try:
                if self._core:
                    loop.run_until_complete(self._core.shutdown())
            except Exception:
                pass

            try:
                loop.close()
            except Exception:
                pass

            return

        self._ready.set()

        try:
            loop.run_forever()
        except BaseException as exc:
            self._startup_error = exc
            logger.exception("Playwright PDF loop crashed")
        finally:
            try:
                if self._core:
                    loop.run_until_complete(self._core.shutdown())
            except Exception:
                pass

            try:
                loop.close()
            except Exception:
                pass

    def _thread_is_usable_unlocked(self) -> bool:
        return bool(
            self._thread
            and self._thread.is_alive()
            and self._loop
            and not self._loop.is_closed()
            and self._core
        )

    def _discard_dead_thread_unlocked(self) -> None:
        self._thread = None
        self._loop = None
        self._core = None
        self._ready.clear()

    def start(self) -> None:
        if self._closed:
            raise RuntimeError("PlaywrightPDFService is closed")

        if self._thread_is_usable_unlocked():
            return

        with self._start_lock:
            if self._thread_is_usable_unlocked():
                return

            self._discard_dead_thread_unlocked()

            self._ready.clear()
            self._startup_error = None

            self._thread = threading.Thread(
                target=self._thread_main,
                name="playwright-pdf-loop",
                daemon=True,
            )
            self._thread.start()

            if not self._ready.wait(timeout=15):
                self._discard_dead_thread_unlocked()
                raise RuntimeError("Timed out starting Playwright PDF service")

            if self._startup_error:
                err = self._startup_error
                self._discard_dead_thread_unlocked()
                raise RuntimeError("Failed to start Playwright PDF service") from err

    def _force_restart_after_crash(self) -> None:
        with self._start_lock:
            loop = self._loop
            thread = self._thread

            if loop and not loop.is_closed() and loop.is_running():
                try:
                    loop.call_soon_threadsafe(loop.stop)
                except Exception:
                    pass

            if thread and thread.is_alive():
                try:
                    thread.join(timeout=3)
                except Exception:
                    pass

            self._discard_dead_thread_unlocked()
            self._startup_error = None

    def generate_pdf(self, html: str, margins: dict | None = None) -> bytes:
        last_error: BaseException | None = None

        for _ in range(2):
            self.start()

            loop = self._loop
            core = self._core
            thread = self._thread

            if not loop or not core or not thread or not thread.is_alive() or loop.is_closed():
                self._force_restart_after_crash()
                continue

            try:
                future = asyncio.run_coroutine_threadsafe(
                    core.generate_pdf(html, margins),
                    loop,
                )
            except RuntimeError as exc:
                last_error = exc
                self._force_restart_after_crash()
                continue

            try:
                return future.result(timeout=_SYNC_WAIT_TIMEOUT_SECONDS)

            except concurrent.futures.TimeoutError as exc:
                last_error = exc

                try:
                    future.cancel()
                except Exception:
                    pass

                if not thread.is_alive() or loop.is_closed():
                    self._force_restart_after_crash()
                    continue

                raise TimeoutError("Timed out waiting for PDF generation") from exc

        if last_error:
            raise RuntimeError("Failed to generate PDF") from last_error

        raise RuntimeError("Failed to generate PDF")

    def shutdown(self) -> None:
        with self._start_lock:
            if self._closed:
                return

            self._closed = True

            loop = self._loop
            core = self._core
            thread = self._thread

            if loop and core and not loop.is_closed():
                try:
                    future = asyncio.run_coroutine_threadsafe(core.shutdown(), loop)
                    future.result(timeout=15)
                except Exception:
                    logger.exception("Failed shutting down Playwright PDF core")

                try:
                    if loop.is_running():
                        loop.call_soon_threadsafe(loop.stop)
                except Exception:
                    pass

            if thread and thread.is_alive():
                try:
                    thread.join(timeout=15)
                except Exception:
                    pass

            self._discard_dead_thread_unlocked()

pdf_service = PlaywrightPDFService()


def generate_pdf_sync(html: str, margins: dict | None = None) -> bytes:
    return pdf_service.generate_pdf(html, margins)


class PDFRenderer(BaseRenderer):
    media_type = "application/pdf"
    format = "pdf"
    charset = None
    render_style = "binary"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b""

        if isinstance(data, bytes):
            return data

        if isinstance(data, bytearray):
            return bytes(data)

        if isinstance(data, str):
            return data.encode("utf-8")
        import json

        response = None
        if renderer_context:
            response = renderer_context.get("response")

        if response is not None:
            try:
                response["Content-Type"] = "application/json; charset=utf-8"
            except Exception:
                pass

        return json.dumps(
            data,
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")


def build_pdf_response(pdf_buffer: bytes, filename: str):
    from django.http import HttpResponse
    from urllib.parse import quote

    filename_encoded = quote(filename)

    response = HttpResponse(
        pdf_buffer,
        content_type="application/pdf",
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"; '
        f"filename*=UTF-8''{filename_encoded}"
    )
    response["Content-Length"] = len(pdf_buffer)
    response["Access-Control-Expose-Headers"] = "Content-Disposition"

    return response


def _shutdown_playwright() -> None:
    try:
        pdf_service.shutdown()
    except Exception:
        pass

atexit.register(_shutdown_playwright)