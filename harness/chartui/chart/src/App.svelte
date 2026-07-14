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
  let hiddenSegments: string[] = [];
  let app: McpApp | null = null;
  let chartEl: HTMLDivElement;
  const renderer = createPlotRenderer(Plot);

  $: segmentOptions = chart ? chartSegments(chart) : [];
  $: renderedChart = chart ? filterSegments(chart, hiddenSegments) : null;
  $: if (chartEl && renderedChart) {
    renderer.render(chartEl, renderedChart);
  }

  onMount(() => {
    if (new URLSearchParams(window.location.search).has("mock")) {
      setChart(normalizeChartPayload({
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
      }));
      status = "Mock result";
      return;
    }

    app = new McpApp({ name: "Procdork Chart", version: "0.1.0" });

    app.ontoolresult = (toolResult) => {
      setChart(normalizeChartPayload(toolResult.structuredContent ?? {}));
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

  function setChart(view: ChartViewModel | null): void {
    chart = view;
    hiddenSegments = [];
  }

  function chartSegments(view: ChartViewModel): string[] {
    if (!view.series || view.chart_kind === "heatmap" || view.chart_kind === "table") return [];
    return Array.from(new Set(view.data.map((datum) => String(datum[view.series ?? ""] ?? "")))).filter(Boolean);
  }

  function toggleSegment(segment: string): void {
    const hidden = hiddenSegments.includes(segment);
    if (!hidden && segmentOptions.length - hiddenSegments.length <= 1) return;
    hiddenSegments = hidden
      ? hiddenSegments.filter((item) => item !== segment)
      : [...hiddenSegments, segment];
  }

  function filterSegments(view: ChartViewModel, hiddenItems: string[]): ChartViewModel {
    if (!view.series || hiddenItems.length === 0) return view;
    const hidden = new Set(hiddenItems);
    const seriesIndex = view.columns.indexOf(view.series);
    const rows = view.rows.filter((row) => !hidden.has(String(row[seriesIndex] ?? "")));
    const data = view.data.filter((datum) => !hidden.has(String(datum[view.series ?? ""] ?? "")));
    return {
      ...view,
      rows,
      data,
      facts: {
        ...view.facts,
        row_count: rows.length,
        group_count: view.facts.group_count === undefined ? undefined : new Set(data.map((datum) => datum[view.dimension])).size,
        segment_count: view.facts.segment_count === undefined ? undefined : chartSegments({ ...view, data }).length,
        total: view.facts.total === undefined ? undefined : data.reduce((sum, datum) => sum + numberValue(datum[view.value]), 0),
        max_group: view.facts.max_group ? maxGroup(view, data) : undefined,
      },
    };
  }

  function maxGroup(view: ChartViewModel, data: ChartViewModel["data"]): ChartViewModel["facts"]["max_group"] {
    const totals = new Map<string, number>();
    data.forEach((datum) => {
      const label = String(datum[view.dimension] ?? "");
      totals.set(label, (totals.get(label) ?? 0) + numberValue(datum[view.value]));
    });
    return Array.from(totals, ([label, value]) => ({ label, value })).sort((a, b) => b.value - a.value)[0];
  }

  function numberValue(value: unknown): number {
    return typeof value === "number" && Number.isFinite(value) ? value : 0;
  }
</script>

<main class="shell">
  {#if chart && renderedChart}
    <header>
      <span>{chart.chart_kind}</span>
      <h1>Analytics</h1>
      <i aria-hidden="true"></i>
    </header>

    {#if segmentOptions.length > 1}
      <div class="segments" aria-label="Visible series">
        {#each segmentOptions as segment}
          <button
            type="button"
            class:muted={hiddenSegments.includes(segment)}
            aria-pressed={!hiddenSegments.includes(segment)}
            on:click={() => toggleSegment(segment)}
          >
            {segment}
          </button>
        {/each}
      </div>
    {/if}

    <div class="chart-host" bind:this={chartEl} aria-label={chart.title}></div>

    <dl class="summary" aria-label="Chart summary">
      {#each summaryItems(renderedChart) as item}
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

  .segments {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin: -8px 0 12px;
  }

  .segments button {
    border: 1px solid rgb(0 0 0 / 18%);
    border-radius: 999px;
    background: #fff;
    color: #000;
    padding: 4px 9px;
    cursor: pointer;
    font-size: 12px;
    font-weight: 700;
  }

  .segments button.muted {
    background: rgb(255 255 255 / 45%);
    color: rgb(0 0 0 / 42%);
    text-decoration: line-through;
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
