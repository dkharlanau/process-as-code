# Process Test DSL

Process tests express deterministic invariants over a process contract.

```yaml
tests:
  - id: happy_path
    path: [request, approve, replicate, complete]
  - id: approval_control
    assert_step:
      step: approve
      controls: [four_eyes]
      actor: data_steward
```

`process-code test process.yaml process.tests.yaml` verifies paths and step assertions. With `--old old.yaml`, the CLI also reports tests whose referenced steps changed, providing regression scoping without executing a workflow engine.
