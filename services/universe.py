"""Universe loading utilities."""

import json
from typing import List


def load_universe(path: str) -> List[str]:
    """Load a universe of tickers from a JSON file.

    Args:
        path: Path to the JSON file containing ticker symbols.

    Returns:
        List of ticker strings.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid JSON array of strings.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Universe file not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in universe file {path}: {e}")

    if not isinstance(data, list):
        raise ValueError(f"Universe file {path} must contain a JSON array")

    if not all(isinstance(item, str) for item in data):
        raise ValueError(f"Universe file {path} must contain an array of strings")

    return data
