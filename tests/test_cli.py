from pathlib import Path
from process_as_code.cli import main

ROOT = Path(__file__).parents[1]


def test_cli_validation_policy_and_resolution(tmp_path):
    process = str(ROOT / "examples/customer-creation.process.yaml")
    assert main(["validate", process, "--strict"]) == 0
    assert main(["policy", process, "--policy", str(ROOT / "examples/policy.yaml")]) == 0
    enterprise = str(ROOT / "examples/enterprise-change/customer.process.yaml")
    assert main(["resolve", enterprise, "--base-dir", str(ROOT / "examples/enterprise-change"), "--json"]) == 0


def test_cli_bpmn_import(tmp_path):
    process = str(ROOT / "examples/customer-creation.process.yaml")
    bpmn = tmp_path / "p.bpmn"
    imported = tmp_path / "imported.yaml"
    assert main(["bpmn", process, "-o", str(bpmn)]) == 0
    assert main(["bpmn-import", str(bpmn), "-o", str(imported)]) == 0
    assert main(["validate", str(imported), "--strict"]) == 0
