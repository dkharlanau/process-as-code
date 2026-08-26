# GitHub Action — PR Impact Gate

The repository root is a composite GitHub Action. It installs the checked-out action package and runs `scripts/pr_impact.py` in the caller repository.

## Consumer workflow

```yaml
name: Process contract review
on: [pull_request]
permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  process-impact:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: dkharlanau/process-as-code@main
        with:
          process-glob: "**/*.process.yaml"
          policy-file: process-policy.yaml
          github-token: ${{ github.token }}
```

The default shallow checkout is supported. On pull requests the Action reads the exact base/head SHAs from the GitHub event and fetches missing commit objects itself, so consumers do not need `fetch-depth: 0` merely for semantic comparison.

The Action writes `process-impact-report.md` and `process-impact-report.json`, publishes the Markdown to `$GITHUB_STEP_SUMMARY`, and updates one marker-based PR comment when a token is supplied. Validation or blocking policy failures return a non-zero exit code.

## Permissions

- `contents: read` is sufficient for validation/diff/impact output.
- Add `issues: write` and `pull-requests: write`, and pass `github-token: ${{ github.token }}`, to publish/update the PR comment.
- Fork pull requests normally receive a read-only token. In that case comment publication is skipped with a warning while validation and generated reports still run.

Removed `*.process.*` files are retained in `process-impact-report.json` with `status: removed` and a `process-removal` risk flag so downstream automation can distinguish deletion from an unchanged repository.
