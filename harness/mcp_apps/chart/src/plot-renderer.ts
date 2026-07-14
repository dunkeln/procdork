import type { ChartViewModel } from "./chart-contract";

type PlotModule = typeof import("@observablehq/plot");
type PlotOptions = Parameters<PlotModule["plot"]>[0];
const SERIES_COLORS = ["#2274A5", "#78C091", "#87B3D4", "#131B23", "#816C61"];

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
  const width = Math.max(target.clientWidth || 560, 320);
  const markOptions = {
    x: chart.dimension,
    y: chart.value,
    title: (d: Record<string, unknown>) =>
      chart.columns.map((column) => `${column}: ${String(d[column] ?? "")}`).join("\n"),
  };
  const marks =
    chart.chart_kind === "heatmap"
      ? [
          Plot.cell(chart.data, {
            x: chart.dimension,
            y: chart.series,
            fill: chart.value,
            inset: 1,
            title: markOptions.title,
          }),
        ]
      : chart.chart_kind === "line"
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
          ];

  return Plot.plot({
    width,
    height: 260,
    marginTop: 12,
    marginRight: 18,
    marginBottom: 48,
    marginLeft: 54,
    x: { label: chart.dimension },
    y: { grid: true, label: chart.value },
    color: chart.series
      ? { legend: true, range: SERIES_COLORS }
      : chart.chart_kind === "heatmap"
        ? { legend: true }
        : undefined,
    style: {
      background: "transparent",
      color: "#000",
      fontFamily: "inherit",
      fontSize: "12px",
    },
    marks,
  } satisfies PlotOptions);
}

function renderTable(chart: ChartViewModel): HTMLTableElement {
  const table = document.createElement("table");
  const thead = table.createTHead();
  const header = thead.insertRow();
  chart.columns.forEach((column) => {
    header.appendChild(document.createElement("th")).textContent = column;
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
