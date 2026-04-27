import json
from pathlib import Path
from typing import Dict


def load_config(path: str = "config.json") -> Dict:
    full_path = Path(path)
    with open(full_path, "r") as f:
        return json.load(f)
