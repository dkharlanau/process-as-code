from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from process_as_code.cli import main
from process_as_code.diff import semantic_diff
from process_as_code.impact import impact_analysis
from process_as_code.io import load_process
from process_as_code.output_contract import (
    OUTPUT_FORMAT_VERSION,
    output_metadata,
    output_schema_dict,
    output_schema_text,
)


ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "examples/customer-creation.process.yaml"
NEW = ROOT / "examples/changes/customer-creation-v2.process.yaml"

SCHEMAS = {
    "semantic-diff": "semantic-diff-v1.schema.json",
    "impact": "impact-v1.schema.json",
}


def test_semantic_diff_has_stable_output_contract() -> None:
    result = semantic_diff(load_process(OLD), load_process(NEW))

    assert result["output"] == {
        "format": "process-as-code.semantic-diff",
        "version": "1.0",
        "schema": "https://dkharlanau.github.io/process-as-code/schemas/outputs/semantic-diff-v1.schema.json",
    }
    assert {"process", "sections", "analysis"} <= set(result)
    Draft202012Validator(output_schema_dict("semantic-diff")).validate(result)


def test_impact_has_stable_output_contract_and_tagged_nested_diff() -> None:
    result = impact_analysis(load_process(OLD), load_process(NEW))

    assert result["output"] == {
        "format": "process-as-code.impact",
        "version": "1.0",
        "schema": "https://dkharlanau.github.io/process-as-code/schemas/outputs/impact-v1.schema.json",
    }
    assert {"changed_steps", "affected", "risk_flags", "recommended_tests", "semantic_diff"} <= set(result)
    assert result["semantic_diff"]["output"]["format"] == "process-as-code.semantic-diff"
    Draft202012Validator(output_schema_dict("impact")).validate(result)


def test_output_schema_source_and_package_copies_match() -> None:
    for kind, filename in SCHEMAS.items():
        source = (ROOT / "schemas" / "outputs" / filename).read_text(encoding="utf-8")
        assert output_schema_text(kind) == source
        parsed = json.loads(source)
        assert parsed["properties"]["output"]["properties"]["version"]["const"] == OUTPUT_FORMAT_VERSION


def test_output_contract_metadata_is_explicit() -> None:
    assert output_metadata("semantic-diff")["format"] != output_metadata("impact")["format"]
    assert output_metadata("impact")["version"] == OUTPUT_FORMAT_VERSION


def test_cli_exports_bundled_output_schema(tmp_path: Path) -> None:
    target = tmp_path / "impact.schema.json"
    assert main(["output-schema", "impact", "-o", str(target)]) == 0
    assert target.read_text(encoding="utf-8") == output_schema_text("impact")
