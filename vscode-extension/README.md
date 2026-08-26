# Process as Code VS Code extension

A lightweight authoring companion for the CLI. It provides a starter snippet, JSON Schema association for `*.process.json`, validation diagnostics for YAML/JSON process files through `process-code validate`, and a documentation preview command.

The extension declares both `jsonValidation` and `yamlValidation` against a bundled copy of the v0.2 schema. It depends on Red Hat YAML for YAML completion/hover/validation.

Run `npm run check` to syntax-check the extension. Marketplace publication is a distribution activation step and is not required to use the folder as an unpacked extension during development.
