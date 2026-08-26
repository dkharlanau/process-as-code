# External references and enterprise traceability

An `artifact` gives a stable local ID to something maintained outside the process contract.

```yaml
artifacts:
  - id: customer_replication
    kind: interface-as-code
    relation: implements
    uri: file:interface.yaml#customer_replication
```

Supported URI forms:

- `file:path/to/file.yaml#stable_id`
- `file:openapi.yaml#/paths/~1customers/post` using JSON Pointer
- `github://owner/repo/path/to/file.yaml?ref=main#stable_id`

## Security boundary

External resolution is designed for process contracts that may be reviewed in CI.

Local `file:` references are sandboxed to the supplied `base_dir` after canonical path and symlink resolution. Absolute paths, `..` traversal and symlinks that escape the process workspace return `status: outside-base`; the file is not read.

Network access is disabled unless the caller explicitly passes `--allow-network`. `github://` resolution uses only `https://raw.githubusercontent.com/` after validating GitHub owner, repository, path and ref components. Arbitrary `http://` or `https://` hosts are not supported by the resolver.

Remote artifacts are read with a 5 MiB maximum payload. Oversized responses return `status: too-large` rather than being loaded into memory without a bound.

These restrictions are intentional. If an enterprise needs references outside the process workspace, prefer a versioned GitHub artifact or copy a safe machine-readable contract into the workspace instead of weakening the resolver sandbox.

## Traceability

Local resolution is deterministic and offline. A resolved object can itself contain `artifacts`, allowing the resolver to traverse process -> interface -> mapping -> reconciliation chains up to the configured maximum depth.

Recommended `kind` values are open strings. Current examples use `interface-as-code`, `mapping-as-code`, `reconciliation-as-code`, `openapi-operation`, `asyncapi-channel`, and `json-schema`.

Example:

```bash
process-code resolve process.process.yaml --json
process-code resolve process.process.yaml --allow-network --json
```

Use network resolution only when the referenced GitHub content is expected and trusted for the review being performed.
