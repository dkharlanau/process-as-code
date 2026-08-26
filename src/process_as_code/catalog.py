from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from .io import load_process
from .compose import compose_catalogs
from .raci import extract_raci
from .render import to_mermaid
from .validate import validate_process


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


def _layout(title: str, body: str, description: str = "", root_prefix: str = "") -> str:
    desc = html.escape(description or title, quote=True)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{desc}">
<style>body{{font-family:system-ui,sans-serif;max-width:1120px;margin:auto;padding:32px;line-height:1.55;color:#18181b}}a{{color:#0969da}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #d0d7de;padding:8px;text-align:left}}code,pre{{background:#f6f8fa}}pre{{padding:16px;overflow:auto}}.meta{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}}.card{{border:1px solid #d0d7de;border-radius:8px;padding:16px;margin:12px 0}}input{{width:100%;padding:10px;font-size:1rem}}nav{{margin-bottom:28px}}</style></head>
<body><nav><a href="{root_prefix}index.html">Process Catalog</a> · <a href="{root_prefix}guides/index.html">Guides</a></nav>{body}</body></html>'''


def _entity_names(data: dict[str, Any], section: str, ids: list[str]) -> str:
    index = {i.get("id"): i.get("name", i.get("id")) for i in data.get(section, []) or [] if isinstance(i, dict)}
    return ", ".join(html.escape(str(index.get(i, i))) for i in ids) or "—"


def _process_page(data: dict[str, Any]) -> str:
    meta = data.get("process", {})
    steps = [s for s in data.get("steps", []) or [] if isinstance(s, dict)]
    step_rows = []
    for step in steps:
        step_rows.append(f"<tr><td><code>{html.escape(str(step.get('id','')))}</code></td><td>{html.escape(str(step.get('name','')))}</td><td>{html.escape(str(step.get('actor','')))}</td><td>{html.escape(str(step.get('system','')))}</td><td>{_entity_names(data,'controls',step.get('controls',[]) or [])}</td><td>{_entity_names(data,'interfaces',step.get('interfaces',[]) or [])}</td></tr>")
    raci_rows = []
    for row in extract_raci(data):
        raci_rows.append(f"<tr><td><code>{html.escape(row['step'])}</code></td><td>{html.escape(', '.join(row['responsible']))}</td><td>{html.escape(', '.join(row['accountable']))}</td><td>{html.escape(', '.join(row['consulted']))}</td><td>{html.escape(', '.join(row['informed']))}</td></tr>")
    mermaid = html.escape(to_mermaid(data))
    body = f'''<h1>{html.escape(str(meta.get('name', meta.get('id','Process'))))}</h1>
<p>{html.escape(str(meta.get('description','')))}</p>
<div class="meta"><div class="card"><b>ID</b><br><code>{html.escape(str(meta.get('id','')))}</code></div><div class="card"><b>Owner</b><br>{html.escape(str(meta.get('owner','—')))}</div><div class="card"><b>Version</b><br>{html.escape(str(data.get('version','')))}</div><div class="card"><b>Steps</b><br>{len(steps)}</div></div>
<h2>Process flow</h2><pre class="mermaid">{mermaid}</pre>
<h2>Steps and dependencies</h2><table><thead><tr><th>ID</th><th>Step</th><th>Actor</th><th>System</th><th>Controls</th><th>Interfaces</th></tr></thead><tbody>{''.join(step_rows)}</tbody></table>
<h2>RACI</h2><table><thead><tr><th>Step</th><th>R</th><th>A</th><th>C</th><th>I</th></tr></thead><tbody>{''.join(raci_rows)}</tbody></table>
<h2>Machine-readable contract</h2><p>This page is generated from a validated Process as Code contract. Stable IDs are intended for CI, impact analysis, cross-repository references and AI context.</p>'''
    return _layout(str(meta.get("name", "Process")), body, str(meta.get("description") or "Versioned business process contract"), "../")


GUIDES = {
    "bpmn-version-control-with-git": ("BPMN version control with Git", "Store the process contract next to code, use stable step IDs, import/export the supported BPMN subset, and review semantic changes instead of raw XML diffs."),
    "business-process-as-yaml": ("Business process as YAML", "A Process as Code YAML file is a reviewable contract for steps, roles, systems, objects, controls, risks, evidence, SLAs and transitions."),
    "semantic-bpmn-diff": ("Semantic BPMN diff", "Compare process entities by stable IDs so a pull request can explain added, removed and changed steps, transitions and enterprise metadata."),
    "process-change-impact-analysis": ("Business process change impact analysis", "Derive affected roles, systems, interfaces, controls, risks, linked artifacts and regression tests from a process change."),
    "process-governance-as-code": ("Process governance as code", "Use deterministic policy gates to require ownership, controls, evidence, SLAs and acknowledgement of breaking process changes."),
    "process-context-for-ai-agents": ("Process context for AI agents", "Expose validated process steps, allowed transitions, ownership and controls through MCP instead of giving agents unstructured process documents."),
    "sap-process-documentation-in-git": ("SAP process documentation in Git", "Model SAP business processes with vendor-neutral core fields and namespaced SAP extensions while keeping interfaces and data mappings traceable."),
}


def generate_catalog(root: str | Path, output: str | Path, base_url: str | None = None) -> dict[str, Any]:
    root, output = Path(root), Path(output)
    output.mkdir(parents=True, exist_ok=True); (output / "processes").mkdir(exist_ok=True); (output / "guides").mkdir(exist_ok=True)
    processes = discover_processes(root)
    index_items = []
    urls = ["index.html", "guides/index.html"]
    for path, data in processes:
        meta = data.get("process", {})
        slug = _slug(str(meta.get("id", path.stem)))
        rel = f"processes/{slug}.html"; urls.append(rel)
        (output / rel).write_text(_process_page(data), encoding="utf-8")
        search = " ".join([str(meta.get("name","")), str(meta.get("id","")), str(meta.get("owner",""))] + [str(s.get("name","")) for s in data.get("systems",[]) or [] if isinstance(s,dict)])
        index_items.append(f'<div class="card process" data-search="{html.escape(search.lower(),quote=True)}"><a href="{rel}"><b>{html.escape(str(meta.get("name", meta.get("id"))))}</b></a><br><code>{html.escape(str(meta.get("id","")))}</code> · owner: {html.escape(str(meta.get("owner","—")))}</div>')
    body = '<h1>Process as Code Catalog</h1><p>Searchable, generated documentation for validated process contracts.</p><p><a href="playground/index.html"><b>Open browser playground</b></a> · paste YAML/JSON locally without uploading it.</p><input id="q" type="search" placeholder="Search processes, systems, owners…"><div id="items">' + ''.join(index_items) + '</div><script>const q=document.getElementById("q");q.addEventListener("input",()=>{const v=q.value.toLowerCase();document.querySelectorAll(".process").forEach(x=>x.style.display=x.dataset.search.includes(v)?"block":"none")});</script>'
    (output / "index.html").write_text(_layout("Process as Code Catalog", body, "Searchable process contracts, semantic impact and governance documentation."), encoding="utf-8")

    guide_cards = []
    for slug, (title, text) in GUIDES.items():
        rel = f"guides/{slug}.html"; urls.append(rel)
        guide_body = f"<h1>{html.escape(title)}</h1><p>{html.escape(text)}</p><h2>Why Process as Code</h2><p>The source of truth stays machine-readable and versioned. Human diagrams, documentation, RACI, policy results and AI context are generated from the same contract.</p>"
        (output / rel).write_text(_layout(title, guide_body, text, "../"), encoding="utf-8")
        guide_cards.append(f'<div class="card"><a href="{slug}.html"><b>{html.escape(title)}</b></a><p>{html.escape(text)}</p></div>')
    (output / "guides/index.html").write_text(_layout("Process as Code Guides", "<h1>Problem-oriented guides</h1>" + ''.join(guide_cards), "Guides for BPMN Git workflows, semantic diff, governance and AI process context.", "../"), encoding="utf-8")

    (output / "robots.txt").write_text("User-agent: *\nAllow: /\n" + (f"Sitemap: {base_url.rstrip('/')}/sitemap.xml\n" if base_url else ""), encoding="utf-8")
    if base_url:
        base = base_url.rstrip("/")
        sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f"  <url><loc>{html.escape(base + '/' + url)}</loc></url>\n" for url in urls) + '</urlset>\n'
        (output / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    manifest = {"process_count": len(processes), "processes": [d.get("process", {}).get("id") for _, d in processes], "guides": sorted(GUIDES)}
    (output / "catalog.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest
