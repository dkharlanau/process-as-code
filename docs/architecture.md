# Architecture

Process as Code separates authored intent from derived artifacts.

```text
YAML / JSON source
      |
      v
 loader -> validator -> normalized graph
                         |      |      |      |      |
                         v      v      v      v      v
                      Mermaid  BPMN   docs   RACI  test scope
                                      |
old source -------------------------- diff <---------------- new source
```

## Why a small core

The repository deliberately avoids a workflow engine. Execution semantics differ by platform and are better handled by BPMN/workflow products. The core instead focuses on portable description and deterministic derivation.

## Validation layers

1. Structural checks: required top-level data and step fields.
2. Identity checks: duplicate entity and step IDs.
3. Referential checks: roles, systems, objects, interfaces, controls, and transition targets.
4. Graph checks: reachability and terminal-state warnings.

## Deterministic outputs

Given the same source definition, every built-in generator should produce the same output. This is important for CI, review, reproducibility, and agent use.

## Future extension points

- domain packs for SAP and other enterprise systems
- BPMN import
- graph-level impact queries
- schema version migrations
- process composition/subprocess references
- link resolution into sibling `*-as-code` repositories
- policy checks in CI
