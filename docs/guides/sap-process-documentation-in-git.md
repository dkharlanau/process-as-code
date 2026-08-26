# SAP process documentation in Git

SAP process knowledge is often distributed across BPMN diagrams, functional specifications, configuration notes, interface documents, mapping sheets, test packs and cutover files. The result is familiar: each artifact is useful, but the relationships between them are difficult to review as one change.

Process as Code provides a lightweight Git-native contract that can sit between the business process and those technical artifacts.

## Keep the core vendor-neutral

A customer creation, Order-to-Cash or Procure-to-Pay process should not require SAP-specific fields just to be valid. Core concepts remain generic:

- process and step IDs;
- roles;
- systems;
- business objects;
- interfaces;
- controls/risks/evidence;
- transitions;
- SLA/KPI metadata.

SAP-specific context can stay under a namespaced extension:

```yaml
extensions:
  sap:
    solution: SAP S/4HANA
    process_area: Sales
```

This keeps the contract reusable while still allowing realistic SAP documentation.

## Example: cross-system customer replication

A process step may say that an approved Business Partner is replicated from MDG to S/4. The step can reference a logical interface, and that interface can link to external technical artifacts:

```text
Customer governance process
  -> customer replication interface
  -> mapping-as-code
  -> transformation rules
  -> reconciliation-as-code
```

Now a process change can be reviewed together with its technical impact without copying the whole mapping into the process file.

## Useful commands

Validate SAP examples:

```bash
process-code validate examples/sap/order-to-cash.process.yaml --strict
process-code validate examples/sap/procure-to-pay.process.yaml --strict
```

Generate documentation:

```bash
process-code docs examples/sap/order-to-cash.process.yaml \
  -o order-to-cash.md
```

Resolve linked enterprise artifacts:

```bash
process-code resolve examples/enterprise-change/customer.process.yaml --json
```

Compare a process change and focus regression scope:

```bash
process-code impact old.process.yaml new.process.yaml
process-code test-scope new.process.yaml
```

## Where this helps in SAP delivery

The approach is most valuable where process knowledge crosses ownership boundaries:

- MDG/master-data governance and replication;
- Order-to-Cash integrations;
- Procure-to-Pay integrations;
- S/4 migration/cutover processes;
- controls and audit-relevant process changes;
- test-scope decisions across SAP and non-SAP systems.

A functional consultant can read generated process documentation. An integration engineer can follow the interface reference. CI can validate IDs and policy. An agent can query governed process context through MCP.

## Relationship to SAP Signavio and other suites

Process as Code is not a replacement for SAP Signavio, SAP Cloud ALM, Solution Manager or enterprise process-mining/modeling platforms. Those products solve broader collaboration, discovery and lifecycle-management problems.

The niche here is narrower: a portable **Git-native process contract** that can travel with technical change and connect to interfaces, mappings, tests and controls.

That makes it particularly useful for engineering-heavy transformation teams where process and integration changes are already reviewed in version control.

## No customer/proprietary data

Public examples should describe realistic patterns without copying customer-specific system names, process variants, IDs or confidential control rules. Vendor-specific detail belongs in extensions; proprietary project knowledge belongs in the customer repository.

See [Business process change impact analysis](process-change-impact-analysis.md) and the [`examples/sap`](../../examples/sap) pack.
