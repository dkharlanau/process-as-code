from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .graph import adjacency


def load_event_traces(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        events = data.get("events", data) if isinstance(data, dict) else data
        if not isinstance(events, list):
            raise ValueError("JSON event log must be a list or an object with 'events'")
        rows = [event for event in events if isinstance(event, dict)]
    else:
        with path.open(newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh))
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        case = row.get("case") or row.get("case_id") or row.get("caseId")
        activity = row.get("activity") or row.get("step") or row.get("step_id")
        if not case or not activity:
            raise ValueError(f"event {index} requires case/case_id and activity/step_id")
        normalized.append({
            "case": str(case),
            "activity": str(activity),
            "timestamp": row.get("timestamp") or row.get("time") or "",
            "_order": index,
        })
    return normalized


def compare_observed(process: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    steps = {s["id"]: s for s in process.get("steps", []) or [] if isinstance(s, dict) and isinstance(s.get("id"), str)}
    graph = adjacency(process)
    start = process.get("process", {}).get("start") or (next(iter(steps)) if steps else None)
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        by_case[str(event["case"])].append(event)
    for case_events in by_case.values():
        case_events.sort(key=lambda e: (str(e.get("timestamp") or ""), int(e.get("_order", 0))))

    cases: list[dict[str, Any]] = []
    variants: Counter[tuple[str, ...]] = Counter()
    total_unknown = total_invalid = incomplete = 0
    for case_id, case_events in sorted(by_case.items()):
        path = [str(event["activity"]) for event in case_events]
        variants[tuple(path)] += 1
        unknown = [activity for activity in path if activity not in steps]
        invalid: list[dict[str, str]] = []
        if path and start and path[0] != start:
            invalid.append({"from": "<start>", "to": path[0], "reason": f"expected process start '{start}'"})
        for source, target in zip(path, path[1:]):
            if source not in steps or target not in steps:
                continue
            allowed = {to for to, _ in graph.get(source, [])}
            if target not in allowed:
                invalid.append({"from": source, "to": target, "reason": "transition is not declared"})
        terminal_ok = bool(path and path[-1] in steps and not graph.get(path[-1], []))
        total_unknown += len(unknown)
        total_invalid += len(invalid)
        if not terminal_ok:
            incomplete += 1
        cases.append({
            "case": case_id,
            "path": path,
            "unknown_activities": unknown,
            "invalid_transitions": invalid,
            "terminal_ok": terminal_ok,
            "conforming": not unknown and not invalid and terminal_ok,
        })

    conforming = sum(1 for case in cases if case["conforming"])
    total = len(cases)
    variant_rows = [
        {"path": list(path), "count": count, "share": round(count / total, 4) if total else 0.0}
        for path, count in sorted(variants.items(), key=lambda item: (-item[1], item[0]))
    ]
    return {
        "process_id": process.get("process", {}).get("id"),
        "metrics": {
            "total_cases": total,
            "conforming_cases": conforming,
            "conformance_rate": round(conforming / total, 4) if total else 0.0,
            "unknown_activity_count": total_unknown,
            "invalid_transition_count": total_invalid,
            "incomplete_case_count": incomplete,
            "variant_count": len(variant_rows),
        },
        "variants": variant_rows,
        "cases": cases,
    }


def observed_markdown(result: dict[str, Any]) -> str:
    metrics = result["metrics"]
    lines = ["# Observed vs designed process", "", f"Process: `{result.get('process_id')}`", "", "## Metrics", "",
             "| Metric | Value |", "| --- | ---: |"]
    for key, value in metrics.items():
        lines.append(f"| {key.replace('_', ' ').title()} | {value} |")
    lines += ["", "## Path variants", "", "| Count | Share | Path |", "| ---: | ---: | --- |"]
    for variant in result["variants"]:
        lines.append(f"| {variant['count']} | {variant['share']:.1%} | `{' -> '.join(variant['path'])}` |")
    deviations = [case for case in result["cases"] if not case["conforming"]]
    lines += ["", "## Deviations", ""]
    if not deviations:
        lines.append("No deviations detected.")
    else:
        for case in deviations:
            lines.append(f"### Case `{case['case']}`")
            lines.append(f"- Path: `{' -> '.join(case['path'])}`")
            if case["unknown_activities"]:
                lines.append("- Unknown activities: " + ", ".join(f"`{x}`" for x in case["unknown_activities"]))
            for transition in case["invalid_transitions"]:
                lines.append(f"- Invalid transition: `{transition['from']} -> {transition['to']}` ({transition['reason']})")
            if not case["terminal_ok"]:
                lines.append("- Case did not finish at a declared terminal step.")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"
