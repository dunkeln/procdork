#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
snapshot=${1:-$(date -u +%Y%m%dT%H%M%SZ)}
output="$root/e2e/snapshots/$snapshot"
mkdir -p "$output"

run() {
    name=$1
    prompt=$2
    codex exec --ephemeral --sandbox read-only --ignore-user-config \
        -c 'mcp_servers.procdork.url="https://procdork.vercel.app/mcp"' \
        --json -o "$output/$name.final.md" "$prompt" \
        >"$output/$name.events.jsonl"
}

run table 'Use only the procdork MCP. Find the available chat summary mart, then return its exact snapshot counts as a table. Preserve the procdork table and key facts verbatim. Do not inspect local files.'

run chart 'Use only the procdork MCP. Find and describe the available chat summary mart, then use a read-only query to return a bar chart comparing its count metrics. Preserve the procdork chart Markdown and key facts verbatim. Do not inspect local files.'

chart_url=$(rg -o 'https://procdork\.vercel\.app/charts/[^"\\ ]+\.svg' "$output/chart.events.jsonl" | head -n 1)
test -n "$chart_url"
printf '%s\n' "$chart_url" >"$output/chart.url"
curl --fail --silent --show-error "$chart_url" >"$output/chart.svg"
printf '%s\n' '<!doctype html><meta charset="utf-8"><title>procdork chart snapshot</title><img src="chart.svg" alt="procdork chart">' >"$output/chart.render.html"

printf '%s\n' "$output"
