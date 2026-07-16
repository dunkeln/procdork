<script lang="ts">
  import { App as McpApp, applyHostStyleVariables } from "@modelcontextprotocol/ext-apps";
  import { onDestroy, onMount } from "svelte";
  import { normalizeChartPayload } from "./chart-contract";
  import type { ChartViewModel } from "./chart-contract";
  import { createPlotRenderer } from "./plot-renderer";

  type StatItem = { label: string; value: string };

  let status = "Connecting...";
  let chart: ChartViewModel | null = null;
  let app: McpApp | null = null;
  let chartEl: HTMLDivElement;
  let chartWidth = 0;
  let observedEl: HTMLDivElement | undefined;
  let resizeObserver: ResizeObserver | undefined;
  const renderer = createPlotRenderer();

  $: yAxisLabel = chart && chart.chart_kind !== "heatmap" ? (chart.chart_kind === "histogram" ? "Count" : displayLabel(chart.value)) : "";
  $: xAxisLabel = chart && chart.chart_kind !== "heatmap" ? displayLabel(chart.dimension) : "";
  $: if (chartEl && chartEl !== observedEl) {
    resizeObserver?.disconnect();
    observedEl = chartEl;
    resizeObserver = new ResizeObserver(() => {
      chartWidth = chartEl.clientWidth;
    });
    resizeObserver.observe(chartEl);
    chartWidth = chartEl.clientWidth;
  }
  $: if (chartEl && chart) {
    chartWidth;
    renderer.render(chartEl, chart);
  }

  onMount(() => {
    const mock = new URLSearchParams(window.location.search).get("mock");
    if (mock !== null) {
      chart = normalizeChartPayload(mockPayload(mock));
      status = "Mock result";
      return;
    }

    app = new McpApp({ name: "Procdork Chart", version: "0.1.0" });

    app.ontoolresult = (toolResult) => {
      chart = normalizeChartPayload(toolResult.structuredContent ?? {});
      status = chart ? "Ready" : "No chartable result";
    };

    app.onhostcontextchanged = (ctx) => {
      if (ctx.styles?.variables) applyHostStyleVariables(ctx.styles.variables);
    };

    app.onerror = (error) => {
      console.error(error);
      status = "MCP App error";
    };

    app.connect().then(() => {
      const ctx = app?.getHostContext();
      if (ctx?.styles?.variables) applyHostStyleVariables(ctx.styles.variables);
      status = "Waiting for chart data";
    });
  });

  onDestroy(() => resizeObserver?.disconnect());

  function mockPayload(mock: string) {
    if (mock === "heatmap") return heatmapMock();
    if (mock === "band") return bandMock();
    if (mock === "scatter") return scatterMock();
    if (mock === "bubble") return bubbleMock();
    if (mock === "histogram") return histogramMock();
    if (mock === "box") return boxMock();
    return barMock();
  }

  function barMock() {
    return {
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
      key_facts: [],
      truncated: false,
    };
  }

  function heatmapMock() {
    const rows = Array.from({ length: 180 }, (_, index) => {
      const x = 0.25 + (index % 45) / 18;
      const band = Math.floor(index / 45);
      const y = 800 + x * x * 2200 + band * 1700 + Math.sin(index * 1.7) * 480;
      return [x, Math.max(300, y), 1];
    });
    return {
      title: "Analytics",
      chart_kind: "heatmap",
      heatmap_mode: "continuous",
      columns: ["carat", "price", "count"],
      rows,
      facts: {
        row_count: rows.length,
        column_count: 3,
        group_count: rows.length,
        segment_count: rows.length,
        truncated: false,
      },
      key_facts: [],
      truncated: false,
    };
  }

  function bandMock() {
    return {
      title: "Judge Drift",
      chart_kind: "line",
      columns: ["evaluated_day", "dimension", "rolling_average_score", "lower_score", "upper_score"],
      rows: [
        ["2026-07-12", "grounding", 3.1, 2.6, 3.6],
        ["2026-07-13", "grounding", 3.4, 2.8, 4.0],
        ["2026-07-14", "grounding", 3.2, 2.5, 3.9],
        ["2026-07-12", "consistency", 3.8, 3.4, 4.2],
        ["2026-07-13", "consistency", 3.7, 3.1, 4.3],
        ["2026-07-14", "consistency", 3.9, 3.5, 4.3],
      ],
      facts: {
        row_count: 6,
        column_count: 5,
        group_count: 3,
        segment_count: 2,
        truncated: false,
      },
      key_facts: [],
      truncated: false,
    };
  }

  function scatterMock() {
    const rows = Array.from({ length: 42 }, (_, index) => [
      80 + index * 12,
      2.2 + Math.sin(index / 5) + index / 34,
      index % 2 ? "harness" : "raw_sql",
    ]);
    return {
      title: "Latency vs Quality",
      chart_kind: "scatter",
      columns: ["elapsed_ms", "quality_score", "treatment"],
      rows,
      facts: { row_count: rows.length, column_count: 3, truncated: false },
      key_facts: [],
      truncated: false,
    };
  }

  function bubbleMock() {
    return {
      title: "Supplier Evidence Tradeoff",
      chart_kind: "bubble",
      columns: ["evidence_source_count", "claim_count", "open_conflict_count", "supplier_confidence"],
      rows: [
        [1, 5, 0, "medium"],
        [1, 6, 2, "medium"],
        [3, 11, 1, "high"],
        [4, 8, 0, "high"],
        [2, 4, 3, "low"],
      ],
      facts: { row_count: 5, column_count: 4, truncated: false },
      key_facts: [],
      truncated: false,
    };
  }

  function histogramMock() {
    const rows = Array.from({ length: 120 }, (_, index) => [240 + Math.sin(index * 1.7) * 90 + (index % 9) * 45]);
    return {
      title: "Session Duration Distribution",
      chart_kind: "histogram",
      columns: ["duration_seconds"],
      rows,
      facts: { row_count: rows.length, column_count: 1, truncated: false },
      key_facts: [],
      truncated: false,
    };
  }

  function boxMock() {
    const rows = ["harness", "raw_sql", "operator"].flatMap((treatment, treatmentIndex) =>
      ["sourcing", "quality"].flatMap((caseFamily, familyIndex) =>
        Array.from({ length: 18 }, (_, index) => [
          caseFamily,
          treatment,
          500 + treatmentIndex * 260 + familyIndex * 140 + Math.sin(index * 1.9) * 120,
        ]),
      ),
    );
    return {
      title: "Elapsed Time by Treatment",
      chart_kind: "box",
      columns: ["case_family", "treatment", "elapsed_ms"],
      rows,
      facts: { row_count: rows.length, column_count: 3, truncated: false },
      key_facts: [],
      truncated: false,
    };
  }

  function statsItems(view: ChartViewModel): StatItem[] {
    const values = view.data
      .map((datum) => finiteNumber(datum[view.value]))
      .filter((value) => Number.isFinite(value))
      .sort((left, right) => left - right);
    if (!values.length) {
      return [
        { label: "Rows", value: formatNumber(view.facts.row_count) },
        { label: "Columns", value: formatNumber(view.facts.column_count) },
      ];
    }
    return [
      { label: "Count", value: formatNumber(values.length) },
      { label: "Min", value: formatNumber(values[0]) },
      { label: "P25", value: formatNumber(quantile(values, 0.25)) },
      { label: "Median", value: formatNumber(quantile(values, 0.5)) },
      { label: "Mean", value: formatNumber(values.reduce((sum, value) => sum + value, 0) / values.length) },
      { label: "P75", value: formatNumber(quantile(values, 0.75)) },
      { label: "Max", value: formatNumber(values[values.length - 1]) },
    ];
  }

  function formatNumber(value: number): string {
    return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
  }

  function quantile(values: number[], q: number): number {
    const index = (values.length - 1) * q;
    const lower = Math.floor(index);
    const upper = Math.ceil(index);
    return values[lower] + (values[upper] - values[lower]) * (index - lower);
  }

  function finiteNumber(value: unknown): number {
    return typeof value === "number" && Number.isFinite(value) ? value : Number.NaN;
  }

  function displayLabel(column: string): string {
    return column.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
  }
</script>

<main class="shell">
  {#if chart}
    <header>
      <h1>{chart.title || "Analytics"}</h1>
    </header>

    <div class="plot-row">
      <p class="axis-y">{yAxisLabel}</p>
      <div class="chart-host" bind:this={chartEl} aria-label={chart.title}></div>
    </div>
    <p class="axis-x">{xAxisLabel}</p>

    <dl class="summary" aria-label="Value summary">
      {#each statsItems(chart) as item}
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
    background: #edf6f9;
    color: #000;
  }

  header {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 14px;
    text-align: center;
  }

  .plot-row {
    display: grid;
    grid-template-columns: 28px 1fr;
    align-items: center;
    gap: 8px;
  }

  .axis-y {
    margin: 0;
    justify-self: center;
    font-size: 12px;
    color: rgb(0 0 0 / 62%);
    writing-mode: sideways-lr;
  }

  .axis-x {
    margin: 8px 18px 12px 36px;
    text-align: center;
    font-size: 12px;
    line-height: 1.3;
    color: rgb(0 0 0 / 62%);
  }

  .axis-y:empty,
  .axis-x:empty {
    display: none;
  }

  .axis-y:empty + .chart-host {
    grid-column: 1 / -1;
  }

  .chart-host {
    min-width: 0;
    min-height: 260px;
    overflow-x: auto;
    overflow-y: hidden;
  }

  .chart-host :global(svg),
  .chart-host :global(figure),
  .chart-host :global(.chartui-echart) {
    display: block;
    margin: 0 auto;
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

  .summary {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 6px 14px;
    margin: 0 auto;
    max-width: 760px;
  }

  .summary div {
    min-width: 0;
    display: flex;
    gap: 4px;
    color: rgb(0 0 0 / 48%);
  }

  dt {
    margin: 0;
    font-size: 11px;
    font-weight: 500;
  }

  dd {
    margin: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 11px;
    font-weight: 600;
    color: rgb(0 0 0 / 64%);
  }

  .status {
    margin: 0;
    color: rgb(0 0 0 / 70%);
  }
</style>
