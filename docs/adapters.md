# Vendor adapter framework

Adapters are import boundaries. The Process as Code core does not import vendor SDKs.

```bash
process-code adapter-list
process-code adapter-import bpmn-file exported-process.bpmn -o process.yaml --report compatibility.json
process-code adapter-import csv-manifest process-manifest.csv -o process.yaml
```

Built-in reference adapters:

- `bpmn-file`: generic BPMN 2.0 import using the documented supported subset.
- `csv-manifest`: a small spreadsheet/export migration format with process and step columns.

A Signavio, Camunda or other repository adapter should consume an exported BPMN file or an openly available vendor API, map into the v0.2 contract, and return an explicit capability/compatibility report. Unsupported semantics must never be silently discarded.
