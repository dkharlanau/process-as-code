from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .graph import (
    incoming_counts,
    is_cycle_component,
    iter_entity_ids,
    reachable_step_ids,
    step_edges,
    steps_reaching_any,
    strongly_connected_components,
    terminal_step_ids,
)


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


def _refs(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _validate_contracts(result: ValidationResult, sid: str, field_name: str, value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        result.errors.append(f"step '{sid}' {field_name} must be a list")
        return
    for index, contract in enumerate(value):
        if not isinstance(contract, dict):
            result.errors.append(f"step '{sid}' {field_name}[{index}] must be an object")
            continue
        if not contract.get("id") and not contract.get("name") and not contract.get("ref"):
            result.errors.append(f"step '{sid}' {field_name}[{index}] requires id, name or ref")


def validate_process(data: dict[str, Any]) -> ValidationResult:
    result = ValidationResult()
    version = data.get("version")
    if not isinstance(version, str):
        result.errors.append("top-level 'version' must be a string")
    elif version not in {"0.1", "0.2", "1.0"}:
        result.warnings.append(f"process version '{version}' is not a documented contract version")

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
    supported_types = {"task", "user_task", "service_task", "decision", "parallel", "event", "end", "subprocess"}
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
        if step.get("type", "task") not in supported_types:
            result.errors.append(f"step '{sid}' has unsupported type '{step.get('type')}'")
        _validate_contracts(result, sid, "inputs", step.get("inputs"))
        _validate_contracts(result, sid, "outputs", step.get("outputs"))
        sla = step.get("sla")
        if sla is not None and (not isinstance(sla, dict) or not (sla.get("duration") or sla.get("target"))):
            result.errors.append(f"step '{sid}' sla requires duration or target")
        agent = step.get("agent")
        if agent is not None:
            if not isinstance(agent, dict):
                result.errors.append(f"step '{sid}' agent must be an object")
            elif "allowed_actions" in agent and not all(isinstance(x, str) for x in agent.get("allowed_actions", [])):
                result.errors.append(f"step '{sid}' agent.allowed_actions must contain strings")

    for duplicate in _duplicates(step_ids):
        result.errors.append(f"duplicate step id '{duplicate}'")
    step_id_set = set(step_ids)
    start = meta.get("start")
    if start is not None and start not in step_id_set:
        result.errors.append(f"process.start references unknown step '{start}'")

    sections = ("roles", "systems", "objects", "interfaces", "controls", "risks", "evidence", "artifacts")
    known: dict[str, set[str]] = {}
    for section in sections:
        ids = list(iter_entity_ids(data, section))
        known[section] = set(ids)
        for duplicate in _duplicates(ids):
            result.errors.append(f"duplicate {section} id '{duplicate}'")

    if meta.get("owner") and known["roles"] and meta.get("owner") not in known["roles"]:
        result.errors.append(f"process.owner references unknown role '{meta.get('owner')}'")

    for step in steps:
        if not isinstance(step, dict) or not isinstance(step.get("id"), str):
            continue
        sid = step["id"]
        edges = step_edges(step)
        for target, _ in edges:
            if target not in step_id_set:
                result.errors.append(f"step '{sid}' references unknown next step '{target}'")
        transitions = step.get("transitions")
        if transitions is not None and not isinstance(transitions, list):
            result.errors.append(f"step '{sid}' transitions must be a list")
        if isinstance(transitions, list):
            for index, transition in enumerate(transitions):
                if not isinstance(transition, dict) or not isinstance(transition.get("to"), str):
                    result.errors.append(f"step '{sid}' transitions[{index}] requires string 'to'")
        if step.get("type") == "end" and edges:
            result.errors.append(f"end step '{sid}' must not declare outgoing transitions")
        if step.get("type") == "decision":
            if not edges:
                result.errors.append(f"decision step '{sid}' requires transitions or branches")
            elif len(edges) < 2:
                result.warnings.append(f"decision step '{sid}' has fewer than two outgoing branches")
        if step.get("type") == "subprocess" and not isinstance(step.get("process_ref"), str):
            result.errors.append(f"subprocess step '{sid}' requires process_ref")

        actor = step.get("actor")
        if actor and actor not in known["roles"]:
            result.errors.append(f"step '{sid}' references unknown role '{actor}'")
        system = step.get("system")
        if system and system not in known["systems"]:
            result.errors.append(f"step '{sid}' references unknown system '{system}'")
        for field_name in ("objects", "interfaces", "controls", "risks", "evidence", "artifacts"):
            for ref in _refs(step.get(field_name)):
                if ref not in known[field_name]:
                    result.errors.append(f"step '{sid}' references unknown {field_name.rstrip('s')} '{ref}'")

        raci = step.get("raci", {}) or {}
        if isinstance(raci, dict):
            for key in ("responsible", "accountable", "consulted", "informed"):
                for ref in _refs(raci.get(key)):
                    if ref not in known["roles"]:
                        result.errors.append(f"step '{sid}' RACI references unknown role '{ref}'")

    if not result.errors:
        reachable = reachable_step_ids(data)
        for sid in sorted(step_id_set - reachable):
            result.warnings.append(f"step '{sid}' is unreachable from process start")

        by_id = {
            step["id"]: step
            for step in steps
            if isinstance(step, dict) and isinstance(step.get("id"), str)
        }
        incoming = incoming_counts(data)
        for sid in sorted(reachable):
            step = by_id[sid]
            edges = step_edges(step)
            if step.get("type") != "end" and not edges:
                result.warnings.append(f"non-end step '{sid}' is an implicit terminal with no outgoing transition")
            if step.get("type") == "parallel" and incoming.get(sid, 0) < 2 and len(edges) < 2:
                result.warnings.append(
                    f"parallel step '{sid}' has neither multiple incoming nor multiple outgoing flows"
                )

        terminals = terminal_step_ids(data, reachable_only=True)
        if not terminals:
            result.warnings.append("process has no reachable terminal step")
        can_reach_terminal = steps_reaching_any(data, terminals)
        for sid in sorted(reachable - can_reach_terminal):
            result.warnings.append(f"reachable step '{sid}' has no path to a terminal step")

        for component in strongly_connected_components(data, reachable):
            if is_cycle_component(data, component) and component.isdisjoint(can_reach_terminal):
                members = ", ".join(sorted(component))
                result.warnings.append(f"trapped cycle component has no path to a terminal step: {members}")

    return result