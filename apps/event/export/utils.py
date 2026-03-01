import os
import base64
import asyncio
import logging
from django.conf import settings
from django.core.cache import cache
from rest_framework.renderers import BaseRenderer
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class PDFRenderer(BaseRenderer):
    media_type = 'application/pdf'
    format = 'pdf'
    charset = None
    render_style = 'binary'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data

def get_report_assets():
    CACHE_KEY = "report_assets"
    cached = cache.get(CACHE_KEY)
    if cached:
        logger.debug("Assets loaded from cache")
        return cached

    assets = {'logo': '', 'font': ''}
    
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'logo', 'logo.png')
    if os.path.exists(logo_path):
        try:
            with open(logo_path, 'rb') as f:
                assets['logo'] = base64.b64encode(f.read()).decode('ascii')
            logger.info("Logo loaded from disk")
        except Exception as e:
            logger.warning(f"Logo loading error: {e}")
    
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Amiri-Regular.ttf')
    if os.path.exists(font_path):
        try:
            with open(font_path, 'rb') as f:
                assets['font'] = base64.b64encode(f.read()).decode('ascii')
            logger.info("Font loaded from disk")
        except Exception as e:
            logger.warning(f"Font loading error: {e}")
    
    cache.set(CACHE_KEY, assets, timeout=60 * 60 * 24)
    return assets

async def _run_playwright_core(html_content, output_path=None, margins=None):
    browser = None
    browser_args = [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
    ]
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=browser_args)
            context = await browser.new_context(viewport={'width': 794, 'height': 1123})
            page = await context.new_page()
            
            await page.set_content(html_content, wait_until='networkidle')
            pdf_margins = margins or {"top": "0px", "right": "0px", "bottom": "0px", "left": "0px"}
            
            pdf_params = {
                'format': 'A4',
                'print_background': True,
                'margin': pdf_margins,
                'display_header_footer': False,
            }
            if output_path:
                pdf_params['path'] = output_path
                
            pdf_bytes = await page.pdf(**pdf_params)
            await browser.close()
            return pdf_bytes
            
    except Exception as e:
        logger.exception("Playwright Error: %s", str(e))
        if browser:
            await browser.close()
        raise

def generate_pdf_from_html(html_content, output_path, margins=None):
    try:
        asyncio.run(_run_playwright_core(html_content, output_path=output_path, margins=margins))
        return True
    except Exception:
        return False

def generate_pdf_sync(html_content, margins=None):
    return asyncio.run(_run_playwright_core(html_content, margins=margins))