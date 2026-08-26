# Enterprise patterns

## 1. Process + interface contract

A process step references an interface by stable ID. The interface can later resolve to a richer contract in Interface as Code.

```yaml
interfaces:
  - id: mdg_to_s4
    name: Customer replication

steps:
  - id: replicate
    name: Replicate customer
    type: service_task
    interfaces: [mdg_to_s4]
```

This makes the process useful for integration impact analysis without embedding transport-specific detail in the process model.

## 2. Process + control traceability

Controls become explicit model entities and can be attached to the exact step that enforces them. Generated test scope then includes a control test automatically.

Typical examples:

- duplicate checks
- four-eyes approval
- credit release
- segregation of duties
- mandatory master-data completeness
- reconciliation thresholds

## 3. SAP migration impact

A migration program can keep an `as-is` and `to-be` process in Git and use semantic diff to surface step additions/removals and changes in systems, actors, interfaces, or controls.

That diff is more reviewable than comparing two screenshots of process diagrams.

## 4. Process-aware agent context

An agent can receive a single machine-readable process definition and answer structured questions such as:

- What system owns the next step?
- Which interface is used here?
- Which role is accountable?
- Which controls apply before replication?
- Which tests should be revisited if this step changes?

The core repository does not require an LLM; it provides better input when an LLM is used.

## 5. Pull-request process governance

A practical CI pattern:

1. validate every changed process file;
2. render or regenerate derived artifacts;
3. run semantic diff against the target branch;
4. require review when controls, interfaces, or accountable roles change;
5. preserve the approved definition in Git history.

This is the process equivalent of configuration-as-code governance.
