# Process as Code

Define business processes as versionable structured files and generate process maps, BPMN, documentation, and test scope.

## Problem

Business processes are usually documented in visual tools or static presentations but are difficult to version, diff, generate, validate, and reuse as machine-readable context.

## Core idea

Define business processes as structured, versionable files and generate process maps, BPMN, documentation, and test scope from them.

## Example

```yaml
process: Customer Creation

steps:
  - id: request
    role: Sales
    action: Request customer

  - id: approve
    role: Data Governance
    system: MDG
    action: Approve request

  - id: replicate
    system: MDG
    target: S4
    action: Replicate customer

  - id: validate
    role: Operations
    action: Validate downstream creation
```

## Initial scope

- structured process schema
- validation
- roles
- systems
- business objects
- interfaces
- controls
- generated process diagrams
- Mermaid export
- BPMN export
- Markdown documentation
- process diff
- RACI extraction
- test-scope generation

## Long-term direction

Git-native process definitions interoperable with enterprise process-management tools.

## Design principles

- versionable
- portable
- machine-readable
- deterministic-first
- visual where useful
- Git-friendly
- vendor-neutral where practical
- interoperable with enterprise tools

## Status

Planning.
