# Chainlit Ollama

Interactive Chainlit UI for local LLMs via Ollama, with optional MCP tool integration.

## Features
- Chat UI powered by Chainlit
- Local inference through Ollama
- Prompt templates and starters
- MCP integration for external tools (optional)

## Prerequisites
- Python 3.13.x
- uv (https://docs.astral.sh/uv/getting-started/installation/)
- Ollama installed and at least one model pulled (e.g., `ollama pull llama3.1`)

Optional (for MCP):
- Node.js (for some MCP servers, e.g., Playwright MCP)
- Any MCP server(s) you intend to use

## Installation
1) Install uv if not already installed:
   https://docs.astral.sh/uv/getting-started/installation/

2) Sync project dependencies:
```bash
uv sync --extra test
```

3) (Optional) Verify import of Chainlit:
```bash
uv run python -c "import chainlit"
```

## Configuration
- Templates live under `data/templates/` and prompts under `data/prompts/`.
- App settings/constants are in `src/config.py` and helper modules under `src/`.
- Ensure Ollama is running locally and the model you want is available. You can configure or reference the model in `src/app_helper.py` and `src/llm_service.py`.

## Start the application
Run the Chainlit app via the Python entry in `src/app.py`:

```bash
uv run src/app.py
```

This starts Chainlit using `run_chainlit(__file__)` defined in `main()` of `src/app.py`.

Alternative (call Chainlit directly):
```bash
uv run chainlit run src/app.py
```

Open the URL printed in the terminal (typically http://localhost:8000).

## Usage Tips
- Type “template” in chat to trigger template usage; starters are populated from `data/templates/`.
- If using MCP, connect your MCP server (e.g., `npx @playwright/mcp@latest`); the app will discover and list available tools upon connection.

## Development
- Source code lives under `src/`.
- Run tests:
```bash
uv run pytest -q
```
- Lint/format: Not configured by default in this repo.

## Troubleshooting
- “Module not found” errors: Run commands from the repo root and use `uv run` so dependencies and paths are correct.
- Chainlit doesn’t start: Confirm uv is installed, dependencies are synced (`uv sync` or `uv sync --extra test`), then run `uv run src/app.py`.
- Missing or incorrect model: Ensure the configured model is pulled in Ollama (`ollama list`) and the Ollama service is running.

## License
See [LICENSE](./LICENSE).
