# Releasing Process as Code

The release path is designed around two independent provenance mechanisms:

1. GitHub build provenance created with `actions/attest` for the built wheel and source distribution.
2. PyPI PEP 740 attestations generated automatically by the official PyPI publishing Action when Trusted Publishing is used.

The build and publish trust boundaries are intentionally separate.

## One-time PyPI setup

Before the first release, configure a PyPI Trusted Publisher with:

- Owner: `dkharlanau`
- Repository: `process-as-code`
- Workflow: `release.yml`
- Environment: `pypi`

No PyPI API token should be added to GitHub Secrets. The publish job receives only `id-token: write` and uses OIDC.

## Release version gate

The GitHub release tag must exactly match the package version:

```text
pyproject.toml version = 0.2.0
runtime __version__   = 0.2.0
release tag           = v0.2.0
```

The workflow runs:

```bash
python scripts/check_release.py v0.2.0
```

A mismatch blocks the release before build provenance or PyPI credentials are requested.

## Release workflow

When a GitHub release is published, `.github/workflows/release.yml` performs:

```text
build (contents: read only)
  -> version/tag gate
  -> pytest + conformance
  -> wheel/sdist build
  -> twine metadata check
  -> workflow artifact

attest (contents: read + id-token + attestations)
  -> download exact prebuilt distributions
  -> GitHub build provenance

publish-pypi (id-token only)
  -> download the same prebuilt distributions
  -> PyPI Trusted Publishing
  -> PyPI PEP 740 publish attestations
```

Build/test code never runs in the PyPI publishing job.

## Verify GitHub provenance

After downloading a released distribution, verify its GitHub build provenance with GitHub CLI:

```bash
gh attestation verify process_as_code-0.2.0-py3-none-any.whl \
  -R dkharlanau/process-as-code
```

PyPI exposes the publish attestations attached to distributions uploaded through Trusted Publishing.

## GitHub release assets and immutability

The Python wheel/sdist are canonically distributed through PyPI. The release workflow stores them as a workflow artifact and attests them on GitHub; it does not mutate an already-published GitHub release to attach files.

This is intentional because GitHub immutable releases prevent release assets from being modified after publication. If immutable releases are enabled, GitHub recommends preparing a draft release, attaching any desired release assets, and only then publishing it.

For the initial `v0.2.0`, GitHub's source archives plus the PyPI distributions are sufficient. If duplicate wheel/sdist assets are desired on the GitHub Release page, attach them to the draft before publishing rather than weakening release immutability.

## GitHub Marketplace

The repository root contains `action.yml`. When publishing `v0.2.0`, select **Publish this Action to the GitHub Marketplace** on the release screen after accepting the Marketplace Developer Agreement if required.

Consumers should then reference the immutable versioned release rather than `main`:

```yaml
uses: dkharlanau/process-as-code@v0.2.0
```

## Remaining activation

Code-side release automation is complete once CI for this workflow is green. The only account-level steps are the PyPI Trusted Publisher registration and the GitHub Marketplace/Release UI actions tracked in issue #21.
