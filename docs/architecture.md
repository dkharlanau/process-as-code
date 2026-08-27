# Architecture

Process as Code is a deterministic contract tool, not a workflow runtime.

```text
YAML/JSON contract
  -> loader
  -> structural + graph/reference validator
     -> reachable graph
     -> reverse terminal reachability
     -> trapped-cycle / gateway diagnostics
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

Graph validation deliberately separates **reachability** from **liveness**. Forward traversal identifies what execution can enter. Reachable edge-less steps define the terminal set. A reverse traversal then determines which reachable steps can eventually reach a terminal. Strongly connected components identify trapped retry/rework cycles that have no terminating path without treating every intentional loop as an error.

The validator remains a static contract analyzer: a liveness-clean graph means the declared model contains a terminating path from every reachable branch, not that external workers or systems are guaranteed to complete it.

Vendor-specific information belongs under extensions. Optional integrations (MCP, editor tooling, external adapters) sit outside the deterministic core and must not change the meaning of a valid contract.