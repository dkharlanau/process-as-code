# Static Process Catalog

`process-code catalog <root> -o <site>` discovers validated `*.process.yaml`, `*.process.yml`, and `*.process.json` files, resolves reusable catalogs, and generates a zero-backend static knowledge surface.

## What is generated

- searchable process index;
- stable process URLs;
- rendered Mermaid process diagrams in the browser;
- process metadata and step/dependency tables;
- RACI;
- search tokens for roles, systems, business objects, interfaces, controls, risks, evidence and process tags;
- practical problem-oriented guide pages;
- `catalog.json`;
- `robots.txt`;
- optional `sitemap.xml` when `--base-url` is supplied;
- canonical and Open Graph metadata when `--base-url` is supplied.

Example:

```bash
process-code catalog examples -o site \
  --base-url https://example.github.io/process-as-code
```

The catalog remains static: no backend or database is required. Mermaid is rendered client-side with a pinned major CDN module and `securityLevel: strict`.

## Problem-oriented entry points

The generated site and [`docs/guides/`](guides/README.md) cover concrete entry points instead of only the product name:

- BPMN version control with Git;
- business process as YAML;
- semantic BPMN/process diff;
- business process change impact analysis;
- process governance as code;
- regression test scope from process changes;
- MCP/business-process context for AI agents;
- SAP process documentation in Git.

The Markdown versions remain useful and indexable directly on GitHub before Pages is activated.

## GitHub Pages

For the first deployment, enable Pages for the repository with **Source = GitHub Actions**, then manually run the included **Process Catalog Pages** workflow. No repository variable is required for that first deployment.

Optionally set repository variable `PAGES_ENABLED=true` afterwards to deploy the catalog automatically on every push to `main`.
