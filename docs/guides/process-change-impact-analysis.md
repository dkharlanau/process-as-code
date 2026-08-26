# Business process change impact analysis

A process change rarely stops at the process diagram. Changing one approval, validation or replication step can affect teams, systems, business objects, interfaces, controls, evidence requirements and regression tests.

Traditional process documentation usually makes those relationships visible only to people who already know the landscape. Process as Code makes them explicit references that can be compared deterministically.

## The problem

Suppose a customer-creation process changes from:

```text
Approve customer -> Replicate to target
```

to:

```text
Approve customer -> Compliance validation -> Replicate to target
```

A useful review should answer more than “one box was added”:

- Which role owns the new step?
- Which systems are now involved?
- Which business objects are touched?
- Did an interface, mapping or reconciliation rule become affected?
- Are new controls or evidence required?
- Which regression tests should be reconsidered?

## Workflow

Keep stable IDs for steps and referenced artifacts. Then compare the old and new contracts:

```bash
process-code diff old.process.yaml new.process.yaml
process-code impact old.process.yaml new.process.yaml
```

For machine-readable automation:

```bash
process-code impact old.process.yaml new.process.yaml --json
```

When the process links to external contracts, mappings or reconciliation artifacts:

```bash
process-code impact old.process.yaml new.process.yaml \
  --resolve-external \
  --json
```

The impact report starts with changed steps and then derives affected roles, systems, business objects, interfaces, controls, risks, evidence and linked artifacts. Generated test scenarios connected to those changes are included as recommended regression scope.

## Pull-request use

The strongest use case is not a report generated after the project meeting. It is a report generated while the change is being reviewed.

The root GitHub Action can run on a normal pull request and publish one marker-based impact comment. A reviewer sees the semantic change and affected context next to the source change instead of reconstructing it manually from several documents.

See [GitHub Action — PR Impact Gate](../github-action.md).

## Cross-repository impact

Large enterprise landscapes should not force every technical detail into the process file. A process step can instead reference external artifacts with portable URIs. This allows a chain such as:

```text
process step
  -> interface contract
  -> mapping
  -> transformation
  -> reconciliation rule
  -> evidence
```

The process remains readable while the change graph becomes traversable.

## Limits

Impact analysis cannot discover dependencies that were never declared. That is intentional: the deterministic layer should report missing or broken references rather than invent undocumented relationships.

Process as Code therefore works best as an incremental contract. Start with the few relationships that matter for review and testing, then enrich the graph as the process becomes operationally important.

## Related commands

```bash
process-code test-scope new.process.yaml
process-code resolve new.process.yaml --json
process-code jsonld new.process.yaml -o process.jsonld
```

See also [Generate regression test scope from process changes](generate-regression-test-scope-from-process-changes.md) and [Process governance as code](process-governance-as-code.md).
