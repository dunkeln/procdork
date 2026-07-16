import { BarChart, BoxplotChart, HeatmapChart, LineChart, ScatterChart } from "echarts/charts";
import { DataZoomComponent, GridComponent, LegendComponent, TooltipComponent, VisualMapComponent } from "echarts/components";
import { init, use } from "echarts/core";
import type { EChartsType } from "echarts/core";
import type { EChartsOption, SeriesOption } from "echarts";
import { SVGRenderer } from "echarts/renderers";
import type { ChartCell, ChartDatum, ChartViewModel } from "./chart-contract";

const SERIES_COLORS = ["#2274A5", "#78C091", "#87B3D4", "#131B23", "#816C61"];
const HEAT_COLORS = ["#edf6f9", "#87B3D4", "#2274A5", "#131B23"];
const instances = new WeakMap<HTMLElement, EChartsType>();

use([
  BarChart,
  BoxplotChart,
  HeatmapChart,
  LineChart,
  ScatterChart,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  VisualMapComponent,
  SVGRenderer,
]);

export function createPlotRenderer() {
  return {
    render(target: HTMLElement, chart: ChartViewModel) {
      instances.get(target)?.dispose();
      if (chart.chart_kind === "table") {
        target.replaceChildren(renderTable(chart));
        return;
      }

      const root = document.createElement("div");
      root.className = "chartui-echart";
      root.style.width = `${chartWidth(target, chart)}px`;
      root.style.height = `${chartHeight(target, chart)}px`;
      target.replaceChildren(root);

      const instance = init(root, null, { renderer: "svg" });
      instances.set(target, instance);
      instance.setOption(optionFor(chart), true);
      requestAnimationFrame(() => instance.resize());
    },
  };
}

function optionFor(chart: ChartViewModel): EChartsOption {
  if (chart.chart_kind === "histogram") return histogramOption(chart);
  if (chart.chart_kind === "scatter" || chart.chart_kind === "bubble") return scatterOption(chart);
  if (chart.chart_kind === "box") return boxOption(chart);
  if (chart.chart_kind === "heatmap") return heatmapOption(chart);
  if (chart.chart_kind === "line") return lineOption(chart);
  return barOption(chart);
}

function barOption(chart: ChartViewModel): EChartsOption {
  const categories = unique(chart.data.map((datum) => datum[chart.dimension]));
  const names = chart.series ? unique(chart.data.map((datum) => datum[chart.series as string])) : ["Value"];
  return baseCartesian(chart, {
    xAxis: categoryAxis(categories),
    yAxis: valueAxis(),
    series: names.map((name) => ({
      name: String(name),
      type: "bar",
      stack: chart.series ? "total" : undefined,
      emphasis: { focus: "series" },
      data: categories.map((category) => sumValue(chart, category, name)),
    })),
  });
}

function lineOption(chart: ChartViewModel): EChartsOption {
  const categories = unique(chart.data.map((datum) => datum[chart.dimension]));
  const names = chart.series ? unique(chart.data.map((datum) => datum[chart.series as string])) : ["Value"];
  return baseCartesian(chart, {
    xAxis: categoryAxis(categories),
    yAxis: valueAxis(),
    series: names.map((name) => ({
      name: String(name),
      type: "line",
      symbolSize: 7,
      data: categories.map((category) => sumValue(chart, category, name)),
    })),
  });
}

function histogramOption(chart: ChartViewModel): EChartsOption {
  const values = chart.data.map((datum) => finiteNumber(datum[chart.value])).filter((value) => value != null);
  const bins = histogramBins(values);
  return baseCartesian(chart, {
    xAxis: categoryAxis(bins.map((bin) => `${formatNumber(bin.start)}-${formatNumber(bin.end)}`)),
    yAxis: valueAxis(),
    series: [
      {
        name: displayLabel(chart.value),
        type: "bar",
        data: bins.map((bin) => bin.count),
      },
    ],
  });
}

function scatterOption(chart: ChartViewModel): EChartsOption {
  const names = chart.series ? unique(chart.data.map((datum) => datum[chart.series as string])) : ["Value"];
  return baseCartesian(chart, {
    xAxis: valueAxis(),
    yAxis: valueAxis(),
    series: names.map((name) => ({
      name: String(name),
      type: "scatter",
      symbolSize: chart.chart_kind === "bubble" ? (value: unknown[]) => Math.max(6, Number(value[2]) * 4) : 8,
      data: chart.data
        .filter((datum) => !chart.series || datum[chart.series] === name)
        .map((datum) => [
          finiteNumber(datum[chart.dimension]) ?? 0,
          finiteNumber(datum[chart.value]) ?? 0,
          chart.size ? finiteNumber(datum[chart.size]) ?? 1 : 1,
        ]),
    })),
  });
}

function boxOption(chart: ChartViewModel): EChartsOption {
  const categories = unique(chart.data.map((datum) => datum[chart.dimension]));
  const names = chart.series ? unique(chart.data.map((datum) => datum[chart.series as string])) : ["Value"];
  return baseCartesian(chart, {
    xAxis: categoryAxis(categories),
    yAxis: valueAxis(),
    series: names.map((name) => ({
      name: String(name),
      type: "boxplot",
      data: categories.map((category) => {
        const values = chart.data
          .filter((datum) => datum[chart.dimension] === category && (!chart.series || datum[chart.series] === name))
          .map((datum) => finiteNumber(datum[chart.value]))
          .filter((value) => value != null)
          .sort((left, right) => left - right);
        return values.length ? [values[0], quantile(values, 0.25), quantile(values, 0.5), quantile(values, 0.75), values[values.length - 1]] : [];
      }),
    })) as SeriesOption[],
  });
}

function heatmapOption(chart: ChartViewModel): EChartsOption {
  const continuous = chart.heatmap_mode === "continuous" || (!chart.heatmap_mode && chart.series && hasContinuousAxis(chart.data, chart.dimension) && hasContinuousAxis(chart.data, chart.series));
  const data = continuous ? continuousHeatmapData(chart) : categoricalHeatmapData(chart);
  const max = Math.max(...data.values.map((item) => Number(item[2])), 1);

  return {
    ...baseOption(chart),
    grid: { top: 50, left: 82, right: 26, bottom: 50, containLabel: false },
    xAxis: { type: "category", data: data.x, splitArea: { show: true }, axisLabel: { color: "#000", fontSize: 11 } },
    yAxis: { type: "category", data: data.y, splitArea: { show: true }, axisLabel: { color: "#000", fontSize: 11 } },
    visualMap: {
      min: 0,
      max,
      calculable: true,
      orient: "horizontal",
      left: "center",
      top: 0,
      inRange: { color: HEAT_COLORS },
      textStyle: { color: "#000", fontSize: 11 },
    },
    series: [{ name: displayLabel(chart.value), type: "heatmap", data: data.values, emphasis: { itemStyle: { borderColor: "#131B23", borderWidth: 1 } } }],
  };
}

function baseCartesian(chart: ChartViewModel, option: Pick<EChartsOption, "xAxis" | "yAxis" | "series">): EChartsOption {
  return {
    ...baseOption(chart),
    grid: { top: chart.series ? 42 : 18, left: 42, right: 18, bottom: 44, containLabel: true },
    dataZoom: [{ type: "inside", xAxisIndex: 0, filterMode: "none" }],
    ...option,
  };
}

function baseOption(chart: ChartViewModel): EChartsOption {
  return {
    backgroundColor: "#edf6f9",
    color: SERIES_COLORS,
    textStyle: { color: "#000", fontFamily: "inherit" },
    tooltip: {
      trigger: chart.chart_kind === "line" ? "axis" : "item",
      confine: true,
      backgroundColor: "#131B23",
      borderWidth: 0,
      textStyle: { color: "#fff", fontSize: 11 },
    },
    legend: chart.series ? { type: "scroll", top: 0, textStyle: { color: "#000", fontSize: 11 } } : undefined,
  };
}

function categoryAxis(values: ChartCell[]) {
  return {
    type: "category" as const,
    data: values.map(String),
    axisLabel: { color: "#000", fontSize: 11, hideOverlap: true },
    axisLine: { lineStyle: { color: "#000" } },
  };
}

function valueAxis() {
  return {
    type: "value" as const,
    splitLine: { lineStyle: { color: "rgb(0 0 0 / 12%)" } },
    axisLabel: { color: "#000", fontSize: 11 },
  };
}

function categoricalHeatmapData(chart: ChartViewModel) {
  const x = unique(chart.data.map((datum) => datum[chart.dimension]));
  const y = unique(chart.data.map((datum) => datum[chart.series ?? ""]));
  return {
    x: x.map(String),
    y: y.map(String),
    values: chart.data.map((datum) => [
      x.findIndex((value) => value === datum[chart.dimension]),
      y.findIndex((value) => value === datum[chart.series ?? ""]),
      finiteNumber(datum[chart.value]) ?? 0,
    ]),
  };
}

function continuousHeatmapData(chart: ChartViewModel) {
  const points = chart.data
    .map((datum) => ({
      x: finiteNumber(datum[chart.dimension]),
      y: chart.series ? finiteNumber(datum[chart.series]) : null,
    }))
    .filter((point): point is { x: number; y: number } => point.x != null && point.y != null);
  const columns = 32;
  const rows = 22;
  const xs = points.map((point) => point.x);
  const ys = points.map((point) => point.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const counts = new Map<string, number>();

  for (const point of points) {
    const x = clamp(Math.floor(((point.x - minX) / (maxX - minX || 1)) * columns), 0, columns - 1);
    const y = clamp(Math.floor(((point.y - minY) / (maxY - minY || 1)) * rows), 0, rows - 1);
    const key = `${x}:${rows - y - 1}`;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  return {
    x: Array.from({ length: columns }, (_, index) => formatNumber(minX + (index / columns) * (maxX - minX || 1))),
    y: Array.from({ length: rows }, (_, index) => formatNumber(minY + ((rows - index - 1) / rows) * (maxY - minY || 1))),
    values: Array.from(counts, ([key, count]) => {
      const [x, y] = key.split(":").map(Number);
      return [x, y, count];
    }),
  };
}

function histogramBins(values: number[]) {
  if (!values.length) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const count = clamp(Math.ceil(Math.sqrt(values.length)), 6, 18);
  const step = (max - min || 1) / count;
  return Array.from({ length: count }, (_, index) => {
    const start = min + index * step;
    const end = index === count - 1 ? max : start + step;
    return {
      start,
      end,
      count: values.filter((value) => value >= start && (index === count - 1 ? value <= end : value < end)).length,
    };
  });
}

function sumValue(chart: ChartViewModel, category: ChartCell, segment: ChartCell): number {
  return chart.data
    .filter((datum) => datum[chart.dimension] === category && (!chart.series || datum[chart.series] === segment))
    .reduce((sum, datum) => sum + (finiteNumber(datum[chart.value]) ?? 0), 0);
}

function hasContinuousAxis(data: ChartDatum[], column: string): boolean {
  const values = data.map((datum) => finiteNumber(datum[column])).filter((value) => value != null);
  return values.length > 0;
}

function chartWidth(target: HTMLElement, chart: ChartViewModel): number {
  if (chart.chart_kind === "histogram") {
    const values = chart.data.map((datum) => finiteNumber(datum[chart.value])).filter((value) => value != null);
    return Math.max(target.clientWidth || 560, 520, histogramBins(values).length * 72);
  }

  const categoryCount = unique(chart.data.map((datum) => datum[chart.dimension])).length || 1;
  if (chart.chart_kind === "heatmap") {
    const shape = heatmapShape(chart);
    return Math.max(target.clientWidth || 560, 520, shape.x * heatmapCellSize(target, shape.x) + 108);
  }
  if (chart.chart_kind === "bar") return Math.max(target.clientWidth || 560, 420, categoryCount * 82);
  return Math.max(target.clientWidth || 560, 420);
}

function chartHeight(target: HTMLElement, chart: ChartViewModel): number {
  if (chart.chart_kind !== "heatmap") return 300;
  const shape = heatmapShape(chart);
  return Math.max(260, shape.y * heatmapCellSize(target, shape.x) + 100);
}

function heatmapShape(chart: ChartViewModel): { x: number; y: number } {
  if (chart.heatmap_mode === "continuous" || (!chart.heatmap_mode && chart.series && hasContinuousAxis(chart.data, chart.dimension) && hasContinuousAxis(chart.data, chart.series))) {
    return { x: 32, y: 22 };
  }
  return {
    x: unique(chart.data.map((datum) => datum[chart.dimension])).length || 1,
    y: unique(chart.data.map((datum) => datum[chart.series ?? ""])).length || 1,
  };
}

function heatmapCellSize(target: HTMLElement, xCount: number): number {
  return clamp(Math.floor(((target.clientWidth || 560) - 108) / Math.max(xCount, 1)), 16, 30);
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

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function quantile(values: number[], q: number): number {
  const index = (values.length - 1) * q;
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  return values[lower] + (values[upper] - values[lower]) * (index - lower);
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
}

function displayLabel(column: string): string {
  return column.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
