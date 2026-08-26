from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .graph import iter_entity_ids, reachable_step_ids, step_edges


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    dup: set[str] = set()
    for value in values:
        if value in seen:
            dup.add(value)
        seen.add(value)
    return sorted(dup)


def validate_process(data: dict[str, Any]) -> ValidationResult:
    result = ValidationResult()

    if not isinstance(data.get("version"), str):
        result.errors.append("top-level 'version' must be a string")

    meta = data.get("process")
    if not isinstance(meta, dict):
        result.errors.append("top-level 'process' must be an object")
        meta = {}
    for key in ("id", "name"):
        if not isinstance(meta.get(key), str) or not meta.get(key, "").strip():
            result.errors.append(f"process.{key} is required")

    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        result.errors.append("'steps' must be a non-empty list")
        return result

    step_ids: list[str] = []
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            result.errors.append(f"steps[{index}] must be an object")
            continue
        sid = step.get("id")
        if not isinstance(sid, str) or not sid.strip():
            result.errors.append(f"steps[{index}].id is required")
            continue
        step_ids.append(sid)
        if not isinstance(step.get("name"), str) or not step.get("name", "").strip():
            result.errors.append(f"step '{sid}' requires name")
        if step.get("type", "task") not in {"task", "user_task", "service_task", "decision", "event", "end"}:
            result.errors.append(f"step '{sid}' has unsupported type '{step.get('type')}'")

    for duplicate in _duplicates(step_ids):
        result.errors.append(f"duplicate step id '{duplicate}'")

    step_id_set = set(step_ids)
    start = meta.get("start")
    if start is not None and start not in step_id_set:
        result.errors.append(f"process.start references unknown step '{start}'")

    for section in ("roles", "systems", "objects", "interfaces", "controls"):
        ids = list(iter_entity_ids(data, section))
        for duplicate in _duplicates(ids):
            result.errors.append(f"duplicate {section} id '{duplicate}'")

    role_ids = set(iter_entity_ids(data, "roles"))
    system_ids = set(iter_entity_ids(data, "systems"))
    object_ids = set(iter_entity_ids(data, "objects"))
    interface_ids = set(iter_entity_ids(data, "interfaces"))
    control_ids = set(iter_entity_ids(data, "controls"))

    for step in steps:
        if not isinstance(step, dict) or not isinstance(step.get("id"), str):
            continue
        sid = step["id"]
        for target, _ in step_edges(step):
            if target not in step_id_set:
                result.errors.append(f"step '{sid}' references unknown next step '{target}'")
        if step.get("type") == "decision" and not step.get("branches"):
            result.errors.append(f"decision step '{sid}' requires branches")

        actor = step.get("actor")
        if actor and actor not in role_ids:
            result.errors.append(f"step '{sid}' references unknown role '{actor}'")
        system = step.get("system")
        if system and system not in system_ids:
            result.errors.append(f"step '{sid}' references unknown system '{system}'")
        for field_name, known in (
            ("objects", object_ids),
            ("interfaces", interface_ids),
            ("controls", control_ids),
        ):
            for ref in step.get(field_name, []) or []:
                if ref not in known:
                    result.errors.append(f"step '{sid}' references unknown {field_name[:-1]} '{ref}'")

        raci = step.get("raci", {}) or {}
        if isinstance(raci, dict):
            for key in ("responsible", "accountable", "consulted", "informed"):
                value = raci.get(key, [])
                refs = [value] if isinstance(value, str) else value if isinstance(value, list) else []
                for ref in refs:
                    if ref not in role_ids:
                        result.errors.append(f"step '{sid}' RACI references unknown role '{ref}'")

    if not result.errors:
        reachable = reachable_step_ids(data)
        for sid in sorted(step_id_set - reachable):
            result.warnings.append(f"step '{sid}' is unreachable from process start")
        if not any(not step_edges(step) for step in steps if isinstance(step, dict)):
            result.warnings.append("process has no terminal step")

    return result
