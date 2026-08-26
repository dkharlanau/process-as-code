from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from .graph import step_edges
from .impact import impact_analysis
from .io import load_process
from .validate import validate_process


class ProcessRepository:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def _files(self) -> list[Path]:
        patterns = ("*.process.yaml", "*.process.yml", "*.process.json")
        found: set[Path] = set()
        for pattern in patterns:
            found.update(p for p in self.root.rglob(pattern) if ".github" not in p.parts and "schemas" not in p.parts and "changes" not in p.parts and "fixtures" not in p.parts)
        return sorted(found)

    def list_processes(self) -> list[dict[str, Any]]:
        items = []
        for path in self._files():
            try:
                data = load_process(path)
            except Exception:
                continue
            result = validate_process(data)
            if not result.ok:
                continue
            meta = data.get("process", {})
            items.append({"id": meta.get("id"), "name": meta.get("name"), "file": str(path.relative_to(self.root)), "owner": meta.get("owner")})
        return items

    def get_process(self, process_id: str) -> dict[str, Any]:
        for item in self.list_processes():
            if item["id"] == process_id:
                data = load_process(self.root / item["file"])
                data = dict(data)
                data["_provenance"] = {"source_file": item["file"], "process_id": process_id, "validated": True}
                return data
        raise ValueError(f"unknown process '{process_id}'")

    def get_step(self, process_id: str, step_id: str) -> dict[str, Any]:
        data = self.get_process(process_id)
        for step in data.get("steps", []) or []:
            if isinstance(step, dict) and step.get("id") == step_id:
                result = dict(step)
                result["_provenance"] = {"process_id": process_id, "step_id": step_id, "source_file": data.get("_provenance", {}).get("source_file")}
                return result
        raise ValueError(f"unknown step '{step_id}' in process '{process_id}'")

    def allowed_transitions(self, process_id: str, step_id: str) -> list[dict[str, Any]]:
        step = self.get_step(process_id, step_id)
        agent = step.get("agent", {}) if isinstance(step.get("agent"), dict) else {}
        if agent.get("exposable") is False:
            return []
        return [{"to": target, "condition": label, "guidance_only": agent.get("executable") is not True} for target, label in step_edges(step)]


def create_server(root: str | Path):
    try:
        from mcp.server import MCPServer
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Install MCP support with: pip install 'process-as-code[mcp]'") from exc
    repo = ProcessRepository(root)
    mcp = MCPServer("Process as Code", instructions="Use validated process contracts as governed operational context. Preserve source IDs and controls.")

    @mcp.tool()
    def list_processes() -> list[dict[str, Any]]:
        """List validated process contracts and their source files."""
        return repo.list_processes()

    @mcp.tool()
    def get_process(process_id: str) -> dict[str, Any]:
        """Return one validated process contract by stable process ID."""
        return repo.get_process(process_id)

    @mcp.tool()
    def get_step(process_id: str, step_id: str) -> dict[str, Any]:
        """Return one step including ownership, systems, controls and agent policy metadata."""
        return repo.get_step(process_id, step_id)

    @mcp.tool()
    def get_allowed_transitions(process_id: str, step_id: str) -> list[dict[str, Any]]:
        """Return deterministic allowed next transitions from a step."""
        return repo.allowed_transitions(process_id, step_id)

    @mcp.tool()
    def get_controls(process_id: str, step_id: str) -> list[dict[str, Any]]:
        """Return controls referenced by a process step."""
        data = repo.get_process(process_id)
        step = repo.get_step(process_id, step_id)
        ids = set(step.get("controls", []) or [])
        return [c for c in data.get("controls", []) or [] if isinstance(c, dict) and c.get("id") in ids]

    @mcp.tool()
    def compare_process_files(old_file: str, new_file: str) -> dict[str, Any]:
        """Return semantic change impact for two process files below the configured root."""
        old_path = (repo.root / old_file).resolve(); new_path = (repo.root / new_file).resolve()
        if repo.root not in old_path.parents or repo.root not in new_path.parents:
            raise ValueError("files must be below configured root")
        return impact_analysis(load_process(old_path), load_process(new_path), base_dir=new_path.parent)

    return mcp


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Expose Process as Code contracts through MCP")
    parser.add_argument("--root", default=os.environ.get("PROCESS_AS_CODE_ROOT", "."))
    args = parser.parse_args(argv)
    create_server(args.root).run()
    return 0
