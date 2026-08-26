from __future__ import annotations

from typing import Any


def _as_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [v for v in value if isinstance(v, str)]
    return []


def extract_raci(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for step in data.get("steps", []) or []:
        if not isinstance(step, dict) or not step.get("id"):
            continue
        raci = step.get("raci", {}) or {}
        responsible = _as_list(raci.get("responsible")) if isinstance(raci, dict) else []
        if not responsible and step.get("actor"):
            responsible = [step["actor"]]
        rows.append({
            "step": step["id"],
            "name": step.get("name", step["id"]),
            "responsible": responsible,
            "accountable": _as_list(raci.get("accountable")) if isinstance(raci, dict) else [],
            "consulted": _as_list(raci.get("consulted")) if isinstance(raci, dict) else [],
            "informed": _as_list(raci.get("informed")) if isinstance(raci, dict) else [],
        })
    return rows


def raci_markdown(data: dict[str, Any]) -> str:
    lines = ["| Step | R | A | C | I |", "| --- | --- | --- | --- | --- |"]
    for row in extract_raci(data):
        lines.append("| `{}` | {} | {} | {} | {} |".format(
            row["step"], ", ".join(row["responsible"]), ", ".join(row["accountable"]),
            ", ".join(row["consulted"]), ", ".join(row["informed"])))
    return "\n".join(lines) + "\n"
