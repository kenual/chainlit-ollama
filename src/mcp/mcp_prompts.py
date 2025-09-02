from mcp.server.fastmcp import FastMCP
from pathlib import Path
import re
import yaml
from typing import Any, Dict, Optional

mcp = FastMCP("Prompt Server")

# Load summarize.yml once and render prompts
_SUMMARIZE_YAML_PATH = Path(__file__).resolve().parents[2] / "data" / "prompts" / "summarize.yml"
_SUMMARIZE_SPEC: Dict[str, Any] = {}
_TEMPLATE: str = ""
_DEFAULTS: Dict[str, Any] = {}

def _load_summarize_spec() -> None:
    global _SUMMARIZE_SPEC, _TEMPLATE, _DEFAULTS
    if _TEMPLATE:
        return
    with _SUMMARIZE_YAML_PATH.open("r", encoding="utf-8") as f:
        spec = yaml.safe_load(f) or {}
    _SUMMARIZE_SPEC = spec
    _TEMPLATE = spec.get("template", "")
    defaults: Dict[str, Any] = {}
    for inp in spec.get("inputs", []):
        if isinstance(inp, dict) and "default" in inp and "name" in inp:
            defaults[inp["name"]] = inp["default"]
    _DEFAULTS = defaults

def _render_template(template: str, context: Dict[str, Any]) -> str:
    def replacer(match: re.Match) -> str:
        key = match.group(1).strip()
        return str(context.get(key, match.group(0)))
    return re.sub(r"{{\s*([^}]+)\s*}}", replacer, template)

@mcp.prompt()
def summarize(text: str, bullets: Optional[int] = None) -> str:
    """
    Summarize the provided text into a set number of bullet points.
    """
    _load_summarize_spec()
    if bullets is None:
        bullets = int(_DEFAULTS.get("bullets", 5))
    context: Dict[str, Any] = {"text": text, "bullets": bullets}
    return _render_template(_TEMPLATE, context)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
