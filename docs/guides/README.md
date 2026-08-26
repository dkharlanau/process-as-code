# Process as Code — practical guides

These guides start from concrete enterprise problems rather than from product features. The common idea is simple: keep the process as a small, versioned contract with stable IDs, then derive review, impact, governance, test scope and AI context from that contract.

Process as Code is not intended to replace BPMN modelers, process-mining platforms or workflow engines. It complements them where teams need Git-native change control and machine-readable process context.

## Guides

- [BPMN version control with Git](bpmn-version-control-with-git.md) — semantic review around BPMN rather than raw XML diffs.
- [Business process as YAML](business-process-as-yaml.md) — when a small process contract is more useful than another static document.
- [Semantic BPMN and process diff](semantic-bpmn-diff.md) — review meaning by stable IDs.
- [Business process change impact analysis](process-change-impact-analysis.md) — derive affected roles, systems, interfaces, controls and tests.
- [Process governance as code](process-governance-as-code.md) — deterministic CI rules for ownership, controls, evidence and breaking changes.
- [Generate regression test scope from process changes](generate-regression-test-scope-from-process-changes.md) — focus regression effort on affected paths and dependencies.
- [MCP server for governed business process context](mcp-business-process-context.md) — give agents exact process context with provenance instead of long documents.
- [SAP process documentation in Git](sap-process-documentation-in-git.md) — connect SAP business flow to interfaces, mappings, controls and reconciliation without making SAP part of the core schema.

## Minimal workflow

```bash
process-code validate process.process.yaml --strict
process-code diff old.process.yaml process.process.yaml
process-code impact old.process.yaml process.process.yaml
process-code policy process.process.yaml --policy process-policy.yaml
```

For the complete contract and CLI, see the repository [README](../../README.md) and [specification](../specification.md).
