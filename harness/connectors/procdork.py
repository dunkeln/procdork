from __future__ import annotations

import json
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from uuid import uuid4

import duckdb


def chat_dataset_version(con: duckdb.DuckDBPyConnection) -> str:
    return con.execute(
        """
        with cases as (
            select
                m.id,
                m.completed_at,
                m.original_request,
                m.content,
                coalesce(string_agg(ms.source_url, '|' order by ms.source_url), '') as sources
            from app_messages m
            left join app_message_sources ms on ms.message_id = m.id
            where m.role = 'assistant'
              and m.completed_at is not null
              and m.original_request is not null
              and m.session_slug not like 'eval-%'
            group by m.id, m.completed_at, m.original_request, m.content
        )
        select sha256(string_agg(
            cast(id as varchar) || ':' || cast(completed_at as varchar) || ':' ||
            sha256(original_request || content || sources),
            '|' order by id
        )) from cases
        """
    ).fetchone()[0][:12]


def load_chat_cases(
    con: duckdb.DuckDBPyConnection,
    *,
    case_id: str | None = None,
    previous_result: str = "all",
    limit: int = 1,
) -> list[dict[str, object]]:
    rows = con.execute(
        """
        with latest as (
            select case_id, result, score, system_version,
                   row_number() over (partition by case_id order by evaluated_at desc) as position
            from raw_evaluation_results
            where evaluator_name = 'inline_citations'
        )
        select
            cast(m.id as varchar) as case_id,
            m.session_slug,
            m.original_request,
            m.content,
            cast(m.completed_at as varchar) as completed_at,
            count(ms.source_url) as source_count,
            l.result as previous_result,
            l.score as previous_score,
            l.system_version as previous_system_version
        from app_messages m
        left join app_message_sources ms on ms.message_id = m.id
        left join latest l on l.case_id = cast(m.id as varchar) and l.position = 1
        where m.role = 'assistant'
          and m.completed_at is not null
          and m.original_request is not null
          and m.session_slug not like 'eval-%'
          and (? is null or cast(m.id as varchar) = ?)
          and (? = 'all' or l.result = ?)
        group by m.id, m.session_slug, m.original_request, m.content, m.completed_at,
                 l.result, l.score, l.system_version
        having count(ms.source_url) > 0
        order by m.completed_at desc
        limit ?
        """,
        [case_id, case_id, previous_result, previous_result, limit],
    ).fetchall()
    columns = [column[0] for column in con.description]
    cases = [dict(zip(columns, row, strict=True)) for row in rows]
    for case in cases:
        case["replay_requests"] = [
            row[0]
            for row in con.execute(
                """
                select original_request
                from app_messages
                where session_slug = ?
                  and role = 'assistant'
                  and completed_at is not null
                  and completed_at <= cast(? as timestamptz)
                order by completed_at
                """,
                [case["session_slug"], case["completed_at"]],
            ).fetchall()
        ]
    return cases


def replay_chat(
    base_url: str, messages: list[str], timeout: int = 180
) -> dict[str, object]:
    session_id = f"eval-{uuid4()}"
    final: dict[str, object] | None = None
    for message in messages:
        request = Request(
            urljoin(base_url.rstrip("/") + "/", "api/chat"),
            data=json.dumps({"message": message, "sessionId": session_id}).encode(),
            headers={
                "content-type": "application/json",
                "user-agent": "procdork-harness/0.1",
            },
            method="POST",
        )
        with urlopen(request, timeout=timeout) as response:
            for raw_line in response:
                event = json.loads(raw_line)
                if event.get("type") == "error":
                    raise RuntimeError(str(event.get("error") or "Chat replay failed"))
                if event.get("type") == "final":
                    final = event
    if not final:
        raise RuntimeError("Chat replay ended without a final event")
    return {
        "session_id": session_id,
        "response": str(final.get("prose") or ""),
        "citations": final.get("citations")
        if isinstance(final.get("citations"), list)
        else [],
        "evidence_uri": urljoin(base_url.rstrip("/") + "/", f"sessions/{session_id}"),
    }
