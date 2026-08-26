from pathlib import Path
from process_as_code.mcp_server import ProcessRepository

ROOT = Path(__file__).parents[1]


def test_mcp_repository_exposes_validated_context():
    repo = ProcessRepository(ROOT / "examples")
    ids = {item["id"] for item in repo.list_processes()}
    assert "customer_creation" in ids
    step = repo.get_step("customer_creation", "approve")
    assert "sanctions_check" in step.get("controls", [])
    assert {t["to"] for t in repo.allowed_transitions("customer_creation", "approve")} == {"replicate", "rejected"}
