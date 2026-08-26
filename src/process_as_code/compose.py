from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .refs import resolve_uri

CATALOG_SECTIONS = ("roles", "systems", "objects", "interfaces", "controls", "risks", "evidence", "artifacts")


def compose_catalogs(data: dict[str, Any], base_dir: str | Path = ".") -> tuple[dict[str, Any], list[str]]:
    composed = deepcopy(data)
    errors: list[str] = []
    for catalog in data.get("catalogs", []) or []:
        if not isinstance(catalog, dict) or not catalog.get("uri"):
            errors.append("catalog entry requires uri")
            continue
        resolved = resolve_uri(str(catalog["uri"]), base_dir=base_dir)
        if resolved.get("status") != "resolved" or not isinstance(resolved.get("target"), dict):
            errors.append(f"cannot resolve catalog '{catalog.get('uri')}': {resolved.get('status')}")
            continue
        source = resolved["target"]
        include = catalog.get("include") or CATALOG_SECTIONS
        for section in include:
            if section not in CATALOG_SECTIONS:
                errors.append(f"unsupported catalog section '{section}'")
                continue
            existing = {i.get("id") for i in composed.get(section, []) or [] if isinstance(i, dict)}
            for item in source.get(section, []) or []:
                if not isinstance(item, dict) or not item.get("id"):
                    continue
                if item["id"] in existing:
                    local = next((i for i in composed.get(section, []) or [] if isinstance(i, dict) and i.get("id") == item["id"]), None)
                    if local != item:
                        errors.append(f"catalog conflict for {section} id '{item['id']}'")
                    continue
                composed.setdefault(section, []).append(deepcopy(item)); existing.add(item["id"])
    return composed, errors


def validate_composition(data: dict[str, Any], base_dir: str | Path = ".") -> list[str]:
    errors: list[str] = []
    seen: set[Path] = set()

    def walk(process: dict[str, Any], directory: Path, chain: list[str]) -> None:
        composed, catalog_errors = compose_catalogs(process, directory)
        errors.extend(catalog_errors)
        for step in composed.get("steps", []) or []:
            if not isinstance(step, dict) or step.get("type") != "subprocess":
                continue
            ref = step.get("process_ref")
            if not isinstance(ref, str):
                errors.append(f"subprocess step '{step.get('id')}' requires process_ref")
                continue
            parsed = ref.removeprefix("file:").split("#", 1)[0]
            path = (directory / parsed).resolve()
            if path in seen or str(path) in chain:
                errors.append(f"cyclic subprocess reference detected at '{path.name}'")
                continue
            resolved = resolve_uri(ref, directory)
            target = resolved.get("target")
            if resolved.get("status") != "resolved" or not isinstance(target, dict) or not isinstance(target.get("process"), dict):
                errors.append(f"cannot resolve subprocess '{ref}' from step '{step.get('id')}'")
                continue
            seen.add(path)
            walk(target, path.parent, chain + [str(path)])

    walk(data, Path(base_dir).resolve(), [])
    return errors


def composition_dependencies(data: dict[str, Any]) -> list[str]:
    return sorted({step["process_ref"] for step in data.get("steps", []) or [] if isinstance(step, dict) and isinstance(step.get("process_ref"), str)})
