# Agent guide

When working in this repository:

1. Treat YAML/JSON process files as the source of truth.
2. Preserve stable entity and step IDs unless the semantic identity truly changes.
3. Validate examples after schema or validator changes.
4. Keep generators deterministic; do not add LLM calls to core generation paths.
5. Prefer extensions that preserve vendor-neutral base semantics.
6. Add or update tests for every behavioral change.
7. When adding a new model field, document it in `docs/specification.md` and consider its effect on diff output.

Useful commands:

```bash
pip install -e .[dev]
pytest -q
process-code validate examples/customer-creation.process.yaml --strict
process-code docs examples/customer-creation.process.yaml
```
