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

For the first GitHub Pages deployment, enable Pages for the repository with **Source = GitHub Actions**, then manually run the included **Process Catalog Pages** workflow. No repository variable is required for that first deployment.

Optionally set repository variable `PAGES_ENABLED=true` afterwards to deploy the catalog automatically on every push to `main`.
