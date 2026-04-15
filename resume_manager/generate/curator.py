import json
from pathlib import Path
from jinja2 import Template
from ..providers import PROVIDERS

PROMPT_PATH = Path(__file__).parent / "prompts" / "curator.txt"

def load_prompt():
    with open(PROMPT_PATH) as f:
        content = f.read()
    system_part, user_part = content.split("USER:", 1)
    system_prompt = system_part.replace("SYSTEM:", "").strip()
    user_template = user_part.strip()
    return system_prompt, user_template

def curate(jd, db_content, provider_name="anthropic", model=None):
    system_prompt, user_template = load_prompt()
    
    template = Template(user_template)
    user_prompt = template.render(jd=jd, db_content=db_content)
    
    provider_class = PROVIDERS.get(provider_name)
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    provider = provider_class(model=model)
    response = provider.complete(system_prompt, user_prompt)
    
    # Try to extract JSON from response
    try:
        # LLMs sometimes wrap JSON in code blocks
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        
        return json.loads(response)
    except Exception as e:
        raise ValueError(f"Failed to parse curator response: {e}\nResponse: {response}")

def filter_content(all_content, selection):
    # Map of job_id -> [bullet_ids]
    job_map = {j['job_id']: j['bullets'] for j in selection.get('jobs', [])}
    # List of skill_ids
    selected_skill_ids = [s.get('skill_id') for s in selection.get('skills', []) if s.get('skill_id')]
    
    filtered_jobs = []
    for job in all_content['jobs']:
        if job['id'] in job_map:
            # Filter bullets
            selected_bullet_ids = job_map[job['id']]
            job_copy = job.copy()
            job_copy['bullets'] = [b for b in job['bullets'] if b['id'] in selected_bullet_ids]
            filtered_jobs.append(job_copy)
            
    filtered_skills = [s for s in all_content['skills'] if s['id'] in selected_skill_ids]
    
    return {
        "profile": all_content['profile'],
        "jobs": filtered_jobs,
        "skills": filtered_skills,
        "education": all_content['education']
    }
