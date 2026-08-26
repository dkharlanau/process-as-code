# Process as Code specification

## Purpose

The specification defines a small portable representation of a business process. It is not intended to reproduce every BPMN construct. Its purpose is to preserve the information most useful for version control, impact analysis, documentation, testing, and agent context.

## Top-level fields

- `version`: format version string.
- `process`: process metadata.
- `roles`: actors referenced by steps and RACI.
- `systems`: systems where work is performed.
- `objects`: business objects touched by the flow.
- `interfaces`: integration points referenced by steps.
- `controls`: business or technical controls enforced by steps.
- `steps`: directed process graph.

## Process metadata

Required fields:

- `id`
- `name`

Recommended fields:

- `description`
- `owner`
- `trigger`
- `outcome`
- `start`

If `start` is omitted, the first step is used as the graph entry point.

## Step types

- `task`: generic activity.
- `user_task`: activity performed by a person/role.
- `service_task`: automated/system activity.
- `decision`: branching point; requires `branches`.
- `event`: intermediate event.
- `end`: terminal state.

A step may reference `actor`, `system`, `objects`, `interfaces`, `controls`, and `raci`.

## Transitions

A simple transition uses `next`:

```yaml
next: validate
```

Multiple unlabeled transitions can use a list:

```yaml
next: [notify, archive]
```

A decision uses named branches:

```yaml
branches:
  approved: replicate
  rejected: close_rejected
```

## RACI

RACI can be explicit per step:

```yaml
raci:
  responsible: data_steward
  accountable: process_owner
  consulted: [sales]
  informed: [operations]
```

When omitted, the renderer uses `actor` as Responsible and `process.owner` as Accountable.

## Reference integrity

The runtime validator requires referenced roles, systems, objects, interfaces, controls, and step targets to exist. This is intentionally stricter than plain YAML and is what makes the process definition useful as an executable contract.

## Extension strategy

Unknown fields are preserved by the file format and allowed by the JSON Schema. Domain-specific extensions should use clear namespaces or documented fields rather than forking the core schema.
