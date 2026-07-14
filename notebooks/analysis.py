import marimo

__generated_with = "0.23.14"
app = marimo.App(width="columns")


@app.cell
def _():
    import os

    import duckdb
    import marimo as mo
    from dotenv import find_dotenv, load_dotenv
    from matplotlib import colors, pyplot as plt

    load_dotenv(find_dotenv(usecwd=True))
    con = duckdb.connect(
        "md:procdork_analytics",
        config={"motherduck_token": os.environ["MOTHERDUCK_TOKEN"]},
    )
    return colors, con, mo, plt


@app.cell
def _(mo):
    mo.md("""
    # Procurement evidence heat map

    The live database does not yet persist canonical supplier identities or
    supplier-to-claim evidence links. These charts show the two honest
    grains available now: evidence captured per research session and facts
    requested per procurement turn.
    """)
    return


@app.cell
def _(con):
    evidence_by_session = con.execute(
        """
        SELECT
            m.session_slug,
            coalesce(s.document_type, s.source_kind, 'unclassified') AS evidence_type,
            count(DISTINCT ms.source_url) AS source_count
        FROM main.app_messages AS m
        JOIN main.app_message_sources AS ms
          ON ms.message_id = m.id
        JOIN main.app_sources AS s
          ON s.url = ms.source_url
        GROUP BY 1, 2
        ORDER BY 1, 2
        """
    ).df()
    return (evidence_by_session,)


@app.cell(hide_code=True)
def _(colors, evidence_by_session, mo, plt):
    evidence_matrix = (
        evidence_by_session.pivot(
            index="session_slug",
            columns="evidence_type",
            values="source_count",
        )
        .fillna(0)
        .astype(int)
    )
    evidence_matrix = evidence_matrix.loc[
        evidence_matrix.sum(axis=1).sort_values(ascending=False).index
    ]

    evidence_fig, _ax = plt.subplots(
        figsize=(10, max(4, len(evidence_matrix) * 0.42))
    )
    _image = _ax.imshow(
        evidence_matrix,
        aspect="auto",
        cmap="YlGnBu",
        norm=colors.Normalize(
            vmin=0,
            vmax=max(1, int(evidence_matrix.to_numpy().max())),
        ),
    )
    _ax.set_title("Evidence material captured by research session", loc="left")
    _ax.set_xlabel("Evidence type")
    _ax.set_ylabel("Research session")
    _ax.set_xticks(
        range(len(evidence_matrix.columns)),
        evidence_matrix.columns,
        rotation=35,
        ha="right",
    )
    _ax.set_yticks(range(len(evidence_matrix.index)), evidence_matrix.index)
    for _row, session_slug in enumerate(evidence_matrix.index):
        for _column, evidence_type in enumerate(evidence_matrix.columns):
            source_count = evidence_matrix.loc[session_slug, evidence_type]
            if source_count:
                _ax.text(
                    _column,
                    _row,
                    str(source_count),
                    ha="center",
                    va="center",
                    fontsize=8,
                )
    evidence_fig.colorbar(_image, ax=_ax, label="Distinct source URLs")
    evidence_fig.tight_layout()
    evidence_chart = mo.vstack([mo.md("## Current evidence capture"), evidence_fig])
    evidence_chart
    return


@app.cell
def _(con):
    requested_facts = con.execute(
        """
        WITH procurement_turns AS (
            SELECT
                session_slug || ' / ' || strftime(created_at, '%m-%d %H:%M') AS work_item,
                lower(coalesce(original_request, content)) AS request
            FROM main.app_messages
            WHERE role = 'user'
              AND session_slug LIKE 'operator-%'
              AND (
                  lower(coalesce(original_request, content)) LIKE '%supplier%'
                  OR lower(coalesce(original_request, content)) LIKE '%sourcing%'
                  OR lower(coalesce(original_request, content)) LIKE '%rfq%'
                  OR lower(coalesce(original_request, content)) LIKE '%coa%'
                  OR lower(coalesce(original_request, content)) LIKE '%spec%'
                  OR lower(coalesce(original_request, content)) LIKE '%ingredient%'
              )
        ),
        fact_flags AS (
            SELECT work_item, 'MOQ' AS fact, request LIKE '%moq%' AS requested FROM procurement_turns
            UNION ALL SELECT work_item, 'Lead time', request LIKE '%lead time%' FROM procurement_turns
            UNION ALL SELECT work_item, 'COA', request LIKE '%coa%' FROM procurement_turns
            UNION ALL SELECT work_item, 'Spec sheet', request LIKE '%spec%' FROM procurement_turns
            UNION ALL SELECT work_item, 'Certification', request LIKE '%certif%' FROM procurement_turns
            UNION ALL SELECT work_item, 'Packaging', request LIKE '%packag%' FROM procurement_turns
            UNION ALL SELECT work_item, 'Origin / stock', request LIKE '%country of origin%' OR request LIKE '%stock location%' FROM procurement_turns
            UNION ALL SELECT work_item, 'Dual source', request LIKE '%dual-source%' OR request LIKE '%dual source%' FROM procurement_turns
        )
        SELECT work_item, fact, 1 AS request_count
        FROM fact_flags
        WHERE requested
        ORDER BY 1, 2
        """
    ).df()
    return (requested_facts,)


@app.cell(hide_code=True)
def _(colors, mo, plt, requested_facts):
    demand_matrix = (
        requested_facts.pivot(
            index="work_item",
            columns="fact",
            values="request_count",
        )
        .fillna(0)
        .astype(int)
    )
    demand_matrix = demand_matrix.loc[
        demand_matrix.sum(axis=1).sort_values(ascending=False).index
    ]

    demand_fig, _ax = plt.subplots(
        figsize=(10, max(3, len(demand_matrix) * 0.48))
    )
    _image = _ax.imshow(
        demand_matrix,
        aspect="auto",
        cmap="Oranges",
        norm=colors.Normalize(vmin=0, vmax=max(1, int(demand_matrix.to_numpy().max()))),
    )
    _ax.set_title("Procurement facts requested by work item", loc="left")
    _ax.set_xlabel("Requested fact")
    _ax.set_ylabel("Work item")
    _ax.set_xticks(
        range(len(demand_matrix.columns)),
        demand_matrix.columns,
        rotation=35,
        ha="right",
    )
    _ax.set_yticks(range(len(demand_matrix.index)), demand_matrix.index)
    for _row, work_item in enumerate(demand_matrix.index):
        for _column, fact in enumerate(demand_matrix.columns):
            if demand_matrix.loc[work_item, fact]:
                _ax.text(
                    _column,
                    _row,
                    "requested",
                    ha="center",
                    va="center",
                    fontsize=7,
                )
    demand_fig.colorbar(_image, ax=_ax, label="Requests mentioning the fact")
    demand_fig.tight_layout()
    demand_chart = mo.vstack(
        [
            mo.md("## Coordination demand"),
            demand_fig,
            mo.md(
                "This records demand for supplier facts, not their availability. "
                "Supplier-level cells require canonical suppliers and evidence-backed claims."
            ),
        ]
    )
    demand_chart
    return


@app.cell
def _(con, mo):
    _df = mo.sql(
        f"""
        WITH procurement_turns AS (
                SELECT
                    session_slug || ' / ' || strftime(created_at, '%m-%d %H:%M') AS work_item,
                    lower(coalesce(original_request, content)) AS request
                FROM main.app_messages
                WHERE role = 'user'
                  AND session_slug LIKE 'operator-%'
                  AND (
                      lower(coalesce(original_request, content)) LIKE '%supplier%'
                      OR lower(coalesce(original_request, content)) LIKE '%sourcing%'
                      OR lower(coalesce(original_request, content)) LIKE '%rfq%'
                      OR lower(coalesce(original_request, content)) LIKE '%coa%'
                      OR lower(coalesce(original_request, content)) LIKE '%spec%'
                      OR lower(coalesce(original_request, content)) LIKE '%ingredient%'
                  )
            ),
            fact_flags AS (
                SELECT work_item, 'MOQ' AS fact, request LIKE '%moq%' AS requested FROM procurement_turns
                UNION ALL SELECT work_item, 'Lead time', request LIKE '%lead time%' FROM procurement_turns
                UNION ALL SELECT work_item, 'COA', request LIKE '%coa%' FROM procurement_turns
                UNION ALL SELECT work_item, 'Spec sheet', request LIKE '%spec%' FROM procurement_turns
                UNION ALL SELECT work_item, 'Certification', request LIKE '%certif%' FROM procurement_turns
                UNION ALL SELECT work_item, 'Packaging', request LIKE '%packag%' FROM procurement_turns
                UNION ALL SELECT work_item, 'Origin / stock', request LIKE '%country of origin%' OR request LIKE '%stock location%' FROM procurement_turns
                UNION ALL SELECT work_item, 'Dual source', request LIKE '%dual-source%' OR request LIKE '%dual source%' FROM procurement_turns
            )
            SELECT work_item, fact, 1 AS request_count
            FROM fact_flags
            WHERE requested
            ORDER BY 1, 2
        """,
        engine=con
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
