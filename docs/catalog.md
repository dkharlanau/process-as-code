# Static Process Catalog

`process-code catalog <root> -o <site>` discovers validated `*.process.yaml`, `*.process.yml`, and `*.process.json` files, resolves reusable catalogs, and generates a zero-backend static catalog.

Outputs include:

- searchable process index;
- stable process URLs;
- process metadata and step/dependency tables;
- RACI;
- Mermaid source;
- problem-oriented guide pages;
- `catalog.json`;
- `robots.txt`;
- optional `sitemap.xml` when `--base-url` is supplied.

For GitHub Pages, enable Pages for the repository with **Source = GitHub Actions**, then set repository variable `PAGES_ENABLED=true`. The included Pages workflow builds and deploys the catalog from examples as the public reference site.
