# Procdork Chart MCP App

Isolated Svelte island for rendering MCP tool results. This follows the MCP App
shape used by frameworks like `mcp-use`: the server returns structured widget
props plus a short text message; the widget only renders those props.

Boundary:

- This app receives data from the MCP host.
- It does not query DuckDB or MotherDuck.
- It does not read OKF files.
- It does not import Python harness code.
- Python registers and serves the built `src/harness/chartui/mcp-app.html`.

Contract:

- Python returns `structuredContent` with `title`, `chart_kind`, `columns`,
  `rows`, `facts`, `key_facts`, and `truncated`.
- ChartUI normalizes that payload in `src/chart-contract.ts`.
- ECharts renders the normalized view model in `src/plot-renderer.ts`.
- The text result remains the fallback for clients that do not show the app.

Commands:

```sh
bun install
bun run build
bun run preview
```

Preview URL:

```text
http://127.0.0.1:5180/mcp-app.html?mock=1
http://127.0.0.1:5180/mcp-app.html?mock=heatmap
http://127.0.0.1:5180/mcp-app.html?mock=scatter
http://127.0.0.1:5180/mcp-app.html?mock=bubble
http://127.0.0.1:5180/mcp-app.html?mock=histogram
http://127.0.0.1:5180/mcp-app.html?mock=box
```
