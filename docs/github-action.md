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
        with:
          fetch-depth: 0
      - uses: dkharlanau/process-as-code@main
        with:
          process-glob: "**/*.process.yaml"
          policy-file: process-policy.yaml
          github-token: ${{ github.token }}
```

The action writes `process-impact-report.md` and `process-impact-report.json`, publishes the Markdown to `$GITHUB_STEP_SUMMARY`, and updates one marker-based PR comment when a token is supplied. Validation or blocking policy failures return a non-zero exit code.

The consumer workflow must use a full history or otherwise make the PR base commit available for semantic comparison.
