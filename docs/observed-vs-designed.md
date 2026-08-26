# Observed vs designed process comparison

`process-code observe` provides a lightweight conformance check between a Process as Code contract and observed event traces. It is intentionally not a full process-mining engine.

CSV input requires `case` (or `case_id`) and `activity` (or `step_id`) columns; `timestamp` is optional. JSON may be a list of event objects or `{ "events": [...] }`.

```bash
process-code observe examples/sap/order-to-cash.process.yaml \
  examples/observed/order-to-cash.events.csv
```

The report highlights unknown activities, undeclared transitions, cases that do not end at a terminal step, path variants, and aggregate conformance rate. Activity values are stable process step IDs, so no fuzzy matching is performed by the core.
