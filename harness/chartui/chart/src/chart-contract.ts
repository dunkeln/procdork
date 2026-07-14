export type ChartKind = "line" | "bar" | "heatmap" | "scatter" | "bubble" | "histogram" | "box" | "table";
export type HeatmapMode = "auto" | "categorical" | "continuous" | "calendar";
export type ChartCell = string | number | boolean | null;

export type ChartPayload = {
  title: string;
  chart_kind: ChartKind;
  columns: string[];
  rows: ChartCell[][];
  facts: ChartFacts;
  key_facts: string[];
  truncated: boolean;
  heatmap_mode?: HeatmapMode;
};

export type ChartFacts = {
  row_count: number;
  column_count: number;
  group_count?: number;
  segment_count?: number;
  total?: number;
  max_group?: {
    label: string;
    value: number;
  };
  truncated: boolean;
};

export type ChartDatum = Record<string, ChartCell>;

export type ChartViewModel = ChartPayload & {
  data: ChartDatum[];
  dimension: string;
  value: string;
  series?: string;
  size?: string;
  lower?: string;
  upper?: string;
};

export function normalizeChartPayload(input: unknown): ChartViewModel | null {
  if (!input || typeof input !== "object") return null;
  const raw = input as Record<string, unknown>;
  const columns = stringArray(raw.columns);
  const rows = Array.isArray(raw.rows)
    ? raw.rows.filter(Array.isArray).map((row) => row.map(cell).slice(0, columns.length))
    : [];
  if (!columns.length || !rows.length) return null;

  const chart_kind = chartKind(raw.chart_kind);
  const data = rows.map((row) => {
    const datum: ChartDatum = Object.create(null);
    columns.forEach((column, index) => {
      datum[column] = row[index] ?? null;
    });
    return datum;
  });

  const banded = chart_kind === "line" && columns.length >= 5;
  const dimension = columns[0];
  const value =
    chart_kind === "line" && banded
      ? columns[2]
      : chart_kind === "scatter" || chart_kind === "bubble"
        ? columns[1]
        : columns[columns.length - 1];
  return {
    title: typeof raw.title === "string" && raw.title.trim() ? raw.title : "Analytics result",
    chart_kind,
    columns,
    rows,
    facts: chartFacts(raw.facts, columns, rows, raw.truncated === true),
    key_facts: stringArray(raw.key_facts),
    truncated: raw.truncated === true,
    heatmap_mode: heatmapMode(raw.heatmap_mode),
    data,
    dimension,
    value,
    series: seriesColumn(chart_kind, columns),
    size: chart_kind === "bubble" ? columns[2] : undefined,
    lower: banded ? columns[3] : undefined,
    upper: banded ? columns[4] : undefined,
  };
}

function chartFacts(
  value: unknown,
  columns: string[],
  rows: ChartCell[][],
  truncated: boolean,
): ChartFacts {
  const raw = value && typeof value === "object" ? (value as Record<string, unknown>) : {};
  const max_group =
    raw.max_group && typeof raw.max_group === "object"
      ? (raw.max_group as Record<string, unknown>)
      : {};
  return {
    row_count: natural(raw.row_count) ?? rows.length,
    column_count: natural(raw.column_count) ?? columns.length,
    group_count: natural(raw.group_count),
    segment_count: natural(raw.segment_count),
    total: finite(raw.total),
    max_group:
      typeof max_group.label === "string" && finite(max_group.value) !== undefined
        ? { label: max_group.label, value: finite(max_group.value) as number }
        : undefined,
    truncated,
  };
}

function chartKind(value: unknown): ChartKind {
  return value === "line" ||
    value === "bar" ||
    value === "heatmap" ||
    value === "scatter" ||
    value === "bubble" ||
    value === "histogram" ||
    value === "box" ||
    value === "table"
    ? value
    : "table";
}

function seriesColumn(kind: ChartKind, columns: string[]): string | undefined {
  if (kind === "scatter") return columns[2];
  if (kind === "bubble") return columns[3];
  if (kind === "box") return columns.length >= 3 ? columns[1] : undefined;
  return columns.length >= 3 ? columns[1] : undefined;
}

function heatmapMode(value: unknown): HeatmapMode | undefined {
  return value === "auto" || value === "categorical" || value === "continuous" || value === "calendar"
    ? value
    : undefined;
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function cell(value: unknown): ChartCell {
  if (value == null) return null;
  if (typeof value === "string" || typeof value === "boolean") return value;
  if (typeof value === "number" && Number.isFinite(value)) return value;
  return String(value);
}

function natural(value: unknown): number | undefined {
  return typeof value === "number" && Number.isInteger(value) && value >= 0 ? value : undefined;
}

function finite(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}
