from playwright.sync_api import sync_playwright
def generate_pdf_sync(html_content):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.set_content(html_content, wait_until='networkidle')
            pdf_bytes = page.pdf(
                format='A4',
                print_background=True,
                margin={
                    'top': '10mm',
                    'bottom': '10mm',
                    'left': '10mm',
                    'right': '10mm'
                },
                display_header_footer=False
            )
            browser.close()
            return pdf_bytes
    except Exception as e:
        print(f"Playwright Error: {e}")
        raise e