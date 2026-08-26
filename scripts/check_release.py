from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path

_PROJECT_SECTION = re.compile(r"(?ms)^\[project\]\s*(.*?)(?=^\[|\Z)")
_VERSION_LINE = re.compile(r'(?m)^version\s*=\s*"([^"]+)"\s*$')


def pyproject_version(path: str | Path = "pyproject.toml") -> str:
    text = Path(path).read_text(encoding="utf-8")
    section = _PROJECT_SECTION.search(text)
    if not section:
        raise ValueError("pyproject.toml has no [project] section")
    match = _VERSION_LINE.search(section.group(1))
    if not match:
        raise ValueError("pyproject.toml [project] has no literal version")
    return match.group(1)


def runtime_version(path: str | Path = "src/process_as_code/__init__.py") -> str:
    tree = ast.parse(Path(path).read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(isinstance(target, ast.Name) and target.id == "__version__" for target in targets):
            value = node.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                return value.value
            raise ValueError("__version__ must be a literal string")
    raise ValueError("runtime __version__ is missing")


def validate_release_tag(
    tag: str,
    pyproject_path: str | Path = "pyproject.toml",
    runtime_path: str | Path = "src/process_as_code/__init__.py",
) -> list[str]:
    package_version = pyproject_version(pyproject_path)
    code_version = runtime_version(runtime_path)
    errors: list[str] = []
    if code_version != package_version:
        errors.append(f"runtime __version__ '{code_version}' does not match pyproject version '{package_version}'")
    expected_tag = f"v{package_version}"
    if tag != expected_tag:
        errors.append(f"release tag '{tag}' does not match expected tag '{expected_tag}'")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Process as Code release tag/version parity")
    parser.add_argument("tag", help="GitHub release tag, for example v0.2.0")
    parser.add_argument("--pyproject", default="pyproject.toml")
    parser.add_argument("--runtime", default="src/process_as_code/__init__.py")
    args = parser.parse_args(argv)

    try:
        errors = validate_release_tag(args.tag, args.pyproject, args.runtime)
    except (OSError, SyntaxError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK release {args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
