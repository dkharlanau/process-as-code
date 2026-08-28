# Security policy

Process as Code validates and derives views from process contracts, BPMN documents and referenced artifacts. Treat those inputs as untrusted data. A valid process contract or external reference is not executable authority, and agent-facing metadata does not grant permission to perform business actions.

## Supported versions

Security fixes target the current supported release line and `main`. Advisories/release notes should identify the earliest fixed version when older releases are affected; indefinite support for every historical schema/package version is not implied.

## Reporting a vulnerability

Use GitHub private vulnerability reporting / Security Advisories for this repository when available. Do not publish credentials, proprietary process material, exploit payloads or sensitive generated reports in a public issue.

A useful report includes the affected version/commit, input/command surface, expected boundary, observed impact and privacy-safe reproduction steps.

Ordinary process-model validation, semantic-diff or rendering defects can use public issues when no sensitive data is included.

## Security boundaries

### Process and BPMN inputs are data, not code

YAML/JSON process contracts and imported BPMN influence validation, rendering and analysis. Accepting a file must not silently permit arbitrary command execution, unrestricted filesystem access or unrelated network access. Unsupported BPMN semantics should remain explicit rather than being converted into executable assumptions.

### External references are offline by default

Local artifact resolution is the normal trust boundary. Network-backed references require the documented explicit network opt-in such as `--allow-network`. A `github://`, HTTP or other external reference identifies upstream material; it does not make that material trusted or authorized.

Network resolution should remain bounded to supported schemes/targets, use caller-provided credentials only where documented, and fail explicitly on unsupported or ambiguous content rather than searching broadly for a substitute.

### GitHub Action permissions

The reusable Action runs with permissions granted by the caller workflow and may use the caller-provided GitHub token for PR/report behavior. Grant the least permissions needed by the intended workflow. The Action must not silently widen repository permissions or treat content from an untrusted pull request as permission to execute arbitrary commands.

### MCP and agent guidance

The MCP surface exposes governed process context. Process metadata such as `agent.exposable`, `executable` or `allowed_actions` describes process-level guidance; it does not override the authorization model of the caller, external system or runtime.

Run the MCP server with a deliberately bounded root. A process reference or prompt must not expand that filesystem/network boundary. Read/context capabilities must not silently become an unrestricted workflow executor.

### Vendor adapters and imported artifacts

Adapter discovery/import, BPMN import and external artifact links are untrusted inputs. New executable adapter/plugin mechanisms require an explicit trust model, version compatibility contract and provenance; a data artifact must not smuggle executable behavior through a field that is documented as descriptive.

### Secrets and enterprise data

Credentials, tokens, passwords and private keys do not belong in portable process contracts, examples or generated catalogs. Generated impact reports, catalogs and documentation may contain system names, roles, controls, risks and other enterprise metadata; review them before public publication or CI artifact retention.

Public fixtures should remain synthetic or deliberately non-sensitive.

## Examples of security issues

Private security reports are appropriate for issues such as:

- path traversal or arbitrary local file access from crafted process/artifact references;
- network access occurring without the documented explicit opt-in;
- command/code execution from process/BPMN fields intended to be data-only;
- leakage of GitHub tokens or other credentials into reports/logs;
- MCP requests escaping the configured root or authority boundary;
- reusable Action behavior that unnecessarily widens permissions;
- integrity/provenance bypass that makes different upstream content appear to be the referenced artifact;
- practical resource-exhaustion behavior outside documented bounds.

A wrong process diff, impact result or transition classification is normally a correctness defect unless it also crosses a security/trust boundary.

## Security claim boundary

The project provides deterministic process validation, governance and bounded context surfaces. It does not claim formal security certification, authorization for underlying enterprise systems, or production suitability for confidential process data without the operator's surrounding filesystem, CI, network, identity and access controls.
