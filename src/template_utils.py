import logging
import re
from pathlib import Path
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader
import toml

TEMPLATES_DIR = 'data/templates'

logger = logging.getLogger(__name__)


def list_templates() -> List[str]:
    templates_folder = Path(TEMPLATES_DIR)
    jinja_file_names = [file.stem for file in sorted(templates_folder.glob('*.jinja'))]
    return jinja_file_names


def get_template_file_name(name: str, path: str = TEMPLATES_DIR) -> str:
    file_name = f'{path}/' if path else ''
    file_name += f'{name}.jinja' if not name.endswith('.jinja') else name
    return (file_name)

def get_template_content(name: str) -> str:
    with open(get_template_file_name(name=name), "r") as f:
        return f.read()


def extract_template_vars(name: str) -> Dict[str, str]:
    template = get_template_content(name)

    # Regular expression to extract the TOML parameters
    pattern = r'\{#(.*?)#\}'
    match = re.search(pattern, template, re.DOTALL)

    if match:
        toml_content = match.group(1).strip()
        # Parse the TOML content
        try:
            parameters = toml.loads(toml_content)
            return parameters
        except toml.TomlDecodeError as e:
            logger.error(f"Failed to parse TOML in template: {name}")
            raise e
    else:
        {}


def extract_template_name(command: str) -> str:
    # Regular expression to match the template name (a phrase enclosed in quotes or after the word "template")
    match = re.search(
        r'(?:template\s*["\']?)([\w\s]+)(?:["\']?)', command, re.IGNORECASE)

    if match:
        return match.group(1).strip()
    else:
        return None


def render_template_with_vars(name: str, context: Dict[str, str]) -> str:
    # Render the template with the context variables
    env = Environment(loader=FileSystemLoader(searchpath=TEMPLATES_DIR))
    template = env.get_template(get_template_file_name(name=name, path=None))
    output = template.render(context)
    return output
