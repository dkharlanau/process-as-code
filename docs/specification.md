# Process Contract Specification v0.2

This document is normative for the concepts described here. `schemas/process.schema.json` is the machine-readable schema. The Python validator additionally checks graph reachability, liveness, gateway semantics and cross-reference integrity that JSON Schema alone cannot express conveniently.

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

A step may include `actor`, `system`, referenced catalog IDs, `inputs`, `outputs`, `timing`, `ownership`, `sla`, `kpis`, `raci`, `agent`, and `transitions`.

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

## Graph liveness

A structurally connected process is not necessarily able to finish. The reference validator therefore evaluates liveness on the graph reachable from `process.start`.

A **terminal step** is a reachable step with no outgoing transition. `type: end` is the explicit terminal form and must not declare outgoing transitions. For v0.1 compatibility a reachable non-`end` step with no outgoing transition remains valid, but it is reported as an **implicit terminal** warning.

The validator computes the reverse reachability set from all reachable terminals. Every reachable step outside that set is reported because execution can enter it but can never reach a terminal. An unreachable terminal does not make an otherwise trapped process live.

Cycles are allowed. A retry/rework loop is valid when at least one path can leave the loop and eventually reach a terminal. A strongly connected cycle component whose reachable nodes cannot reach any terminal is reported separately as a **trapped cycle** so it is distinguishable from ordinary loop semantics.

Gateway guidance is deliberately conservative:

- a `decision` requires at least one outgoing edge structurally and warns when it has fewer than two branches;
- a `parallel` step warns when it has neither multiple incoming nor multiple outgoing flows, because it is then not acting as a meaningful split or join;
- these checks describe graph semantics only; the core does not execute conditions or parallel runtime behavior.

Liveness findings are deterministic model-quality diagnostics. They do not claim that external systems, humans or runtime workers will actually complete the business process.

## Inputs and outputs

Each contract can declare `id`, `name`, `type`, `ref`, and `required`. At least one of `id`, `name`, or `ref` must exist.

## Process analysis fields

Process discovery and process design are different concerns. The contract therefore separates observed execution from targets:

- `timing.touch_time`: active work time observed or measured for the step.
- `timing.wait_time`: time spent waiting before the step can continue.
- `timing.elapsed_time`: end-to-end time for the step when it is known.
- `sla.duration`: target or service commitment. It is not a substitute for observed duration.
- `ownership.process_owner`: role accountable for the business behavior of the step.
- `ownership.change_owner`: role or team allowed to change the step, configuration, or supporting solution.

The optional top-level `analysis` object records facts that belong to the process analysis rather than to one step:

- `analysis.variants`: conditions that create a different path or handling rule.
- `analysis.pain_points`: evidence-backed observations, causes, impacts, and affected steps.
- `analysis.data_flows`: system-to-system data movement and field-level source-of-truth ownership.

A recommended terminology is:

- **Process Discovery**: the activity of observing the real process.
- **Process Analysis Canvas**: the one-page visual summary generated from the contract.
- **Process Analysis Note**: the detailed evidence-backed analysis document.
- **Process as Code**: the machine-readable source behind those views.

The reference renderer exposes the one-page view with:

```bash
process-code canvas process.yaml -o process-analysis.html
```

The canvas is intentionally not a BPMN replacement. BPMN focuses on process flow semantics. The analysis canvas focuses on how the process actually operates: actor, system, input, output, observed time, variants, pain points, data movement, and ownership.

## Risk, control and evidence

Risks are catalog entities and may include a severity such as `low`, `medium`, `high`, or `critical`. Policy gates can require controls and evidence for high-risk steps.

## Agent policy

`agent.exposable: false` prevents the reference MCP server from returning transition guidance for the step. `agent.executable` communicates whether an allowed transition is operationally executable or guidance-only. The core server never executes enterprise actions itself.

## Extensions

Unknown fields are allowed so vendor/domain extensions can evolve independently. Namespaced extension objects are recommended, for example `extensions.sap`.