# CLI reference

Core authoring and review:

- `validate FILE [--strict]`
- `migrate FILE`
- `mermaid FILE`
- `bpmn FILE`
- `bpmn-import FILE`
- `docs FILE`
- `raci FILE`
- `diff OLD NEW [--json]`
- `output-schema {semantic-diff,impact} [-o FILE]`
- `diff-visual OLD NEW`
- `impact OLD NEW [--resolve-external]`
- `policy FILE --policy POLICY [--old OLD]`
- `test FILE SUITE [--old OLD]`
- `test-scope FILE`

Enterprise/context tooling:

- `resolve FILE [--allow-network]`
- `compose FILE`
- `observe FILE EVENTS`
- `jsonld FILE [--base-uri URI]`
- `catalog ROOT -o SITE [--base-url URL]`
- `conformance ROOT`

Adoption and AI tooling:

- `draft-context DESCRIPTION [--schema SCHEMA]`
- `adapter-list`
- `adapter-import ADAPTER SOURCE`
- `mcp --root ROOT`

`diff --json` and `impact --json` use versioned machine-output contracts with bundled JSON Schemas. See [Machine-readable output contracts](machine-output-contracts.md).

Commands that support `--json` emit deterministic machine-readable output suitable for CI/agents. The CLI returns non-zero for validation, policy, test or import validation failures.
