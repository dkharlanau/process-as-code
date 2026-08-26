# Process as Code

**Open process contracts for Git, CI, enterprise change impact, and AI agents.**

Process as Code turns a business process into a small, versioned YAML/JSON contract. The same source can be validated, reviewed semantically, rendered as Mermaid/BPMN, governed in CI, linked to technical contracts, used to derive regression scope, published as a searchable catalog, and exposed to AI agents through MCP.

It is deliberately **not another BPMN editor or workflow engine**. The product wedge is the review and change-control workflow around a process.

## The core workflow

```text
process definition
  -> validate
  -> semantic diff
  -> impact analysis
  -> policy gate
  -> generated docs/catalog
  -> governed agent context
```

Cross-repository references extend the chain:

```text
process -> interface -> mapping -> transformation -> reconciliation -> evidence
```

## Installation

Install the current Git version without cloning the repository:

```bash
python -m pip install "git+https://github.com/dkharlanau/process-as-code.git"
```

After the `v0.2.0` PyPI activation is complete, the standard install is:

```bash
python -m pip install process-as-code
```

For development from a source checkout:

```bash
python -m pip install -e '.[dev]'
```

The installed wheel is self-contained: the v0.2 JSON Schema is bundled in the package and can be retrieved anywhere with:

```bash
process-code schema -o process.schema.json
```

## Ten-minute example

```bash
process-code validate examples/customer-creation.process.yaml --strict
process-code mermaid examples/customer-creation.process.yaml
process-code bpmn examples/customer-creation.process.yaml -o customer.bpmn
process-code diff examples/customer-creation.process.yaml examples/changes/customer-creation-v2.process.yaml
process-code impact examples/customer-creation.process.yaml examples/changes/customer-creation-v2.process.yaml
process-code policy examples/customer-creation.process.yaml --policy examples/policy.yaml
```

When using an installed package outside a source checkout, point the commands at your own `*.process.yaml` files. The example files above live in this repository.

## Contract v0.2

A process can describe more than flow:

```yaml
version: "0.2"
process:
  id: customer_creation
  name: Customer Creation
  owner: data_governance_lead
  start: request

roles:
  - {id: data_governance_lead, name: Data Governance Lead}

systems:
  - {id: mdg, name: SAP Master Data Governance}

controls:
  - {id: sanctions_check, name: Sanctions screening}

risks:
  - {id: restricted_party, severity: high}

evidence:
  - {id: screening_result, name: Screening result}

steps:
  - id: request
    name: Submit customer request
    type: user_task
    system: mdg
    transitions: [{to: approve}]

  - id: approve
    name: Approve customer
    type: decision
    actor: data_governance_lead
    system: mdg
    controls: [sanctions_check]
    risks: [restricted_party]
    evidence: [screening_result]
    sla: {duration: PT4H}
    agent:
      exposable: true
      executable: false
      allowed_actions: [explain_status, list_controls]
    transitions:
      - {to: complete, when: approved, label: approved}
      - {to: rejected, when: rejected, label: rejected}

  - {id: complete, name: Customer approved, type: end}
  - {id: rejected, name: Request rejected, type: end}
```

The source-tree schema is [`schemas/process.schema.json`](schemas/process.schema.json); installed packages expose the identical copy through `process-code schema`.

## Capabilities

| Capability | Command |
| --- | --- |
| Bundled JSON Schema | `process-code schema` |
| Contract validation | `process-code validate` |
| v0.1 -> v0.2 migration | `process-code migrate` |
| Mermaid | `process-code mermaid` |
| BPMN 2.0 export | `process-code bpmn` |
| BPMN supported-subset import | `process-code bpmn-import` |
| Markdown documentation | `process-code docs` |
| RACI | `process-code raci` |
| Generated test scope | `process-code test-scope` |
| Semantic diff | `process-code diff` |
| Visual semantic diff | `process-code diff-visual` |
| Change impact | `process-code impact` |
| Governance policies | `process-code policy` |
| External references | `process-code resolve` |
| Reusable catalogs/subprocesses | `process-code compose` |
| Process Test DSL | `process-code test` |
| Static searchable catalog | `process-code catalog` |
| Conformance suite | `process-code conformance` |
| MCP stdio server | `process-code mcp` / `process-code-mcp` |
| Observed vs designed | `process-code observe` |
| JSON-LD graph export | `process-code jsonld` |
| AI drafting context | `process-code draft-context` |
| Vendor adapter discovery/import | `process-code adapter-list` / `adapter-import` |

## Pull-request impact gate

The repository contains a reusable composite GitHub Action. In a consumer repository:

```yaml
- uses: dkharlanau/process-as-code@main
  with:
    process-glob: "**/*.process.yaml"
    policy-file: "process-policy.yaml"
    github-token: ${{ github.token }}
```

It validates changed contracts, calculates semantic impact against the PR base, emits Markdown and JSON reports, writes the GitHub Step Summary, can update a PR comment, and fails on validation/policy violations. The Action works with the normal shallow `actions/checkout` configuration and fetches the exact comparison commits itself when needed.

See [`docs/github-action.md`](docs/github-action.md).

## BPMN interoperability

`process-code bpmn-import` supports a deterministic subset of BPMN 2.0: tasks, user/service tasks, subprocess nodes, exclusive/parallel gateways, intermediate catch events, end events, sequence flows and lanes. Unsupported semantics are reported explicitly rather than silently discarded.

See [`docs/bpmn-compatibility.md`](docs/bpmn-compatibility.md).

## Enterprise traceability

External artifacts use portable URIs:

```yaml
artifacts:
  - id: customer_api
    kind: openapi-operation
    relation: invokes
    uri: file:openapi.yaml#/paths/~1customers/post

  - id: mapping_customer
    kind: mapping-as-code
    relation: transforms-with
    uri: github://owner/mapping-as-code/mappings/customer.yaml?ref=main#customer_mapping
```

Local files are resolved offline. GitHub references can be resolved explicitly with `--allow-network`. Nested artifact links are followed transitively. JSON Pointer fragments allow direct links into OpenAPI and AsyncAPI documents.

See [`examples/enterprise-change`](examples/enterprise-change) and [`examples/contracts`](examples/contracts).

## MCP: governed process context for agents

Install the optional MCP dependency from a source checkout with:

```bash
pip install -e '.[mcp]'
process-code-mcp --root examples
```

For a released package use `pip install 'process-as-code[mcp]'`.

The MCP server exposes validated process lookup, step lookup, allowed transitions, controls and process-file impact. Responses preserve process/step IDs and source provenance. `agent` metadata can hide a step from transition guidance or mark guidance as non-executable.

The implementation targets the official MCP Python SDK v2.

## SAP extension pack

The vendor-neutral core is complemented by realistic examples under [`examples/sap`](examples/sap):

- Order to Cash
- Procure to Pay
- Business Partner / MDG governance
- Cross-system Business Partner replication

SAP-specific metadata stays under `extensions.sap`; it is not required by the core schema.

## Searchable Process Catalog

```bash
process-code catalog examples -o site \
  --base-url https://example.github.io/process-as-code
```

This generates stable process pages, RACI and dependency tables, search, `robots.txt`, `sitemap.xml`, `catalog.json`, and problem-oriented pages for topics such as BPMN Git version control, semantic BPMN diff, process governance as code, process change impact, SAP process documentation in Git, and AI-agent process context.

## Observed vs designed

```bash
process-code observe examples/sap/order-to-cash.process.yaml \
  examples/observed/order-to-cash.events.csv
```

This lightweight conformance check reports unknown activities, undeclared transitions, incomplete cases, path variants, and aggregate conformance metrics from CSV/JSON traces.

## JSON-LD graph export

```bash
process-code jsonld examples/customer-creation.process.yaml -o customer.jsonld
```

The deterministic graph keeps stable links across process, steps, systems, interfaces, controls, risks, evidence, and external artifacts.

## AI drafting, adapters, playground and VS Code

- `process-code draft-context` builds a provider-neutral proposal bundle for an external LLM and includes the bundled JSON Schema by default; `--schema` can override it. Deterministic validation remains authoritative.
- `process-code adapter-list` / `adapter-import` provide a vendor-neutral adapter boundary with BPMN and CSV reference adapters.
- `web/playground/` is a zero-backend browser playground; no process text is uploaded or stored.
- `vscode-extension/` provides CLI-backed diagnostics, snippets, JSON Schema association and documentation preview.

## Design principles

- deterministic core before AI generation;
- stable IDs are the backbone of change analysis;
- vendor-neutral core, vendor-specific extensions;
- process models link to operational artifacts instead of becoming isolated diagrams;
- human-readable and machine-readable outputs are equally important;
- Git/CI is a first-class user experience;
- incremental adoption: one process file must provide value before the wider graph exists.

## Status

`0.2.0` alpha reference implementation. The specification is intentionally explicit but not frozen until 1.0. See [`PRODUCT_BACKLOG.md`](PRODUCT_BACKLOG.md), [`ROADMAP.md`](ROADMAP.md), and the public conformance suite.

MIT License.
