<script lang="ts">
  import { App as McpApp, applyDocumentTheme, applyHostStyleVariables } from "@modelcontextprotocol/ext-apps";
  import * as Plot from "@observablehq/plot";
  import { onMount } from "svelte";
  import { normalizeChartPayload } from "./chart-contract";
  import type { ChartViewModel } from "./chart-contract";
  import { createPlotRenderer } from "./plot-renderer";

  type SummaryItem = { label: string; value: string };

  let status = "Connecting...";
  let chart: ChartViewModel | null = null;
  let app: McpApp | null = null;
  let chartEl: HTMLDivElement;
  const renderer = createPlotRenderer(Plot);

  $: if (chartEl && chart) {
    renderer.render(chartEl, chart);
  }

  onMount(() => {
    if (new URLSearchParams(window.location.search).has("mock")) {
      chart = normalizeChartPayload({
        title: "Analytics",
        chart_kind: "bar",
        columns: ["evidence_type", "status", "count"],
        rows: [
          ["citation", "accepted", 19],
          ["citation", "review", 10],
          ["source", "accepted", 12],
          ["source", "review", 6],
          ["tool", "accepted", 5],
          ["tool", "review", 2],
        ],
        facts: {
          row_count: 6,
          column_count: 3,
          group_count: 3,
          segment_count: 2,
          total: 54,
          max_group: { label: "citation", value: 29 },
          truncated: false,
        },
        key_facts: [
          "3 evidence types plotted.",
          "Highest total count: 29 at citation.",
          "Displayed total count: 54.",
        ],
        truncated: false,
      });
      status = "Mock result";
      return;
    }

    app = new McpApp({ name: "Procdork Chart", version: "0.1.0" });

    app.ontoolresult = (toolResult) => {
      chart = normalizeChartPayload(toolResult.structuredContent ?? {});
      status = chart ? "Ready" : "No chartable result";
    };

    app.onhostcontextchanged = (ctx) => {
      if (ctx.theme) applyDocumentTheme(ctx.theme);
      if (ctx.styles?.variables) applyHostStyleVariables(ctx.styles.variables);
    };

    app.onerror = (error) => {
      console.error(error);
      status = "MCP App error";
    };

    app.connect().then(() => {
      const ctx = app?.getHostContext();
      if (ctx?.theme) applyDocumentTheme(ctx.theme);
      if (ctx?.styles?.variables) applyHostStyleVariables(ctx.styles.variables);
      status = "Waiting for chart data";
    });
  });

  function summaryItems(view: ChartViewModel): SummaryItem[] {
    const items: SummaryItem[] = [];
    if (view.facts.total !== undefined) {
      items.push({ label: "Total", value: formatNumber(view.facts.total) });
    } else {
      items.push({ label: "Rows", value: formatNumber(view.facts.row_count) });
    }
    if (view.facts.max_group) {
      items.push({
        label: "Peak",
        value: `${view.facts.max_group.label} ${formatNumber(view.facts.max_group.value)}`,
      });
    }
    items.push({
      label: view.facts.segment_count !== undefined ? "Segments" : "Columns",
      value: formatNumber(view.facts.segment_count ?? view.facts.column_count),
    });
    return items;
  }

  function formatNumber(value: number): string {
    return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
  }
</script>

<main class="shell">
  {#if chart}
    <header>
      <span>{chart.chart_kind}</span>
      <h1>Analytics</h1>
      <i aria-hidden="true"></i>
    </header>

    <div class="chart-host" bind:this={chartEl} aria-label={chart.title}></div>

    <dl class="summary" aria-label="Chart summary">
      {#each summaryItems(chart) as item}
        <div>
          <dt>{item.label}</dt>
          <dd>{item.value}</dd>
        </div>
      {/each}
    </dl>
  {:else}
    <p class="status">{status}</p>
  {/if}
</main>

<style>
  .shell {
    box-sizing: border-box;
    width: 100%;
    min-height: 100vh;
    padding: 16px;
    background: transparent;
    color: #000;
  }

  header {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 12px;
    margin-bottom: 18px;
    text-align: center;
  }

  .chart-host {
    min-height: 260px;
    margin-bottom: 14px;
  }

  .chart-host :global(svg),
  .chart-host :global(figure) {
    display: block;
    max-width: 100%;
    margin: 0;
  }

  .chart-host :global(table) {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }

  .chart-host :global(th),
  .chart-host :global(td) {
    padding: 8px 6px;
    border-bottom: 1px solid rgb(0 0 0 / 12%);
    text-align: left;
  }

  .chart-host :global(th) {
    font-weight: 700;
  }

  h1 {
    margin: 0;
    font-size: 18px;
    line-height: 1.2;
  }

  span {
    justify-self: start;
    background: #fff;
    border: 1px solid rgb(0 0 0 / 18%);
    border-radius: 999px;
    padding: 3px 8px;
    font-size: 12px;
    color: #000;
  }

  .summary {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
    margin: 0;
  }

  .summary div {
    min-width: 0;
    background: rgb(255 255 255 / 76%);
    border: 1px solid rgb(0 0 0 / 13%);
    border-radius: 8px;
    padding: 10px 12px;
  }

  dt {
    margin-bottom: 3px;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    color: rgb(0 0 0 / 58%);
  }

  dd {
    margin: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 14px;
    font-weight: 800;
  }

  .status {
    margin: 0;
    color: rgb(0 0 0 / 70%);
  }
</style>
