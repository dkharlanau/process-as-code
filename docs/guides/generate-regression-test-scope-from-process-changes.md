# Generate regression test scope from process changes

Enterprise regression testing often starts with a manual question: “what could this process change break?” The answer is usually reconstructed from analyst knowledge, interface lists and previous test packs.

Process as Code uses the declared process graph and dependencies to make that first pass deterministic.

## Two levels of testing

There are two complementary mechanisms.

First, generate baseline scenarios from the process itself:

```bash
process-code test-scope customer.process.yaml
```

This can create candidate scenarios for functional steps, decisions, interfaces, controls and SLA checks.

Second, compare a changed process with its previous version:

```bash
process-code impact old.process.yaml new.process.yaml
```

The impact result identifies changed steps and selects generated tests connected to the changed process context.

## Example

If this step changes:

```yaml
- id: validate
  name: Validate downstream creation
  actor: operations
  system: s4
  sla: {duration: PT30M}
```

an impact report can recommend tests such as:

```text
validate:happy-path
validate:sla
```

If the changed step references an interface or control, the regression scope can include integration/control scenarios as well.

## Process Test DSL

Generated test scope is intentionally generic. Critical business paths should be captured explicitly as deterministic Process Test assertions.

```bash
process-code test new.process.yaml process.tests.yaml
```

When an old process is supplied:

```bash
process-code test new.process.yaml process.tests.yaml \
  --old old.process.yaml \
  --json
```

the output can identify which explicit tests are affected by the semantic process change.

This gives a useful separation:

- generated scope helps discover what should be reconsidered;
- explicit Process Tests protect important paths/invariants;
- real test execution remains in the appropriate application/integration test tools.

## Where this is valuable

This is especially useful when a process spans multiple teams or systems and the expensive part is identifying the right regression boundary. Examples include:

- customer/master-data replication;
- Order-to-Cash integrations;
- approval/control changes;
- API/event contract changes;
- cutover or migration processes.

## Limits

Process as Code does not generate production-quality test data and does not execute SAP/API/UI tests. It generates and prioritizes test intent based on declared process semantics.

The result is only as complete as the process dependencies. If a real dependency is absent from the contract, the deterministic engine should not invent it.

See [Business process change impact analysis](process-change-impact-analysis.md) for the upstream impact workflow.
