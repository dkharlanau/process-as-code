from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def drafting_bundle(description: str, schema_path: str | Path | None = None) -> dict[str, Any]:
    schema: dict[str, Any] | None = None
    if schema_path:
        schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    return {
        "contract_status": "proposal",
        "task": "Draft a Process as Code v0.2 contract from the business description. Do not invent proprietary facts. Preserve uncertainty in descriptions or extension metadata rather than fabricating IDs.",
        "business_description": description.strip(),
        "rules": [
            "Return exactly one YAML object using version 0.2.",
            "Use stable snake_case IDs for process entities and steps.",
            "Represent flow with transitions[].to and optional when/label.",
            "Declare every referenced role, system, object, interface, control, risk, evidence and artifact in its catalog.",
            "Use risks, controls and evidence only when supported by the description or explicitly marked as assumptions.",
            "Keep vendor-specific metadata under extensions.<vendor>.",
            "Do not treat the draft as approved until deterministic validation and policy checks pass.",
        ],
        "authoritative_checks": [
            "process-code validate draft.process.yaml --strict",
            "process-code policy draft.process.yaml --policy process-policy.yaml",
        ],
        "schema": schema,
    }


def drafting_prompt(bundle: dict[str, Any]) -> str:
    rules = "\n".join(f"- {rule}" for rule in bundle["rules"])
    schema_note = "The full JSON Schema is included in the attached/context bundle." if bundle.get("schema") else "Follow Process as Code v0.2 specification."
    return f"""# Process as Code drafting task

Status: PROPOSAL — not validated/approved.

## Business description

{bundle['business_description']}

## Rules

{rules}

{schema_note}

Return only the proposed YAML contract. After generation it must pass deterministic validation and policy gates.
"""
