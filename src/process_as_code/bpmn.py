from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .graph import step_edges

BPMN = "http://www.omg.org/spec/BPMN/20100524/MODEL"
ET.register_namespace("bpmn", BPMN)


def _q(name: str) -> str:
    return f"{{{BPMN}}}{name}"


def to_bpmn(data: dict[str, Any]) -> str:
    meta = data.get("process", {})
    process_id = meta.get("id", "process")
    definitions = ET.Element(_q("definitions"), {
        "id": f"Definitions_{process_id}",
        "targetNamespace": "https://github.com/dkharlanau/process-as-code",
    })
    proc = ET.SubElement(definitions, _q("process"), {
        "id": process_id,
        "name": meta.get("name", process_id),
        "isExecutable": "false",
    })

    steps = [s for s in data.get("steps", []) if isinstance(s, dict) and s.get("id")]
    start_id = meta.get("start") or (steps[0]["id"] if steps else None)
    incoming: dict[str, list[str]] = {s["id"]: [] for s in steps}
    outgoing: dict[str, list[str]] = {s["id"]: [] for s in steps}
    flows: list[tuple[str, str, str, str | None]] = []
    if start_id:
        start = ET.SubElement(proc, _q("startEvent"), {"id": "StartEvent", "name": "Start"})
        flow_id = f"Flow_Start_{start_id}"
        ET.SubElement(start, _q("outgoing")).text = flow_id
        incoming.setdefault(start_id, []).append(flow_id)
        flows.append((flow_id, "StartEvent", start_id, None))

    node_tags = {
        "task": "task", "user_task": "userTask", "service_task": "serviceTask",
        "decision": "exclusiveGateway", "parallel": "parallelGateway",
        "event": "intermediateCatchEvent", "end": "endEvent", "subprocess": "subProcess",
    }
    for step in steps:
        for index, (target, label) in enumerate(step_edges(step), 1):
            flow_id = f"Flow_{step['id']}_{target}_{index}"
            outgoing[step["id"]].append(flow_id)
            incoming.setdefault(target, []).append(flow_id)
            flows.append((flow_id, step["id"], target, label))

    for step in steps:
        tag = node_tags.get(step.get("type", "task"), "task")
        node = ET.SubElement(proc, _q(tag), {"id": step["id"], "name": step.get("name", step["id"])})
        for flow_id in incoming.get(step["id"], []):
            ET.SubElement(node, _q("incoming")).text = flow_id
        for flow_id in outgoing.get(step["id"], []):
            ET.SubElement(node, _q("outgoing")).text = flow_id

    roles = {r["id"]: r for r in data.get("roles", []) or [] if isinstance(r, dict) and r.get("id")}
    lanes: dict[str, list[str]] = {}
    for step in steps:
        actor = step.get("actor")
        if actor:
            lanes.setdefault(actor, []).append(step["id"])
    if lanes:
        lane_set = ET.SubElement(proc, _q("laneSet"), {"id": "LaneSet_1"})
        for actor, node_ids in lanes.items():
            lane = ET.SubElement(lane_set, _q("lane"), {"id": f"Lane_{actor}", "name": roles.get(actor, {}).get("name", actor)})
            for node_id in node_ids:
                ET.SubElement(lane, _q("flowNodeRef")).text = node_id

    for flow_id, source, target, label in flows:
        attrs = {"id": flow_id, "sourceRef": source, "targetRef": target}
        if label:
            attrs["name"] = label
        ET.SubElement(proc, _q("sequenceFlow"), attrs)

    ET.indent(definitions, space="  ")
    return ET.tostring(definitions, encoding="unicode", xml_declaration=True) + "\n"


def import_bpmn(source: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Import a deterministic BPMN 2.0 subset.

    Supported: tasks, user/service tasks, sub-process nodes, exclusive/parallel
    gateways, intermediate catch events, end events, sequence flows and lanes.
    Start events are represented by `process.start`, not as an explicit step.
    """
    path = Path(source)
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    processes = root.findall(f".//{_q('process')}")
    if not processes:
        raise ValueError("BPMN contains no process")
    proc = processes[0]
    report: dict[str, Any] = {"warnings": [], "unsupported": []}
    if len(processes) > 1:
        report["warnings"].append("multiple BPMN processes found; imported the first")

    type_map = {
        "task": "task", "userTask": "user_task", "serviceTask": "service_task",
        "exclusiveGateway": "decision", "parallelGateway": "parallel",
        "intermediateCatchEvent": "event", "endEvent": "end", "subProcess": "subprocess",
    }
    steps: dict[str, dict[str, Any]] = {}
    supported_tags = set(type_map) | {"startEvent", "sequenceFlow", "laneSet", "lane"}
    for child in list(proc):
        local = child.tag.split("}")[-1]
        if local in type_map:
            sid = child.get("id")
            if sid:
                steps[sid] = {"id": sid, "name": child.get("name") or sid, "type": type_map[local]}
        elif local not in supported_tags and local not in {"documentation", "extensionElements"}:
            report["unsupported"].append(local)

    roles: list[dict[str, str]] = []
    lane_names: set[str] = set()
    for lane in proc.findall(f".//{_q('lane')}"):
        lane_id = lane.get("id") or lane.get("name") or "lane"
        role_id = lane_id.removeprefix("Lane_")
        role_name = lane.get("name") or role_id
        if role_id not in lane_names:
            roles.append({"id": role_id, "name": role_name})
            lane_names.add(role_id)
        for node_ref in lane.findall(_q("flowNodeRef")):
            if node_ref.text in steps:
                steps[node_ref.text]["actor"] = role_id

    starts = proc.findall(_q("startEvent"))
    if len(starts) > 1:
        report["warnings"].append("multiple start events found; first outgoing target becomes process.start")
    start_ids = {start.get("id") for start in starts if start.get("id")}
    process_start: str | None = None
    outgoing: dict[str, list[dict[str, Any]]] = {}
    for flow in proc.findall(_q("sequenceFlow")):
        source_ref = flow.get("sourceRef")
        target_ref = flow.get("targetRef")
        if not source_ref or not target_ref:
            continue
        if source_ref in start_ids:
            if process_start is None:
                process_start = target_ref
            continue
        if source_ref not in steps or target_ref not in steps:
            report["warnings"].append(f"sequenceFlow '{flow.get('id')}' references unsupported/missing node")
            continue
        transition: dict[str, Any] = {"to": target_ref}
        if flow.get("name"):
            transition["label"] = flow.get("name")
            if steps[source_ref].get("type") == "decision":
                transition["when"] = flow.get("name")
        outgoing.setdefault(source_ref, []).append(transition)
    for sid, transitions in outgoing.items():
        steps[sid]["transitions"] = transitions

    data: dict[str, Any] = {
        "version": "0.2",
        "process": {
            "id": proc.get("id") or "imported_process",
            "name": proc.get("name") or proc.get("id") or "Imported Process",
            "start": process_start or (next(iter(steps)) if steps else None),
        },
        "steps": list(steps.values()),
    }
    if roles:
        data["roles"] = roles
    report["unsupported"] = sorted(set(report["unsupported"]))
    report["supported_subset"] = sorted(type_map)
    return data, report
