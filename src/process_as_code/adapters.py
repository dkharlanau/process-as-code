from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .bpmn import import_bpmn


@dataclass(frozen=True)
class AdapterInfo:
    name: str
    description: str
    import_formats: tuple[str, ...]
    export_formats: tuple[str, ...] = ()


class Adapter:
    info: AdapterInfo
    def import_process(self, source: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
        raise NotImplementedError


class BpmnFileAdapter(Adapter):
    info = AdapterInfo("bpmn-file", "Generic BPMN 2.0 file adapter using the documented supported subset.", (".bpmn", ".xml"), (".bpmn",))
    def import_process(self, source: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
        data, report = import_bpmn(source)
        return data, {"adapter": self.info.name, "capabilities": list(self.info.import_formats), **report}


class CsvManifestAdapter(Adapter):
    info = AdapterInfo("csv-manifest", "Simple process manifest adapter for migration spreadsheets/exports.", (".csv",))
    def import_process(self, source: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
        with Path(source).open(newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh))
        if not rows:
            raise ValueError("CSV manifest is empty")
        required = {"process_id", "process_name", "step_id", "step_name"}
        missing = required - set(rows[0])
        if missing:
            raise ValueError("CSV manifest missing columns: " + ", ".join(sorted(missing)))
        pid, pname = rows[0]["process_id"], rows[0]["process_name"]
        roles: dict[str, dict[str, str]] = {}
        systems: dict[str, dict[str, str]] = {}
        steps: list[dict[str, Any]] = []
        for row in rows:
            if row["process_id"] != pid:
                raise ValueError("CSV manifest must contain exactly one process_id")
            step: dict[str, Any] = {"id": row["step_id"], "name": row["step_name"], "type": row.get("type") or "task"}
            if row.get("actor"):
                step["actor"] = row["actor"]; roles.setdefault(row["actor"], {"id": row["actor"], "name": row.get("actor_name") or row["actor"]})
            if row.get("system"):
                step["system"] = row["system"]; systems.setdefault(row["system"], {"id": row["system"], "name": row.get("system_name") or row["system"]})
            if row.get("next"):
                step["transitions"] = [{"to": target.strip()} for target in row["next"].split(";") if target.strip()]
            steps.append(step)
        data: dict[str, Any] = {"version": "0.2", "process": {"id": pid, "name": pname, "start": steps[0]["id"]}, "steps": steps}
        if roles: data["roles"] = list(roles.values())
        if systems: data["systems"] = list(systems.values())
        return data, {"adapter": self.info.name, "warnings": [], "unsupported": [], "row_count": len(rows)}


_ADAPTERS: dict[str, Callable[[], Adapter]] = {"bpmn-file": BpmnFileAdapter, "csv-manifest": CsvManifestAdapter}


def adapter_names() -> list[str]:
    return sorted(_ADAPTERS)


def get_adapter(name: str) -> Adapter:
    factory = _ADAPTERS.get(name)
    if not factory:
        raise ValueError(f"unknown adapter '{name}'; available: {', '.join(adapter_names())}")
    return factory()


def adapter_capabilities() -> list[dict[str, Any]]:
    rows = []
    for name in adapter_names():
        info = get_adapter(name).info
        rows.append({"name": info.name, "description": info.description, "import_formats": list(info.import_formats), "export_formats": list(info.export_formats)})
    return rows
