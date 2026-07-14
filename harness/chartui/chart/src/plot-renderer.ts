import type { ChartDatum, ChartViewModel, HeatmapMode } from "./chart-contract";

type PlotModule = typeof import("@observablehq/plot");
type PlotOptions = Parameters<PlotModule["plot"]>[0];
type PlotDatum = Record<string, unknown>;

const SERIES_COLORS = ["#2274A5", "#78C091", "#87B3D4", "#131B23", "#816C61"];
const HEAT_COLORS = ["#edf6f9", "#87B3D4", "#2274A5", "#131B23"];

export function createPlotRenderer(Plot: PlotModule) {
  return {
    render(target: HTMLElement, chart: ChartViewModel) {
      target.replaceChildren(
        chart.chart_kind === "table" ? renderTable(chart) : renderPlot(Plot, target, chart),
      );
    },
  };
}

function renderPlot(Plot: PlotModule, target: HTMLElement, chart: ChartViewModel): HTMLElement | SVGSVGElement {
  if (chart.chart_kind === "heatmap") return renderHeatmap(Plot, target, chart);

  const markOptions = {
    x: chart.dimension,
    y: chart.value,
    title: tooltip(chart),
  };

  return Plot.plot({
    width: plotWidth(target),
    height: 260,
    marginTop: 12,
    marginRight: 18,
    marginBottom: 48,
    marginLeft: 54,
    x: { label: null },
    y: { grid: true, label: null },
    color: chart.series
      ? { label: displayLabel(chart.series), legend: true, range: SERIES_COLORS }
      : undefined,
    style: plotStyle(),
    marks:
      chart.chart_kind === "line"
        ? [
            Plot.ruleY([0]),
            Plot.lineY(chart.data, {
              ...markOptions,
              stroke: chart.series ?? "#000",
              z: chart.series,
              marker: true,
            }),
          ]
        : [
            Plot.ruleY([0]),
            Plot.barY(chart.data, {
              ...markOptions,
              fill: chart.series ?? "#000",
              z: chart.series,
              inset: 2,
            }),
          ],
  } satisfies PlotOptions);
}

function renderHeatmap(Plot: PlotModule, target: HTMLElement, chart: ChartViewModel): HTMLElement | SVGSVGElement {
  return resolveHeatmapMode(chart) === "continuous"
    ? renderContinuousHeatmap(Plot, target, chart)
    : renderCategoricalHeatmap(Plot, target, chart);
}

function renderCategoricalHeatmap(Plot: PlotModule, target: HTMLElement, chart: ChartViewModel): HTMLElement | SVGSVGElement {
  const data = compactHeatmapData(chart);
  const xCount = new Set(data.map((datum) => datum.__x)).size || 1;
  const yCount = new Set(data.map((datum) => datum[chart.series ?? ""])).size || 1;
  const margins = { top: 30, right: 18, bottom: 34, left: 84 };
  const width = plotWidth(target);

  return Plot.plot({
    width,
    height: heatmapHeight(width, yCount),
    marginTop: margins.top,
    marginRight: margins.right,
    marginBottom: margins.bottom,
    marginLeft: margins.left,
    x: { label: displayLabel(chart.dimension), tickSize: 0 },
    y: { label: displayLabel(chart.series ?? ""), tickSize: 0 },
    color: { label: displayLabel(chart.value), legend: true, type: "linear", range: HEAT_COLORS },
    style: plotStyle(),
    marks: [
      Plot.cell(data, {
        x: "__x",
        y: chart.series,
        fill: chart.value,
        inset: xCount * yCount > 80 ? 0.4 : 1,
        title: tooltip(chart),
      }),
    ],
  } satisfies PlotOptions);
}

function renderContinuousHeatmap(Plot: PlotModule, target: HTMLElement, chart: ChartViewModel): HTMLElement | SVGSVGElement {
  const width = plotWidth(target);
  const columns = Math.max(24, Math.min(42, Math.floor((width - 88) / 18)));
  const rows = Math.max(16, Math.min(38, Math.round(columns * 0.72)));
  const cell = Math.max(14, Math.min(20, Math.floor((width - 96) / columns)));
  return Plot.plot({
    width: Math.max(520, 76 + columns * cell),
    height: Math.max(340, 52 + rows * cell),
    marginTop: 24,
    marginRight: 18,
    marginBottom: 42,
    marginLeft: 54,
    x: { axis: null },
    y: { axis: null },
    color: { label: displayLabel(chart.value), legend: true, type: "linear", range: HEAT_COLORS },
    style: plotStyle(),
    marks: [
      Plot.cell(squareHeatmapData(chart, columns, rows), {
        x: "__x",
        y: "__y",
        fill: "count",
        inset: 1.7,
        title: (datum) =>
          `${displayLabel(chart.dimension)} bin: ${datum.__x}\n${displayLabel(chart.series ?? "")} bin: ${datum.__y}\nCount: ${datum.count}`,
      }),
    ],
  } satisfies PlotOptions);
}

function resolveHeatmapMode(chart: ChartViewModel): Exclude<HeatmapMode, "auto" | "calendar"> {
  if (chart.heatmap_mode === "continuous") return "continuous";
  if (chart.heatmap_mode === "categorical" || chart.heatmap_mode === "calendar") return "categorical";
  return chart.series && hasContinuousAxis(chart.data, chart.dimension) && hasContinuousAxis(chart.data, chart.series)
    ? "continuous"
    : "categorical";
}

function compactHeatmapData(chart: ChartViewModel): PlotDatum[] {
  const labels = new Map<unknown, string>();
  return chart.data.map((datum) => {
    const category = datum[chart.dimension];
    if (!labels.has(category)) labels.set(category, String(labels.size + 1));
    return { ...datum, __x: labels.get(category) ?? "" };
  });
}

function hasContinuousAxis(data: ChartDatum[], column: string): boolean {
  const values = data.filter((datum) => datum[column] != null);
  return values.length > 0 && values.every((datum) => continuousValue(datum[column]) != null);
}

function squareHeatmapData(chart: ChartViewModel, columns: number, rows: number): PlotDatum[] {
  const points = chart.data
    .map((datum) => ({
      x: continuousValue(datum[chart.dimension]),
      y: continuousValue(datum[chart.series ?? ""]),
    }))
    .filter((point): point is { x: number | Date; y: number | Date } => point.x != null && point.y != null);
  if (!points.length) return [];

  const xs = points.map((point) => Number(point.x));
  const ys = points.map((point) => Number(point.y));
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const counts = new Map<string, number>();

  for (const point of points) {
    const x = clamp(Math.floor(((Number(point.x) - minX) / (maxX - minX || 1)) * columns), 0, columns - 1);
    const y = clamp(Math.floor(((Number(point.y) - minY) / (maxY - minY || 1)) * rows), 0, rows - 1);
    const key = `${x}:${rows - y - 1}`;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  return Array.from(counts, ([key, count]) => {
    const [x, y] = key.split(":").map(Number);
    return { __x: x, __y: y, count };
  });
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function continuousValue(value: unknown): number | Date | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value !== "string") return null;

  const number = Number(value);
  if (Number.isFinite(number)) return number;

  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? new Date(timestamp) : null;
}

function tooltip(chart: ChartViewModel): (datum: Record<string, unknown>) => string {
  return (datum) =>
    chart.columns.map((column) => `${displayLabel(column)}: ${String(datum[column] ?? "")}`).join("\n");
}

function displayLabel(column: string): string {
  return column.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function plotStyle() {
  return {
    background: "#edf6f9",
    color: "#000",
    fontFamily: "inherit",
    fontSize: "12px",
  };
}

function plotWidth(target: HTMLElement): number {
  return Math.max(target.clientWidth || 560, 320);
}

function heatmapHeight(width: number, yCount = 10): number {
  return Math.max(260, Math.min(520, Math.round(width * 0.68), yCount * 34 + 92));
}

function renderTable(chart: ChartViewModel): HTMLTableElement {
  const table = document.createElement("table");
  const thead = table.createTHead();
  const header = thead.insertRow();
  chart.columns.forEach((column) => {
    header.appendChild(document.createElement("th")).textContent = displayLabel(column);
  });

  const tbody = table.createTBody();
  chart.rows.forEach((row) => {
    const tr = tbody.insertRow();
    row.forEach((value) => {
      tr.appendChild(document.createElement("td")).textContent = value == null ? "" : String(value);
    });
  });
  return table;
}
