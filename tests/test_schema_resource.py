from __future__ import annotations

from pathlib import Path

from process_as_code.draft import drafting_bundle
from process_as_code.schema import schema_dict, schema_text

ROOT = Path(__file__).resolve().parents[1]


def test_schema_copies_remain_identical() -> None:
    root_schema = (ROOT / "schemas/process.schema.json").read_text(encoding="utf-8")
    vscode_schema = (ROOT / "vscode-extension/process.schema.json").read_text(encoding="utf-8")
    assert schema_text() == root_schema
    assert vscode_schema == root_schema
    assert schema_dict()["properties"]["version"]["const"] == "0.2"


def test_drafting_bundle_uses_packaged_schema_by_default() -> None:
    bundle = drafting_bundle("Create and approve a customer request.")
    assert bundle["schema"]["title"] == "Process as Code contract v0.2"
    assert bundle["schema_source"].startswith("package:")
    assert bundle["contract_status"] == "proposal"
