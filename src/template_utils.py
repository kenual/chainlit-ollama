import logging
import re
from typing import Dict

import toml

TEMPLATES_DIR = 'data/templates'

logger = logging.getLogger(__name__)


def get_template(name: str) -> str:
    with open(f"{TEMPLATES_DIR}/{name}.jinja", "r") as f:
        return f.read()


def extract_template_vars(name: str) -> Dict[str, str]:
    template = get_template(name)

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
