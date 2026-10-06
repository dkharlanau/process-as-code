# Machine-readable output contracts

Process as Code exposes deterministic JSON for automation. The first versioned output contracts cover:

- `process-code diff OLD NEW --json`
- `process-code impact OLD NEW --json`

These JSON documents are used by CI pipelines, repository tooling, agent integrations and other as-code tools. Their structure therefore needs an explicit compatibility boundary.

## Output metadata

Each versioned JSON document contains an `output` object:

```json
{
  "output": {
    "format": "process-as-code.semantic-diff",
    "version": "1.0",
    "schema": "https://dkharlanau.github.io/process-as-code/schemas/outputs/semantic-diff-v1.schema.json"
  },
  "process": {},
  "sections": {},
  "analysis": {}
}
```

The impact report uses `process-as-code.impact` and its own schema URI. Its nested `semantic_diff` object keeps the semantic-diff metadata as well.

The output contract version is independent from:

- the Process Contract version such as `0.2`;
- the Python package version such as `0.2.0`.

## Compatibility rule

Version `1.0` follows these rules:

1. Existing documented fields keep their meaning and type.
2. New optional fields may be added.
3. Consumers should ignore fields they do not understand.
4. Removing, renaming or changing the type of an existing documented field requires a new major output contract.
5. Machine output stays deterministic. It does not include timestamps, random IDs or environment-specific values unless a command explicitly models them as business data.

This policy lets a CI consumer depend on fields such as `sections.steps.changed` or `affected.interfaces` without depending on the internal Python implementation.

## JSON Schemas

The schemas are stored in:

- `schemas/outputs/semantic-diff-v1.schema.json`
- `schemas/outputs/impact-v1.schema.json`

They are bundled in the Python package and published with the project site.

Retrieve the bundled copies without network access:

```bash
process-code output-schema semantic-diff -o semantic-diff.schema.json
process-code output-schema impact -o impact.schema.json
```

## Consumer pattern

A consumer should check the metadata before reading the payload:

```python
result = json.loads(payload)

output = result["output"]
if output["format"] != "process-as-code.impact":
    raise ValueError("unexpected Process as Code output")
if output["version"] != "1.0":
    raise ValueError("unsupported impact contract version")

interfaces = result["affected"]["interfaces"]
```

For validation, use the schema from `output.schema` or a bundled copy retrieved with `process-code output-schema`.

## Scope

The first contract boundary is intentionally focused on semantic change control: diff and impact. Other JSON-producing commands can adopt the same pattern when their payloads become integration surfaces with external consumers.
