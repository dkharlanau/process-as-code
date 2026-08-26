from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .cli import build_parser, main as cli_main
from .schema import schema_text


def _schema_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="process-code schema", description="Print the bundled Process as Code JSON Schema")
    parser.add_argument("-o", "--output", help="write schema to a file instead of stdout")
    return parser


def _print_root_help() -> int:
    parser = build_parser()
    sub_actions = [action for action in parser._actions if isinstance(action, argparse._SubParsersAction)]
    if sub_actions and "schema" not in sub_actions[0].choices:
        cmd = sub_actions[0].add_parser("schema", help="print the bundled Process as Code JSON Schema")
        cmd.add_argument("-o", "--output")
    parser.print_help()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"}:
        return _print_root_help()
    if args[0] == "schema":
        parsed = _schema_parser().parse_args(args[1:])
        text = schema_text()
        if parsed.output:
            Path(parsed.output).write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return 0
    return cli_main(args)
