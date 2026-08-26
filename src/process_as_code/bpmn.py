from __future__ import annotations

import xml.etree.ElementTree as ET
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
    if start_id:
        start = ET.SubElement(proc, _q("startEvent"), {"id": "StartEvent", "name": "Start"})
        ET.SubElement(start, _q("outgoing")).text = f"Flow_Start_{start_id}"

    node_tags = {
        "task": "task",
        "user_task": "userTask",
        "service_task": "serviceTask",
        "decision": "exclusiveGateway",
        "event": "intermediateCatchEvent",
        "end": "endEvent",
    }
    incoming: dict[str, list[str]] = {s["id"]: [] for s in steps}
    outgoing: dict[str, list[str]] = {s["id"]: [] for s in steps}
    flows: list[tuple[str, str, str, str | None]] = []

    if start_id:
        incoming.setdefault(start_id, []).append(f"Flow_Start_{start_id}")
        flows.append((f"Flow_Start_{start_id}", "StartEvent", start_id, None))

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

    for flow_id, source, target, label in flows:
        attrs = {"id": flow_id, "sourceRef": source, "targetRef": target}
        if label:
            attrs["name"] = label
        ET.SubElement(proc, _q("sequenceFlow"), attrs)

    ET.indent(definitions, space="  ")
    return ET.tostring(definitions, encoding="unicode", xml_declaration=True) + "\n"
