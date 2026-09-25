import json
from pathlib import Path

from jinja2 import Template
from local_first_common.cli import resolve_provider
from local_first_common.providers import PROVIDERS
from local_first_common.providers.base import BaseProvider

PROMPT_PATH = Path(__file__).parent / "prompts" / "strategist.txt"

def load_prompt():
    with open(PROMPT_PATH) as f:
        content = f.read()
    system_part, user_part = content.split("USER:", 1)
    system_prompt = system_part.replace("SYSTEM:", "").strip()
    user_template = user_part.strip()
    return system_prompt, user_template

def strategize(selection, target_questions, provider_name="anthropic", model=None, provider: BaseProvider | None = None):
    system_prompt, user_template = load_prompt()

    template = Template(user_template)
    user_prompt = template.render(selection=selection, target_questions=target_questions)

    if provider is None:
        provider = resolve_provider(PROVIDERS, provider_name, model=model, tool_name="resume-manager")

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
        raise ValueError(f"Failed to parse strategist response: {e}\nResponse: {response}")

    return result
