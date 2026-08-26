from __future__ import annotations

from typing import Any


def extract_raci(data: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    process_owner = data.get("process", {}).get("owner", "")
    for step in data.get("steps", []) or []:
        if not isinstance(step, dict):
            continue
        raci = step.get("raci", {}) or {}
        responsible = raci.get("responsible") or step.get("actor", "")
        accountable = raci.get("accountable") or process_owner
        rows.append({
            "step": step.get("id", ""),
            "name": step.get("name", ""),
            "responsible": _join(responsible),
            "accountable": _join(accountable),
            "consulted": _join(raci.get("consulted", "")),
            "informed": _join(raci.get("informed", "")),
        })
    return rows


def _join(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value or "")


def raci_markdown(data: dict[str, Any]) -> str:
    lines = ["| Step | Responsible | Accountable | Consulted | Informed |", "| --- | --- | --- | --- | --- |"]
    for row in extract_raci(data):
        lines.append(
            f"| {row['name']} (`{row['step']}`) | {row['responsible']} | {row['accountable']} | "
            f"{row['consulted']} | {row['informed']} |"
        )
    return "\n".join(lines) + "\n"
