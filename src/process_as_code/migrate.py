from __future__ import annotations

from copy import deepcopy
from typing import Any


def migrate_process(data: dict[str, Any], target_version: str = "0.2") -> dict[str, Any]:
    if target_version != "0.2":
        raise ValueError(f"unsupported target version '{target_version}'")
    current = str(data.get("version", ""))
    if current == target_version:
        return deepcopy(data)
    if current not in {"0.1", "1.0"}:
        raise ValueError(f"cannot migrate process version '{current}' to {target_version}")

    migrated = deepcopy(data)
    migrated["version"] = target_version
    for step in migrated.get("steps", []) or []:
        if not isinstance(step, dict) or "transitions" in step:
            continue
        transitions: list[dict[str, Any]] = []
        nxt = step.pop("next", None)
        if isinstance(nxt, str):
            transitions.append({"to": nxt})
        elif isinstance(nxt, list):
            transitions.extend({"to": target} for target in nxt if isinstance(target, str))
        branches = step.pop("branches", None)
        if isinstance(branches, dict):
            for label, target in branches.items():
                if isinstance(target, str):
                    transitions.append({"to": target, "label": str(label), "when": str(label)})
        if transitions:
            step["transitions"] = transitions
    return migrated
