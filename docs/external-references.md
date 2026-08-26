# External references and enterprise traceability

An `artifact` gives a stable local ID to something maintained outside the process contract.

```yaml
artifacts:
  - id: customer_replication
    kind: interface-as-code
    relation: implements
    uri: file:interface.yaml#customer_replication
```

Supported URI forms:

- `file:path/to/file.yaml#stable_id`
- `file:openapi.yaml#/paths/~1customers/post` using JSON Pointer
- `github://owner/repo/path/to/file.yaml?ref=main#stable_id`

Network access is opt-in. Local resolution is deterministic and offline. A resolved object can itself contain `artifacts`, allowing the resolver to traverse process -> interface -> mapping -> reconciliation chains.

Recommended `kind` values are open strings. Current examples use `interface-as-code`, `mapping-as-code`, `reconciliation-as-code`, `openapi-operation`, `asyncapi-channel`, and `json-schema`.
