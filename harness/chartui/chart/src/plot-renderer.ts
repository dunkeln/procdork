import type { ChartCell, ChartDatum, ChartViewModel, HeatmapMode } from "./chart-contract";

type PlotModule = typeof import("@observablehq/plot");
type PlotOptions = Parameters<PlotModule["plot"]>[0];
type RectYOptions = NonNullable<Parameters<PlotModule["rectY"]>[1]>;
type HeatmapBin = Record<string, unknown> & {
  __x: number;
  __y: number;
  count: number;
  x0: number;
  x1: number;
  y0: number;
  y1: number;
};

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
  if (chart.chart_kind === "scatter" || chart.chart_kind === "bubble") return renderScatter(Plot, target, chart);
  if (chart.chart_kind === "histogram") return renderHistogram(Plot, target, chart);
  if (chart.chart_kind === "box") return renderBox(Plot, target, chart);

  const markOptions = {
    x: chart.dimension,
    y: chart.value,
    title: tooltip(chart),
  };

  const xCount = new Set(chart.data.map((datum) => datum[chart.dimension])).size || 1;

  return Plot.plot({
    width: Math.max(plotWidth(target), 126 + xCount * 96),
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
            ...(chart.lower && chart.upper
              ? [
                  Plot.areaY(chart.data, {
                    x: chart.dimension,
                    y1: chart.lower,
                    y2: chart.upper,
                    fill: chart.series ?? "#000",
                    z: chart.series,
                    opacity: 0.18,
                  }),
                ]
              : []),
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

function renderScatter(Plot: PlotModule, target: HTMLElement, chart: ChartViewModel): HTMLElement | SVGSVGElement {
  return Plot.plot({
    width: plotWidth(target),
    height: 260,
    marginTop: 12,
    marginRight: 18,
    marginBottom: 48,
    marginLeft: 54,
    x: { grid: true, label: null },
    y: { grid: true, label: null },
    r: chart.size ? { range: [3, 16] } : undefined,
    color: chart.series ? { label: displayLabel(chart.series), legend: true, range: SERIES_COLORS } : undefined,
    style: plotStyle(),
    marks: [
      Plot.dot(chart.data, {
        x: chart.dimension,
        y: chart.value,
        r: chart.size ?? 4,
        fill: chart.series ?? SERIES_COLORS[0],
        stroke: "#fff",
        strokeWidth: 0.8,
        fillOpacity: 0.72,
        title: tooltip(chart),
      }),
    ],
  } satisfies PlotOptions);
}

function renderHistogram(Plot: PlotModule, target: HTMLElement, chart: ChartViewModel): HTMLElement | SVGSVGElement {
  return Plot.plot({
    width: plotWidth(target),
    height: 260,
    marginTop: 12,
    marginRight: 18,
    marginBottom: 48,
    marginLeft: 54,
    x: { grid: true, label: null },
    y: { grid: true, label: null },
    color: chart.series ? { label: displayLabel(chart.series), legend: true, range: SERIES_COLORS } : undefined,
    style: plotStyle(),
    marks: [
      Plot.ruleY([0]),
      Plot.rectY(
        chart.data,
        Plot.binX<RectYOptions>({ y: "count" }, { x: chart.value, fill: chart.series ?? SERIES_COLORS[0], inset: 1 }),
      ),
    ],
  } satisfies PlotOptions);
}

function renderBox(Plot: PlotModule, target: HTMLElement, chart: ChartViewModel): HTMLElement | SVGSVGElement {
  const grouped = chart.series != null;
  return Plot.plot({
    width: Math.max(plotWidth(target), 420),
    height: 260,
    marginTop: 42,
    marginRight: 18,
    marginBottom: 48,
    marginLeft: 54,
    x: { label: null },
    y: { grid: true, label: null },
    fx: grouped ? { label: null } : undefined,
    color: grouped ? { label: displayLabel(chart.series as string), legend: true, range: SERIES_COLORS } : undefined,
    style: plotStyle(),
    marks: [
      Plot.ruleY([0]),
      Plot.boxY(chart.data, {
        x: grouped ? chart.series : chart.dimension,
        fx: grouped ? chart.dimension : undefined,
        y: chart.value,
        fill: grouped ? chart.series : SERIES_COLORS[0],
        stroke: grouped ? chart.series : SERIES_COLORS[0],
        fillOpacity: 0.38,
      }),
    ],
  } satisfies PlotOptions);
}

function renderHeatmap(_Plot: PlotModule, target: HTMLElement, chart: ChartViewModel): HTMLElement {
  return resolveHeatmapMode(chart) === "continuous"
    ? renderContinuousHeatmap(target, chart)
    : renderCategoricalHeatmap(chart);
}

function renderCategoricalHeatmap(chart: ChartViewModel): HTMLElement {
  const xValues = unique(chart.data.map((datum) => datum[chart.dimension]));
  const yValues = unique(chart.data.map((datum) => datum[chart.series ?? ""]));
  const values = chart.data.map((datum) => finiteNumber(datum[chart.value])).filter((value) => value != null);
  const min = Math.min(...values, 0);
  const max = Math.max(...values, min + 1);
  const byCell = new Map<string, ChartDatum>();
  const root = document.createElement("section");
  const grid = document.createElement("div");
  const cellSize = xValues.length * yValues.length > 80 ? 22 : 34;

  root.className = "chartui-heatmap";
  grid.className = "chartui-heatmap-grid";
  grid.style.setProperty("--cell", `${cellSize}px`);
  grid.style.gridTemplateColumns = `minmax(84px, max-content) repeat(${xValues.length}, var(--cell))`;

  for (const datum of chart.data) {
    byCell.set(`${String(datum[chart.dimension])}\u0000${String(datum[chart.series ?? ""])}`, datum);
  }

  grid.appendChild(labelCell(""));
  xValues.forEach((value, index) => grid.appendChild(labelCell(String(index + 1), String(value))));

  for (const y of yValues) {
    grid.appendChild(labelCell(String(y), String(y), "chartui-y-label"));
    for (const x of xValues) {
      const datum = byCell.get(`${String(x)}\u0000${String(y)}`);
      grid.appendChild(datum ? heatCell(categoricalTooltip(chart, datum), datum[chart.value], min, max) : emptyCell());
    }
  }

  root.append(legend(min, max, chart.value), grid);
  attachHeatmapTooltip(root);
  return root;
}

function renderContinuousHeatmap(target: HTMLElement, chart: ChartViewModel): HTMLElement {
  const width = plotWidth(target);
  const columns = Math.max(24, Math.min(42, Math.floor((width - 88) / 18)));
  const rows = Math.max(16, Math.min(38, Math.round(columns * 0.72)));
  const cell = Math.max(14, Math.min(20, Math.floor((width - 96) / columns)));
  const data = squareHeatmapData(chart, columns, rows);
  const max = Math.max(...data.map((datum) => Number(datum.count)), 1);
  const root = document.createElement("section");
  const grid = document.createElement("div");

  root.className = "chartui-heatmap";
  grid.className = "chartui-heatmap-grid chartui-heatmap-grid-continuous";
  grid.style.setProperty("--cell", `${cell}px`);
  grid.style.gridTemplateColumns = `repeat(${columns}, var(--cell))`;
  grid.style.width = `${columns * cell}px`;

  const byCell = new Map(data.map((datum) => [`${datum.__x}:${datum.__y}`, datum]));
  for (let y = 0; y < rows; y += 1) {
    for (let x = 0; x < columns; x += 1) {
      const datum = byCell.get(`${x}:${y}`);
      const node = datum ? heatCell(continuousTooltip(chart, datum), datum.count, 0, max) : emptyCell();
      grid.appendChild(node);
    }
  }

  root.append(legend(0, max, chart.value), grid);
  attachHeatmapTooltip(root);
  return root;
}

function resolveHeatmapMode(chart: ChartViewModel): Exclude<HeatmapMode, "auto" | "calendar"> {
  if (chart.heatmap_mode === "continuous") return "continuous";
  if (chart.heatmap_mode === "categorical" || chart.heatmap_mode === "calendar") return "categorical";
  return chart.series && hasContinuousAxis(chart.data, chart.dimension) && hasContinuousAxis(chart.data, chart.series)
    ? "continuous"
    : "categorical";
}

function hasContinuousAxis(data: ChartDatum[], column: string): boolean {
  const values = data.filter((datum) => datum[column] != null);
  return values.length > 0 && values.every((datum) => continuousValue(datum[column]) != null);
}

function squareHeatmapData(chart: ChartViewModel, columns: number, rows: number): HeatmapBin[] {
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
    return {
      __x: x,
      __y: y,
      count,
      x0: minX + (x / columns) * (maxX - minX || 1),
      x1: minX + ((x + 1) / columns) * (maxX - minX || 1),
      y0: minY + ((rows - y - 1) / rows) * (maxY - minY || 1),
      y1: minY + ((rows - y) / rows) * (maxY - minY || 1),
    };
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

function heatCell(tooltipText: string, rawValue: unknown, min: number, max: number): HTMLDivElement {
  const cell = document.createElement("div");
  const value = finiteNumber(rawValue) ?? 0;
  cell.className = "chartui-heat-cell";
  cell.style.backgroundColor = heatColor((value - min) / (max - min || 1));
  cell.dataset.tooltip = tooltipText;
  return cell;
}

function emptyCell(): HTMLDivElement {
  const cell = document.createElement("div");
  cell.className = "chartui-heat-cell chartui-heat-cell-empty";
  return cell;
}

function labelCell(text: string, title = text, className = "chartui-heat-label"): HTMLDivElement {
  const cell = document.createElement("div");
  cell.className = className;
  cell.textContent = text;
  cell.title = title;
  return cell;
}

function legend(min: number, max: number, column: string): HTMLDivElement {
  const node = document.createElement("div");
  node.className = "chartui-heat-legend";
  node.innerHTML = `<span>${displayLabel(column)}</span><i></i><small>${formatNumber(min)}</small><small>${formatNumber(max)}</small>`;
  return node;
}

function attachHeatmapTooltip(root: HTMLElement): void {
  const tooltip = document.createElement("div");
  tooltip.className = "chartui-heat-tooltip";
  root.appendChild(tooltip);

  root.addEventListener("pointermove", (event) => {
    const target = event.target instanceof HTMLElement ? event.target.closest<HTMLElement>("[data-tooltip]") : null;
    if (!target?.dataset.tooltip) {
      tooltip.removeAttribute("data-visible");
      return;
    }
    const rect = root.getBoundingClientRect();
    tooltip.textContent = target.dataset.tooltip;
    tooltip.style.left = `${event.clientX - rect.left + 12}px`;
    tooltip.style.top = `${event.clientY - rect.top + 12}px`;
    tooltip.dataset.visible = "true";
  });

  root.addEventListener("pointerleave", () => tooltip.removeAttribute("data-visible"));
}

function categoricalTooltip(chart: ChartViewModel, datum: ChartDatum): string {
  return [
    `${displayLabel(chart.dimension)}: ${String(datum[chart.dimension] ?? "")}`,
    chart.series ? `${displayLabel(chart.series)}: ${String(datum[chart.series] ?? "")}` : "",
    `${displayLabel(chart.value)}: ${formatNumber(finiteNumber(datum[chart.value]) ?? 0)}`,
  ]
    .filter(Boolean)
    .join("\n");
}

function continuousTooltip(chart: ChartViewModel, datum: HeatmapBin): string {
  return [
    `${displayLabel(chart.dimension)}: ${formatNumber(datum.x0)}-${formatNumber(datum.x1)}`,
    chart.series ? `${displayLabel(chart.series)}: ${formatNumber(datum.y0)}-${formatNumber(datum.y1)}` : "",
    `Count: ${formatNumber(datum.count)}`,
  ]
    .filter(Boolean)
    .join("\n");
}

function unique(values: unknown[]): ChartCell[] {
  const seen = new Set<string>();
  return values.filter((value): value is ChartCell => {
    const key = String(value);
    if (seen.has(key)) return false;
    seen.add(key);
    return value == null || typeof value === "string" || typeof value === "number" || typeof value === "boolean";
  });
}

function finiteNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function heatColor(value: number): string {
  const ratio = clamp(value, 0, 1);
  const index = Math.min(HEAT_COLORS.length - 2, Math.floor(ratio * (HEAT_COLORS.length - 1)));
  const local = ratio * (HEAT_COLORS.length - 1) - index;
  return mixHex(HEAT_COLORS[index], HEAT_COLORS[index + 1], local);
}

function mixHex(left: string, right: string, ratio: number): string {
  const a = parseInt(left.slice(1), 16);
  const b = parseInt(right.slice(1), 16);
  const channel = (shift: number) =>
    Math.round(((a >> shift) & 255) * (1 - ratio) + ((b >> shift) & 255) * ratio);
  return `rgb(${channel(16)} ${channel(8)} ${channel(0)})`;
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
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
