# Architecture

Process as Code is a deterministic contract tool, not a workflow runtime.

```text
YAML/JSON contract
  -> loader
  -> structural + graph/reference validator
  -> semantic model by stable IDs
     -> Mermaid / BPMN / Markdown / RACI
     -> semantic & visual diff
     -> change impact + regression scope
     -> policy gates
     -> Process Test DSL
     -> external reference resolver
     -> JSON-LD graph
     -> MCP context
     -> static catalog / playground
     -> observed-vs-designed comparison
```

The v0.2 JSON Schema describes syntax; Python validation enforces graph and cross-reference invariants. Stable IDs are the semantic backbone for diff, impact, tests, external links and knowledge-graph export.

Vendor-specific information belongs under extensions. Optional integrations (MCP, editor tooling, external adapters) sit outside the deterministic core and must not change the meaning of a valid contract.
