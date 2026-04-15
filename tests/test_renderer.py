import json
import jinja2
from pathlib import Path
from resume_manager.render.renderer import TEMPLATE_DIR

def test_render_html_compact():
    fixture_path = Path("tests/fixtures/demo_profile.json")
    with open(fixture_path) as f:
        data = json.load(f)
        
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True
    )
    template = env.get_template("compact.html.j2")
    html_content = template.render(**data)
    
    assert data["profile"]["name"] in html_content
    assert "Experience" in html_content
    assert "CloudScale Solutions" in html_content
    assert "BS in Computer Science" in html_content

def test_render_html_brand():
    fixture_path = Path("tests/fixtures/demo_profile.json")
    with open(fixture_path) as f:
        data = json.load(f)
        
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True
    )
    template = env.get_template("brand.html.j2")
    html_content = template.render(**data)
    
    assert data["profile"]["name"] in html_content
    assert "EXPERIENCE" in html_content.upper()
    assert "#10b981" in html_content # emerald
    assert "Inter" in html_content
