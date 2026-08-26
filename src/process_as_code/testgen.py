from __future__ import annotations

from typing import Any


def generate_test_scope(data: dict[str, Any]) -> list[dict[str, str]]:
    tests: list[dict[str, str]] = []
    for step in data.get("steps", []) or []:
        if not isinstance(step, dict) or not step.get("id"):
            continue
        sid = step["id"]
        name = step.get("name", sid)
        kind = step.get("type", "task")
        if kind not in {"event", "end"}:
            tests.append({"id": f"{sid}:happy-path", "step": sid, "type": "functional", "scenario": f"Verify '{name}' completes with expected inputs and outputs"})
        transitions = step.get("transitions") or []
        if kind in {"decision", "parallel"} and isinstance(transitions, list):
            for index, transition in enumerate(transitions, 1):
                if not isinstance(transition, dict):
                    continue
                label = transition.get("label") or transition.get("when") or f"path-{index}"
                tests.append({"id": f"{sid}:branch:{label}", "step": sid, "type": "branch", "scenario": f"Verify '{name}' follows transition '{label}'"})
        elif kind == "decision":
            for branch in (step.get("branches") or {}).keys():
                tests.append({"id": f"{sid}:branch:{branch}", "step": sid, "type": "branch", "scenario": f"Verify decision '{name}' follows branch '{branch}'"})
        for interface in step.get("interfaces", []) or []:
            tests.append({"id": f"{sid}:interface:{interface}", "step": sid, "type": "integration", "scenario": f"Verify interface '{interface}' success and failure handling at '{name}'"})
        for control in step.get("controls", []) or []:
            tests.append({"id": f"{sid}:control:{control}", "step": sid, "type": "control", "scenario": f"Verify control '{control}' is enforced at '{name}'"})
        for risk in step.get("risks", []) or []:
            tests.append({"id": f"{sid}:risk:{risk}", "step": sid, "type": "risk", "scenario": f"Verify mitigation for risk '{risk}' at '{name}'"})
        if step.get("sla"):
            tests.append({"id": f"{sid}:sla", "step": sid, "type": "sla", "scenario": f"Verify SLA for '{name}' is measured and met"})
    return tests


def test_scope_markdown(data: dict[str, Any]) -> str:
    lines = ["| Test ID | Type | Step | Scenario |", "| --- | --- | --- | --- |"]
    for test in generate_test_scope(data):
        lines.append(f"| `{test['id']}` | {test['type']} | `{test['step']}` | {test['scenario']} |")
    return "\n".join(lines) + "\n"
