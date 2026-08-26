from pathlib import Path

from process_as_code.bpmn import to_bpmn
from process_as_code.io import load_process
from process_as_code.render import to_markdown, to_mermaid

ROOT = Path(__file__).parents[1]
DATA = load_process(ROOT / "examples/customer-creation.yaml")


def test_mermaid_contains_decision_branch():
    text = to_mermaid(DATA)
    assert 'approve{"Approve customer"}' in text
    assert 'approve -->|"approved"| replicate' in text


def test_markdown_contains_flow_and_steps():
    text = to_markdown(DATA)
    assert "## Flow" in text
    assert "## Steps" in text
    assert "MDG to S/4 replication" in text


def test_bpmn_contains_gateway_and_flows():
    text = to_bpmn(DATA)
    assert "exclusiveGateway" in text
    assert 'name="approved"' in text
    assert "sequenceFlow" in text
