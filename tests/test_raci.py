from pathlib import Path

from process_as_code.io import load_process
from process_as_code.raci import extract_raci
from process_as_code.testgen import generate_test_scope

ROOT = Path(__file__).parents[1]
DATA = load_process(ROOT / "examples/customer-creation.yaml")


def test_raci_uses_step_actor_and_process_owner_defaults():
    rows = {row["step"]: row for row in extract_raci(DATA)}
    assert rows["request"]["responsible"] == "sales"
    assert rows["request"]["accountable"] == "data_governance_lead"


def test_test_scope_covers_branches_interfaces_and_controls():
    tests = generate_test_scope(DATA)
    ids = {test["id"] for test in tests}
    assert "approve:branch:approved" in ids
    assert "replicate:interface:mdg_to_s4" in ids
    assert "validate:control:duplicate_check" in ids
