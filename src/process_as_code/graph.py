from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Iterable


def step_edges(step: dict[str, Any]) -> list[tuple[str, str | None]]:
    """Return (target, label) edges declared by a step.

    v0.2 `transitions` are preferred. Legacy `next` and `branches` remain supported
    so v0.1 contracts continue to work during migration.
    """
    transitions = step.get("transitions")
    if isinstance(transitions, list):
        edges: list[tuple[str, str | None]] = []
        for transition in transitions:
            if isinstance(transition, dict) and isinstance(transition.get("to"), str):
                label = transition.get("label") or transition.get("when")
                edges.append((transition["to"], str(label) if label is not None else None))
        return edges

    edges = []
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


def terminal_step_ids(process: dict[str, Any], *, reachable_only: bool = False) -> set[str]:
    """Return steps with no outgoing graph edges.

    A non-`end` step can still be an implicit terminal for v0.1 compatibility. The
    validator reports that shape separately; this helper only models graph liveness.
    """
    graph = adjacency(process)
    terminals = {node for node, edges in graph.items() if not edges}
    if reachable_only:
        terminals &= reachable_step_ids(process)
    return terminals


def steps_reaching_any(process: dict[str, Any], targets: set[str]) -> set[str]:
    """Return nodes that can reach at least one target, including targets themselves."""
    graph = adjacency(process)
    reverse: dict[str, set[str]] = defaultdict(set)
    for source, edges in graph.items():
        for target, _ in edges:
            if target in graph:
                reverse[target].add(source)

    seen: set[str] = set()
    queue = deque(sorted(targets & set(graph)))
    while queue:
        node = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        for source in sorted(reverse.get(node, set())):
            if source not in seen:
                queue.append(source)
    return seen


def strongly_connected_components(process: dict[str, Any], nodes: set[str] | None = None) -> list[set[str]]:
    """Return deterministic strongly connected components for the selected graph nodes."""
    graph = adjacency(process)
    allowed = set(graph) if nodes is None else set(graph) & nodes
    index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[set[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for target, _ in graph.get(node, []):
            if target not in allowed:
                continue
            if target not in indices:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[target])

        if lowlinks[node] != indices[node]:
            return
        component: set[str] = set()
        while stack:
            member = stack.pop()
            on_stack.remove(member)
            component.add(member)
            if member == node:
                break
        components.append(component)

    for node in sorted(allowed):
        if node not in indices:
            visit(node)
    return sorted(components, key=lambda component: tuple(sorted(component)))


def is_cycle_component(process: dict[str, Any], component: set[str]) -> bool:
    if len(component) > 1:
        return True
    if not component:
        return False
    node = next(iter(component))
    return any(target == node for target, _ in adjacency(process).get(node, []))


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