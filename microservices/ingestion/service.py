from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

from .artifacts import ExtractionArtifact
from .contracts import DocumentIngestionRequest, IngestionJob, IngestionResult
from .events import completed_job_event, emit_completed_job
from .extraction import attach_canonical_claims, canonicalize_suppliers, extract_claims, extract_observed_suppliers, find_conflicts
from .util import now
from .vendors import ParserRouter


@dataclass
class StoredJob:
    job: IngestionJob
    artifacts: list[ExtractionArtifact]


class JobService:
    def __init__(self, router: ParserRouter | None = None) -> None:
        self.router = router or ParserRouter()
        self.jobs: dict[str, StoredJob] = {}

    def create(
        self,
        sources: list[DocumentIngestionRequest],
        *,
        session_id: str | None = None,
        turn_id: str | None = None,
    ) -> IngestionJob:
        started = perf_counter()
        artifacts = [self.router.extract(source) for source in sources]
        observed = []
        claims = []
        for artifact in artifacts:
            source_observed = extract_observed_suppliers(artifact)
            observed.extend(source_observed)
            claims.extend(extract_claims(artifact, source_observed))

        canonical = canonicalize_suppliers(observed)
        attach_canonical_claims(claims, canonical)
        parser_errors = [f"{artifact.source.source_id}: {error}" for artifact in artifacts for error in artifact.errors]
        result = IngestionResult(
            observed_suppliers=observed,
            canonical_suppliers=canonical,
            source_claims=claims,
            conflicts=find_conflicts(claims),
        )
        job = IngestionJob(
            job_id=f"ing_{uuid4().hex[:12]}",
            status="partial" if parser_errors else "succeeded",
            created_at=now(),
            updated_at=now(),
            sources=sources,
            result=result,
            error="; ".join(parser_errors) or None,
        )
        event = completed_job_event(
            job,
            artifacts,
            session_id=session_id,
            turn_id=turn_id,
            duration_ms=round((perf_counter() - started) * 1000),
        )
        job = job.model_copy(update={"event": event})
        self.jobs[job.job_id] = StoredJob(job=job, artifacts=artifacts)
        emit_completed_job(event)
        return job

    def get(self, job_id: str) -> IngestionJob | None:
        stored = self.jobs.get(job_id)
        return stored.job if stored else None
