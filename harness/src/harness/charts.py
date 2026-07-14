from __future__ import annotations

from base64 import urlsafe_b64encode
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
from math import isfinite
import os
from pathlib import Path
from tempfile import gettempdir
from typing import Literal

from cryptography.fernet import Fernet, InvalidToken
from lets_plot import (
    aes,
    element_rect,
    element_text,
    geom_bar,
    geom_line,
    geom_point,
    geom_tile,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_fill_gradient,
    theme,
)
from pydantic import BaseModel


ChartKind = Literal["auto", "line", "bar", "heatmap", "table"]
CHART_TTL_SECONDS = 15 * 60


def configure_chart_fonts() -> None:
    if "FONTCONFIG_FILE" in os.environ:
        return
    font_directory = Path(__file__).parent / "fonts"
    config = Path(gettempdir()) / "procdork-fonts.conf"
    config.write_text(
        '<?xml version="1.0"?>\n'
        '<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">\n'
        "<fontconfig>\n"
        f"  <dir>{font_directory}</dir>\n"
        f"  <cachedir>{Path(gettempdir()) / 'procdork-font-cache'}</cachedir>\n"
        "</fontconfig>\n",
        encoding="utf-8",
    )
    os.environ["FONTCONFIG_FILE"] = str(config)


configure_chart_fonts()


class ChartPayload(BaseModel):
    title: str
    chart_kind: Literal["line", "bar", "heatmap", "table"]
    columns: list[str]
    rows: list[list[str | int | float | bool | None]]
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
        value_index = numeric_column(rows)
        if value_index is None or len(columns) < 2:
            raise ValueError(f"{kind} charts require a dimension and a numeric measure")
        if kind == "heatmap" and (len(columns) != 3 or value_index != 2):
            raise ValueError(
                "heatmap charts require category, segment, and numeric value columns"
            )
        segmented = len(columns) == 3 and value_index == 2
        selected_columns = columns if segmented else [columns[0], columns[value_index]]
        selected_rows = (
            [list(row) for row in rows[:12]]
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
        key_facts=facts,
        truncated=truncated,
    )


def choose_chart_kind(
    columns: list[str], rows: list[tuple[object, ...]], requested: ChartKind
) -> Literal["line", "bar", "heatmap", "table"]:
    if requested != "auto":
        return requested
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


def numeric_column(rows: list[tuple[object, ...]]) -> int | None:
    width = max((len(row) for row in rows), default=0)
    for index in range(1, width):
        values = [
            row[index] for row in rows if index < len(row) and row[index] is not None
        ]
        if values and all(
            isinstance(value, (int, float, Decimal))
            and not isinstance(value, bool)
            and isfinite(float(value))
            for value in values
        ):
            return index
    return None


def chart_facts(
    kind: str,
    columns: list[str],
    rows: list[list[str | int | float | bool | None]],
    truncated: bool,
) -> list[str]:
    if kind == "table":
        row_label = "row" if len(rows) == 1 else "rows"
        facts = [f"{len(rows)} {row_label} shown across {len(columns)} columns."]
    else:
        value_index = len(columns) - 1
        points = [
            (str(row[0]), float(row[value_index]))
            for row in rows
            if isinstance(row[value_index], (int, float))
        ]
        measure = columns[value_index]
        if len(columns) == 3:
            totals: dict[str, float] = {}
            for label, value in points:
                totals[label] = totals.get(label, 0) + value
            highest = max(totals.items(), key=lambda point: point[1])
            facts = [
                f"{len(points)} points plotted across {len({str(row[1]) for row in rows})} segments.",
                f"Highest total {measure}: {number(highest[1])} at {highest[0]}.",
                f"Displayed total {measure}: {number(sum(value for _, value in points))}.",
            ]
        else:
            highest = max(points, key=lambda point: point[1])
            facts = [
                f"{len(points)} points plotted.",
                f"Highest {measure}: {number(highest[1])} at {highest[0]}.",
                f"Displayed total {measure}: {number(sum(value for _, value in points))}.",
            ]
        if kind == "line" and len(points) > 1 and len(columns) == 2:
            start, end = points[0][1], points[-1][1]
            change = (
                f"{number(end - start)} absolute"
                if start == 0
                else f"{number((end - start) / abs(start) * 100)}%"
            )
            facts.append(
                f"{columns[1]} changed from {number(start)} to {number(end)} ({change})."
            )
    if truncated:
        facts.append("The rendered dataset was truncated to the chart limit.")
    return facts


def encode_chart(payload: ChartPayload) -> tuple[str, str]:
    token = cipher().encrypt(payload.model_dump_json().encode()).decode()
    expires_at = datetime.now(UTC) + timedelta(seconds=CHART_TTL_SECONDS)
    return token, expires_at.isoformat()


def decode_chart(token: str) -> ChartPayload:
    try:
        content = cipher().decrypt(token.encode(), ttl=CHART_TTL_SECONDS)
        return ChartPayload.model_validate_json(content)
    except (InvalidToken, ValueError) as error:
        raise ValueError("Chart link is invalid or expired") from error


def render_png(payload: ChartPayload) -> bytes:
    if payload.chart_kind == "table":
        raise ValueError("Tables render as Markdown, not PNG")

    segmented = len(payload.columns) == 3
    data = {
        "label": [str(row[0]) for row in payload.rows],
        "value": [float(row[-1]) for row in payload.rows],
        "series": [str(row[1]) for row in payload.rows]
        if segmented
        else [payload.columns[1]] * len(payload.rows),
    }
    if payload.chart_kind == "heatmap":
        plot = ggplot(data, aes("label", "series", fill="value")) + geom_tile()
        plot += scale_fill_gradient(low="#b8b8ff", high="#ce4257") + labs(
            title=payload.title,
            x=payload.columns[0],
            y=payload.columns[1],
            fill=payload.columns[2],
        )
    else:
        colors = segment_palette(len(set(data["series"])))
        plot = ggplot(data, aes("label", "value", group="series"))
        if payload.chart_kind == "line":
            plot += (
                geom_line(aes(color="series"), size=1.2)
                + geom_point(aes(color="series"), size=4)
                + scale_color_manual(values=colors)
                if segmented
                else geom_line(color="#b8b8ff", size=1.2)
                + geom_point(color="#b8b8ff", size=4)
            )
        else:
            plot += (
                geom_bar(aes(fill="series"), stat="identity", width=0.65)
                + scale_fill_manual(values=colors)
                if segmented
                else geom_bar(stat="identity", fill="#b8b8ff", width=0.65)
            )
        plot += labs(
            title=payload.title,
            x=payload.columns[0],
            y=payload.columns[-1],
            color=payload.columns[1],
            fill=payload.columns[1],
        )

    image = BytesIO()
    themed(plot).to_png(image, w=960, h=540, unit="px")
    return image.getvalue()


def themed(plot):
    return plot + theme(
        text=element_text(family="Roboto"),
        axis_text_x=element_text(angle=30, hjust=1),
        legend_position="bottom",
        panel_background=element_rect(fill="#ffffff"),
        plot_background=element_rect(fill="#ffffff"),
        plot_title=element_text(size=20, face="bold"),
    )


def segment_palette(count: int) -> list[str]:
    start, end = (184, 184, 255), (206, 66, 87)
    steps = max(count - 1, 1)
    return [
        "#"
        + "".join(
            f"{round(a + (b - a) * index / steps):02x}"
            for a, b in zip(start, end)
        )
        for index in range(count)
    ]


def render_markdown_table(payload: ChartPayload) -> str:
    def cell(value: object) -> str:
        return (
            str(value if value is not None else "")
            .replace("|", "\\|")
            .replace("\n", "<br>")
        )

    lines = [payload.columns, ["---"] * len(payload.columns), *payload.rows]
    return "\n".join(f"| {' | '.join(cell(value) for value in row)} |" for row in lines)


# Encrypt chart payloads so public links stay stateless, private, and tamper-evident.
def cipher() -> Fernet:
    secret = os.getenv("CHART_SIGNING_KEY", "")
    if len(secret) < 32:
        raise RuntimeError("CHART_SIGNING_KEY must contain at least 32 characters")
    return Fernet(urlsafe_b64encode(sha256(secret.encode()).digest()))


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
