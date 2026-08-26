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
ZERO_SHA = "0" * 40


def git(*args: str, check: bool = True) -> str:
    return subprocess.run(["git", *args], check=check, text=True, capture_output=True).stdout.strip()


def event() -> dict:
    path = os.environ.get("GITHUB_EVENT_PATH")
    return json.loads(Path(path).read_text()) if path and Path(path).exists() else {}


def _has_commit(ref: str) -> bool:
    if not ref:
        return False
    return subprocess.run(
        ["git", "cat-file", "-e", f"{ref}^{{commit}}"],
        text=True,
        capture_output=True,
    ).returncode == 0


def _fetch_commit(ref: str) -> None:
    """Ensure a commit is available even when actions/checkout used fetch-depth: 1."""
    if not ref or _has_commit(ref):
        return
    proc = subprocess.run(
        ["git", "fetch", "--no-tags", "--depth=1", "origin", ref],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0 or not _has_commit(ref):
        detail = proc.stderr.strip() or proc.stdout.strip() or "unknown git fetch error"
        raise RuntimeError(f"could not fetch comparison commit {ref}: {detail}")


def compare_refs(ev: dict) -> tuple[str, str]:
    pull = ev.get("pull_request", {}) if isinstance(ev, dict) else {}
    if isinstance(pull, dict) and pull:
        base = pull.get("base", {}).get("sha")
        head = pull.get("head", {}).get("sha")
    else:
        before = ev.get("before") if isinstance(ev, dict) else None
        after = ev.get("after") if isinstance(ev, dict) else None
        base = before if before and before != ZERO_SHA else os.environ.get("GITHUB_BASE_SHA")
        head = after or os.environ.get("GITHUB_SHA") or "HEAD"

    if not head:
        head = "HEAD"
    _fetch_commit(head)

    if not base:
        # Non-GitHub/local invocation fallback. Deepen only enough to resolve HEAD^.
        if subprocess.run(["git", "rev-parse", "--verify", "HEAD^"], text=True, capture_output=True).returncode != 0:
            subprocess.run(["git", "fetch", "--no-tags", "--deepen=2", "origin"], check=False, text=True, capture_output=True)
        base = git("rev-parse", "HEAD^")
    _fetch_commit(base)
    return base, head


def changed_files(base: str, head: str, pattern: str) -> list[str]:
    # Comparing the two trees does not require their merge base to be present, which is
    # important for shallow PR checkouts where only the exact base/head objects are fetched.
    names = git("diff", "--name-only", base, head).splitlines()
    return sorted(
        name
        for name in names
        if fnmatch.fnmatch(name, pattern) or name.endswith((".process.yaml", ".process.yml", ".process.json"))
    )


def old_file(base: str, path: str) -> Path | None:
    proc = subprocess.run(["git", "show", f"{base}:{path}"], text=True, capture_output=True)
    if proc.returncode != 0:
        return None
    handle = tempfile.NamedTemporaryFile("w", suffix=Path(path).suffix, delete=False, encoding="utf-8")
    handle.write(proc.stdout)
    handle.close()
    return Path(handle.name)


def upsert_comment(body: str, ev: dict) -> None:
    token = os.environ.get("PROCESS_GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    pr = ev.get("pull_request", {}).get("number")
    if not token or not repo or not pr:
        return
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }
    comments_url = f"https://api.github.com/repos/{repo}/issues/{pr}/comments"
    try:
        with urllib.request.urlopen(urllib.request.Request(comments_url, headers=headers), timeout=15) as response:
            comments = json.loads(response.read().decode())
        existing = next((c for c in comments if MARKER in c.get("body", "")), None)
        payload = json.dumps({"body": MARKER + "\n" + body}).encode()
        url = f"https://api.github.com/repos/{repo}/issues/comments/{existing['id']}" if existing else comments_url
        method = "PATCH" if existing else "POST"
        with urllib.request.urlopen(urllib.request.Request(url, data=payload, headers=headers, method=method), timeout=15):
            pass
    except Exception as exc:
        # Comment publication is presentation, not validation. Keep the gate result usable
        # for fork PRs/read-only tokens while surfacing the permission problem clearly.
        print(f"WARNING: could not publish PR comment: {exc}", file=sys.stderr)


def main() -> int:
    ev = event()
    try:
        base, head = compare_refs(ev)
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: cannot resolve comparison refs: {exc}", file=sys.stderr)
        return 1

    files = changed_files(base, head, os.environ.get("PROCESS_GLOB", "**/*.process.yaml"))
    report = ["# Process as Code — PR impact", ""]
    machine = {"base": base, "head": head, "files": [], "failures": 0, "warnings": 0}
    failures = 0
    warnings = 0
    policy_path = os.environ.get("PROCESS_POLICY")
    policy_config = load_process(policy_path) if policy_path and Path(policy_path).exists() else None

    if not files:
        report.append("No changed process contracts detected.")

    for file in files:
        path = Path(file)
        if not path.exists():
            old = old_file(base, file)
            old_data = load_process(old) if old else None
            removed = {
                "file": file,
                "status": "removed",
                "validation": {"errors": [], "warnings": []},
                "risk_flags": ["process-removal"],
            }
            if old_data:
                meta = old_data.get("process", {})
                removed["removed_process"] = {"id": meta.get("id"), "name": meta.get("name")}
            machine["files"].append(removed)
            report += [f"## `{file}`", "", "- Status: **removed**", "- Risk flag: `process-removal`", ""]
            continue

        data = load_process(path)
        validation = validate_process(data)
        failures += len(validation.errors)
        warnings += len(validation.warnings)
        file_record = {
            "file": file,
            "status": "added-or-modified",
            "validation": {"errors": validation.errors, "warnings": validation.warnings},
        }
        machine["files"].append(file_record)
        report += [f"## `{file}`", ""]
        report += [f"- Validation error: {e}" for e in validation.errors]
        report += [f"- Validation warning: {w}" for w in validation.warnings]

        old = old_file(base, file)
        old_data = load_process(old) if old else None
        if old_data and validation.ok:
            impact = impact_analysis(old_data, data, base_dir=path.parent)
            file_record["impact"] = impact
            report += ["", impact_markdown(impact).replace("# Process change impact\n", "").strip(), ""]
        elif not old_data:
            file_record["change"] = "added"
            report += ["- Change: new process contract", ""]

        if policy_config and validation.ok:
            policy_result = evaluate_policy(data, policy_config, old_data)
            failures += len(policy_result.errors)
            warnings += len(policy_result.warnings)
            file_record["policy"] = {
                "ok": policy_result.ok,
                "errors": policy_result.errors,
                "warnings": policy_result.warnings,
            }
            report += ["", policy_markdown(policy_result).replace("# Process policy result\n", "").strip(), ""]

    body = "\n".join(report).rstrip() + "\n"
    out = Path("process-impact-report.md")
    out.write_text(body, encoding="utf-8")
    machine["failures"] = failures
    machine["warnings"] = warnings
    Path("process-impact-report.json").write_text(json.dumps(machine, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    output = os.environ.get("GITHUB_OUTPUT")
    if summary:
        Path(summary).write_text(body, encoding="utf-8")
    if output:
        with Path(output).open("a", encoding="utf-8") as fh:
            fh.write(f"report-file={out}\n")

    upsert_comment(body, ev)
    return 1 if failures or (warnings and os.environ.get("PROCESS_FAIL_ON_WARNING", "false").lower() == "true") else 0


if __name__ == "__main__":
    raise SystemExit(main())
