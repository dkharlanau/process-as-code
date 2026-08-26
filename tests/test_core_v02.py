from pathlib import Path

from process_as_code.bpmn import import_bpmn, to_bpmn
from process_as_code.diff import semantic_diff, visual_diff_mermaid
from process_as_code.impact import impact_analysis
from process_as_code.io import load_process
from process_as_code.migrate import migrate_process
from process_as_code.policy import evaluate_policy
from process_as_code.process_tests import affected_process_tests, run_process_tests
from process_as_code.refs import parse_artifact_uri, resolve_artifacts
from process_as_code.validate import validate_process

ROOT = Path(__file__).parents[1]


def test_v02_example_validates_strictly():
    result = validate_process(load_process(ROOT / "examples/customer-creation.process.yaml"))
    assert result.ok
    assert result.warnings == []


def test_migrate_v01_next_and_branches():
    old = {"version":"0.1","process":{"id":"p","name":"P","start":"a"},"steps":[{"id":"a","name":"A","type":"decision","branches":{"yes":"b","no":"c"}},{"id":"b","name":"B","type":"end"},{"id":"c","name":"C","type":"end"}]}
    new = migrate_process(old)
    assert new["version"] == "0.2"
    assert {t["to"] for t in new["steps"][0]["transitions"]} == {"b","c"}
    assert validate_process(new).ok


def test_policy_high_risk_and_breaking_changes():
    data = load_process(ROOT / "examples/customer-creation.process.yaml")
    policy = load_process(ROOT / "examples/policy.yaml")
    result = evaluate_policy(data, policy)
    assert result.ok
    broken = load_process(ROOT / "examples/changes/customer-creation-v2.process.yaml")
    assert evaluate_policy(broken, policy, data).ok
    policy["acknowledge"]["breaking_changes"] = False
    changed = {**data, "steps": [s for s in data["steps"] if s["id"] != "validate"]}
    assert not evaluate_policy(changed, policy, data).ok


def test_bpmn_round_trip_supported_subset(tmp_path):
    data = load_process(ROOT / "examples/customer-creation.process.yaml")
    xml = to_bpmn(data)
    bpmn = tmp_path / "process.bpmn"
    bpmn.write_text(xml, encoding="utf-8")
    imported, report = import_bpmn(bpmn)
    assert report["unsupported"] == []
    assert validate_process(imported).ok
    assert imported["process"]["start"] == "request"
    assert {s["id"] for s in imported["steps"]} >= {"request", "approve", "replicate", "validate", "complete", "rejected"}


def test_semantic_and_visual_diff_include_new_compliance_step():
    old = load_process(ROOT / "examples/customer-creation.process.yaml")
    new = load_process(ROOT / "examples/changes/customer-creation-v2.process.yaml")
    diff = semantic_diff(old, new)
    assert "screen" in diff["sections"]["steps"]["added"]
    assert "class screen added" in visual_diff_mermaid(old, new)


def test_impact_includes_risk_and_interface():
    old = load_process(ROOT / "examples/customer-creation.process.yaml")
    new = load_process(ROOT / "examples/changes/customer-creation-v2.process.yaml")
    result = impact_analysis(old, new)
    assert "compliance_api" in result["affected"]["interfaces"]
    assert "restricted_party" in result["affected"]["risks"]
    assert "integration-change" in result["risk_flags"]


def test_transitive_external_artifact_resolution():
    process_path = ROOT / "examples/enterprise-change/customer.process.yaml"
    result = resolve_artifacts(load_process(process_path), base_dir=process_path.parent)
    assert [r["id"] for r in result] == ["interface_customer_replication", "mapping_customer", "reconciliation_customer"]
    assert all(r["status"] == "resolved" for r in result)


def test_github_uri_parser():
    parsed = parse_artifact_uri("github://acme/contracts/interfaces/customer.yaml?ref=v1#customer")
    assert parsed["owner"] == "acme" and parsed["repo"] == "contracts" and parsed["ref"] == "v1" and parsed["fragment"] == "customer"


def test_process_test_dsl_and_regression_scope():
    old = load_process(ROOT / "examples/customer-creation.process.yaml")
    suite = load_process(ROOT / "examples/customer-creation.tests.yaml")
    assert all(r["ok"] for r in run_process_tests(old, suite))
    new = load_process(ROOT / "examples/changes/customer-creation-v2.process.yaml")
    assert "happy_path" in affected_process_tests(old, new, suite)


def test_catalog_and_subprocess_composition():
    from process_as_code.compose import compose_catalogs, validate_composition
    path = ROOT / "examples/composition/customer-onboarding.process.yaml"
    data = load_process(path)
    composed, errors = compose_catalogs(data, path.parent)
    assert errors == []
    assert {r["id"] for r in composed["roles"]} == {"process_owner"}
    assert validate_composition(data, path.parent) == []
    assert validate_process(composed).ok


def test_static_catalog_generation(tmp_path):
    from process_as_code.catalog import generate_catalog
    manifest = generate_catalog(ROOT / "examples", tmp_path, "https://example.test/process-as-code")
    assert manifest["process_count"] >= 3
    assert (tmp_path / "index.html").exists()
    assert (tmp_path / "guides/process-change-impact-analysis.html").exists()
    assert "sitemap" in (tmp_path / "robots.txt").read_text().lower()


def test_openapi_asyncapi_and_json_schema_references_resolve():
    path = ROOT / "examples/contracts/api-driven.process.yaml"
    result = resolve_artifacts(load_process(path), base_dir=path.parent)
    assert len(result) == 3
    assert all(r["status"] == "resolved" for r in result)
    assert next(r for r in result if r["id"] == "create_customer_api")["target"]["operationId"] == "createCustomer"


def test_public_conformance_suite():
    from process_as_code.conformance import run_conformance
    assert run_conformance(ROOT / "conformance/v0.2")["ok"]


def test_sap_extension_pack_examples_are_valid():
    for path in sorted((ROOT / "examples/sap").glob("*.process.yaml")):
        result = validate_process(load_process(path))
        assert result.ok, (path.name, result.errors)
