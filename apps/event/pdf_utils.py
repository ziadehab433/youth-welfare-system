from playwright.sync_api import sync_playwright
import logging

logger = logging.getLogger(__name__)
def generate_pdf_sync(html_content: str) -> bytes:
    browser = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                ]
            )
            context = browser.new_context(
                viewport={'width': 794, 'height': 1123},
            )
            page = context.new_page()
            page.set_default_timeout(60000)
            page.set_content(html_content, wait_until='networkidle')
            pdf_bytes = page.pdf(
                format='A4',
                print_background=True,
                margin={'top': '10mm', 'bottom': '10mm', 'left': '10mm', 'right': '10mm'},
                display_header_footer=False,
            )
            logger.info("PDF generated | size: %d bytes", len(pdf_bytes))
            return pdf_bytes
    except Exception as e:
        logger.exception("Playwright error during PDF generation: %s", str(e))
        raise
    finally:
        if browser:
            try:
                browser.close()
            except Exception:
                logger.warning("Failed to close Playwright browser")