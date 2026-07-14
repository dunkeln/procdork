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
    x: { label: displayLabel(chart.dimension) },
    y: { grid: true, label: displayLabel(chart.value) },
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
  const cellSize = Math.max(14, Math.min(30, Math.floor((plotWidth(target) - margins.left - margins.right) / xCount)));
  const cutoff = valueCutoff(data, chart.value);
  const marks = [
    Plot.cell(data, {
      x: "__x",
      y: chart.series,
      fill: chart.value,
      inset: 1,
      title: tooltip(chart),
    }),
  ];

  if (cellSize >= 22) {
    marks.push(
      Plot.text(data, {
        x: "__x",
        y: chart.series,
        text: (d) => formatCellValue(d[chart.value]),
        fill: (d) => (numberValue(d[chart.value]) >= cutoff ? "#fff" : "#000"),
        fontSize: 10,
        fontWeight: "700",
        pointerEvents: "none",
      }),
    );
  }

  return Plot.plot({
    width: margins.left + margins.right + cellSize * xCount,
    height: margins.top + margins.bottom + cellSize * yCount,
    marginTop: margins.top,
    marginRight: margins.right,
    marginBottom: margins.bottom,
    marginLeft: margins.left,
    x: { label: displayLabel(chart.dimension), tickSize: 0 },
    y: { label: displayLabel(chart.series ?? ""), tickSize: 0 },
    color: { label: displayLabel(chart.value), legend: true, type: "linear", range: HEAT_COLORS },
    style: plotStyle(),
    marks,
  } satisfies PlotOptions);
}

function renderContinuousHeatmap(Plot: PlotModule, target: HTMLElement, chart: ChartViewModel): HTMLElement | SVGSVGElement {
  return Plot.plot({
    width: plotWidth(target),
    height: 280,
    marginTop: 24,
    marginRight: 18,
    marginBottom: 42,
    marginLeft: 54,
    x: { label: displayLabel(chart.dimension), grid: true },
    y: { label: displayLabel(chart.series ?? ""), grid: true },
    color: { label: displayLabel(chart.value), legend: true, type: "linear", range: HEAT_COLORS },
    style: plotStyle(),
    marks: [
      Plot.rect(
        continuousHeatmapData(chart),
        Plot.bin(
          { fill: "count" },
          {
            x: "__x",
            y: "__y",
          },
        ),
      ),
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

function continuousHeatmapData(chart: ChartViewModel): PlotDatum[] {
  return chart.data.map((datum) => ({
    ...datum,
    __x: continuousValue(datum[chart.dimension]),
    __y: continuousValue(datum[chart.series ?? ""]),
  }));
}

function hasContinuousAxis(data: ChartDatum[], column: string): boolean {
  const values = data.filter((datum) => datum[column] != null);
  return values.length > 0 && values.every((datum) => continuousValue(datum[column]) != null);
}

function continuousValue(value: unknown): number | Date | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value !== "string") return null;

  const number = Number(value);
  if (Number.isFinite(number)) return number;

  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? new Date(timestamp) : null;
}

function valueCutoff(data: PlotDatum[], valueColumn: string): number {
  const values = data.map((datum) => numberValue(datum[valueColumn])).filter(Number.isFinite);
  if (!values.length) return Number.POSITIVE_INFINITY;
  return Math.min(...values) + (Math.max(...values) - Math.min(...values)) * 0.58;
}

function numberValue(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : Number.NaN;
}

function formatCellValue(value: unknown): string {
  const number = numberValue(value);
  return Number.isFinite(number)
    ? new Intl.NumberFormat("en-US", {
        maximumFractionDigits: 1,
        notation: Math.abs(number) >= 1000 ? "compact" : "standard",
      }).format(number)
    : "";
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
    background: "transparent",
    color: "#000",
    fontFamily: "inherit",
    fontSize: "12px",
  };
}

function plotWidth(target: HTMLElement): number {
  return Math.max(target.clientWidth || 560, 320);
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
