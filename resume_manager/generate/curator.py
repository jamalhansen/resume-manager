import json
from pathlib import Path

from jinja2 import Template
from local_first_common.cli import resolve_provider
from local_first_common.providers import PROVIDERS
from local_first_common.providers.base import BaseProvider
from local_first_common.tracking import timed_run

PROMPT_PATH = Path(__file__).parent / "prompts" / "curator.txt"

def load_prompt():
    with open(PROMPT_PATH) as f:
        content = f.read()
    system_part, user_part = content.split("USER:", 1)
    system_prompt = system_part.replace("SYSTEM:", "").strip()
    user_template = user_part.strip()
    return system_prompt, user_template

def curate(jd, db_content, provider_name="anthropic", model=None, provider: BaseProvider | None = None):
    system_prompt, user_template = load_prompt()

    # Limit to 10 most recent jobs to avoid sending all personal data to the LLM
    # get_all_content already sorts by start_date DESC so first 10 = most recent
    if isinstance(db_content, dict):
        truncated_content = {**db_content, "jobs": db_content.get("jobs", [])[:10]}
    else:
        truncated_content = db_content

    template = Template(user_template)
    user_prompt = template.render(jd=jd, db_content=truncated_content)

    if provider is None:
        provider = resolve_provider(PROVIDERS, provider_name, model=model, tool_name="resume-manager")

    with timed_run("resume-manager", provider.model, provider=provider.provider_name) as run:
        response = provider.complete(system_prompt, user_prompt)

        # Try to extract JSON from response
        try:
            # LLMs sometimes wrap JSON in code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            result = json.loads(response)
        except Exception as e:  # noqa: BLE001 - json.loads plus string slicing above can fail several ways (JSONDecodeError, IndexError); all convert to the same domain error
            raise ValueError(f"Failed to parse curator response: {e}\nResponse: {response}")

        run.item_count = len(result.get("jobs", [])) + len(result.get("skills", []))
        return result

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
