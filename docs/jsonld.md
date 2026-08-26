# JSON-LD and enterprise knowledge graphs

`process-code jsonld` exports a validated process contract as deterministic JSON-LD without requiring a graph database.

```bash
process-code jsonld process.yaml --base-uri https://example.com/processes/customer_creation -o process.jsonld
```

The graph contains the process, steps, transitions, roles, systems, business objects, interfaces, controls, risks, evidence, and external artifacts. External artifact URIs are preserved as provenance links.

The default vocabulary is `https://dkharlanau.github.io/process-as-code/vocab#`. Consumers may extend the document with domain-specific JSON-LD terms while preserving core entity IDs.
