from __future__ import annotations

from pathlib import Path
from typing import Any

from .diff import semantic_diff
from .output_contract import attach_output_contract
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


ANALYSIS_SECTIONS = ("variants", "pain_points", "data_flows")


def _analysis_by_id(data: dict[str, Any], section: str) -> dict[str, dict[str, Any]]:
    analysis = data.get("analysis", {})
    if not isinstance(analysis, dict):
        return {}
    return _by_id(analysis.get(section))


def _analysis_refs(section: str, item: dict[str, Any]) -> dict[str, set[str]]:
    steps: set[str] = set()
    systems: set[str] = set()
    evidence: set[str] = set()
    if section == "variants":
        path = item.get("path", [])
        if isinstance(path, list):
            steps.update(value for value in path if isinstance(value, str))
    elif section == "pain_points":
        if isinstance(item.get("step"), str):
            steps.add(item["step"])
        refs = item.get("evidence", [])
        if isinstance(refs, list):
            evidence.update(value for value in refs if isinstance(value, str))
    elif section == "data_flows":
        for field in ("from", "to"):
            if isinstance(item.get(field), str):
                systems.add(item[field])
    return {"steps": steps, "systems": systems, "evidence": evidence}


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

    analysis_changes: dict[str, list[str]] = {}
    analysis_affected_steps: set[str] = set()
    for section in ANALYSIS_SECTIONS:
        changes = diff.get("analysis", {}).get(section, {"added": [], "removed": [], "changed": {}})
        changed_ids = set(changes["added"]) | set(changes["removed"]) | set(changes["changed"])
        analysis_changes[section] = sorted(changed_ids)
        old_items, new_items = _analysis_by_id(old, section), _analysis_by_id(new, section)
        for item_id in changed_ids:
            for source in (old_items.get(item_id), new_items.get(item_id)):
                if not source:
                    continue
                refs = _analysis_refs(section, source)
                analysis_affected_steps.update(refs["steps"])
                affected["systems"].update(refs["systems"])
                affected["evidence"].update(refs["evidence"])

    for section in affected:
        if section not in diff["sections"]:
            continue
        changes = diff["sections"][section]
        affected[section].update(changes["added"])
        affected[section].update(changes["removed"])
        affected[section].update(changes["changed"].keys())

    test_steps = changed_steps | analysis_affected_steps
    tests = [test for test in generate_test_scope(new) if test["step"] in test_steps or any(ref in test["id"] for ref in affected["interfaces"] | affected["controls"] | affected["risks"])]
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

    return attach_output_contract("impact", {
        "changed_steps": sorted(changed_steps),
        "analysis_changes": analysis_changes,
        "analysis_affected_steps": sorted(analysis_affected_steps),
        "affected": {name: sorted(values) for name, values in affected.items()},
        "risk_flags": risk_flags,
        "recommended_tests": tests,
        "resolved_artifacts": resolved,
        "semantic_diff": diff,
    })

def impact_markdown(result: dict[str, Any]) -> str:
    lines = ["# Process change impact", "", "## Changed steps", ""]
    lines += [f"- `{step}`" for step in result["changed_steps"]] or ["No step-level changes."]

    analysis_changes = result.get("analysis_changes", {})
    if any(analysis_changes.values()):
        lines += ["", "## Process analysis changes", ""]
        for section, values in analysis_changes.items():
            if values:
                rendered = ", ".join(f"`{value}`" for value in values)
                lines.append(f"- **{section.replace('_', ' ').title()}**: {rendered}")
        affected_steps = result.get("analysis_affected_steps", [])
        if affected_steps:
            rendered = ", ".join(f"`{value}`" for value in affected_steps)
            lines.append(f"- **Affected steps from analysis**: {rendered}")

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
        lines.append("No generated tests are directly linked to the changed steps or analysis context.")
    return "\n".join(lines).rstrip() + "\n"
