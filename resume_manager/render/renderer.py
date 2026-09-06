import jinja2
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

TEMPLATE_DIR = Path(__file__).parent / "templates"

async def render_to_pdf(template_name, data, output_path):
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True
    )
    template = env.get_template(f"{template_name}.html.j2")
    html_content = template.render(**data)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html_content)
        
        # Wait for fonts to load
        await page.wait_for_load_state("networkidle")
        
        await page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            margin={"top": "0.5in", "right": "0.5in", "bottom": "0.5in", "left": "0.5in"}
        )
        await browser.close()

def render(template_name, data, output_path):
    """
    Synchronous wrapper for render_to_pdf
    """
    asyncio.run(render_to_pdf(template_name, data, output_path))
