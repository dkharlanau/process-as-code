from __future__ import annotations

from html import escape
from typing import Any

from .graph import step_edges


def _escape(text: str) -> str:
    return text.replace('"', "'")


def _html(value: Any, fallback: str = "—") -> str:
    if value is None or value == "":
        return fallback
    return escape(str(value))


def _catalog_names(data: dict[str, Any], section: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in data.get(section, []) or []:
        if isinstance(item, dict) and item.get("id"):
            result[str(item["id"])] = str(item.get("name") or item["id"])
    return result


def _contract_list(items: Any) -> str:
    labels: list[str] = []
    for item in items or []:
        if isinstance(item, dict):
            labels.append(str(item.get("name") or item.get("id") or item.get("ref") or ""))
        elif item:
            labels.append(str(item))
    return ", ".join(label for label in labels if label) or "—"


def _compact_value(value: Any) -> str:
    if isinstance(value, dict):
        parts = [f"{key}: {val}" for key, val in value.items() if val not in (None, "", [], {})]
        return "; ".join(parts) or "—"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "—"
    return str(value) if value not in (None, "") else "—"


def to_mermaid(data: dict[str, Any]) -> str:
    lines = ["flowchart TD"]
    steps = [s for s in data.get("steps", []) if isinstance(s, dict) and s.get("id")]
    for step in steps:
        sid = step["id"]
        label = _escape(step.get("name", sid))
        kind = step.get("type", "task")
        if kind in {"decision", "parallel"}:
            lines.append(f'  {sid}{{"{label}"}}')
        elif kind in {"event", "end"}:
            lines.append(f'  {sid}(["{label}"])')
        else:
            lines.append(f'  {sid}["{label}"]')
    for step in steps:
        for target, label in step_edges(step):
            if label:
                lines.append(f'  {step["id"]} -->|"{_escape(label)}"| {target}')
            else:
                lines.append(f'  {step["id"]} --> {target}')
    return "\n".join(lines) + "\n"


def to_analysis_canvas(data: dict[str, Any]) -> str:
    """Render a compact, evidence-oriented one-page process analysis view."""
    meta = data.get("process", {}) or {}
    analysis = data.get("analysis", {}) or {}
    steps = [step for step in data.get("steps", []) if isinstance(step, dict)]
    role_names = _catalog_names(data, "roles")
    system_names = _catalog_names(data, "systems")
    system_count = len({step.get("system") for step in steps if step.get("system")})
    variants = analysis.get("variants", []) or []
    pain_points = analysis.get("pain_points", []) or []
    data_flows = analysis.get("data_flows", []) or []

    rows: list[str] = []
    ownership_rows: list[str] = []
    for index, step in enumerate(steps, 1):
        timing = step.get("timing") if isinstance(step.get("timing"), dict) else {}
        ownership = step.get("ownership") if isinstance(step.get("ownership"), dict) else {}
        sla = step.get("sla") if isinstance(step.get("sla"), dict) else {}
        actor = role_names.get(str(step.get("actor")), str(step.get("actor") or "—"))
        system = system_names.get(str(step.get("system")), str(step.get("system") or "—"))
        rows.append(
            "<tr>"
            f"<td class='num'>{index:02d}</td>"
            f"<td><strong>{_html(step.get('name'))}</strong><span class='sub'>{_html(step.get('id'), '')}</span></td>"
            f"<td>{_html(actor)}</td>"
            f"<td>{_html(system)}</td>"
            f"<td>{_html(_contract_list(step.get('inputs')))}</td>"
            f"<td>{_html(_contract_list(step.get('outputs')))}</td>"
            f"<td class='time'>{_html(timing.get('touch_time'))}</td>"
            f"<td class='time'>{_html(timing.get('wait_time'))}</td>"
            f"<td class='time'>{_html(sla.get('duration'))}</td>"
            "</tr>"
        )
        if ownership:
            owner = role_names.get(str(ownership.get("process_owner")), str(ownership.get("process_owner") or "—"))
            changer = role_names.get(str(ownership.get("change_owner")), str(ownership.get("change_owner") or "—"))
            ownership_rows.append(
                f"<div class='mini-row'><strong>{_html(step.get('name'))}</strong>"
                f"<span>Process: {_html(owner)} · Change: {_html(changer)}</span></div>"
            )

    variant_cards: list[str] = []
    for item in variants:
        if not isinstance(item, dict):
            continue
        title = item.get("name") or item.get("id") or "Variant"
        condition = item.get("when") or item.get("condition")
        path = item.get("path")
        variant_cards.append(
            "<div class='mini-card'>"
            f"<strong>{_html(title)}</strong>"
            f"<span>{_html(condition)}</span>"
            f"<small>Path: {_html(_compact_value(path))}</small>"
            "</div>"
        )

    pain_cards: list[str] = []
    for item in pain_points:
        if not isinstance(item, dict):
            continue
        title = item.get("observation") or item.get("name") or item.get("id") or "Pain point"
        cause = item.get("cause")
        impact = item.get("impact")
        step = item.get("step")
        evidence = item.get("evidence")
        detail_parts = []
        if step:
            detail_parts.append(f"Step: {step}")
        if cause:
            detail_parts.append(f"Cause: {cause}")
        if evidence:
            detail_parts.append(f"Evidence: {_compact_value(evidence)}")
        if impact:
            detail_parts.append(f"Impact: {_compact_value(impact)}")
        pain_cards.append(
            "<div class='mini-card pain'>"
            f"<strong>{_html(title)}</strong>"
            f"<span>{_html(' · '.join(detail_parts))}</span>"
            "</div>"
        )

    flow_cards: list[str] = []
    for item in data_flows:
        if not isinstance(item, dict):
            continue
        source = system_names.get(str(item.get("from")), str(item.get("from") or "—"))
        target = system_names.get(str(item.get("to")), str(item.get("to") or "—"))
        payload = _compact_value(item.get("data"))
        truth = _compact_value(item.get("source_of_truth"))
        flow_cards.append(
            "<div class='flow-card'>"
            f"<strong>{_html(source)} <span>→</span> {_html(target)}</strong>"
            f"<span>{_html(payload)}</span>"
            f"<small>Source of truth: {_html(truth)}</small>"
            "</div>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_html(meta.get("name", "Process"))} — Process Analysis Canvas</title>
<style>
:root {{ --ink:#172033; --muted:#64748b; --line:#dbe3ef; --soft:#f6f8fc; --accent:#3157d5; --accent-soft:#edf2ff; --warn:#a33a2b; --warn-soft:#fff2ef; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:#eef2f7; color:var(--ink); font-family:Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
.canvas {{ width:min(1600px, 100%); margin:0 auto; background:white; min-height:100vh; padding:28px 32px 30px; }}
header {{ display:grid; grid-template-columns:1fr auto; gap:24px; align-items:start; margin-bottom:18px; }}
.eyebrow {{ text-transform:uppercase; letter-spacing:.12em; font-size:11px; font-weight:800; color:var(--accent); }}
h1 {{ margin:4px 0 10px; font-size:32px; line-height:1.08; }}
.scope {{ display:flex; gap:12px; align-items:stretch; }}
.scope-box {{ background:var(--soft); border:1px solid var(--line); border-radius:12px; padding:10px 13px; min-width:240px; }}
.scope-box small {{ display:block; color:var(--muted); font-size:10px; text-transform:uppercase; letter-spacing:.08em; margin-bottom:4px; }}
.arrow {{ align-self:center; color:var(--muted); font-size:20px; }}
.stats {{ display:grid; grid-template-columns:repeat(4, minmax(78px,1fr)); gap:8px; }}
.stat {{ border:1px solid var(--line); border-radius:12px; padding:10px 12px; text-align:center; background:var(--soft); }}
.stat b {{ display:block; font-size:22px; }}
.stat span {{ color:var(--muted); font-size:11px; }}
.section {{ border:1px solid var(--line); border-radius:14px; overflow:hidden; margin-top:12px; }}
.section-title {{ display:flex; align-items:center; justify-content:space-between; padding:10px 14px; background:var(--soft); border-bottom:1px solid var(--line); }}
.section-title strong {{ font-size:13px; text-transform:uppercase; letter-spacing:.06em; }}
.section-title span {{ color:var(--muted); font-size:11px; }}
table {{ width:100%; border-collapse:collapse; table-layout:fixed; }}
th {{ color:var(--muted); text-transform:uppercase; letter-spacing:.05em; font-size:9px; text-align:left; padding:8px 7px; background:#fbfcfe; border-bottom:1px solid var(--line); }}
td {{ padding:8px 7px; border-bottom:1px solid #edf1f6; vertical-align:top; font-size:11px; overflow-wrap:anywhere; }}
tr:last-child td {{ border-bottom:0; }}
td strong {{ font-size:11px; }}
.sub {{ display:block; color:var(--muted); font-size:9px; margin-top:2px; }}
.num {{ width:38px; color:var(--muted); font-weight:700; }}
.time {{ white-space:nowrap; font-variant-numeric:tabular-nums; }}
.grid {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; margin-top:12px; }}
.panel {{ border:1px solid var(--line); border-radius:14px; padding:12px; min-height:150px; }}
.panel h2 {{ font-size:12px; margin:0 0 9px; text-transform:uppercase; letter-spacing:.06em; }}
.mini-card {{ border-left:3px solid var(--accent); background:var(--accent-soft); border-radius:8px; padding:8px 9px; margin-top:7px; }}
.mini-card.pain {{ border-left-color:var(--warn); background:var(--warn-soft); }}
.mini-card strong, .flow-card strong {{ display:block; font-size:11px; }}
.mini-card span, .mini-row span, .flow-card span {{ display:block; color:#334155; font-size:10px; margin-top:3px; }}
.mini-card small, .flow-card small {{ display:block; color:var(--muted); font-size:9px; margin-top:3px; }}
.mini-row {{ padding:7px 0; border-bottom:1px solid #edf1f6; }}
.mini-row:last-child {{ border-bottom:0; }}
.mini-row strong {{ display:block; font-size:10px; }}
.flows {{ display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; }}
.flow-card {{ border:1px solid var(--line); border-radius:10px; padding:9px; background:#fbfcfe; }}
.flow-card strong span {{ display:inline; color:var(--accent); margin:0 4px; }}
.empty {{ color:var(--muted); font-size:10px; }}
footer {{ margin-top:10px; color:var(--muted); font-size:9px; display:flex; justify-content:space-between; }}
@media (max-width:1000px) {{ header,.grid {{ grid-template-columns:1fr; }} .scope {{ flex-direction:column; }} .arrow {{ transform:rotate(90deg); }} .flows {{ grid-template-columns:1fr; }} table {{ table-layout:auto; }} }}
@media print {{ @page {{ size:landscape; margin:8mm; }} body {{ background:white; }} .canvas {{ width:100%; min-height:auto; padding:0; }} }}
</style>
</head>
<body>
<main class="canvas">
<header>
<div>
<div class="eyebrow">Process Analysis Canvas</div>
<h1>{_html(meta.get("name") or meta.get("id") or "Process")}</h1>
<div class="scope">
<div class="scope-box"><small>Trigger</small><strong>{_html(meta.get("trigger"))}</strong></div>
<div class="arrow">→</div>
<div class="scope-box"><small>End state</small><strong>{_html(meta.get("outcome"))}</strong></div>
</div>
</div>
<div class="stats">
<div class="stat"><b>{len(steps)}</b><span>steps</span></div>
<div class="stat"><b>{system_count}</b><span>systems</span></div>
<div class="stat"><b>{len(variants)}</b><span>variants</span></div>
<div class="stat"><b>{len(pain_points)}</b><span>pain points</span></div>
</div>
</header>

<section class="section">
<div class="section-title"><strong>Actual execution</strong><span>Actor · system · input · output · observed time · target</span></div>
<table>
<thead><tr><th style="width:3%">#</th><th style="width:17%">Step</th><th style="width:11%">Actor</th><th style="width:11%">System</th><th style="width:14%">Input</th><th style="width:14%">Output</th><th style="width:9%">Touch</th><th style="width:9%">Wait</th><th style="width:9%">Target</th></tr></thead>
<tbody>{"".join(rows)}</tbody>
</table>
</section>

<div class="grid">
<section class="panel"><h2>Variants & exceptions</h2>{"".join(variant_cards) or "<div class='empty'>No variants recorded.</div>"}</section>
<section class="panel"><h2>Pain points with evidence</h2>{"".join(pain_cards) or "<div class='empty'>No evidence-backed pain points recorded.</div>"}</section>
<section class="panel"><h2>Ownership</h2>{"".join(ownership_rows) or "<div class='empty'>No step-level ownership recorded.</div>"}</section>
</div>

<section class="section">
<div class="section-title"><strong>Data flow</strong><span>Movement and source-of-truth responsibility</span></div>
<div style="padding:10px 12px"><div class="flows">{"".join(flow_cards) or "<div class='empty'>No data flows recorded.</div>"}</div></div>
</section>

<footer><span>Process as Code · Process Analysis Canvas</span><span>Process owner: {_html(role_names.get(str(meta.get("owner")), meta.get("owner")))}</span></footer>
</main>
</body>
</html>
"""


def to_markdown(data: dict[str, Any]) -> str:
    meta = data.get("process", {})
    lines = [f'# {meta.get("name", meta.get("id", "Process"))}', ""]
    if meta.get("description"):
        lines += [meta["description"], ""]
    summary = [("Process ID", meta.get("id")), ("Owner", meta.get("owner")), ("Trigger", meta.get("trigger")), ("Outcome", meta.get("outcome")), ("Version", data.get("version"))]
    lines += ["## Summary", "", "| Field | Value |", "| --- | --- |"]
    for key, value in summary:
        if value:
            lines.append(f"| {key} | {value} |")
    lines += ["", "## Flow", "", "```mermaid", to_mermaid(data).rstrip(), "```", ""]
    lines += ["## Steps", "", "| # | ID | Step | Actor | System | Input | Output | Touch | Wait | SLA |", "| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for idx, step in enumerate(data.get("steps", []), 1):
        if not isinstance(step, dict):
            continue
        sla = step.get("sla") or {}
        timing = step.get("timing") or {}
        sla_value = sla.get("duration") if isinstance(sla, dict) else ""
        touch = timing.get("touch_time") if isinstance(timing, dict) else ""
        wait = timing.get("wait_time") if isinstance(timing, dict) else ""
        lines.append(
            f"| {idx} | `{step.get('id', '')}` | {step.get('name', '')} | {step.get('actor', '')} | {step.get('system', '')} | "
            f"{_contract_list(step.get('inputs'))} | {_contract_list(step.get('outputs'))} | {touch or ''} | {wait or ''} | {sla_value or ''} |"
        )
    for section, title in (("controls", "Controls"), ("risks", "Risks"), ("evidence", "Evidence"), ("interfaces", "Interfaces"), ("objects", "Business objects"), ("artifacts", "Linked artifacts")):
        items = data.get(section, []) or []
        if items:
            lines += ["", f"## {title}", ""]
            for item in items:
                if isinstance(item, dict):
                    description = item.get("description") or item.get("name") or item.get("uri") or ""
                    lines.append(f"- `{item.get('id', '')}` — {description}")
    return "\n".join(lines).rstrip() + "\n"
