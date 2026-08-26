from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = runpy.run_path(str(ROOT / "scripts/check_release.py"))
validate_release_tag = RELEASE["validate_release_tag"]


def test_release_tag_matches_package_and_runtime_versions() -> None:
    assert validate_release_tag(
        "v0.2.0",
        ROOT / "pyproject.toml",
        ROOT / "src/process_as_code/__init__.py",
    ) == []


def test_release_tag_mismatch_is_rejected() -> None:
    errors = validate_release_tag(
        "v0.2.1",
        ROOT / "pyproject.toml",
        ROOT / "src/process_as_code/__init__.py",
    )
    assert errors == ["release tag 'v0.2.1' does not match expected tag 'v0.2.0'"]


def test_runtime_version_mismatch_is_rejected(tmp_path: Path) -> None:
    runtime = tmp_path / "__init__.py"
    runtime.write_text('__version__ = "0.1.0"\n', encoding="utf-8")
    errors = validate_release_tag("v0.2.0", ROOT / "pyproject.toml", runtime)
    assert any("does not match pyproject version" in error for error in errors)


def test_release_workflow_preserves_privilege_separation_and_pins() -> None:
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    build = workflow.split("\n  attest:\n", 1)[0]
    attest_and_publish = workflow.split("\n  attest:\n", 1)[1]
    publish = workflow.split("\n  publish-pypi:\n", 1)[1]

    assert "python scripts/check_release.py" in build
    assert "pytest -q" in build
    assert "python -m twine check dist/*" in build
    assert "id-token: write" not in build
    assert "attestations: write" not in build

    assert "actions/attest@508db95dd578ae2727ebd6217d5ba78e4fbda05d" in attest_and_publish
    assert "attestations: write" in attest_and_publish
    assert "needs: [build, attest]" in publish
    assert "id-token: write" in publish
    assert "pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33" in publish
    assert "attestations: true" in publish
