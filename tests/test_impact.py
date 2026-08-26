from pathlib import Path

from process_as_code.impact import impact_analysis
from process_as_code.io import load_process

ROOT = Path(__file__).parents[1]


def test_impact_derives_enterprise_context_and_risk_flags():
    old = load_process(ROOT / "examples/customer-creation.yaml")
    new = load_process(ROOT / "examples/change-request-v2.yaml")
    result = impact_analysis(old, new)

    assert "approve" in result["changed_steps"]
    assert "mdg_to_s4" in result["affected"]["interfaces"]
    assert "duplicate_check" in result["affected"]["controls"]
    assert "integration-change" in result["risk_flags"]
    assert "control-change" in result["risk_flags"]
    assert "step-removal" in result["risk_flags"]
