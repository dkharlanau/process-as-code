from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import yaml


def parse_artifact_uri(uri: str) -> dict[str, Any]:
    if uri.startswith("github://"):
        parsed = urllib.parse.urlparse(uri)
        owner = parsed.netloc
        parts = parsed.path.strip("/").split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"invalid github artifact URI '{uri}'")
        repo, path = parts
        query = urllib.parse.parse_qs(parsed.query)
        return {"scheme": "github", "owner": owner, "repo": repo, "path": path, "ref": query.get("ref", ["main"])[0], "fragment": parsed.fragment or None}
    raw = uri.removeprefix("file:")
    path_part, _, fragment = raw.partition("#")
    return {"scheme": "file", "path": path_part, "fragment": fragment or None}


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


def resolve_uri(uri: str, base_dir: str | Path = ".", allow_network: bool = False) -> dict[str, Any]:
    parsed = parse_artifact_uri(uri)
    try:
        if parsed["scheme"] == "file":
            path = (Path(base_dir) / parsed["path"]).resolve()
            text = path.read_text(encoding="utf-8")
            data = _load_text(text, path.suffix)
            target = _find_id(data, parsed["fragment"])
            return {"uri": uri, "status": "resolved" if target is not None else "missing-fragment", "target": target, "source": str(path)}
        if not allow_network:
            return {"uri": uri, "status": "network-disabled", "target": None}
        raw_url = f"https://raw.githubusercontent.com/{parsed['owner']}/{parsed['repo']}/{parsed['ref']}/{parsed['path']}"
        with urllib.request.urlopen(raw_url, timeout=10) as response:  # nosec - explicit user-authored artifact URI
            text = response.read().decode("utf-8")
        data = _load_text(text, Path(parsed["path"]).suffix)
        target = _find_id(data, parsed["fragment"])
        return {"uri": uri, "status": "resolved" if target is not None else "missing-fragment", "target": target, "source": raw_url}
    except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        return {"uri": uri, "status": "error", "error": str(exc), "target": None}


def resolve_artifacts(data: dict[str, Any], base_dir: str | Path = ".", allow_network: bool = False, max_depth: int = 4) -> list[dict[str, Any]]:
    artifacts = {a["id"]: a for a in data.get("artifacts", []) or [] if isinstance(a, dict) and a.get("id") and a.get("uri")}
    results: list[dict[str, Any]] = []
    seen: set[str] = set()

    def walk(artifact: dict[str, Any], depth: int) -> None:
        aid = artifact["id"]
        if aid in seen:
            return
        seen.add(aid)
        resolved = resolve_uri(str(artifact["uri"]), base_dir=base_dir, allow_network=allow_network)
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
