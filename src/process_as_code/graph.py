from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Iterable


def step_edges(step: dict[str, Any]) -> list[tuple[str, str | None]]:
    """Return (target, label) edges declared by a step."""
    edges: list[tuple[str, str | None]] = []
    nxt = step.get("next")
    if isinstance(nxt, str):
        edges.append((nxt, None))
    elif isinstance(nxt, list):
        edges.extend((target, None) for target in nxt if isinstance(target, str))

    branches = step.get("branches", {})
    if isinstance(branches, dict):
        for label, target in branches.items():
            if isinstance(target, str):
                edges.append((target, str(label)))
    return edges


def adjacency(process: dict[str, Any]) -> dict[str, list[tuple[str, str | None]]]:
    return {
        step["id"]: step_edges(step)
        for step in process.get("steps", [])
        if isinstance(step, dict) and isinstance(step.get("id"), str)
    }


def reachable_step_ids(process: dict[str, Any]) -> set[str]:
    steps = [s for s in process.get("steps", []) if isinstance(s, dict) and s.get("id")]
    if not steps:
        return set()
    start = process.get("process", {}).get("start") or steps[0]["id"]
    graph = adjacency(process)
    seen: set[str] = set()
    queue = deque([start])
    while queue:
        node = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        for target, _ in graph.get(node, []):
            if target not in seen:
                queue.append(target)
    return seen


def incoming_counts(process: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for edges in adjacency(process).values():
        for target, _ in edges:
            counts[target] += 1
    return dict(counts)


def iter_entity_ids(process: dict[str, Any], section: str) -> Iterable[str]:
    for item in process.get(section, []) or []:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            yield item["id"]
