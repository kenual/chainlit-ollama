from pathlib import Path
from typing import Any

import toml


def load_config(file: str) -> dict[str, Any]:
    toml_file = f'config/{file}'
    if not Path(toml_file).exists():
        return {}

    settings = toml.load(toml_file)
    return settings


def dump_config(settings: dict[str, Any], file: str):
    toml_file = f'config/{file}'

    file_path = Path('config/settings.toml')
    if not file_path.exists():
        # Create the directory structure if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # Create the file
        file_path.touch()

    with open(toml_file, 'w') as f:
        toml.dump(settings, f)
