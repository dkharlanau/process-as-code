# CLI reference

## Validate

```bash
process-code validate process.yaml
process-code validate process.yaml --strict
```

`--strict` returns a non-zero exit code for warnings as well as errors, which is useful in CI.

## Mermaid

```bash
process-code mermaid process.yaml
process-code mermaid process.yaml -o process.mmd
```

## BPMN 2.0

```bash
process-code bpmn process.yaml -o process.bpmn
```

The current exporter maps tasks, user tasks, service tasks, decisions, events, end states, and sequence flows into BPMN 2.0 XML. It is intended as an interchange baseline rather than full BPMN coverage.

## Documentation

```bash
process-code docs process.yaml -o process.md
```

## RACI

```bash
process-code raci process.yaml
process-code raci process.yaml --json
```

## Test scope

```bash
process-code test-scope process.yaml
process-code test-scope process.yaml --json
```

Generated tests cover normal task execution, decision branches, referenced interfaces, and controls.

## Semantic diff

```bash
process-code diff process-v1.yaml process-v2.yaml
process-code diff process-v1.yaml process-v2.yaml --json
```

The diff compares entities by stable ID rather than line position, so reordering does not create meaningless process changes.
