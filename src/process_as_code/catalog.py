from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from .compose import compose_catalogs
from .io import load_process
from .raci import extract_raci
from .render import to_mermaid
from .validate import validate_process

MERMAID_MODULE = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.lower().replace("_", "-")).strip("-") or "process"


def discover_processes(root: str | Path) -> list[tuple[Path, dict[str, Any]]]:
    root = Path(root)
    found: list[tuple[Path, dict[str, Any]]] = []
    seen: set[Path] = set()
    for pattern in ("*.process.yaml", "*.process.yml", "*.process.json"):
        for path in sorted(root.rglob(pattern)):
            if path in seen or "changes" in path.parts or "fixtures" in path.parts:
                continue
            seen.add(path)
            try:
                data = load_process(path)
            except Exception:
                continue
            composed, errors = compose_catalogs(data, path.parent)
            if not errors and validate_process(composed).ok:
                found.append((path, composed))
    return found


def _layout(
    title: str,
    body: str,
    description: str = "",
    root_prefix: str = "",
    canonical_url: str | None = None,
    extra_head: str = "",
    extra_body: str = "",
) -> str:
    escaped_title = html.escape(title)
    desc = html.escape(description or title, quote=True)
    canonical = ""
    if canonical_url:
        url = html.escape(canonical_url, quote=True)
        canonical = (
            f'<link rel="canonical" href="{url}">'
            f'<meta property="og:title" content="{html.escape(title, quote=True)}">'
            f'<meta property="og:description" content="{desc}">'
            '<meta property="og:type" content="website">'
            f'<meta property="og:url" content="{url}">'
        )
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escaped_title}</title><meta name="description" content="{desc}">{canonical}{extra_head}
<style>body{{font-family:system-ui,sans-serif;max-width:1120px;margin:auto;padding:32px;line-height:1.55;color:#18181b}}a{{color:#0969da}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #d0d7de;padding:8px;text-align:left;vertical-align:top}}code,pre{{background:#f6f8fa}}pre{{padding:16px;overflow:auto}}.meta{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}}.card{{border:1px solid #d0d7de;border-radius:8px;padding:16px;margin:12px 0}}input{{width:100%;padding:10px;font-size:1rem}}nav{{margin-bottom:28px}}.muted{{color:#59636e}}.workflow li{{margin:.45rem 0}}.mermaid{{text-align:center;background:#fff}}.guide-code{{white-space:pre-wrap}}</style></head>
<body><nav><a href="{root_prefix}index.html">Process Catalog</a> · <a href="{root_prefix}guides/index.html">Guides</a> · <a href="{root_prefix}playground/index.html">Playground</a></nav>{body}{extra_body}</body></html>'''


def _entity_names(data: dict[str, Any], section: str, ids: list[str]) -> str:
    index = {
        item.get("id"): item.get("name", item.get("id"))
        for item in data.get(section, []) or []
        if isinstance(item, dict)
    }
    return ", ".join(html.escape(str(index.get(item_id, item_id))) for item_id in ids) or "—"


def _search_terms(data: dict[str, Any]) -> str:
    meta = data.get("process", {}) or {}
    values: list[str] = [str(meta.get(key, "")) for key in ("name", "id", "owner", "description", "trigger", "outcome")]
    values.extend(str(tag) for tag in meta.get("tags", []) or [])
    for section in ("roles", "systems", "objects", "interfaces", "controls", "risks", "evidence"):
        for item in data.get(section, []) or []:
            if isinstance(item, dict):
                values.extend(str(item.get(key, "")) for key in ("id", "name", "description"))
    for step in data.get("steps", []) or []:
        if isinstance(step, dict):
            values.extend(str(step.get(key, "")) for key in ("id", "name", "actor", "system"))
    return " ".join(value for value in values if value).lower()


def _mermaid_loader() -> str:
    return f'''<script type="module">
import mermaid from "{MERMAID_MODULE}";
mermaid.initialize({{startOnLoad:true,securityLevel:"strict",theme:"neutral"}});
</script>'''


def _process_page(data: dict[str, Any], source: str, canonical_url: str | None = None) -> str:
    meta = data.get("process", {})
    steps = [step for step in data.get("steps", []) or [] if isinstance(step, dict)]
    step_rows = []
    for step in steps:
        step_rows.append(
            f"<tr><td><code>{html.escape(str(step.get('id','')))}</code></td>"
            f"<td>{html.escape(str(step.get('name','')))}</td>"
            f"<td>{html.escape(str(step.get('actor','')))}</td>"
            f"<td>{html.escape(str(step.get('system','')))}</td>"
            f"<td>{_entity_names(data,'controls',step.get('controls',[]) or [])}</td>"
            f"<td>{_entity_names(data,'interfaces',step.get('interfaces',[]) or [])}</td></tr>"
        )
    raci_rows = []
    for row in extract_raci(data):
        raci_rows.append(
            f"<tr><td><code>{html.escape(row['step'])}</code></td>"
            f"<td>{html.escape(', '.join(row['responsible']))}</td>"
            f"<td>{html.escape(', '.join(row['accountable']))}</td>"
            f"<td>{html.escape(', '.join(row['consulted']))}</td>"
            f"<td>{html.escape(', '.join(row['informed']))}</td></tr>"
        )
    mermaid = html.escape(to_mermaid(data))
    process_id = str(meta.get("id", "process"))
    body = f'''<h1>{html.escape(str(meta.get('name', process_id)))}</h1>
<p>{html.escape(str(meta.get('description','')))}</p>
<div class="meta"><div class="card"><b>ID</b><br><code>{html.escape(process_id)}</code></div><div class="card"><b>Owner</b><br>{html.escape(str(meta.get('owner','—')))}</div><div class="card"><b>Version</b><br>{html.escape(str(data.get('version','')))}</div><div class="card"><b>Steps</b><br>{len(steps)}</div></div>
<p class="muted">Source: <code>{html.escape(source)}</code></p>
<h2>Process flow</h2><pre class="mermaid">{mermaid}</pre>
<h2>Steps and dependencies</h2><table><thead><tr><th>ID</th><th>Step</th><th>Actor</th><th>System</th><th>Controls</th><th>Interfaces</th></tr></thead><tbody>{''.join(step_rows)}</tbody></table>
<h2>RACI</h2><table><thead><tr><th>Step</th><th>R</th><th>A</th><th>C</th><th>I</th></tr></thead><tbody>{''.join(raci_rows)}</tbody></table>
<h2>Review this contract in Git</h2><pre class="guide-code"><code>process-code validate {html.escape(source)} --strict
process-code impact old.process.yaml {html.escape(source)}
process-code test-scope {html.escape(source)}</code></pre>
<h2>Machine-readable contract</h2><p>This page is generated from a validated Process as Code contract. Stable IDs are intended for CI, semantic impact analysis, cross-repository references and governed AI context.</p>'''
    return _layout(
        str(meta.get("name", "Process")),
        body,
        str(meta.get("description") or "Versioned business process contract with semantic change impact."),
        "../",
        canonical_url,
        extra_body=_mermaid_loader(),
    )


GUIDES: dict[str, dict[str, Any]] = {
    "bpmn-version-control-with-git": {
        "title": "BPMN version control with Git",
        "description": "Use Git for reviewable process changes without treating raw BPMN XML diffs as the business review experience.",
        "problem": "BPMN files can live in Git, but raw XML diffs rarely tell a process owner which step, role, control or interface actually changed.",
        "workflow": ["Keep stable process and step IDs.", "Import/export the supported BPMN subset when a diagram is needed.", "Review semantic diff and impact in the pull request.", "Use generated diagrams as a view, not as a second source of truth."],
        "commands": ["process-code bpmn-import process.bpmn -o process.process.yaml", "process-code diff old.process.yaml new.process.yaml", "process-code impact old.process.yaml new.process.yaml"],
        "limits": "Process as Code does not replace a BPMN modeler and does not execute BPMN. It adds a Git-native contract and review/governance layer around process change.",
    },
    "business-process-as-yaml": {
        "title": "Business process as YAML",
        "description": "Represent a business process as a small versioned YAML contract for flow, ownership, systems, controls, risks and test scope.",
        "problem": "Static process documents are easy to read but difficult to validate, diff, link to technical contracts or consume reliably from CI and agents.",
        "workflow": ["Model steps and transitions with stable IDs.", "Declare referenced roles, systems, objects, interfaces and controls once.", "Validate the contract in CI.", "Generate diagrams, RACI, documentation and tests from the same file."],
        "commands": ["process-code schema -o process.schema.json", "process-code validate customer.process.yaml --strict", "process-code docs customer.process.yaml -o customer.md", "process-code mermaid customer.process.yaml"],
        "limits": "YAML is the machine-readable source, not the desired presentation format for every stakeholder. Human views should be generated from it.",
    },
    "semantic-bpmn-diff": {
        "title": "Semantic BPMN and process diff",
        "description": "Compare process meaning by stable IDs instead of reviewing line-oriented YAML or BPMN XML changes.",
        "problem": "A textual diff answers which characters changed. A process review needs to answer which steps, transitions, responsibilities and enterprise dependencies changed.",
        "workflow": ["Compare old and new contracts by stable ID.", "Separate added, removed and field-level changes.", "Render a visual semantic diff when a diagram is useful.", "Feed changed steps into impact and regression-scope analysis."],
        "commands": ["process-code diff old.process.yaml new.process.yaml", "process-code diff-visual old.process.yaml new.process.yaml -o diff.mmd", "process-code impact old.process.yaml new.process.yaml"],
        "limits": "Meaningful semantic diff depends on stable IDs. Renaming IDs should be treated as a breaking identity change unless an explicit migration is recorded.",
    },
    "process-change-impact-analysis": {
        "title": "Business process change impact analysis",
        "description": "Derive affected roles, systems, objects, interfaces, controls, risks, linked artifacts and regression tests from a process change.",
        "problem": "Enterprise changes propagate beyond a diagram. A changed approval or replication step can affect teams, integration contracts, mappings, controls and regression scope.",
        "workflow": ["Compute semantic step changes.", "Collect referenced enterprise context from old and new versions.", "Resolve linked artifacts when needed.", "Generate focused regression scenarios and risk flags."],
        "commands": ["process-code impact old.process.yaml new.process.yaml", "process-code impact old.process.yaml new.process.yaml --resolve-external --json", "process-code test-scope new.process.yaml"],
        "limits": "Impact is only as complete as the declared links. The tool should surface missing/ambiguous references rather than pretend to infer undocumented dependencies.",
    },
    "process-governance-as-code": {
        "title": "Process governance as code",
        "description": "Enforce deterministic process ownership, control, evidence, SLA and breaking-change rules in CI.",
        "problem": "A structurally valid process can still violate enterprise governance: a high-risk step may lack a control, an owner may be missing or a breaking change may be unacknowledged.",
        "workflow": ["Keep structural validation separate from organization-specific policy.", "Encode blocking and warning rules in a policy file.", "Run policies on every changed process contract.", "Require explicit acknowledgement for governed breaking changes."],
        "commands": ["process-code validate process.process.yaml --strict", "process-code policy process.process.yaml --policy process-policy.yaml", "process-code policy new.process.yaml --old old.process.yaml --policy process-policy.yaml --json"],
        "limits": "The policy engine is deterministic governance, not a substitute for risk judgement, legal review or formal approval workflows.",
    },
    "generate-regression-test-scope-from-process-changes": {
        "title": "Generate regression test scope from process changes",
        "description": "Use changed process steps and dependencies to focus business, integration, control and SLA regression tests.",
        "problem": "Regression scope is often rebuilt manually from workshop knowledge after every process change, which is slow and easy to miss when integrations or controls are affected.",
        "workflow": ["Generate baseline scenarios from the declared process.", "Calculate changed steps and affected dependencies.", "Select tests connected to those steps/interfaces/controls.", "Add explicit Process Test DSL assertions for critical paths and invariants."],
        "commands": ["process-code test-scope process.process.yaml", "process-code impact old.process.yaml new.process.yaml", "process-code test new.process.yaml process.tests.yaml --old old.process.yaml --json"],
        "limits": "Generated scope is a starting point for risk-based testing. It does not replace domain-specific data design or end-to-end test evidence.",
    },
    "mcp-business-process-context": {
        "title": "MCP server for governed business process context",
        "description": "Expose validated process structure, ownership, controls and allowed transitions to AI agents through MCP.",
        "problem": "Giving an agent long process documents produces noisy context and weak provenance. Agents need exact process IDs, step relationships, controls and source references.",
        "workflow": ["Validate contracts before exposing them.", "Index process and step IDs with source provenance.", "Expose read-only lookup, transition and impact tools.", "Use agent metadata to limit what can be presented as executable guidance."],
        "commands": ["pip install 'process-as-code[mcp]'", "process-code-mcp --root processes", "process-code validate processes/customer.process.yaml --strict"],
        "limits": "MCP exposes governed context; it does not authorize enterprise transactions. Execution permissions belong in the target systems and agent platform.",
    },
    "sap-process-documentation-in-git": {
        "title": "SAP process documentation in Git",
        "description": "Keep SAP process-to-system, interface, control and data relationships reviewable in Git while preserving a vendor-neutral core.",
        "problem": "SAP transformations frequently scatter process knowledge across diagrams, configuration notes, interface documents, test sheets and cutover files.",
        "workflow": ["Model the business flow in vendor-neutral Process as Code fields.", "Keep SAP-specific metadata under extensions.sap.", "Link process steps to interfaces, mappings and reconciliation artifacts.", "Review change impact and test scope before transport/cutover changes."],
        "commands": ["process-code validate examples/sap/order-to-cash.process.yaml --strict", "process-code docs examples/sap/order-to-cash.process.yaml", "process-code resolve examples/enterprise-change/customer.process.yaml --json"],
        "limits": "This does not replace SAP Signavio, Solution Manager/Cloud ALM or system configuration. It provides a lightweight Git-native contract and traceability layer around them.",
    },
}


def _guide_body(guide: dict[str, Any]) -> str:
    workflow = "".join(f"<li>{html.escape(item)}</li>" for item in guide["workflow"])
    commands = "\n".join(guide["commands"])
    return f'''<h1>{html.escape(guide['title'])}</h1>
<p>{html.escape(guide['description'])}</p>
<h2>The problem</h2><p>{html.escape(guide['problem'])}</p>
<h2>Practical workflow</h2><ol class="workflow">{workflow}</ol>
<h2>Commands</h2><pre class="guide-code"><code>{html.escape(commands)}</code></pre>
<h2>What Process as Code adds</h2><p>The contract stays versionable and machine-readable while semantic diff, impact, policy, diagrams, tests and agent context are derived from the same stable IDs.</p>
<h2>Limitations</h2><p>{html.escape(guide['limits'])}</p>'''


def _canonical(base_url: str | None, rel: str) -> str | None:
    if not base_url:
        return None
    return base_url.rstrip("/") + "/" + rel.lstrip("/")


def generate_catalog(root: str | Path, output: str | Path, base_url: str | None = None) -> dict[str, Any]:
    root, output = Path(root), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "processes").mkdir(exist_ok=True)
    (output / "guides").mkdir(exist_ok=True)
    processes = discover_processes(root)
    index_items = []
    urls = ["index.html", "guides/index.html"]

    for path, data in processes:
        meta = data.get("process", {})
        slug = _slug(str(meta.get("id", path.stem)))
        rel = f"processes/{slug}.html"
        urls.append(rel)
        try:
            source = path.relative_to(root.parent).as_posix()
        except ValueError:
            source = path.as_posix()
        (output / rel).write_text(_process_page(data, source, _canonical(base_url, rel)), encoding="utf-8")
        index_items.append(
            f'<div class="card process" data-search="{html.escape(_search_terms(data),quote=True)}">'
            f'<a href="{rel}"><b>{html.escape(str(meta.get("name", meta.get("id"))))}</b></a><br>'
            f'<code>{html.escape(str(meta.get("id","")))}</code> · owner: {html.escape(str(meta.get("owner","—")))}</div>'
        )

    body = (
        '<h1>Process as Code Catalog</h1>'
        '<p>Searchable, generated documentation for validated process contracts, semantic change impact and governed AI context.</p>'
        '<p><a href="playground/index.html"><b>Open browser playground</b></a> · paste YAML/JSON locally without uploading it.</p>'
        '<input id="q" type="search" placeholder="Search processes, roles, systems, objects, interfaces, controls…">'
        '<div id="items">' + "".join(index_items) + '</div>'
        '<script>const q=document.getElementById("q");q.addEventListener("input",()=>{const v=q.value.toLowerCase();document.querySelectorAll(".process").forEach(x=>x.style.display=x.dataset.search.includes(v)?"block":"none")});</script>'
    )
    (output / "index.html").write_text(
        _layout(
            "Process as Code Catalog",
            body,
            "Searchable process contracts for semantic change impact, enterprise governance, regression scope and AI context.",
            canonical_url=_canonical(base_url, "index.html"),
        ),
        encoding="utf-8",
    )

    guide_cards = []
    for slug, guide in GUIDES.items():
        rel = f"guides/{slug}.html"
        urls.append(rel)
        (output / rel).write_text(
            _layout(
                guide["title"],
                _guide_body(guide),
                guide["description"],
                "../",
                _canonical(base_url, rel),
            ),
            encoding="utf-8",
        )
        guide_cards.append(
            f'<div class="card"><a href="{slug}.html"><b>{html.escape(guide["title"])}</b></a><p>{html.escape(guide["description"])}</p></div>'
        )
    (output / "guides/index.html").write_text(
        _layout(
            "Process as Code Guides",
            "<h1>Problem-oriented guides</h1><p>Practical entry points for Git-native process change, impact, governance, testing and agent context.</p>" + "".join(guide_cards),
            "Guides for BPMN Git workflows, semantic process diff, change impact, governance, regression testing and MCP process context.",
            "../",
            _canonical(base_url, "guides/index.html"),
        ),
        encoding="utf-8",
    )

    (output / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n" + (f"Sitemap: {base_url.rstrip('/')}/sitemap.xml\n" if base_url else ""),
        encoding="utf-8",
    )
    if base_url:
        base = base_url.rstrip("/")
        sitemap = (
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(f"  <url><loc>{html.escape(base + '/' + url)}</loc></url>\n" for url in urls)
            + "</urlset>\n"
        )
        (output / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    manifest = {
        "process_count": len(processes),
        "processes": [data.get("process", {}).get("id") for _, data in processes],
        "guides": sorted(GUIDES),
    }
    (output / "catalog.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest
