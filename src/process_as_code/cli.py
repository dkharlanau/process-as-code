from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .bpmn import import_bpmn, to_bpmn
from .compose import compose_catalogs, validate_composition
from .catalog import generate_catalog
from .conformance import run_conformance
from .diff import diff_markdown, semantic_diff, visual_diff_mermaid
from .impact import impact_analysis, impact_markdown
from .io import dump_json, dump_yaml, load_process
from .migrate import migrate_process
from .policy import evaluate_policy, policy_markdown
from .process_tests import affected_process_tests, run_process_tests
from .raci import extract_raci, raci_markdown
from .refs import resolve_artifacts
from .render import to_markdown, to_mermaid
from .testgen import generate_test_scope, test_scope_markdown
from .validate import validate_process


def _write(text: str, output: str | None) -> None:
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="process-code", description="Open process contracts for Git, CI, enterprise change, and AI")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate a process definition")
    validate.add_argument("file"); validate.add_argument("--strict", action="store_true")

    for name, help_text in (("mermaid", "render Mermaid flowchart"), ("bpmn", "export BPMN 2.0 XML"), ("docs", "generate Markdown documentation"), ("raci", "extract RACI table"), ("test-scope", "generate test scope"), ("resolve", "resolve linked external artifacts")):
        cmd = sub.add_parser(name, help=help_text); cmd.add_argument("file"); cmd.add_argument("-o", "--output")
        if name in {"raci", "test-scope", "resolve"}: cmd.add_argument("--json", action="store_true")
        if name == "resolve":
            cmd.add_argument("--base-dir"); cmd.add_argument("--allow-network", action="store_true")

    diff = sub.add_parser("diff", help="semantic diff between two process versions")
    diff.add_argument("old"); diff.add_argument("new"); diff.add_argument("-o", "--output"); diff.add_argument("--json", action="store_true")
    diff_visual = sub.add_parser("diff-visual", help="render semantic process diff as Mermaid")
    diff_visual.add_argument("old"); diff_visual.add_argument("new"); diff_visual.add_argument("-o", "--output")

    impact = sub.add_parser("impact", help="derive enterprise change impact between two process versions")
    impact.add_argument("old"); impact.add_argument("new"); impact.add_argument("-o", "--output"); impact.add_argument("--json", action="store_true")
    impact.add_argument("--resolve-external", action="store_true"); impact.add_argument("--allow-network", action="store_true"); impact.add_argument("--base-dir")

    migrate = sub.add_parser("migrate", help="migrate a process contract to schema v0.2")
    migrate.add_argument("file"); migrate.add_argument("-o", "--output"); migrate.add_argument("--json", action="store_true")

    bpmn_import = sub.add_parser("bpmn-import", help="import the supported BPMN 2.0 subset")
    bpmn_import.add_argument("file"); bpmn_import.add_argument("-o", "--output"); bpmn_import.add_argument("--json", action="store_true"); bpmn_import.add_argument("--report")

    policy = sub.add_parser("policy", help="evaluate governance policy gates")
    policy.add_argument("file"); policy.add_argument("--policy", required=True); policy.add_argument("--old"); policy.add_argument("--json", action="store_true"); policy.add_argument("-o", "--output")

    tests = sub.add_parser("test", help="run deterministic Process Test DSL assertions")
    tests.add_argument("file"); tests.add_argument("suite"); tests.add_argument("--old"); tests.add_argument("--json", action="store_true")

    conformance = sub.add_parser("conformance", help="run the public specification conformance suite")
    conformance.add_argument("root"); conformance.add_argument("--json", action="store_true")

    catalog = sub.add_parser("catalog", help="generate a searchable static Process Catalog")
    catalog.add_argument("root"); catalog.add_argument("-o", "--output", required=True); catalog.add_argument("--base-url")

    compose = sub.add_parser("compose", help="resolve reusable catalogs and validate subprocess composition")
    compose.add_argument("file"); compose.add_argument("-o", "--output"); compose.add_argument("--json", action="store_true")

    mcp = sub.add_parser("mcp", help="run the optional MCP stdio server")
    mcp.add_argument("--root", default=".")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            result = validate_process(load_process(args.file))
            for warning in result.warnings: print(f"WARNING: {warning}")
            for error in result.errors: print(f"ERROR: {error}")
            if result.ok and not (args.strict and result.warnings): print("OK"); return 0
            return 1

        if args.command == "diff":
            change = semantic_diff(load_process(args.old), load_process(args.new)); _write(dump_json(change) if args.json else diff_markdown(change), args.output); return 0
        if args.command == "diff-visual":
            _write(visual_diff_mermaid(load_process(args.old), load_process(args.new)), args.output); return 0
        if args.command == "impact":
            new_path = Path(args.new)
            result = impact_analysis(load_process(args.old), load_process(args.new), base_dir=args.base_dir or new_path.parent, resolve_external=args.resolve_external, allow_network=args.allow_network)
            _write(dump_json(result) if args.json else impact_markdown(result), args.output); return 0
        if args.command == "migrate":
            migrated = migrate_process(load_process(args.file)); _write(dump_json(migrated) if args.json else dump_yaml(migrated), args.output); return 0
        if args.command == "bpmn-import":
            data, report = import_bpmn(args.file); _write(dump_json(data) if args.json else dump_yaml(data), args.output)
            if args.report: Path(args.report).write_text(dump_json(report) if args.report.endswith(".json") else "# BPMN compatibility report\n\n" + "\n".join([*(f"- Warning: {w}" for w in report["warnings"]), *(f"- Unsupported: `{u}`" for u in report["unsupported"])] ) + "\n", encoding="utf-8")
            return 0
        if args.command == "policy":
            result = evaluate_policy(load_process(args.file), load_process(args.policy), load_process(args.old) if args.old else None)
            _write(dump_json({"ok": result.ok, "errors": result.errors, "warnings": result.warnings}) if args.json else policy_markdown(result), args.output); return 0 if result.ok else 1
        if args.command == "test":
            process = load_process(args.file); suite = load_process(args.suite); results = run_process_tests(process, suite)
            payload = {"ok": all(r["ok"] for r in results), "results": results}
            if args.old: payload["affected_tests"] = affected_process_tests(load_process(args.old), process, suite)
            if args.json: sys.stdout.write(dump_json(payload))
            else:
                for result in results: print(("PASS" if result["ok"] else "FAIL") + f" {result['id']}" + (": " + "; ".join(result["failures"]) if result["failures"] else ""))
                if args.old: print("Affected: " + ", ".join(payload.get("affected_tests", [])))
            return 0 if payload["ok"] else 1
        if args.command == "conformance":
            result = run_conformance(args.root)
            if args.json: print(dump_json(result), end="")
            else:
                for case in result["results"]: print(("PASS" if case["ok"] else "FAIL") + " " + case["id"])
            return 0 if result["ok"] else 1
        if args.command == "catalog":
            manifest = generate_catalog(args.root, args.output, args.base_url); print(dump_json(manifest), end=""); return 0
        if args.command == "compose":
            source = load_process(args.file); composed, errors = compose_catalogs(source, Path(args.file).parent); errors.extend(validate_composition(source, Path(args.file).parent))
            if errors:
                for error in sorted(set(errors)): print(f"ERROR: {error}", file=sys.stderr)
                return 1
            _write(dump_json(composed) if args.json else dump_yaml(composed), args.output); return 0
        if args.command == "mcp":
            from .mcp_server import create_server
            create_server(args.root).run(); return 0

        data = load_process(args.file)
        validation = validate_process(data)
        if not validation.ok:
            for error in validation.errors: print(f"ERROR: {error}", file=sys.stderr)
            return 1
        if args.command == "mermaid": text = to_mermaid(data)
        elif args.command == "bpmn": text = to_bpmn(data)
        elif args.command == "docs": text = to_markdown(data)
        elif args.command == "raci": text = dump_json(extract_raci(data)) if args.json else raci_markdown(data)
        elif args.command == "test-scope": text = dump_json(generate_test_scope(data)) if args.json else test_scope_markdown(data)
        elif args.command == "resolve":
            resolved = resolve_artifacts(data, base_dir=args.base_dir or Path(args.file).parent, allow_network=args.allow_network)
            text = dump_json(resolved) if args.json else "\n".join(f"{r['id']}: {r['status']} {r.get('source','')}" for r in resolved) + "\n"
        else: raise AssertionError(args.command)
        _write(text, args.output); return 0
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr); return 2
