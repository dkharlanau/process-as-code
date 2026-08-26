# BPMN version control with Git

BPMN files can be stored in Git, but putting XML under version control does not automatically create a useful process-review workflow. A line diff can show that XML changed while still hiding the business meaning of the change.

Process as Code complements BPMN by keeping a compact contract with stable semantic IDs and using BPMN as an interoperable visual/modeling representation where appropriate.

## The problem with raw BPMN diffs

A process reviewer usually cares about questions such as:

- Was a business step added or removed?
- Did an approval route change?
- Did ownership move to another role?
- Is a new system or interface now involved?
- Did a governed control disappear?
- What regression scope follows from the change?

Those questions are difficult to answer from a generic XML diff because BPMN files contain serialization/layout details in addition to business semantics.

## A Git-native workflow

A practical workflow is:

```text
BPMN/modeling tool
   <-> supported BPMN import/export
Process as Code contract
   -> semantic diff
   -> impact analysis
   -> policy gate
   -> pull-request review
```

Import the supported subset:

```bash
process-code bpmn-import process.bpmn \
  -o process.process.yaml \
  --report bpmn-compatibility.md
```

Validate and review the contract:

```bash
process-code validate process.process.yaml --strict
process-code diff old.process.yaml process.process.yaml
process-code impact old.process.yaml process.process.yaml
```

When a diagram is needed again:

```bash
process-code bpmn process.process.yaml -o process.bpmn
process-code mermaid process.process.yaml -o process.mmd
```

## Stable IDs are the key

Git becomes much more useful for process review when entity identity survives formatting changes. Process as Code therefore treats stable process/step IDs as the backbone of semantic diff.

Changing a label can then be distinguished from removing one business step and introducing another. That difference matters for downstream impact and test selection.

## Pull requests instead of document comparison meetings

The root GitHub Action can validate changed process contracts and publish semantic impact directly on a pull request. A reviewer can see business-level changes next to the change history without manually opening two exported diagrams.

This is especially useful for process changes that accompany application/configuration changes in the same Git workflow.

## What Process as Code does not replace

It is not a collaborative BPMN editor, workflow engine or process-mining suite. Use a specialized modeler when rich BPMN authoring is the primary task.

The value here is the **contract and change-control layer**:

- stable semantic IDs;
- deterministic validation;
- semantic diff;
- enterprise impact;
- CI policy;
- generated documentation/test scope;
- machine-readable context for automation and agents.

See [Semantic BPMN and process diff](semantic-bpmn-diff.md) and [Business process change impact analysis](process-change-impact-analysis.md).
