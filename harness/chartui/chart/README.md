# Procdork Chart MCP App

Isolated Svelte island for rendering MCP tool results.

Boundary:

- This app receives data from the MCP host.
- It does not query DuckDB or MotherDuck.
- It does not read OKF files.
- It does not import Python harness code.
- Python registers and serves the built `dist/mcp-app.html` later.

Commands:

```sh
bun install
bun run build
```

