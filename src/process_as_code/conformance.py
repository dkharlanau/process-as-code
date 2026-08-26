from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .io import load_process
from .validate import validate_process


def run_conformance(root: str | Path) -> dict[str, Any]:
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    results = []
    for case in manifest.get("cases", []):
        path = root / case["file"]
        validation = validate_process(load_process(path))
        expected_ok = bool(case["expected_ok"])
        matched = validation.ok == expected_ok
        for needle in case.get("error_contains", []):
            matched = matched and any(needle in error for error in validation.errors)
        for needle in case.get("warning_contains", []):
            matched = matched and any(needle in warning for warning in validation.warnings)
        results.append({"id": case["id"], "file": case["file"], "ok": matched, "actual_valid": validation.ok, "errors": validation.errors, "warnings": validation.warnings})
    return {"spec_version": manifest.get("spec_version"), "ok": all(r["ok"] for r in results), "results": results}
