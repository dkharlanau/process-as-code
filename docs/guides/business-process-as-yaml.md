# Business process as YAML

A business process can be written as YAML without turning YAML into a workflow engine. The useful pattern is to treat the file as a **versioned process contract**: a compact source of truth for steps, transitions, ownership and enterprise dependencies.

## Why a process contract instead of another document

Slides, diagrams and wiki pages are excellent for communication but weak as deterministic inputs. They are difficult to validate, diff semantically, connect to CI or expose reliably to software agents.

A small YAML contract makes explicit facts such as:

```yaml
version: "0.2"
process:
  id: customer_creation
  name: Customer Creation
  owner: data_governance_lead
  start: request

steps:
  - id: request
    name: Submit customer request
    actor: sales
    system: mdg
    transitions: [{to: approve}]

  - id: approve
    name: Approve customer
    type: decision
    actor: data_governance_lead
    controls: [sanctions_check]
    transitions:
      - {to: replicate, when: approved}
      - {to: rejected, when: rejected}
```

The contract can additionally declare roles, systems, business objects, interfaces, controls, risks, evidence, SLA/KPI metadata and external artifacts.

## Start small

You do not need an enterprise ontology before the first useful file. A practical adoption path is:

1. model steps and transitions;
2. add the roles/systems that matter for ownership;
3. add interfaces or controls where change impact matters;
4. validate it in CI;
5. generate diagrams/docs rather than maintaining them separately.

Get the authoritative schema from an installed package:

```bash
process-code schema -o process.schema.json
```

Validate a contract:

```bash
process-code validate customer.process.yaml --strict
```

Generate human views:

```bash
process-code mermaid customer.process.yaml
process-code docs customer.process.yaml -o customer.md
process-code raci customer.process.yaml
```

## Why YAML is not the user interface

Process owners should not be forced to read YAML for every review. The same contract can generate Mermaid/BPMN, Markdown, a searchable process catalog and pull-request impact reports.

The source stays structured while presentation changes by audience.

## Stable IDs matter more than formatting

The core advantage over prose is not YAML syntax itself. It is stable identity. A step ID such as `approve_customer` can be referenced by tests, impact reports, external artifacts and MCP tools even when the displayed name changes.

This gives Git meaningful semantics instead of merely storing another text file.

## When not to use this

Use a workflow engine when the goal is executing orchestration. Use a full BPMN suite when collaborative diagram modeling is the primary need. Use process mining when the primary question is discovering process behavior from event data.

Process as Code is strongest when you need a small, portable **contract around process change** that CI, developers, analysts and agents can share.

See [Process governance as code](process-governance-as-code.md) and [Semantic BPMN and process diff](semantic-bpmn-diff.md).
