from pathlib import Path

from process_as_code.adapters import adapter_capabilities, get_adapter
from process_as_code.draft import drafting_bundle, drafting_prompt
from process_as_code.io import load_process
from process_as_code.jsonld import to_jsonld
from process_as_code.observed import compare_observed, load_event_traces
from process_as_code.validate import validate_process

ROOT = Path(__file__).parents[1]


def test_observed_vs_designed_detects_real_deviations():
    process = load_process(ROOT / "examples/sap/order-to-cash.process.yaml")
    events = load_event_traces(ROOT / "examples/observed/order-to-cash.events.csv")
    result = compare_observed(process, events)
    assert result["metrics"]["total_cases"] == 3
    assert result["metrics"]["conforming_cases"] == 1
    assert result["metrics"]["invalid_transition_count"] >= 1
    assert result["metrics"]["unknown_activity_count"] == 1
    assert result["metrics"]["variant_count"] == 3


def test_jsonld_graph_preserves_process_links():
    process = load_process(ROOT / "examples/customer-creation.process.yaml")
    graph = to_jsonld(process, "https://example.test/process/customer_creation")
    nodes = {node["@id"]: node for node in graph["@graph"]}
    process_node = nodes["https://example.test/process/customer_creation"]
    assert len(process_node["hasStep"]) == 6
    approve = nodes["https://example.test/process/customer_creation/step/approve"]
    assert approve["system"].endswith("/system/mdg")
    assert approve["control"][0].endswith("/control/sanctions_check")
    assert len(approve["nextStep"]) == 2


def test_drafting_bundle_is_provider_neutral_and_proposal():
    description = (ROOT / "examples/drafting/customer-onboarding.txt").read_text(encoding="utf-8")
    bundle = drafting_bundle(description, ROOT / "schemas/process.schema.json")
    assert bundle["contract_status"] == "proposal"
    assert bundle["schema"]["title"].startswith("Process as Code")
    assert "deterministic validation" in drafting_prompt(bundle)
    proposed = load_process(ROOT / "examples/drafting/customer-onboarding.process.yaml")
    assert validate_process(proposed).ok


def test_adapter_framework_and_csv_reference_adapter():
    names = {row["name"] for row in adapter_capabilities()}
    assert names == {"bpmn-file", "csv-manifest"}
    data, report = get_adapter("csv-manifest").import_process(ROOT / "examples/adapters/process-manifest.csv")
    assert report["adapter"] == "csv-manifest"
    assert validate_process(data).ok
    assert data["process"]["id"] == "simple_order"
    assert data["steps"][0]["transitions"][0]["to"] == "approve"


def test_playground_is_static_and_has_no_upload_endpoint():
    text = (ROOT / "web/playground/index.html").read_text(encoding="utf-8")
    assert "not uploaded or stored" in text
    assert "Validate & inspect" in text
    assert "process-code validate" in text
    assert "fetch(" not in text


def test_vscode_extension_is_present_and_cli_backed():
    package = (ROOT / "vscode-extension/package.json").read_text(encoding="utf-8")
    extension = (ROOT / "vscode-extension/extension.js").read_text(encoding="utf-8")
    assert "processAsCode.validate" in package
    assert "jsonValidation" in package
    assert "yamlValidation" in package
    assert "redhat.vscode-yaml" in package
    assert "process-code" in extension
