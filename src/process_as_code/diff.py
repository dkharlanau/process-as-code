from __future__ import annotations

from typing import Any


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

    for section in ("steps", "roles", "systems", "objects", "interfaces", "controls"):
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

    for section, changes in diff.get("sections", {}).items():
        if not (changes["added"] or changes["removed"] or changes["changed"]):
            continue
        lines += [f"## {section.title()}", ""]
        for item_id in changes["added"]:
            lines.append(f"- Added `{item_id}`")
        for item_id in changes["removed"]:
            lines.append(f"- Removed `{item_id}`")
        for item_id, fields in changes["changed"].items():
            lines.append(f"- Changed `{item_id}`: {', '.join(f'`{field}`' for field in fields)}")
        lines.append("")
    if len(lines) == 2:
        lines.append("No semantic changes.")
    return "\n".join(lines).rstrip() + "\n"
