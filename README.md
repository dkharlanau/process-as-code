# Process as Code

**Git-native business process definitions that can be validated, diffed, rendered, tested, and reused by humans and agents.**

Process documentation normally lives in diagrams, slide decks, wiki pages, or proprietary modeling tools. Those formats are useful for presentation, but weak as a source of truth: changes are hard to review, references drift, test scope is recreated manually, and AI agents receive unstructured context.

Process as Code treats the process definition as a small, versioned YAML/JSON contract. The same file can generate Mermaid, BPMN 2.0 XML, Markdown documentation, RACI, test scope, and semantic change reports.

## Why this repository exists

A process model should be more than a picture. It should be possible to answer, deterministically:

- Which step changed?
- Which role owns it?
- Which systems and business objects are involved?
- Which interfaces and controls are touched?
- What tests should be reconsidered?
- Can the process be rendered for people and parsed by software?
- Can a pull request review a process change like a code change?

This repository provides a compact reference implementation for that workflow.

## Example

```yaml
version: "1.0"
process:
  id: customer_creation
  name: Customer Creation
  owner: data_governance_lead
  start: request

roles:
  - {id: sales, name: Sales}
  - {id: data_governance_lead, name: Data Governance Lead}

systems:
  - {id: mdg, name: SAP Master Data Governance}

steps:
  - id: request
    name: Submit customer request
    actor: sales
    system: mdg
    next: approve

  - id: approve
    name: Approve customer
    type: decision
    actor: data_governance_lead
    system: mdg
    branches:
      approved: complete
      rejected: rejected

  - {id: complete, name: Customer approved, type: end}
  - {id: rejected, name: Request rejected, type: end}
```

## What works today

| Capability | Command | Output |
| --- | --- | --- |
| Reference validation | `process-code validate process.yaml` | errors + warnings |
| Mermaid flow | `process-code mermaid process.yaml` | Mermaid text |
| BPMN export | `process-code bpmn process.yaml` | BPMN 2.0 XML |
| Documentation | `process-code docs process.yaml` | Markdown |
| RACI extraction | `process-code raci process.yaml` | Markdown or JSON |
| Test-scope generation | `process-code test-scope process.yaml` | Markdown or JSON |
| Semantic process diff | `process-code diff old.yaml new.yaml` | Markdown or JSON |
| Change impact analysis | `process-code impact old.yaml new.yaml` | affected context + tests |

The validator checks entity IDs, graph targets, role/system/object/interface/control references, decision branches, unreachable steps, and terminal-path warnings.

## Install

```bash
python -m pip install -e .
```

Development:

```bash
python -m pip install -e .[dev]
pytest -q
```

## Try it

```bash
process-code validate examples/customer-creation.yaml --strict
process-code mermaid examples/customer-creation.yaml
process-code bpmn examples/customer-creation.yaml -o customer-creation.bpmn
process-code docs examples/customer-creation.yaml -o customer-creation.md
process-code raci examples/customer-creation.yaml
process-code test-scope examples/customer-creation.yaml
process-code diff examples/customer-creation.yaml examples/change-request-v2.yaml
process-code impact examples/customer-creation.yaml examples/change-request-v2.yaml
```

Or without installing the console entry point:

```bash
python -m process_as_code validate examples/customer-creation.yaml
```

## Model

A definition has six layers:

1. **Process** — identity, owner, trigger, outcome, start step.
2. **Actors and systems** — roles and execution platforms.
3. **Business context** — objects, interfaces, and controls.
4. **Flow** — tasks, decisions, events, terminal states, and transitions.
5. **Responsibility** — per-step RACI with sensible defaults.
6. **Derived evidence** — diagrams, BPMN, documentation, tests, and diffs.

The JSON Schema is in [`schemas/process.schema.json`](schemas/process.schema.json). Runtime validation adds cross-reference and graph checks that JSON Schema alone cannot express cleanly.

## Design principles

- **Git-first** — readable diffs and pull-request review.
- **Deterministic-first** — core outputs do not require AI.
- **Machine-readable** — a process is structured data, not a screenshot.
- **Vendor-neutral core** — SAP, ServiceNow, Salesforce, custom apps, and others can be modeled without changing the base format.
- **Composable** — references can link into mapping, interface, reconciliation, transformation, control, or evidence repositories.
- **Agent-ready** — a process can be passed to an AI agent as explicit execution context rather than inferred from prose.
- **Progressive detail** — a useful model can start with five steps and become richer over time.

## Enterprise use cases

- SAP process design and fit-to-standard documentation
- S/4HANA migration impact analysis
- MDG governance flows
- O2C/P2P process documentation
- integration and interface impact reviews
- cutover and test planning
- audit/control traceability
- support runbooks and operational procedures
- process-aware AI agent context

See [`docs/enterprise-patterns.md`](docs/enterprise-patterns.md) for concrete patterns.

## Repository layout

```text
examples/                 realistic process definitions
schemas/                  machine-readable schema
src/process_as_code/      validator, renderers, exporters, diff engine
tests/                    executable behavior checks
docs/                     specification and design notes
.github/workflows/ci.yml   multi-version CI
```

## Relationship to adjacent projects

Process as Code describes **what happens and in which order**. Other repositories can describe adjacent layers:

- [Mapping as Code](https://github.com/dkharlanau/mapping-as-code) — field and value transformations
- [Transformation Graph](https://github.com/dkharlanau/transformation-graph) — lineage and transformation dependencies
- [Interface as Code](https://github.com/dkharlanau/interface-as-code) — integration contracts and routes
- [Reconciliation as Code](https://github.com/dkharlanau/reconciliation-as-code) — post-change reconciliation rules
- [Enterprise Change Graph](https://github.com/dkharlanau/enterprise-change-graph) — impact relationships across change artifacts
- [Decision Tables as Code](https://github.com/dkharlanau/decision-tables-as-code) — explicit business decision logic
- [Cutover Graph](https://github.com/dkharlanau/cutover-graph) — migration/cutover dependencies
- [Project Evidence Graph](https://github.com/dkharlanau/project-evidence-graph) — traceable project evidence

The long-term direction is a family of small, interoperable, Git-native enterprise specifications rather than one monolithic platform.

## Status

**Alpha / working reference implementation.** The CLI, examples, schema, CI, and core generators are implemented. The format is intentionally small and may evolve before a stable `1.0` specification.

## License

MIT.
