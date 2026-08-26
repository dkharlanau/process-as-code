from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .bpmn import to_bpmn
from .diff import diff_markdown, semantic_diff
from .io import dump_json, load_process
from .impact import impact_analysis, impact_markdown
from .raci import extract_raci, raci_markdown
from .render import to_markdown, to_mermaid
from .testgen import generate_test_scope, test_scope_markdown
from .validate import validate_process


def _write(text: str, output: str | None) -> None:
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="process-code", description="Git-native business process tooling")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate a process definition")
    validate.add_argument("file")
    validate.add_argument("--strict", action="store_true", help="treat warnings as failure")

    for name, help_text in (
        ("mermaid", "render Mermaid flowchart"),
        ("bpmn", "export BPMN 2.0 XML"),
        ("docs", "generate Markdown documentation"),
        ("raci", "extract RACI table"),
        ("test-scope", "generate test scope"),
    ):
        cmd = sub.add_parser(name, help=help_text)
        cmd.add_argument("file")
        cmd.add_argument("-o", "--output")
        if name in {"raci", "test-scope"}:
            cmd.add_argument("--json", action="store_true")

    diff = sub.add_parser("diff", help="semantic diff between two process versions")
    diff.add_argument("old")
    diff.add_argument("new")
    diff.add_argument("-o", "--output")
    diff.add_argument("--json", action="store_true")

    impact = sub.add_parser("impact", help="derive enterprise change impact between two process versions")
    impact.add_argument("old")
    impact.add_argument("new")
    impact.add_argument("-o", "--output")
    impact.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate":
        result = validate_process(load_process(args.file))
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        for error in result.errors:
            print(f"ERROR: {error}")
        if result.ok and not (args.strict and result.warnings):
            print("OK")
            return 0
        return 1

    if args.command == "diff":
        change = semantic_diff(load_process(args.old), load_process(args.new))
        _write(dump_json(change) if args.json else diff_markdown(change), args.output)
        return 0

    if args.command == "impact":
        impact = impact_analysis(load_process(args.old), load_process(args.new))
        _write(dump_json(impact) if args.json else impact_markdown(impact), args.output)
        return 0

    data = load_process(args.file)
    result = validate_process(data)
    if not result.ok:
        for error in result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.command == "mermaid":
        text = to_mermaid(data)
    elif args.command == "bpmn":
        text = to_bpmn(data)
    elif args.command == "docs":
        text = to_markdown(data)
    elif args.command == "raci":
        text = dump_json(extract_raci(data)) if args.json else raci_markdown(data)
    elif args.command == "test-scope":
        text = dump_json(generate_test_scope(data)) if args.json else test_scope_markdown(data)
    else:
        raise AssertionError(args.command)
    _write(text, args.output)
    return 0
