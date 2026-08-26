# AI-assisted process drafting

AI drafting is deliberately outside the deterministic core. Process as Code provides a provider-neutral context bundle instead of embedding one LLM SDK.

```bash
process-code draft-context examples/drafting/customer-onboarding.txt \
  -o draft-context.json --json
```

The installed package includes the v0.2 JSON Schema, so the default bundle is self-contained even when the command is run outside a source checkout. Use `--schema path/to/custom.schema.json` only when intentionally overriding the bundled contract.

The bundle labels the result as a **proposal**, includes drafting rules and the full JSON Schema, identifies the schema source, and gives the authoritative validation/policy commands. An external LLM/agent can use the bundle to propose YAML; the proposal is not accepted as a valid process until normal validation and governance gates pass.

You can extract the exact packaged schema independently with:

```bash
process-code schema -o process.schema.json
```

`examples/drafting/` contains a short business description and one corresponding validated contract as a reproducible before/after example.
