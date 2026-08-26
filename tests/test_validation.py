from pathlib import Path

from process_as_code.io import load_process
from process_as_code.validate import validate_process

ROOT = Path(__file__).parents[1]


def test_example_is_valid():
    result = validate_process(load_process(ROOT / "examples/customer-creation.yaml"))
    assert result.ok, result.errors
    assert not result.warnings


def test_unknown_target_is_rejected():
    data = {
        "version": "1.0",
        "process": {"id": "x", "name": "X"},
        "steps": [{"id": "a", "name": "A", "next": "missing"}],
    }
    result = validate_process(data)
    assert not result.ok
    assert any("unknown next step" in error for error in result.errors)


def test_unknown_role_is_rejected():
    data = {
        "version": "1.0",
        "process": {"id": "x", "name": "X"},
        "roles": [],
        "steps": [{"id": "a", "name": "A", "actor": "ghost"}],
    }
    result = validate_process(data)
    assert not result.ok
    assert any("unknown role" in error for error in result.errors)
