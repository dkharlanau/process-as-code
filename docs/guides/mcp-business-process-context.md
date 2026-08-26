# MCP server for governed business process context

AI agents often receive business-process knowledge as long documents, wiki pages or exported diagrams. That works for broad retrieval, but it is weak when an agent needs exact operational answers such as:

- What step comes next?
- Who owns this step?
- Which controls apply?
- Which system/interface is involved?
- Is this step exposed as guidance only, or marked executable?
- What source contract supports the answer?

Process as Code exposes validated process contracts through MCP so an agent can query stable process semantics instead of interpreting an arbitrary document each time.

## Install and run

After package publication:

```bash
pip install 'process-as-code[mcp]'
process-code-mcp --root processes
```

From a source checkout:

```bash
pip install -e '.[mcp]'
process-code-mcp --root examples
```

The MCP server indexes validated `*.process.yaml`, `*.process.yml` and `*.process.json` contracts.

## Why validated context matters

A retrieval system can return text even when references inside that text are stale. Process as Code validates stable IDs and graph references before the contract becomes agent context.

A step can carry agent metadata such as:

```yaml
agent:
  exposable: true
  executable: false
  allowed_actions:
    - explain_status
    - list_controls
```

This distinguishes “the agent may explain this part of the process” from “the agent may execute the underlying enterprise action.”

## Read-only context, not transaction authorization

The MCP layer is deliberately a context surface. It can expose process lookup, step lookup, allowed transitions, controls and process-file impact with source provenance.

It does not grant permission to create a customer, approve an invoice or trigger an SAP transaction. Those permissions belong in the target system and the agent platform.

That boundary matters because process knowledge and transaction authorization are different security domains.

## Better than dumping BPMN XML into a prompt

BPMN is valuable for standardized process modeling, but raw BPMN XML is not an efficient runtime context format for many agent queries. Process as Code keeps a compact normalized contract and can still import/export its supported BPMN subset.

The agent sees stable semantic entities such as:

```text
process: customer_creation
step: approve
owner: data_governance_lead
controls: sanctions_check
next: replicate | rejected
source: customer-creation.process.yaml
```

This is easier to cite, validate and govern than a paragraph inferred from a diagram.

## Combine MCP with impact analysis

The same process IDs used for agent context also drive semantic change analysis. That means an agent can query current process context while CI independently validates changes to that context.

The desired lifecycle is:

```text
Git change -> validate -> impact/policy -> merge -> MCP context
```

AI does not become the authority over the contract; it consumes the governed output of the deterministic layer.

See [Process governance as code](process-governance-as-code.md) and [Business process change impact analysis](process-change-impact-analysis.md).
