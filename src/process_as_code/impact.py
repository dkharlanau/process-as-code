from __future__ import annotations

from typing import Any

from .diff import semantic_diff
from .testgen import generate_test_scope


def _by_id(items: list[Any] | None) -> dict[str, dict[str, Any]]:
    return {
        item["id"]: item
        for item in (items or [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


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
    }


def impact_analysis(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    diff = semantic_diff(old, new)
    step_changes = diff["sections"]["steps"]
    changed_steps = set(step_changes["added"]) | set(step_changes["removed"]) | set(step_changes["changed"])

    old_steps, new_steps = _by_id(old.get("steps")), _by_id(new.get("steps"))
    affected = {name: set() for name in ("roles", "systems", "objects", "interfaces", "controls")}
    for step_id in changed_steps:
        for source in (old_steps.get(step_id), new_steps.get(step_id)):
            if not source:
                continue
            refs = _refs_from_step(source)
            for name, values in refs.items():
                affected[name].update(values)

    # Direct catalog changes are also impacts even if no changed step currently references them.
    for section in affected:
        changes = diff["sections"][section]
        affected[section].update(changes["added"])
        affected[section].update(changes["removed"])
        affected[section].update(changes["changed"].keys())

    tests = [
        test for test in generate_test_scope(new)
        if test["step"] in changed_steps
        or any(ref in test["id"] for ref in affected["interfaces"] | affected["controls"])
    ]

    risk_flags: list[str] = []
    if affected["controls"]:
        risk_flags.append("control-change")
    if affected["interfaces"]:
        risk_flags.append("integration-change")
    if step_changes["removed"]:
        risk_flags.append("step-removal")
    if diff.get("process", {}).get("owner"):
        risk_flags.append("ownership-change")

    return {
        "changed_steps": sorted(changed_steps),
        "affected": {name: sorted(values) for name, values in affected.items()},
        "risk_flags": risk_flags,
        "recommended_tests": tests,
        "semantic_diff": diff,
    }


def impact_markdown(result: dict[str, Any]) -> str:
    lines = ["# Process change impact", ""]
    steps = result["changed_steps"]
    lines += ["## Changed steps", ""]
    lines += [f"- `{step}`" for step in steps] or ["No step-level changes."]

    lines += ["", "## Affected context", ""]
    for section, values in result["affected"].items():
        rendered = ", ".join(f"`{value}`" for value in values) if values else "—"
        lines.append(f"- **{section.title()}**: {rendered}")

    lines += ["", "## Risk flags", ""]
    lines += [f"- `{flag}`" for flag in result["risk_flags"]] or ["No elevated risk flags derived."]

    lines += ["", "## Recommended tests", ""]
    if result["recommended_tests"]:
        lines += ["| Test ID | Type | Scenario |", "| --- | --- | --- |"]
        for test in result["recommended_tests"]:
            lines.append(f"| `{test['id']}` | {test['type']} | {test['scenario']} |")
    else:
        lines.append("No generated tests are directly linked to the changed steps.")
    return "\n".join(lines).rstrip() + "\n"
