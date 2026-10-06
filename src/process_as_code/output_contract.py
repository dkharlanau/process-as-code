from __future__ import annotations

import json
from importlib.resources import files
from typing import Any


OUTPUT_FORMAT_VERSION = "1.0"

_OUTPUT_FORMATS = {
    "semantic-diff": "process-as-code.semantic-diff",
    "impact": "process-as-code.impact",
}

_OUTPUT_SCHEMA_FILES = {
    "semantic-diff": "semantic-diff-v1.schema.json",
    "impact": "impact-v1.schema.json",
}

_OUTPUT_SCHEMA_URLS = {
    "semantic-diff": "https://dkharlanau.github.io/process-as-code/schemas/outputs/semantic-diff-v1.schema.json",
    "impact": "https://dkharlanau.github.io/process-as-code/schemas/outputs/impact-v1.schema.json",
}

_RESOURCE_ROOT = files("process_as_code").joinpath("resources/output-schemas")


def output_kinds() -> tuple[str, ...]:
    """Return stable machine-output contract kinds exposed by the CLI."""
    return tuple(_OUTPUT_FORMATS)


def output_metadata(kind: str) -> dict[str, str]:
    """Return the compatibility metadata for one machine-readable output kind."""
    try:
        format_name = _OUTPUT_FORMATS[kind]
    except KeyError as exc:
        raise ValueError(f"unknown output contract kind '{kind}'") from exc
    return {
        "format": format_name,
        "version": OUTPUT_FORMAT_VERSION,
        "schema": _OUTPUT_SCHEMA_URLS[kind],
    }


def attach_output_contract(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Attach additive output metadata without changing existing payload keys."""
    if "output" in payload:
        raise ValueError("machine-readable payload already contains reserved 'output' metadata")
    return {"output": output_metadata(kind), **payload}


def output_schema_text(kind: str) -> str:
    """Return a bundled JSON Schema for a machine-readable output contract."""
    try:
        filename = _OUTPUT_SCHEMA_FILES[kind]
    except KeyError as exc:
        raise ValueError(f"unknown output contract kind '{kind}'") from exc
    return _RESOURCE_ROOT.joinpath(filename).read_text(encoding="utf-8")


def output_schema_dict(kind: str) -> dict[str, Any]:
    """Return a bundled machine-output JSON Schema as a mapping."""
    data = json.loads(output_schema_text(kind))
    if not isinstance(data, dict):
        raise ValueError(f"bundled output schema '{kind}' must be a JSON object")
    return data
