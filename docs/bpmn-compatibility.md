# BPMN compatibility

The project uses BPMN as an interchange format, not as its internal source of truth.

Supported import/export nodes:

- start event (mapped to `process.start` on import)
- end event
- task
- user task
- service task
- sub-process node
- exclusive gateway
- parallel gateway
- intermediate catch event
- sequence flow
- lanes / flow-node membership

Sequence-flow names become transition labels. For exclusive gateways they are also preserved as transition conditions when no richer expression is available.

Unsupported process-level elements are listed in the compatibility report. Missing/unsupported nodes referenced by sequence flows produce warnings. This is intentional: the importer must not silently claim lossless compatibility.
