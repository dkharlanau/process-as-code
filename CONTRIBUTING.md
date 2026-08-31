# Contributing

Contributions should keep the project small, deterministic, and portable.

## Development

```bash
python -m pip install -e .[dev]
pytest -q
```

Before opening a pull request, validate both reference examples:

```bash
process-code validate examples/customer-creation.process.yaml --strict
process-code validate examples/sap/order-to-cash.process.yaml --strict
```

## Model changes

A model change should normally include:

- schema update if applicable;
- runtime validation update if cross-reference semantics change;
- specification documentation;
- at least one fixture/example;
- tests for deterministic output or validation behavior.

Stable IDs are part of the semantic contract. Avoid renaming them merely for presentation changes.
