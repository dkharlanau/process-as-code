# Semantic BPMN and process diff

A normal Git diff is line-oriented. A useful business-process diff is entity-oriented.

If a process owner changes a step name, adds an SLA, moves responsibility to another role or removes an interface, the review should describe those semantic changes directly instead of forcing the reviewer to infer them from YAML/XML lines.

## Stable identity first

Process as Code compares sections by stable IDs. For example:

```yaml
- id: validate
  name: Validate downstream creation
  actor: operations
  system: s4
```

If the new version adds:

```yaml
sla: {duration: PT30M}
```

then the semantic change is “step `validate`: field `sla` changed”, not “one line was inserted”.

That semantic identity can then feed impact and test analysis.

## Text and visual views

Generate a deterministic semantic report:

```bash
process-code diff old.process.yaml new.process.yaml
```

Use JSON in automation:

```bash
process-code diff old.process.yaml new.process.yaml --json
```

Generate a visual Mermaid representation of added, removed and changed process nodes:

```bash
process-code diff-visual old.process.yaml new.process.yaml -o process-diff.mmd
```

The two views serve different reviewers. The machine-readable diff is better for CI and downstream logic; a visual view is useful for a process owner who wants to understand topology quickly.

## Diff is not impact

A semantic diff answers **what changed in the contract**. Impact analysis answers **what else is affected because of that change**.

For example:

```text
Diff:
  validate.sla changed

Impact:
  step: validate
  role: operations
  system: s4
  object: business_partner
  recommended tests: validate:happy-path, validate:sla
```

Run both when reviewing an enterprise change:

```bash
process-code diff old.process.yaml new.process.yaml
process-code impact old.process.yaml new.process.yaml
```

## BPMN interoperability

When the source originates as BPMN, import the supported subset into the normalized contract and report unsupported constructs explicitly:

```bash
process-code bpmn-import process.bpmn \
  -o process.process.yaml \
  --report compatibility.md
```

This avoids pretending that every BPMN serialization detail maps cleanly into the contract.

## Identity changes are breaking changes

If `approve_customer` becomes `approve_bp` with no migration semantics, the deterministic engine cannot know whether that is a rename or a delete/add operation. Stable IDs should therefore be treated as API-like identities.

Changing identity intentionally should be visible as a breaking change and governed accordingly.

## What semantic diff does not do

It does not determine whether a change is commercially or legally correct. It provides a precise, repeatable description of the declared change so human review and policy can operate on better evidence.

See [Business process change impact analysis](process-change-impact-analysis.md) for the next step in the review pipeline.
