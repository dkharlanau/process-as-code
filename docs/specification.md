# Process Contract Specification v0.2

This document is normative for the concepts described here. `schemas/process.schema.json` is the machine-readable schema. The Python validator additionally checks graph reachability and cross-reference integrity that JSON Schema alone cannot express conveniently.

## Required top-level fields

- `version`: `"0.2"`
- `process.id`: stable process identifier
- `process.name`: human-readable name
- `steps`: non-empty ordered list of step definitions

`process.start` should identify the entry step. If omitted by the reference implementation, the first step is treated as the start for graph traversal.

## Stable IDs

IDs are semantic identities, not labels. Renaming a step should normally preserve `step.id`. Deleting one ID and adding another is intentionally treated as structural change.

## Catalog sections

The core catalog sections are `roles`, `systems`, `objects`, `interfaces`, `controls`, `risks`, `evidence`, and `artifacts`. Every referenced item must exist in the corresponding catalog after composition.

## Steps

Supported `type` values are `task`, `user_task`, `service_task`, `decision`, `parallel`, `event`, `end`, and `subprocess`.

A step may include `actor`, `system`, referenced catalog IDs, `inputs`, `outputs`, `sla`, `kpis`, `raci`, `agent`, and `transitions`.

## Transitions

v0.2 uses an explicit transition array:

```yaml
transitions:
  - to: approve
    when: amount < 10000
    label: standard
```

`to` is required and must reference an existing step. `when` is a machine-readable/processable expression only when a consuming implementation defines an expression language; the core treats it as deterministic contract metadata and does not execute it.

Legacy `next` and `branches` remain accepted by the reference validator for migration compatibility, but `process-code migrate` converts them to v0.2 transitions.

## Inputs and outputs

Each contract can declare `id`, `name`, `type`, `ref`, and `required`. At least one of `id`, `name`, or `ref` must exist.

## Risk, control and evidence

Risks are catalog entities and may include a severity such as `low`, `medium`, `high`, or `critical`. Policy gates can require controls and evidence for high-risk steps.

## Agent policy

`agent.exposable: false` prevents the reference MCP server from returning transition guidance for the step. `agent.executable` communicates whether an allowed transition is operationally executable or guidance-only. The core server never executes enterprise actions itself.

## Extensions

Unknown fields are allowed so vendor/domain extensions can evolve independently. Namespaced extension objects are recommended, for example `extensions.sap`.
