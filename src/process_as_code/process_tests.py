from __future__ import annotations

from typing import Any

from .diff import semantic_diff
from .graph import adjacency


def _path_valid(process: dict[str, Any], path: list[str]) -> bool:
    if not path:
        return False
    graph = adjacency(process)
    return all(any(target == b for target, _ in graph.get(a, [])) for a, b in zip(path, path[1:]))


def run_process_tests(process: dict[str, Any], suite: dict[str, Any]) -> list[dict[str, Any]]:
    steps = {s["id"]: s for s in process.get("steps", []) or [] if isinstance(s, dict) and s.get("id")}
    results: list[dict[str, Any]] = []
    for test in suite.get("tests", []) or []:
        if not isinstance(test, dict) or not test.get("id"):
            continue
        failures: list[str] = []
        path = test.get("path")
        if isinstance(path, list) and not _path_valid(process, [p for p in path if isinstance(p, str)]):
            failures.append("declared path is not valid")
        assertion = test.get("assert_step")
        if isinstance(assertion, dict):
            sid = assertion.get("step")
            step = steps.get(sid)
            if not step:
                failures.append(f"step '{sid}' does not exist")
            else:
                for field in ("controls", "interfaces", "risks", "evidence", "artifacts"):
                    expected = set(assertion.get(field, []) or [])
                    actual = set(step.get(field, []) or [])
                    missing = expected - actual
                    if missing:
                        failures.append(f"step '{sid}' missing {field}: {', '.join(sorted(missing))}")
                if assertion.get("actor") and assertion.get("actor") != step.get("actor"):
                    failures.append(f"step '{sid}' actor mismatch")
                if assertion.get("system") and assertion.get("system") != step.get("system"):
                    failures.append(f"step '{sid}' system mismatch")
        results.append({"id": test["id"], "ok": not failures, "failures": failures})
    return results


def affected_process_tests(old: dict[str, Any], new: dict[str, Any], suite: dict[str, Any]) -> list[str]:
    diff = semantic_diff(old, new)
    changes = diff["sections"]["steps"]
    changed = set(changes["added"]) | set(changes["removed"]) | set(changes["changed"])
    affected: list[str] = []
    for test in suite.get("tests", []) or []:
        if not isinstance(test, dict) or not test.get("id"):
            continue
        refs = set(x for x in test.get("path", []) or [] if isinstance(x, str))
        assertion = test.get("assert_step")
        if isinstance(assertion, dict) and isinstance(assertion.get("step"), str):
            refs.add(assertion["step"])
        if refs & changed:
            affected.append(test["id"])
    return sorted(affected)
