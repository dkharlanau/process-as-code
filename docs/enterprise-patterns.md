# Enterprise patterns

## Process change gate

Treat the process contract like an API contract: change it in a pull request, validate references, calculate semantic impact, run policy gates and derive regression scope before merge.

## Process-to-technical traceability

Use `artifacts` to connect a process step to Interface as Code, Mapping as Code, reconciliation definitions, OpenAPI operations, AsyncAPI channels or JSON Schemas. Resolve transitively when one artifact links to another.

## Governed AI context

Expose validated contracts through MCP instead of feeding agents static slide decks or unbounded BPMN XML. Keep execution authority outside the MCP context server; `agent` metadata only describes what may be exposed/guided.

## Designed vs observed

Use stable step IDs in lightweight event traces to detect undeclared transitions, unknown activities, incomplete cases and path variants. This complements process-mining platforms rather than replacing them.

## SAP extension pack

Keep the core vendor-neutral and place SAP metadata under `extensions.sap`. Use realistic process examples to connect business flow to systems, interfaces, controls, data and reconciliation without customer-specific data.
