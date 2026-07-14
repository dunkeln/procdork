#!/usr/bin/env bash
set -euo pipefail

: "${E2E_MCP_URL:?E2E_MCP_URL is required}"
: "${E2E_RUN_ID:?E2E_RUN_ID is required}"
: "${E2E_TRACEPARENT:?E2E_TRACEPARENT is required}"

prompt_file="$1"
config_file="$(mktemp)"
trap 'rm -f "$config_file"' EXIT

printf '%s' "{\"mcpServers\":{\"procdork\":{\"type\":\"http\",\"url\":\"${E2E_MCP_URL}\",\"headers\":{\"traceparent\":\"${E2E_TRACEPARENT}\",\"X-E2E-Run-ID\":\"${E2E_RUN_ID}\"}}}}" > "$config_file"

claude \
  --print \
  --verbose \
  --output-format stream-json \
  --no-session-persistence \
  --strict-mcp-config \
  --mcp-config "$config_file" \
  --permission-mode plan \
  "$(<"$prompt_file")"
