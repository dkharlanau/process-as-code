from __future__ import annotations

import fnmatch
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from process_as_code.impact import impact_analysis, impact_markdown
from process_as_code.io import load_process
from process_as_code.policy import evaluate_policy, policy_markdown
from process_as_code.validate import validate_process

MARKER = "<!-- process-as-code-impact -->"


def git(*args: str, check: bool = True) -> str:
    return subprocess.run(["git", *args], check=check, text=True, capture_output=True).stdout.strip()


def event() -> dict:
    path = os.environ.get("GITHUB_EVENT_PATH")
    return json.loads(Path(path).read_text()) if path and Path(path).exists() else {}


def changed_files(base: str, head: str, pattern: str) -> list[str]:
    names = git("diff", "--name-only", f"{base}...{head}").splitlines()
    return sorted(name for name in names if fnmatch.fnmatch(name, pattern) or name.endswith((".process.yaml", ".process.yml", ".process.json")))


def old_file(base: str, path: str) -> Path | None:
    proc = subprocess.run(["git", "show", f"{base}:{path}"], text=True, capture_output=True)
    if proc.returncode != 0:
        return None
    handle = tempfile.NamedTemporaryFile("w", suffix=Path(path).suffix, delete=False, encoding="utf-8")
    handle.write(proc.stdout); handle.close()
    return Path(handle.name)


def upsert_comment(body: str, ev: dict) -> None:
    token = os.environ.get("PROCESS_GITHUB_TOKEN"); repo = os.environ.get("GITHUB_REPOSITORY"); pr = ev.get("pull_request", {}).get("number")
    if not token or not repo or not pr: return
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"}
    comments_url = f"https://api.github.com/repos/{repo}/issues/{pr}/comments"
    try:
        with urllib.request.urlopen(urllib.request.Request(comments_url, headers=headers), timeout=15) as response:
            comments = json.loads(response.read().decode())
        existing = next((c for c in comments if MARKER in c.get("body", "")), None)
        payload = json.dumps({"body": MARKER + "\n" + body}).encode()
        url = f"https://api.github.com/repos/{repo}/issues/comments/{existing['id']}" if existing else comments_url
        method = "PATCH" if existing else "POST"
        with urllib.request.urlopen(urllib.request.Request(url, data=payload, headers=headers, method=method), timeout=15): pass
    except Exception as exc:
        print(f"WARNING: could not publish PR comment: {exc}", file=sys.stderr)


def main() -> int:
    ev = event(); base = ev.get("pull_request", {}).get("base", {}).get("sha") or os.environ.get("GITHUB_BASE_SHA") or "HEAD^"; head = ev.get("pull_request", {}).get("head", {}).get("sha") or os.environ.get("GITHUB_SHA") or "HEAD"
    files = changed_files(base, head, os.environ.get("PROCESS_GLOB", "**/*.process.yaml"))
    report = ["# Process as Code — PR impact", ""]; machine = {"files": [], "failures": 0, "warnings": 0}; failures = 0; warnings = 0
    policy_path = os.environ.get("PROCESS_POLICY"); policy_config = load_process(policy_path) if policy_path and Path(policy_path).exists() else None
    if not files: report.append("No changed process contracts detected.")
    for file in files:
        path = Path(file)
        if not path.exists(): report += [f"## `{file}`", "", "Process contract was removed.", ""]; continue
        data = load_process(path); validation = validate_process(data); failures += len(validation.errors); warnings += len(validation.warnings)
        file_record = {"file": file, "validation": {"errors": validation.errors, "warnings": validation.warnings}}; machine["files"].append(file_record); report += [f"## `{file}`", ""]
        report += [f"- Validation error: {e}" for e in validation.errors] + [f"- Validation warning: {w}" for w in validation.warnings]
        old = old_file(base, file); old_data = load_process(old) if old else None
        if old_data and validation.ok:
            impact = impact_analysis(old_data, data, base_dir=path.parent); file_record["impact"] = impact; report += ["", impact_markdown(impact).replace("# Process change impact\n", "").strip(), ""]
        if policy_config and validation.ok:
            policy_result = evaluate_policy(data, policy_config, old_data); failures += len(policy_result.errors); warnings += len(policy_result.warnings); file_record["policy"] = {"ok": policy_result.ok, "errors": policy_result.errors, "warnings": policy_result.warnings}; report += ["", policy_markdown(policy_result).replace("# Process policy result\n", "").strip(), ""]
    body = "\n".join(report).rstrip() + "\n"; out = Path("process-impact-report.md"); out.write_text(body, encoding="utf-8"); machine["failures"] = failures; machine["warnings"] = warnings; Path("process-impact-report.json").write_text(json.dumps(machine, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = os.environ.get("GITHUB_STEP_SUMMARY"); output = os.environ.get("GITHUB_OUTPUT")
    if summary: Path(summary).write_text(body, encoding="utf-8")
    if output:
        with Path(output).open("a", encoding="utf-8") as fh: fh.write(f"report-file={out}\n")
    upsert_comment(body, ev)
    return 1 if failures or (warnings and os.environ.get("PROCESS_FAIL_ON_WARNING", "false").lower() == "true") else 0


if __name__ == "__main__":
    raise SystemExit(main())
