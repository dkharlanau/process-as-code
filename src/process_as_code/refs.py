from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, BinaryIO

import yaml

MAX_NETWORK_ARTIFACT_BYTES = 5 * 1024 * 1024
_GITHUB_OWNER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
_GITHUB_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class ArtifactTooLarge(ValueError):
    """Raised when a remote artifact exceeds the bounded resolver payload."""


def _validate_github_uri(owner: str, repo: str, path: str, ref: str, uri: str) -> None:
    if not _GITHUB_OWNER_RE.fullmatch(owner):
        raise ValueError(f"invalid GitHub owner in artifact URI '{uri}'")
    if not _GITHUB_REPO_RE.fullmatch(repo) or repo in {".", ".."}:
        raise ValueError(f"invalid GitHub repository in artifact URI '{uri}'")
    path_parts = path.split("/")
    if not path or any(part in {"", ".", ".."} for part in path_parts):
        raise ValueError(f"invalid GitHub path in artifact URI '{uri}'")
    if any(ord(char) < 32 for char in path):
        raise ValueError(f"invalid GitHub path in artifact URI '{uri}'")
    if not ref or ref.startswith("/") or ref.endswith("/") or "//" in ref or ".." in ref:
        raise ValueError(f"invalid GitHub ref in artifact URI '{uri}'")
    if any(char in ref for char in "~^:?*[\\") or any(ord(char) < 32 for char in ref):
        raise ValueError(f"invalid GitHub ref in artifact URI '{uri}'")


def parse_artifact_uri(uri: str) -> dict[str, Any]:
    if uri.startswith("github://"):
        parsed = urllib.parse.urlparse(uri)
        owner = urllib.parse.unquote(parsed.netloc)
        decoded_path = urllib.parse.unquote(parsed.path).strip("/")
        parts = decoded_path.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"invalid github artifact URI '{uri}'")
        repo, path = parts
        query = urllib.parse.parse_qs(parsed.query)
        ref = query.get("ref", ["main"])[0]
        _validate_github_uri(owner, repo, path, ref, uri)
        return {
            "scheme": "github",
            "owner": owner,
            "repo": repo,
            "path": path,
            "ref": ref,
            "fragment": urllib.parse.unquote(parsed.fragment) or None,
        }
    raw = uri.removeprefix("file:")
    path_part, _, fragment = raw.partition("#")
    return {"scheme": "file", "path": urllib.parse.unquote(path_part), "fragment": urllib.parse.unquote(fragment) or None}


def _load_text(text: str, suffix: str) -> Any:
    return json.loads(text) if suffix.lower() == ".json" else yaml.safe_load(text)


def _json_pointer(data: Any, pointer: str) -> Any:
    current = data
    for raw in pointer.lstrip("/").split("/") if pointer else []:
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            return None
    return current


def _find_id(data: Any, item_id: str | None) -> Any:
    if not item_id:
        return data
    if item_id.startswith("/"):
        return _json_pointer(data, item_id)
    if isinstance(data, dict):
        if data.get("id") == item_id or data.get("$id") == item_id:
            return data
        for value in data.values():
            found = _find_id(value, item_id)
            if found is not None:
                return found
    elif isinstance(data, list):
        for value in data:
            found = _find_id(value, item_id)
            if found is not None:
                return found
    return None


def _safe_local_path(base_dir: str | Path, artifact_path: str) -> Path | None:
    base = Path(base_dir).resolve()
    candidate = Path(artifact_path)
    if candidate.is_absolute():
        return None
    resolved = (base / candidate).resolve()
    try:
        resolved.relative_to(base)
    except ValueError:
        return None
    return resolved


def _read_bounded(response: BinaryIO, max_bytes: int = MAX_NETWORK_ARTIFACT_BYTES) -> bytes:
    headers = getattr(response, "headers", None)
    if headers is not None:
        length = headers.get("Content-Length")
        if length:
            try:
                if int(length) > max_bytes:
                    raise ArtifactTooLarge(f"remote artifact exceeds {max_bytes} bytes")
            except ValueError as exc:
                if isinstance(exc, ArtifactTooLarge):
                    raise
    payload = response.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise ArtifactTooLarge(f"remote artifact exceeds {max_bytes} bytes")
    return payload


def _github_raw_url(parsed: dict[str, Any]) -> str:
    owner = urllib.parse.quote(str(parsed["owner"]), safe="-")
    repo = urllib.parse.quote(str(parsed["repo"]), safe="-._")
    ref = urllib.parse.quote(str(parsed["ref"]), safe="/-._")
    path = urllib.parse.quote(str(parsed["path"]), safe="/-._~")
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"


def resolve_uri(uri: str, base_dir: str | Path = ".", allow_network: bool = False) -> dict[str, Any]:
    try:
        parsed = parse_artifact_uri(uri)
        if parsed["scheme"] == "file":
            path = _safe_local_path(base_dir, parsed["path"])
            if path is None:
                return {"uri": uri, "status": "outside-base", "target": None}
            text = path.read_text(encoding="utf-8")
            data = _load_text(text, path.suffix)
            target = _find_id(data, parsed["fragment"])
            return {
                "uri": uri,
                "status": "resolved" if target is not None else "missing-fragment",
                "target": target,
                "source": str(path),
            }
        if not allow_network:
            return {"uri": uri, "status": "network-disabled", "target": None}
        raw_url = _github_raw_url(parsed)
        with urllib.request.urlopen(raw_url, timeout=10) as response:  # nosec B310 - host is fixed and URI fields are validated
            payload = _read_bounded(response)
        text = payload.decode("utf-8")
        data = _load_text(text, Path(parsed["path"]).suffix)
        target = _find_id(data, parsed["fragment"])
        return {
            "uri": uri,
            "status": "resolved" if target is not None else "missing-fragment",
            "target": target,
            "source": raw_url,
        }
    except ArtifactTooLarge as exc:
        return {"uri": uri, "status": "too-large", "error": str(exc), "target": None}
    except (OSError, UnicodeDecodeError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        return {"uri": uri, "status": "error", "error": str(exc), "target": None}


def resolve_artifacts(
    data: dict[str, Any],
    base_dir: str | Path = ".",
    allow_network: bool = False,
    max_depth: int = 4,
) -> list[dict[str, Any]]:
    artifacts = {
        artifact["id"]: artifact
        for artifact in data.get("artifacts", []) or []
        if isinstance(artifact, dict) and artifact.get("id") and artifact.get("uri")
    }
    results: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def walk(artifact: dict[str, Any], depth: int) -> None:
        aid = str(artifact["id"])
        uri = str(artifact["uri"])
        identity = (aid, uri)
        if identity in seen:
            return
        seen.add(identity)
        resolved = resolve_uri(uri, base_dir=base_dir, allow_network=allow_network)
        record = {"id": aid, "kind": artifact.get("kind"), "relation": artifact.get("relation"), **resolved}
        results.append(record)
        if depth >= max_depth or resolved.get("status") != "resolved":
            return
        target = resolved.get("target")
        if isinstance(target, dict):
            for nested in target.get("artifacts", []) or []:
                if isinstance(nested, dict) and nested.get("id") and nested.get("uri"):
                    walk(nested, depth + 1)

    for artifact in artifacts.values():
        walk(artifact, 0)
    return results
