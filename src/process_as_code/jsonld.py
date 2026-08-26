from __future__ import annotations

from typing import Any

from .graph import step_edges

VOCAB = "https://dkharlanau.github.io/process-as-code/vocab#"


def _safe(value: str) -> str:
    return value.replace(" ", "-")


def to_jsonld(data: dict[str, Any], base_uri: str | None = None) -> dict[str, Any]:
    meta = data.get("process", {})
    pid = str(meta.get("id", "process"))
    base = (base_uri or f"urn:process-as-code:{pid}").rstrip("/")
    def uri(section: str, item_id: str) -> str:
        return f"{base}/{section}/{_safe(item_id)}"

    context = {
        "@vocab": VOCAB,
        "name": "http://schema.org/name",
        "description": "http://schema.org/description",
        "Process": VOCAB + "Process",
        "Step": VOCAB + "Step",
        "Role": VOCAB + "Role",
        "System": VOCAB + "System",
        "BusinessObject": VOCAB + "BusinessObject",
        "Interface": VOCAB + "Interface",
        "Control": VOCAB + "Control",
        "Risk": VOCAB + "Risk",
        "Evidence": VOCAB + "Evidence",
        "Artifact": VOCAB + "Artifact",
        "hasStep": {"@id": VOCAB + "hasStep", "@type": "@id"},
        "nextStep": {"@id": VOCAB + "nextStep", "@type": "@id"},
        "actor": {"@id": VOCAB + "actor", "@type": "@id"},
        "system": {"@id": VOCAB + "system", "@type": "@id"},
        "control": {"@id": VOCAB + "control", "@type": "@id"},
        "risk": {"@id": VOCAB + "risk", "@type": "@id"},
        "evidence": {"@id": VOCAB + "evidence", "@type": "@id"},
        "interface": {"@id": VOCAB + "interface", "@type": "@id"},
        "object": {"@id": VOCAB + "object", "@type": "@id"},
        "artifact": {"@id": VOCAB + "artifact", "@type": "@id"},
        "externalUri": {"@id": VOCAB + "externalUri", "@type": "@id"},
    }
    graph: list[dict[str, Any]] = []
    process_node: dict[str, Any] = {
        "@id": base,
        "@type": "Process",
        "name": meta.get("name", pid),
        "hasStep": [uri("step", s["id"]) for s in data.get("steps", []) or [] if isinstance(s, dict) and s.get("id")],
    }
    if meta.get("description"):
        process_node["description"] = meta["description"]
    if meta.get("owner"):
        process_node["owner"] = uri("role", str(meta["owner"]))
    graph.append(process_node)

    catalog_types = {
        "roles": ("role", "Role"), "systems": ("system", "System"), "objects": ("object", "BusinessObject"),
        "interfaces": ("interface", "Interface"), "controls": ("control", "Control"), "risks": ("risk", "Risk"),
        "evidence": ("evidence", "Evidence"), "artifacts": ("artifact", "Artifact"),
    }
    for section, (segment, node_type) in catalog_types.items():
        for item in data.get(section, []) or []:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            node: dict[str, Any] = {"@id": uri(segment, str(item["id"])), "@type": node_type, "name": item.get("name", item["id"])}
            if item.get("description"):
                node["description"] = item["description"]
            if section == "artifacts" and item.get("uri"):
                node["externalUri"] = item["uri"]
                if item.get("kind"):
                    node["kind"] = item["kind"]
                if item.get("relation"):
                    node["relation"] = item["relation"]
            graph.append(node)

    for step in data.get("steps", []) or []:
        if not isinstance(step, dict) or not step.get("id"):
            continue
        node = {"@id": uri("step", str(step["id"])), "@type": "Step", "name": step.get("name", step["id"]), "stepType": step.get("type", "task")}
        if step.get("actor"):
            node["actor"] = uri("role", str(step["actor"]))
        if step.get("system"):
            node["system"] = uri("system", str(step["system"]))
        for field, segment, singular in (("objects", "object", "object"), ("interfaces", "interface", "interface"), ("controls", "control", "control"), ("risks", "risk", "risk"), ("evidence", "evidence", "evidence"), ("artifacts", "artifact", "artifact")):
            refs = [uri(segment, str(ref)) for ref in step.get(field, []) or []]
            if refs:
                node[singular] = refs
        edges = step_edges(step)
        if edges:
            node["nextStep"] = [uri("step", target) for target, _ in edges]
            node["transition"] = [{"to": uri("step", target), "condition": label} for target, label in edges]
        graph.append(node)
    return {"@context": context, "@id": base, "@graph": graph}
