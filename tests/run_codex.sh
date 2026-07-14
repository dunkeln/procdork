#!/usr/bin/env bash
set -euo pipefail

: "${E2E_MCP_URL:?E2E_MCP_URL is required}"
: "${E2E_RUN_ID:?E2E_RUN_ID is required}"
: "${E2E_TRACEPARENT:?E2E_TRACEPARENT is required}"

prompt_file="$1"

exec codex exec \
  --ephemeral \
  --sandbox read-only \
  --ignore-user-config \
  -c "mcp_servers.procdork.url=\"${E2E_MCP_URL}\"" \
  -c "mcp_servers.procdork.http_headers={traceparent=\"${E2E_TRACEPARENT}\", \"X-E2E-Run-ID\"=\"${E2E_RUN_ID}\"}" \
  --json \
  - < "$prompt_file"
