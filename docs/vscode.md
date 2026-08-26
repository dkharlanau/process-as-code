# VS Code authoring extension

The `vscode-extension/` folder contains an unpacked extension that delegates authoritative validation to the `process-code` CLI.

Features:

- starter Process as Code snippet;
- JSON Schema association for `*.process.json`;
- save/command validation diagnostics for YAML and JSON contracts;
- Markdown documentation preview command;
- zero Node runtime dependencies beyond VS Code itself.

The extension declares `yamlValidation` and `jsonValidation` contribution points against a bundled copy of the v0.2 schema and declares Red Hat YAML as an extension dependency for YAML completion/hover/validation.

`npm run check` performs a deterministic JavaScript syntax build check. VS Code Marketplace publication is an external distribution activation step.
