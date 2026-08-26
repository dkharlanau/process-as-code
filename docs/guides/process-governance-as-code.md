# Process governance as code

Structural validity and enterprise acceptability are different questions. A process can be syntactically valid and still violate the rules an organization cares about: no owner, no control on a high-risk step, missing evidence, no SLA on an automated activity, or an unacknowledged breaking change.

Process governance as code separates those organization-specific rules from the portable process contract and evaluates them deterministically in CI.

## Why separate validation and policy

The core schema should remain vendor-neutral and reusable. Requiring every process in every company to have the same control model would make the contract brittle.

Instead:

```text
process contract -> structural validation -> organization policy -> review decision
```

The validator checks IDs, references and graph structure. The policy engine checks the rules your repository has chosen to enforce.

## Example policy

A policy can require:

- a process owner;
- controls and evidence for high/critical risks;
- SLA metadata on service tasks;
- explicit acknowledgement of breaking changes.

Run it with:

```bash
process-code validate customer.process.yaml --strict
process-code policy customer.process.yaml --policy process-policy.yaml
```

When reviewing a change against a previous version:

```bash
process-code policy new.process.yaml \
  --old old.process.yaml \
  --policy process-policy.yaml \
  --json
```

Warnings and blocking errors are distinct, so teams can introduce governance gradually instead of turning every missing metadata field into an immediate delivery blocker.

## Pull-request gate

Governance becomes more useful when it runs before a process change is merged. The Process as Code GitHub Action can validate changed contracts, calculate impact and evaluate the policy in one pull-request workflow.

A high-risk process change can therefore produce a review result such as:

```text
Changed step: approve_customer
Risk: restricted_party
Control: sanctions_check
Evidence: screening_result
Policy: PASS
```

or fail explicitly when required evidence/control metadata is missing.

## What this does not do

The policy engine does not replace risk management, legal interpretation, segregation-of-duties analysis or a formal approval system. It is best used for rules that should be objective and repeatable.

Examples of good policy-as-code checks:

- “all critical-risk steps must reference at least one control”;
- “service tasks must have SLA metadata”;
- “removing an interface requires explicit breaking-change acknowledgement.”

Examples of poor deterministic checks:

- “this process is commercially sensible”;
- “this control is legally sufficient in every jurisdiction.”

## Why this matters for AI agents

Governed process context is safer than arbitrary process text. An agent can be given validated ownership, controls and allowed actions while the deterministic contract remains the authority.

See [MCP server for governed business process context](mcp-business-process-context.md) and the repository [policy documentation](../enterprise-patterns.md).
