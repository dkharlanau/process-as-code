from __future__ import annotations

from pathlib import Path
from typing import Any

from .diff import semantic_diff
from .refs import resolve_artifacts
from .testgen import generate_test_scope


def _by_id(items: list[Any] | None) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in (items or []) if isinstance(item, dict) and isinstance(item.get("id"), str)}


def _refs_from_step(step: dict[str, Any]) -> dict[str, set[str]]:
    raci = step.get("raci", {}) or {}
    roles: set[str] = set()
    if step.get("actor"):
        roles.add(step["actor"])
    if isinstance(raci, dict):
        for key in ("responsible", "accountable", "consulted", "informed"):
            value = raci.get(key, [])
            if isinstance(value, str):
                roles.add(value)
            elif isinstance(value, list):
                roles.update(v for v in value if isinstance(v, str))
    return {
        "roles": roles,
        "systems": {step["system"]} if step.get("system") else set(),
        "objects": set(step.get("objects", []) or []),
        "interfaces": set(step.get("interfaces", []) or []),
        "controls": set(step.get("controls", []) or []),
        "risks": set(step.get("risks", []) or []),
        "evidence": set(step.get("evidence", []) or []),
        "artifacts": set(step.get("artifacts", []) or []),
        "subprocesses": {step["process_ref"]} if isinstance(step.get("process_ref"), str) else set(),
    }


def impact_analysis(old: dict[str, Any], new: dict[str, Any], *, base_dir: str | Path | None = None, resolve_external: bool = False, allow_network: bool = False) -> dict[str, Any]:
    diff = semantic_diff(old, new)
    step_changes = diff["sections"]["steps"]
    changed_steps = set(step_changes["added"]) | set(step_changes["removed"]) | set(step_changes["changed"])
    old_steps, new_steps = _by_id(old.get("steps")), _by_id(new.get("steps"))
    affected = {name: set() for name in ("roles", "systems", "objects", "interfaces", "controls", "risks", "evidence", "artifacts", "subprocesses")}
    for step_id in changed_steps:
        for source in (old_steps.get(step_id), new_steps.get(step_id)):
            if not source:
                continue
            for name, values in _refs_from_step(source).items():
                affected[name].update(values)
    for section in affected:
        if section not in diff["sections"]:
            continue
        changes = diff["sections"][section]
        affected[section].update(changes["added"])
        affected[section].update(changes["removed"])
        affected[section].update(changes["changed"].keys())

    tests = [test for test in generate_test_scope(new) if test["step"] in changed_steps or any(ref in test["id"] for ref in affected["interfaces"] | affected["controls"] | affected["risks"])]
    risk_flags: list[str] = []
    if affected["controls"]: risk_flags.append("control-change")
    if affected["interfaces"]: risk_flags.append("integration-change")
    if affected["risks"]: risk_flags.append("risk-change")
    if affected["artifacts"]: risk_flags.append("external-artifact-change")
    if step_changes["removed"]: risk_flags.append("step-removal")
    if diff.get("process", {}).get("owner"): risk_flags.append("ownership-change")

    resolved: list[dict[str, Any]] = []
    if resolve_external:
        resolved_all = resolve_artifacts(new, base_dir=base_dir or ".", allow_network=allow_network)
        affected_artifacts = affected["artifacts"]
        resolved = [r for r in resolved_all if r.get("id") in affected_artifacts]

    return {
        "changed_steps": sorted(changed_steps),
        "affected": {name: sorted(values) for name, values in affected.items()},
        "risk_flags": risk_flags,
        "recommended_tests": tests,
        "resolved_artifacts": resolved,
        "semantic_diff": diff,
    }


def impact_markdown(result: dict[str, Any]) -> str:
    lines = ["# Process change impact", "", "## Changed steps", ""]
    lines += [f"- `{step}`" for step in result["changed_steps"]] or ["No step-level changes."]
    lines += ["", "## Affected context", ""]
    for section, values in result["affected"].items():
        rendered = ", ".join(f"`{value}`" for value in values) if values else "—"
        lines.append(f"- **{section.title()}**: {rendered}")
    lines += ["", "## Risk flags", ""]
    lines += [f"- `{flag}`" for flag in result["risk_flags"]] or ["No elevated risk flags derived."]
    if result.get("resolved_artifacts"):
        lines += ["", "## Resolved external artifacts", "", "| ID | Kind | Status | Source |", "| --- | --- | --- | --- |"]
        for item in result["resolved_artifacts"]:
            lines.append(f"| `{item.get('id','')}` | {item.get('kind','')} | {item.get('status','')} | {item.get('source','')} |")
    lines += ["", "## Recommended tests", ""]
    if result["recommended_tests"]:
        lines += ["| Test ID | Type | Scenario |", "| --- | --- | --- |"]
        for test in result["recommended_tests"]:
            lines.append(f"| `{test['id']}` | {test['type']} | {test['scenario']} |")
    else:
        lines.append("No generated tests are directly linked to the changed steps.")
    return "\n".join(lines).rstrip() + "\n"
