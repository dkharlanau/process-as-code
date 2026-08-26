from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

_RESOURCE = files("process_as_code").joinpath("resources/process.schema.json")


def schema_text() -> str:
    """Return the bundled Process as Code JSON Schema as UTF-8 text."""
    return _RESOURCE.read_text(encoding="utf-8")


def schema_dict() -> dict[str, Any]:
    """Return the bundled Process as Code JSON Schema as a mapping."""
    data = json.loads(schema_text())
    if not isinstance(data, dict):
        raise ValueError("bundled Process as Code schema must be a JSON object")
    return data
