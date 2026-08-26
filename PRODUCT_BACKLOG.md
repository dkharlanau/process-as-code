# Process as Code — Product Strategy & Backlog

## Product thesis

Process as Code should not become another BPMN editor or workflow engine.

The product should become an **open process contract layer** for enterprise change: a small vendor-neutral definition that humans can review, CI can validate, other repositories can reference, and AI agents can consume as deterministic business context.

A useful process contract should answer:

- what happens and in which order;
- who owns and performs each step;
- which systems, business objects, interfaces and controls are involved;
- what data enters and leaves a step;
- which conditions, SLAs, risks and evidence apply;
- what changed between two versions;
- what systems, roles, tests and controls are affected by the change;
- what an AI agent is allowed to know or do in the process.

## Primary users

1. Enterprise / solution architects maintaining process-to-system traceability.
2. Process owners and business analysts reviewing process changes in Git.
3. QA and test leads deriving regression scope from process changes.
4. Integration and data architects tracing processes to interfaces, mappings and reconciliation.
5. SAP transformation teams that need lightweight, versionable process documentation outside proprietary suites.
6. AI platform teams that need structured, governed process context for agents.

## Product wedge

The first compelling workflow should be:

> Change one process definition in a pull request and automatically receive a human-readable and machine-readable report showing semantic process changes, affected roles, systems, interfaces, controls, business objects and recommended regression tests.

This is materially different from simply drawing BPMN.

## North-star workflow

`process definition -> validate -> diff -> impact -> policy gate -> generated docs -> agent context`

Later, cross-repository references extend this into:

`process -> interface -> mapping -> transformation -> reconciliation -> evidence`

## Prioritized backlog

### P0 — Make the product uniquely useful

1. **Process Contract Schema v0.2** — transition conditions, typed inputs/outputs, SLAs, KPIs, risks, controls, evidence and agent policy fields.
2. **GitHub Action / PR Impact Gate** — validate changed process files and post semantic diff + impact report directly on pull requests.
3. **BPMN import + stronger BPMN export** — supported-subset round trip with stable IDs and explicit compatibility reporting.
4. **Cross-repository reference resolver** — resolve links to Interface as Code, Mapping as Code and Reconciliation as Code and derive transitive impact.
5. **Agent Context Bundle + MCP server** — expose exact process context, allowed transitions, controls and linked artifacts to AI agents.
6. **Process policy gates** — configurable CI rules for high-risk steps, missing controls, ownership, evidence, SLA and breaking changes.

### P1 — Make it enterprise-ready and adoptable

7. **Process Test DSL** — deterministic path, decision, control and invariant tests; generate regression tests from impact analysis.
8. **Reusable catalogs and subprocess composition** — centrally defined roles, systems, controls and reusable subprocess contracts.
9. **Static Process Catalog** — searchable generated site with process maps, metadata, dependency views, RACI, controls and change history.
10. **Visual semantic diff** — render added/removed/changed steps and dependency changes without diffing raw YAML/XML.
11. **SAP Process Pack** — realistic O2C, P2P, customer master/MDG and integration examples with SAP-specific metadata kept as extensions.
12. **Conformance suite** — versioned fixtures and compatibility tests so other tools can implement the Process as Code specification.
13. **Release and distribution** — PyPI package, signed releases, changelog, semantic versioning and reusable GitHub Action published to Marketplace.
14. **OpenAPI / AsyncAPI / data-contract links** — first-class links between process steps and external API/event/data contracts.

### P2 — Expand reach and intelligence

15. **Web playground** — paste or upload YAML/BPMN and immediately validate, render, diff and inspect impact without installation.
16. **VS Code extension** — schema completion, validation, preview, navigation and impact analysis in the editor.
17. **Observed-vs-designed comparison** — ingest event traces and highlight where execution deviates from the declared process contract.
18. **Natural-language drafting** — use AI only to propose process definitions; deterministic validation remains the authority.
19. **Semantic graph export** — JSON-LD/graph representation for enterprise knowledge graphs and cross-domain querying.
20. **Vendor adapters** — import/export helpers for common process repositories where open APIs or standard BPMN exports exist.

## Discoverability backlog

The repository itself is part of the product. Build searchable entry points for concrete problems, not only the phrase “Process as Code”.

Target pages and examples:

- BPMN version control with Git
- business process as YAML
- semantic BPMN diff
- business process change impact analysis
- generate test scope from process changes
- process governance as code
- process context for AI agents
- MCP server for business process context
- SAP process documentation in Git
- SAP Signavio BPMN Git workflow
- process-to-interface traceability
- RACI generation from process models

Required distribution surfaces:

- GitHub topics and strong repository description;
- GitHub Pages documentation / process playground;
- PyPI package page;
- GitHub Marketplace Action;
- example repositories and copy-paste starter templates;
- release notes with concrete use cases;
- articles that demonstrate one problem and one reproducible solution.

## Product principles

- Deterministic core before AI generation.
- Stable IDs are the backbone of meaningful change analysis.
- Vendor-neutral core; vendor-specific behavior belongs in extensions.
- A process model must link to operational artifacts, not remain an isolated diagram.
- Every major feature should produce useful machine-readable output as well as human-readable output.
- Git workflow is a first-class UX, not an implementation detail.
- Optimize for an incremental adoption path: one YAML file should provide value before an enterprise adopts the wider graph.

## Success criteria for 0.2

A new user should be able to clone the repository and within ten minutes:

1. model or import a real process;
2. validate it;
3. open a PR changing one step;
4. see a semantic diff and impact report;
5. identify affected tests/interfaces/controls;
6. generate browsable documentation;
7. query the same process through an agent-safe machine-readable interface.
