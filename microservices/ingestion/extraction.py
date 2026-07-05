from __future__ import annotations

import re

from .artifacts import ExtractedBlock, ExtractionArtifact
from .contracts import CanonicalSupplier, ObservedSupplier, SourceClaim, SourceRef, SupplierConflict
from .util import canonical_name, clean_value, now, stable_id

PROCUREMENT_FIELDS = {
    "moq": re.compile(r"\b(?:moq|minimum order quantity)\b\s*[:\-]?\s*([^\n;,]+)", re.I),
    "lead-time-text": re.compile(r"\blead\s*time\b\s*[:\-]?\s*([^\n;,]+)", re.I),
    "grade": re.compile(r"\bgrade\b\s*[:\-]?\s*([^\n;,]+)", re.I),
    "price": re.compile(r"\b(?:price|unit price)\b\s*[:\-]?\s*([$€£]?\s*\d[\d,]*(?:\.\d+)?)", re.I),
}
CERT_RE = re.compile(r"\b(organic|non-gmo|kosher|halal|gfsi|sqf|brc|fssc\s*22000|haccp)\b", re.I)
SUPPLIER_RE = re.compile(
    r"\b(?:supplier|vendor|manufacturer|distributor|broker)\b\s*[:\-]\s*([A-Z][A-Za-z0-9&.,' \-]{2,80})",
    re.I,
)
COMPANY_HINT_RE = re.compile(r"\b(?:gmbh|kg|spa|llc|inc|ltd|corp|company|co\.?)\b", re.I)
COUNTRY_OR_LABEL = {"germany", "italy", "supplier", "production", "manufacturing", "place of origin raw material"}


def extract_observed_suppliers(artifact: ExtractionArtifact) -> list[ObservedSupplier]:
    seen: set[str] = set()
    suppliers: list[ObservedSupplier] = []
    def add_supplier(name: str, block: ExtractedBlock, span: str) -> None:
        if not name or name.lower() in seen:
            return
        seen.add(name.lower())
        suppliers.append(
            ObservedSupplier(
                observed_supplier_id=stable_id("obs", block.source.source_id, name),
                name=name,
                source=source_ref(block, span),
                extraction_method=method_for(block),
                confidence="medium" if block.parser != "pointer" else "low",
            )
        )

    for idx, block in enumerate(artifact.blocks):
        for name, span in supplier_mentions(block.text):
            add_supplier(name, block, span)
        if not supplier_label_block(block.text) or SUPPLIER_RE.search(block.text):
            continue
        for candidate in artifact.blocks[idx + 1 : idx + 5]:
            name = supplier_line_name(candidate.text)
            if name:
                add_supplier(name, candidate, candidate.text)
                break
    return suppliers


def supplier_mentions(text: str) -> list[tuple[str, str]]:
    mentions = [(clean_value(match.group(1)), match.group(0)) for match in SUPPLIER_RE.finditer(text)]
    lines = [line.strip() for line in text.splitlines()]
    for idx, line in enumerate(lines):
        if "supplier" not in line.lower():
            continue
        if SUPPLIER_RE.search(line):
            continue
        for candidate in lines[idx + 1 : idx + 5]:
            name = supplier_line_name(candidate)
            if name:
                mentions.append((name, candidate))
                break
    return mentions


def supplier_label_block(text: str) -> bool:
    normalized = text.strip().lower()
    return "supplier" in normalized and (normalized.endswith(":") or "/" in normalized)


def supplier_line_name(line: str) -> str:
    line = clean_value(line.split("(", 1)[0].split(" - ", 1)[0])
    if not line or line.startswith("("):
        return ""
    if line.lower() in COUNTRY_OR_LABEL or "/" in line or ":" in line:
        return ""
    if COMPANY_HINT_RE.search(line):
        return line
    return line if len(line.split()) >= 2 and line.isupper() else ""


def extract_claims(artifact: ExtractionArtifact, suppliers: list[ObservedSupplier]) -> list[SourceClaim]:
    observed_id = suppliers[0].observed_supplier_id if suppliers else None
    claims: list[SourceClaim] = []
    for block in artifact.blocks:
        for field, pattern in PROCUREMENT_FIELDS.items():
            for match in pattern.finditer(block.text):
                value = clean_value(match.group(1))
                if value:
                    claims.append(make_claim(block, field, value, match.group(0), observed_id, "medium"))
        for match in CERT_RE.finditer(block.text):
            claims.append(make_claim(block, "certification", clean_value(match.group(1)), match.group(0), observed_id, "low"))
    return claims


def canonicalize_suppliers(observed: list[ObservedSupplier]) -> list[CanonicalSupplier]:
    groups: dict[str, list[ObservedSupplier]] = {}
    for supplier in observed:
        groups.setdefault(canonical_name(supplier.name).lower(), []).append(supplier)
    return [
        CanonicalSupplier(
            canonical_supplier_id=stable_id("sup", key),
            name=canonical_name(items[0].name),
            observed_supplier_ids=[item.observed_supplier_id for item in items],
            confidence="medium",
            updated_at=now(),
        )
        for key, items in groups.items()
    ]


def attach_canonical_claims(claims: list[SourceClaim], canonical: list[CanonicalSupplier]) -> None:
    by_observed = {
        observed_id: supplier.canonical_supplier_id
        for supplier in canonical
        for observed_id in supplier.observed_supplier_ids
    }
    for claim in claims:
        if claim.observed_supplier_id:
            claim.canonical_supplier_id = by_observed.get(claim.observed_supplier_id)


def find_conflicts(claims: list[SourceClaim]) -> list[SupplierConflict]:
    grouped: dict[tuple[str | None, str], list[SourceClaim]] = {}
    for claim in claims:
        grouped.setdefault((claim.canonical_supplier_id, claim.field), []).append(claim)
    conflicts: list[SupplierConflict] = []
    for (supplier_id, field), items in grouped.items():
        if len({str(item.value).lower() for item in items}) > 1:
            conflicts.append(
                SupplierConflict(
                    conflict_id=stable_id("conflict", supplier_id or "unknown", field, *[item.claim_id for item in items]),
                    canonical_supplier_id=supplier_id,
                    field=field,
                    claim_ids=[item.claim_id for item in items],
                    status="open",
                    note="Multiple extracted values disagree; preserve for review.",
                )
            )
    return conflicts


def make_claim(block: ExtractedBlock, field: str, value: str, span: str, observed_id: str | None, confidence: str) -> SourceClaim:
    return SourceClaim(
        claim_id=stable_id("claim", block.source.source_id, field, value, span),
        observed_supplier_id=observed_id,
        field=field,
        value=value,
        source=source_ref(block, span),
        extraction_method=method_for(block),
        confidence=confidence,
        retrieved_at=block.source.retrieved_at,
    )


def source_ref(block: ExtractedBlock, text_span: str | None = None) -> SourceRef:
    source = block.source
    return SourceRef(
        source_id=source.source_id,
        artifact_type=source.artifact_type,
        title=source.title,
        retrieved_at=source.retrieved_at,
        url=str(source.url) if source.url else None,
        mime_hint=source.mime_hint,
        page=block.page,
        row=block.row,
        text_span=text_span,
    )


def method_for(block: ExtractedBlock) -> str:
    return "email-ingestion" if block.source.artifact_type == "email-thread" else "document-ingestion"
