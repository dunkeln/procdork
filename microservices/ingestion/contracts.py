from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

ArtifactType = Literal[
    "web-page",
    "email-thread",
    "quote",
    "price-list",
    "coa",
    "sds",
    "spec-sheet",
    "certificate",
    "supplier-questionnaire",
    "other",
]
Confidence = Literal["high", "medium", "low", "unknown", "other"]
ExtractionMethod = Literal["web-search", "web-fetch", "document-ingestion", "email-ingestion", "manual-review", "other"]
JobStatus = Literal["queued", "running", "succeeded", "failed", "partial"]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DocumentIngestionRequest(ContractModel):
    source_id: str
    artifact_type: ArtifactType
    title: str
    retrieved_at: datetime
    url: HttpUrl | None = None
    mime_hint: str | None = None
    reason: str | None = None


class CreateIngestionJobRequest(ContractModel):
    session_id: str
    sources: list[DocumentIngestionRequest] = Field(min_length=1)
    turn_id: str | None = None


class SourceRef(ContractModel):
    source_id: str
    artifact_type: ArtifactType
    title: str
    retrieved_at: datetime
    url: str | None = None
    mime_hint: str | None = None
    page: float | None = None
    row: float | None = None
    text_span: str | None = None


class ObservedSupplier(ContractModel):
    observed_supplier_id: str
    name: str
    source: SourceRef
    extraction_method: ExtractionMethod
    confidence: Confidence


class CanonicalSupplier(ContractModel):
    canonical_supplier_id: str
    name: str
    observed_supplier_ids: list[str]
    confidence: Confidence
    updated_at: datetime


class SourceClaim(ContractModel):
    claim_id: str
    field: str
    value: Any
    source: SourceRef
    extraction_method: ExtractionMethod
    confidence: Confidence
    retrieved_at: datetime
    canonical_supplier_id: str | None = None
    observed_supplier_id: str | None = None


class SupplierConflict(ContractModel):
    conflict_id: str
    field: str
    claim_ids: list[str] = Field(min_length=2)
    status: Literal["open", "resolved", "other"]
    canonical_supplier_id: str | None = None
    note: str | None = None


class IngestionResult(ContractModel):
    observed_suppliers: list[ObservedSupplier]
    canonical_suppliers: list[CanonicalSupplier]
    source_claims: list[SourceClaim]
    conflicts: list[SupplierConflict]


class IngestionJob(ContractModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    sources: list[DocumentIngestionRequest]
    result: IngestionResult
    updated_at: datetime | None = None
    error: str | None = None
