# Process as Code in the as-code suite

Process as Code owns business flow: stable steps, roles, systems, transitions, controls, risks, evidence, and change impact. Its artifact layer connects a process step to specialist contracts without copying their semantics into the process model.

## Resolve the existing cross-tool example

[`examples/enterprise-change/`](../examples/enterprise-change/) demonstrates the local, offline traceability chain:

```text
process step
  -> interface-as-code artifact
      -> mapping-as-code artifact
          -> reconciliation-as-code artifact
```

Run it with:

```bash
process-code resolve \
  examples/enterprise-change/customer.process.yaml \
  --base-dir examples/enterprise-change \
  --json
```

The resolver follows stable `id` fragments and reports provenance/status for each hop. The foreign files in this fixture are intentionally small resolver documents. Resolution proves traceability and sandbox behavior; it does not validate those documents against the full foreign schemas or execute their CLIs.

## Reference a governed decision

The artifact kind is open, so a decision step can point to an immutable Decision Tables as Code table:

```yaml
artifacts:
  - id: approval_strategy
    kind: decision-tables-as-code
    relation: decides-with
    uri: github://dkharlanau/decision-tables-as-code/examples/sap/approval-matrix.yaml?ref=<immutable-revision>#sap-approval-matrix
```

Network resolution is disabled unless `--allow-network` is explicitly supplied. Even after resolution, use `dtac validate` and `dtac test` to establish decision-table correctness.

## Related projects

- [Interface as Code](https://github.com/dkharlanau/interface-as-code) owns the operational interface invoked by a process step.
- [Mapping as Code](https://github.com/dkharlanau/mapping-as-code) owns field transformation intent referenced through an interface or directly for traceability.
- [Reconciliation as Code](https://github.com/dkharlanau/reconciliation-as-code) owns executable assurance controls and retained evidence used by a process or cutover gate.
- [Decision Tables as Code](https://github.com/dkharlanau/decision-tables-as-code) owns the bounded rule semantics behind a decision step.

## Handoff rule

Process artifact resolution is an evidence-preserving navigation layer, not a universal foreign-schema validator or workflow engine. Keep stable IDs and immutable revisions, and run each specialist tool for its own validation and evidence.
