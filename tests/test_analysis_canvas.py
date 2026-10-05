from copy import deepcopy
from pathlib import Path

from process_as_code.cli import main
from process_as_code.diff import diff_markdown, semantic_diff
from process_as_code.impact import impact_analysis, impact_markdown
from process_as_code.io import load_process
from process_as_code.render import to_analysis_canvas
from process_as_code.validate import validate_process

ROOT = Path(__file__).parents[1]
EXAMPLE = ROOT / "examples/process-analysis/order-entry.process.yaml"


def test_process_analysis_example_and_canvas():
    data = load_process(EXAMPLE)
    result = validate_process(data)
    assert result.ok, result.errors

    html = to_analysis_canvas(data)
    assert "Process Analysis Canvas" in html
    assert "Save order as draft" in html
    assert "Check approval email" in html
    assert "Customer search takes 20 minutes" in html
    assert "Source of truth" in html
    assert "PT45M" in html


def test_cli_canvas_writes_standalone_html(tmp_path):
    output = tmp_path / "analysis.html"
    assert main(["canvas", str(EXAMPLE), "-o", str(output)]) == 0
    rendered = output.read_text(encoding="utf-8")
    assert rendered.startswith("<!doctype html>")
    assert "Actual execution" in rendered
    assert "Variants & exceptions" in rendered


def test_analysis_references_are_governed():
    data = load_process(EXAMPLE)
    broken = deepcopy(data)
    broken["analysis"]["variants"][0]["path"].append("missing_step")
    broken["analysis"]["pain_points"][0]["step"] = "missing_step"
    broken["analysis"]["pain_points"][0]["evidence"].append("missing_evidence")
    broken["analysis"]["data_flows"][0]["to"] = "missing_system"

    result = validate_process(broken)
    assert not result.ok
    errors = "\n".join(result.errors)
    assert "analysis variant 'high_value_order' references unknown step 'missing_step'" in errors
    assert "analysis pain point 'slow_customer_search' references unknown step 'missing_step'" in errors
    assert "analysis pain point 'slow_customer_search' references unknown evidence 'missing_evidence'" in errors
    assert "analysis data flow 'customer_po_to_s4' references unknown system 'missing_system'" in errors


def test_analysis_changes_flow_into_diff_impact_and_test_scope():
    old = load_process(EXAMPLE)
    new = deepcopy(old)
    new["analysis"]["pain_points"][0]["cause"] = "Customer search filters are incomplete"
    new["analysis"]["pain_points"][0]["evidence"] = ["observed_session_01"]
    new["analysis"]["variants"][0]["path"].append("check_customer")
    new["analysis"]["data_flows"][0]["data"].append("sales_org")

    diff = semantic_diff(old, new)
    assert "slow_customer_search" in diff["analysis"]["pain_points"]["changed"]
    assert "high_value_order" in diff["analysis"]["variants"]["changed"]
    assert "customer_po_to_s4" in diff["analysis"]["data_flows"]["changed"]
    rendered_diff = diff_markdown(diff)
    assert "## Process analysis" in rendered_diff
    assert "slow_customer_search" in rendered_diff

    impact = impact_analysis(old, new)
    assert impact["analysis_changes"]["pain_points"] == ["slow_customer_search"]
    assert "check_customer" in impact["analysis_affected_steps"]
    assert {"outlook", "s4"} <= set(impact["affected"]["systems"])
    assert "search_screen_01" in impact["affected"]["evidence"]
    assert any(test["id"] == "check_customer:happy-path" for test in impact["recommended_tests"])
    rendered_impact = impact_markdown(impact)
    assert "## Process analysis changes" in rendered_impact
    assert "Affected steps from analysis" in rendered_impact
