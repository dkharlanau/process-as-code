# MCP server

Process as Code exposes validated process context through the official MCP Python SDK v2 as an optional dependency.

```bash
pip install 'process-as-code[mcp]'
process-code-mcp --root ./processes
```

Tools:

- `list_processes`
- `get_process`
- `get_step`
- `get_allowed_transitions`
- `get_controls`
- `compare_process_files`

The repository scanner ignores `changes` and `fixtures` directories so historical versions are not accidentally exposed as the current process source of truth. Returned process/step data includes `_provenance` with the source file and stable IDs.

The server is context-only: it does not call business systems and does not use an LLM. `agent.exposable` and `agent.executable` metadata let a process owner narrow how a consumer should interpret guidance.
