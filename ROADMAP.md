# Roadmap

For product strategy and acceptance criteria, see [PRODUCT_BACKLOG.md](PRODUCT_BACKLOG.md) and GitHub issues.

## 0.1 — working core

- [x] YAML/JSON process definition
- [x] cross-reference and graph validation
- [x] Mermaid and BPMN export
- [x] Markdown/RACI/test-scope generation
- [x] semantic diff and change impact

## 0.2 — open process contract

- [x] Process Contract Schema v0.2
- [x] deterministic 0.1 -> 0.2 migration
- [x] policy gates
- [x] BPMN supported-subset import/round-trip
- [x] transitive external references
- [x] MCP process-context server
- [x] Process Test DSL
- [x] reusable catalogs and subprocess composition
- [x] visual semantic diff
- [x] searchable static Process Catalog generator
- [x] SAP extension pack
- [x] OpenAPI / AsyncAPI / JSON Schema references
- [x] public conformance suite
- [x] GitHub Action implementation
- [x] PyPI OIDC and GitHub Pages workflows prepared

## Distribution activation

- [ ] enable GitHub Pages and set `PAGES_ENABLED=true`
- [ ] configure the PyPI Trusted Publisher
- [ ] create the first GitHub release/tag and publish the Action to Marketplace
- [ ] publish the VS Code extension to Marketplace

## 0.3 — ecosystem depth

- [x] event-log / observed-vs-designed comparison
- [x] knowledge-graph / JSON-LD export
- [x] VS Code extension implementation (Marketplace activation pending)
- [x] zero-backend browser playground
- [x] adapter framework + BPMN/CSV reference adapters
- [x] provider-neutral AI-assisted drafting bundle

## 1.0 — stable contract

- [ ] freeze the normative specification
- [ ] compatibility guarantees across schema versions
- [ ] broader third-party conformance feedback
