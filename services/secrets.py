import json
from pathlib import Path
from typing import Dict


def load_secrets(path: str = "secrets/encrypted.json") -> Dict[str, str]:
    full_path = Path(path)
    with open(full_path, "r") as f:
        return json.load(f)
