import asyncio
from playwright.async_api import async_playwright

async def run_playwright_pdf(html_content, output_path):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html_content, wait_until='networkidle')
        await page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            margin={
                "top": "0px",
                "right": "0px",
                "bottom": "0px",
                "left": "0px"
            }
        )
        await browser.close()

def generate_pdf_from_html(html_content, output_path):
    try:
        asyncio.run(run_playwright_pdf(html_content, output_path))
        return True
    except Exception as e:
        print(f"Playwright Error: {e}")
        return False