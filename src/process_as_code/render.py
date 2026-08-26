from __future__ import annotations

from typing import Any

from .graph import step_edges


def _escape(text: str) -> str:
    return text.replace('"', "'")


def to_mermaid(data: dict[str, Any]) -> str:
    lines = ["flowchart TD"]
    steps = [s for s in data.get("steps", []) if isinstance(s, dict) and s.get("id")]
    for step in steps:
        sid = step["id"]
        label = _escape(step.get("name", sid))
        kind = step.get("type", "task")
        if kind == "decision":
            lines.append(f'  {sid}{{"{label}"}}')
        elif kind in {"event", "end"}:
            lines.append(f'  {sid}(["{label}"])')
        else:
            lines.append(f'  {sid}["{label}"]')

    for step in steps:
        for target, label in step_edges(step):
            if label:
                lines.append(f'  {step["id"]} -->|"{_escape(label)}"| {target}')
            else:
                lines.append(f'  {step["id"]} --> {target}')
    return "\n".join(lines) + "\n"


def to_markdown(data: dict[str, Any]) -> str:
    meta = data.get("process", {})
    lines = [f'# {meta.get("name", meta.get("id", "Process"))}', ""]
    if meta.get("description"):
        lines += [meta["description"], ""]

    summary = [
        ("Process ID", meta.get("id")),
        ("Owner", meta.get("owner")),
        ("Trigger", meta.get("trigger")),
        ("Outcome", meta.get("outcome")),
        ("Version", data.get("version")),
    ]
    lines += ["## Summary", "", "| Field | Value |", "| --- | --- |"]
    for key, value in summary:
        if value:
            lines.append(f"| {key} | {value} |")

    lines += ["", "## Flow", "", "```mermaid", to_mermaid(data).rstrip(), "```", ""]
    lines += ["## Steps", "", "| # | ID | Step | Actor | System | Type |", "| ---: | --- | --- | --- | --- | --- |"]
    for idx, step in enumerate(data.get("steps", []), 1):
        if not isinstance(step, dict):
            continue
        lines.append(
            f"| {idx} | `{step.get('id', '')}` | {step.get('name', '')} | "
            f"{step.get('actor', '')} | {step.get('system', '')} | {step.get('type', 'task')} |"
        )

    for section, title in (("controls", "Controls"), ("interfaces", "Interfaces"), ("objects", "Business objects")):
        items = data.get(section, []) or []
        if items:
            lines += ["", f"## {title}", ""]
            for item in items:
                if isinstance(item, dict):
                    description = item.get("description") or item.get("name") or ""
                    lines.append(f"- `{item.get('id', '')}` — {description}")
    return "\n".join(lines).rstrip() + "\n"
