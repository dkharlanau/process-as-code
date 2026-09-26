from pathlib import Path

from process_as_code.cli import main
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
