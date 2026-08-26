# AI-assisted process drafting

AI drafting is deliberately outside the deterministic core. Process as Code provides a provider-neutral context bundle instead of embedding one LLM SDK.

```bash
process-code draft-context examples/drafting/customer-onboarding.txt \
  --schema schemas/process.schema.json -o draft-context.json --json
```

The bundle labels the result as a **proposal**, includes drafting rules and optionally the full JSON Schema, and gives the authoritative validation/policy commands. An external LLM/agent can use the bundle to propose YAML; the proposal is not accepted as a valid process until normal validation and governance gates pass.

`examples/drafting/` contains a short business description and one corresponding validated contract as a reproducible before/after example.
