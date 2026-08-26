from __future__ import annotations

import io
from pathlib import Path

import pytest

from process_as_code.refs import (
    ArtifactTooLarge,
    _read_bounded,
    parse_artifact_uri,
    resolve_uri,
)


def test_valid_local_reference_resolves_inside_base(tmp_path: Path) -> None:
    base = tmp_path / "workspace"
    base.mkdir()
    (base / "artifact.yaml").write_text("id: customer_mapping\nname: Customer mapping\n", encoding="utf-8")

    result = resolve_uri("file:artifact.yaml#customer_mapping", base_dir=base)

    assert result["status"] == "resolved"
    assert result["target"]["id"] == "customer_mapping"
    assert Path(result["source"]).is_relative_to(base.resolve())


def test_parent_traversal_is_rejected(tmp_path: Path) -> None:
    base = tmp_path / "workspace"
    base.mkdir()
    (tmp_path / "secret.yaml").write_text("secret: value\n", encoding="utf-8")

    result = resolve_uri("file:../secret.yaml", base_dir=base)

    assert result == {"uri": "file:../secret.yaml", "status": "outside-base", "target": None}


def test_absolute_local_path_is_rejected(tmp_path: Path) -> None:
    base = tmp_path / "workspace"
    base.mkdir()
    secret = tmp_path / "secret.yaml"
    secret.write_text("secret: value\n", encoding="utf-8")

    result = resolve_uri(f"file:{secret}", base_dir=base)

    assert result["status"] == "outside-base"
    assert "source" not in result


def test_symlink_escape_is_rejected(tmp_path: Path) -> None:
    base = tmp_path / "workspace"
    base.mkdir()
    secret = tmp_path / "secret.yaml"
    secret.write_text("secret: value\n", encoding="utf-8")
    link = base / "link.yaml"
    try:
        link.symlink_to(secret)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable in this environment")

    result = resolve_uri("file:link.yaml", base_dir=base)

    assert result["status"] == "outside-base"


def test_github_network_is_opt_in_and_host_is_not_user_controlled() -> None:
    result = resolve_uri("github://octocat/hello-world/README.md?ref=main")
    assert result["status"] == "network-disabled"


def test_malformed_github_components_are_rejected_before_request() -> None:
    with pytest.raises(ValueError):
        parse_artifact_uri("github://bad%20owner/repo/file.yaml?ref=main")
    with pytest.raises(ValueError):
        parse_artifact_uri("github://owner/repo/%2e%2e/secret.yaml?ref=main")
    with pytest.raises(ValueError):
        parse_artifact_uri("github://owner/repo/file.yaml?ref=main..evil")


def test_remote_payload_is_bounded() -> None:
    with pytest.raises(ArtifactTooLarge):
        _read_bounded(io.BytesIO(b"x" * 11), max_bytes=10)
