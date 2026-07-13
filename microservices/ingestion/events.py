from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from .contracts import (
    CanonicalSupplier,
    ContractModel,
    DocumentIngestionRequest,
    IngestionJob,
    ObservedSupplier,
    SourceClaim,
    SupplierConflict,
)
from .util import now

if TYPE_CHECKING:
    from .artifacts import ExtractionArtifact


class ArtifactSummary(ContractModel):
    source_id: str
    parsers_attempted: list[str]
    block_count: int
    errors: list[str]


class IngestionEvent(ContractModel):
    event_id: str
    event_type: str = "ingestion.job.completed"
    schema_version: str = "1"
    emitted_at: datetime
    job_id: str
    session_id: str | None = None
    turn_id: str | None = None
    status: str
    duration_ms: int
    sources: list[DocumentIngestionRequest]
    observed_suppliers: list[ObservedSupplier]
    canonical_suppliers: list[CanonicalSupplier]
    source_claims: list[SourceClaim]
    conflicts: list[SupplierConflict]
    artifacts: list[ArtifactSummary]


def emit_completed_job(
    job: IngestionJob,
    artifacts: list[ExtractionArtifact],
    *,
    session_id: str | None,
    turn_id: str | None,
    duration_ms: int,
) -> None:
    path = os.environ.get("INGESTION_EVENT_JSONL")
    if not path:
        return

    event = IngestionEvent(
        event_id=f"evt_{job.job_id}",
        job_id=job.job_id,
        session_id=session_id,
        turn_id=turn_id,
        status=job.status,
        duration_ms=duration_ms,
        emitted_at=now(),
        sources=job.sources,
        observed_suppliers=job.result.observed_suppliers,
        canonical_suppliers=job.result.canonical_suppliers,
        source_claims=job.result.source_claims,
        conflicts=job.result.conflicts,
        artifacts=[
            ArtifactSummary(
                source_id=artifact.source.source_id,
                parsers_attempted=artifact.parsers_attempted,
                block_count=len(artifact.blocks),
                errors=artifact.errors,
            )
            for artifact in artifacts
        ],
    )
    # ponytail: local JSONL assumes one service writer; use object storage or a queue if concurrent writers appear.
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event.model_dump(mode="json"), sort_keys=True) + "\n")
