from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .diff import semantic_diff


@dataclass
class PolicyResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _emit(result: PolicyResult, severity: str | bool | None, message: str) -> None:
    if severity in (None, False, "off", "disabled"):
        return
    if severity in (True, "error", "block"):
        result.errors.append(message)
    else:
        result.warnings.append(message)


def _risk_index(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {r["id"]: r for r in data.get("risks", []) or [] if isinstance(r, dict) and isinstance(r.get("id"), str)}


def evaluate_policy(data: dict[str, Any], config: dict[str, Any], old: dict[str, Any] | None = None) -> PolicyResult:
    result = PolicyResult()
    rules = config.get("rules", config) if isinstance(config, dict) else {}
    if not isinstance(rules, dict):
        rules = {}

    owner_rule = rules.get("required_process_owner")
    if owner_rule and not data.get("process", {}).get("owner"):
        _emit(result, owner_rule, "process owner is required by policy")

    high_controls = rules.get("high_risk_requires_controls")
    high_evidence = rules.get("high_risk_requires_evidence")
    service_sla = rules.get("service_tasks_require_sla")
    risks = _risk_index(data)
    for step in data.get("steps", []) or []:
        if not isinstance(step, dict) or not step.get("id"):
            continue
        sid = step["id"]
        high = [rid for rid in step.get("risks", []) or [] if str(risks.get(rid, {}).get("severity", "")).lower() in {"high", "critical"}]
        if high and not step.get("controls"):
            _emit(result, high_controls, f"high-risk step '{sid}' requires at least one control")
        if high and not step.get("evidence"):
            _emit(result, high_evidence, f"high-risk step '{sid}' requires evidence references")
        if step.get("type") == "service_task" and not step.get("sla"):
            _emit(result, service_sla, f"service task '{sid}' requires SLA metadata")

    if old is not None:
        diff = semantic_diff(old, data)
        breaking = []
        for section in ("steps", "interfaces", "controls", "objects", "artifacts"):
            breaking.extend(f"{section}:{item}" for item in diff["sections"][section]["removed"])
        if "owner" in diff.get("process", {}):
            breaking.append("process:owner")
        severity = rules.get("breaking_change_ack")
        acknowledged = bool(config.get("acknowledge", {}).get("breaking_changes")) if isinstance(config.get("acknowledge"), dict) else False
        if breaking and not acknowledged:
            _emit(result, severity, "breaking changes require explicit acknowledgement: " + ", ".join(sorted(breaking)))
    return result


def policy_markdown(result: PolicyResult) -> str:
    lines = ["# Process policy result", ""]
    lines += ["## Errors", ""] + ([f"- {e}" for e in result.errors] or ["None."])
    lines += ["", "## Warnings", ""] + ([f"- {w}" for w in result.warnings] or ["None."])
    return "\n".join(lines) + "\n"
