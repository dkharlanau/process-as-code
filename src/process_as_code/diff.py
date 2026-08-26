from __future__ import annotations

from typing import Any


SECTIONS = ("steps", "roles", "systems", "objects", "interfaces", "controls", "risks", "evidence", "artifacts")


def _by_id(items: list[Any] | None) -> dict[str, dict[str, Any]]:
    return {
        item["id"]: item
        for item in (items or [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def semantic_diff(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"process": {}, "sections": {}}
    old_meta, new_meta = old.get("process", {}), new.get("process", {})
    for field in sorted(set(old_meta) | set(new_meta)):
        if old_meta.get(field) != new_meta.get(field):
            result["process"][field] = {"old": old_meta.get(field), "new": new_meta.get(field)}

    for section in SECTIONS:
        before, after = _by_id(old.get(section)), _by_id(new.get(section))
        added = sorted(set(after) - set(before))
        removed = sorted(set(before) - set(after))
        changed: dict[str, Any] = {}
        for item_id in sorted(set(before) & set(after)):
            if before[item_id] != after[item_id]:
                fields: dict[str, Any] = {}
                for field in sorted(set(before[item_id]) | set(after[item_id])):
                    if before[item_id].get(field) != after[item_id].get(field):
                        fields[field] = {"old": before[item_id].get(field), "new": after[item_id].get(field)}
                changed[item_id] = fields
        result["sections"][section] = {"added": added, "removed": removed, "changed": changed}
    return result


def diff_markdown(diff: dict[str, Any]) -> str:
    lines = ["# Process semantic diff", ""]
    if diff.get("process"):
        lines += ["## Process metadata", ""]
        for field, change in diff["process"].items():
            lines.append(f"- `{field}`: `{change['old']}` → `{change['new']}`")
        lines.append("")

    changed_any = bool(diff.get("process"))
    for section, changes in diff.get("sections", {}).items():
        if not (changes["added"] or changes["removed"] or changes["changed"]):
            continue
        changed_any = True
        lines += [f"## {section.title()}", ""]
        for item_id in changes["added"]:
            lines.append(f"- Added `{item_id}`")
        for item_id in changes["removed"]:
            lines.append(f"- Removed `{item_id}`")
        for item_id, fields in changes["changed"].items():
            lines.append(f"- Changed `{item_id}`: {', '.join(f'`{field}`' for field in fields)}")
        lines.append("")
    if not changed_any:
        lines.append("No semantic changes.")
    return "\n".join(lines).rstrip() + "\n"


def visual_diff_mermaid(old: dict[str, Any], new: dict[str, Any]) -> str:
    """Render a deterministic semantic diff as Mermaid.

    The new graph is primary; removed nodes from the old graph are retained as
    dashed nodes so reviewers can understand deletions without reading YAML.
    """
    from .graph import step_edges

    diff = semantic_diff(old, new)
    changes = diff["sections"]["steps"]
    added = set(changes["added"])
    removed = set(changes["removed"])
    changed = set(changes["changed"])
    new_steps = _by_id(new.get("steps"))
    old_steps = _by_id(old.get("steps"))

    lines = ["flowchart TD"]
    for sid, step in new_steps.items():
        label = str(step.get("name", sid)).replace('"', "'")
        lines.append(f'  {sid}["{label}"]')
    for sid in sorted(removed):
        label = str(old_steps[sid].get("name", sid)).replace('"', "'")
        lines.append(f'  removed_{sid}["REMOVED: {label}"]')
    for sid, step in new_steps.items():
        for target, label in step_edges(step):
            suffix = f'|"{str(label).replace(chr(34), chr(39))}"|' if label else ""
            lines.append(f"  {sid} -->{suffix} {target}")
    for sid in sorted(added):
        lines.append(f"  class {sid} added")
    for sid in sorted(changed):
        lines.append(f"  class {sid} changed")
    for sid in sorted(removed):
        lines.append(f"  class removed_{sid} removed")
    lines += [
        "  classDef added fill:#e6ffed,stroke:#22863a,stroke-width:2px",
        "  classDef changed fill:#fff5b1,stroke:#b08800,stroke-width:2px",
        "  classDef removed fill:#ffeef0,stroke:#cb2431,stroke-width:2px,stroke-dasharray: 5 5",
    ]
    return "\n".join(lines) + "\n"
