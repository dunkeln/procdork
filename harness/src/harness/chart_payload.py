from __future__ import annotations

"""Build MCP chart payloads; ChartUI owns rendering."""

from datetime import date, datetime
from decimal import Decimal
from math import isfinite
from typing import Literal

from pydantic import BaseModel


ChartKind = Literal[
    "auto", "line", "bar", "heatmap", "scatter", "bubble", "histogram", "box", "table"
]


class ChartMaxGroup(BaseModel):
    label: str
    value: float


class ChartFacts(BaseModel):
    row_count: int
    column_count: int
    group_count: int | None = None
    segment_count: int | None = None
    total: float | None = None
    max_group: ChartMaxGroup | None = None
    truncated: bool = False


class ChartPayload(BaseModel):
    title: str
    chart_kind: Literal[
        "line", "bar", "heatmap", "scatter", "bubble", "histogram", "box", "table"
    ]
    columns: list[str]
    rows: list[list[str | int | float | bool | None]]
    facts: ChartFacts
    key_facts: list[str]
    truncated: bool


def build_chart(
    columns: list[str],
    rows: list[tuple[object, ...]],
    title: str,
    requested_kind: ChartKind = "auto",
    truncated: bool = False,
) -> ChartPayload:
    if not columns or not rows:
        raise ValueError("The query returned no chartable rows")

    kind = choose_chart_kind(columns, rows, requested_kind)
    if kind == "table":
        selected_columns = columns[:6]
        selected_rows = [list(row[:6]) for row in rows[:12]]
        truncated = truncated or len(columns) > 6 or len(rows) > 12
    else:
        value_index = numeric_column(rows, start=0 if kind == "histogram" else 1)
        if value_index is None or (kind != "histogram" and len(columns) < 2):
            raise ValueError(f"{kind} charts require a dimension and a numeric measure")
        if kind == "histogram":
            selected_columns = [columns[value_index]]
            selected_rows = [[row[value_index]] for row in rows[:200]]
            truncated = truncated or len(rows) > 200
        elif kind in ("scatter", "bubble"):
            validate_xy_chart(kind, columns, rows)
            selected_columns = (
                columns[:4] if kind == "bubble" and len(columns) >= 4 else columns[:3]
            )
            selected_rows = [list(row[: len(selected_columns)]) for row in rows[:200]]
            truncated = truncated or len(rows) > 200
        elif kind == "box":
            if len(columns) not in (2, 3) or value_index != len(columns) - 1:
                raise ValueError(
                    "box charts require category, optional group, and numeric value columns"
                )
            selected_columns = columns[:3]
            selected_rows = [list(row[: len(selected_columns)]) for row in rows[:200]]
            truncated = truncated or len(rows) > 200
        else:
            line_band = (
                kind == "line"
                and len(columns) >= 5
                and numeric_columns(rows)[:3] == [2, 3, 4]
            )
            if kind == "heatmap" and (len(columns) != 3 or value_index != 2):
                raise ValueError(
                    "heatmap charts require category, segment, and numeric value columns"
                )
            segmented = (len(columns) == 3 and value_index == 2) or line_band
            selected_columns = (
                columns[:5]
                if line_band
                else columns
                if segmented
                else [columns[0], columns[value_index]]
            )
            selected_rows = (
                [list(row[: len(selected_columns)]) for row in rows[:12]]
                if segmented
                else [[row[0], row[value_index]] for row in rows[:12]]
            )
            truncated = truncated or len(rows) > 12

    normalized_rows = [[json_value(value) for value in row] for row in selected_rows]
    facts = chart_facts(kind, selected_columns, normalized_rows, truncated)
    return ChartPayload(
        title=title.strip()[:80] or "Analytics result",
        chart_kind=kind,
        columns=selected_columns,
        rows=normalized_rows,
        facts=facts,
        key_facts=chart_fact_text(facts, selected_columns, kind),
        truncated=truncated,
    )


def choose_chart_kind(
    columns: list[str], rows: list[tuple[object, ...]], requested: ChartKind
) -> Literal["line", "bar", "heatmap", "scatter", "bubble", "histogram", "box", "table"]:
    if requested != "auto":
        return requested
    if len(columns) == 1 and numeric_column(rows, start=0) is not None:
        return "histogram"
    if len(columns) < 2 or numeric_column(rows) is None:
        return "table"
    first_value = next((row[0] for row in rows if row and row[0] is not None), None)
    if isinstance(first_value, (int, float, Decimal)) and not isinstance(
        first_value, bool
    ):
        return "table"
    if isinstance(first_value, (date, datetime)) or any(
        token in columns[0].lower()
        for token in ("date", "day", "week", "month", "time")
    ):
        return "line"
    return "bar"


def numeric_column(rows: list[tuple[object, ...]], start: int = 1) -> int | None:
    return next(iter(numeric_columns(rows, start)), None)


def numeric_columns(rows: list[tuple[object, ...]], start: int = 1) -> list[int]:
    width = max((len(row) for row in rows), default=0)
    indexes = []
    for index in range(start, width):
        values = [
            row[index] for row in rows if index < len(row) and row[index] is not None
        ]
        if values and all(
            isinstance(value, (int, float, Decimal))
            and not isinstance(value, bool)
            and isfinite(float(value))
            for value in values
        ):
            indexes.append(index)
    return indexes


def validate_xy_chart(kind: str, columns: list[str], rows: list[tuple[object, ...]]) -> None:
    required = 3 if kind == "bubble" else 2
    if len(columns) < required:
        raise ValueError(f"{kind} charts require {required} leading numeric columns")
    for index in range(required):
        values = [row[index] for row in rows if index < len(row) and row[index] is not None]
        if not values or not all(
            isinstance(value, (int, float, Decimal))
            and not isinstance(value, bool)
            and isfinite(float(value))
            for value in values
        ):
            raise ValueError(f"{kind} charts require {required} leading numeric columns")


def chart_facts(
    kind: str,
    columns: list[str],
    rows: list[list[str | int | float | bool | None]],
    truncated: bool,
) -> ChartFacts:
    if kind == "table":
        return ChartFacts(row_count=len(rows), column_count=len(columns), truncated=truncated)
    value_index = chart_value_index(kind, columns)
    points = [
        (str(row[0]), float(row[value_index]))
        for row in rows
        if isinstance(row[value_index], (int, float))
    ]
    total = sum(value for _, value in points)
    if len(columns) >= 3:
        totals: dict[str, float] = {}
        for label, value in points:
            totals[label] = totals.get(label, 0) + value
        highest = max(totals.items(), key=lambda point: point[1])
        return ChartFacts(
            row_count=len(points),
            column_count=len(columns),
            group_count=len(totals),
            segment_count=len({str(row[1]) for row in rows}),
            total=total,
            max_group=ChartMaxGroup(label=highest[0], value=highest[1]),
            truncated=truncated,
        )
    highest = max(points, key=lambda point: point[1])
    return ChartFacts(
        row_count=len(points),
        column_count=len(columns),
        group_count=len(points),
        total=total,
        max_group=ChartMaxGroup(label=highest[0], value=highest[1]),
        truncated=truncated,
    )


def chart_fact_text(
    facts: ChartFacts, columns: list[str], kind: str
) -> list[str]:
    if kind == "table":
        row_label = "row" if facts.row_count == 1 else "rows"
        text = [f"{facts.row_count} {row_label} shown across {facts.column_count} columns."]
    else:
        measure = display_label(columns[chart_value_index(kind, columns)])
        if facts.segment_count is not None:
            text = [
                f"{facts.row_count} points plotted across {facts.segment_count} segments.",
            ]
        else:
            text = [f"{facts.row_count} points plotted."]
        if facts.max_group:
            text.append(
                f"Highest total {measure}: {number(facts.max_group.value)} at {facts.max_group.label}."
            )
        if facts.total is not None:
            text.append(f"Displayed total {measure}: {number(facts.total)}.")
    if facts.truncated:
        text.append("The rendered dataset was truncated to the chart limit.")
    return text


def chart_value_index(kind: str, columns: list[str]) -> int:
    if kind == "line" and len(columns) >= 5:
        return 2
    if kind in ("scatter", "bubble"):
        return 1
    return len(columns) - 1


def render_markdown_table(payload: ChartPayload) -> str:
    def cell(value: object) -> str:
        return (
            str(value if value is not None else "")
            .replace("|", "\\|")
            .replace("\n", "<br>")
        )

    headers = [display_label(column) for column in payload.columns]
    lines = [headers, ["---"] * len(headers), *payload.rows]
    return "\n".join(f"| {' | '.join(cell(value) for value in row)} |" for row in lines)


def json_value(value: object) -> str | int | float | bool | None:
    if isinstance(value, float) and not isfinite(value):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value if not isinstance(value, str) else value[:48]
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)[:48]


def number(value: float) -> str:
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def display_label(column: str) -> str:
    return column.replace("_", " ").strip().title()
