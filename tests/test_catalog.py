from __future__ import annotations

from pathlib import Path

from process_as_code.catalog import MERMAID_MODULE, generate_catalog

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://example.test/process-as-code"


def test_catalog_generates_rendered_process_and_searchable_guides(tmp_path: Path) -> None:
    manifest = generate_catalog(ROOT / "examples", tmp_path, BASE)

    assert manifest["process_count"] >= 4
    assert "customer_creation" in manifest["processes"]
    assert "process-change-impact-analysis" in manifest["guides"]
    assert "generate-regression-test-scope-from-process-changes" in manifest["guides"]
    assert "mcp-business-process-context" in manifest["guides"]

    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert '<link rel="canonical" href="https://example.test/process-as-code/index.html">' in index
    assert 'property="og:title"' in index
    assert "sanctions_check" in index
    assert "Search processes, roles, systems, objects, interfaces, controls" in index

    process_page = (tmp_path / "processes/customer-creation.html").read_text(encoding="utf-8")
    assert MERMAID_MODULE in process_page
    assert 'class="mermaid"' in process_page
    assert 'securityLevel:"strict"' in process_page
    assert '<link rel="canonical" href="https://example.test/process-as-code/processes/customer-creation.html">' in process_page
    assert "process-code impact old.process.yaml" in process_page

    guide = (tmp_path / "guides/process-change-impact-analysis.html").read_text(encoding="utf-8")
    assert "The problem" in guide
    assert "Practical workflow" in guide
    assert "process-code impact old.process.yaml new.process.yaml" in guide
    assert "Limitations" in guide
    assert '<link rel="canonical" href="https://example.test/process-as-code/guides/process-change-impact-analysis.html">' in guide

    sitemap = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
    assert f"{BASE}/processes/customer-creation.html" in sitemap
    assert f"{BASE}/guides/mcp-business-process-context.html" in sitemap
