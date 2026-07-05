from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app import app
from ingestion.artifacts import ExtractedBlock, ExtractionArtifact
from ingestion.contracts import DocumentIngestionRequest
from ingestion.service import JobService
from ingestion.vendors import ParserRouter
from tests.fixtures import LYRECO_COA_TEXT, PRICE_LIST_TEXT, PRICE_UPDATE_TEXT, PUBLIC_COA_URL


class TextParser:
    name = "fixture-vendor"

    def __init__(self, by_source: dict[str, str]) -> None:
        self.by_source = by_source

    def parse(self, source: DocumentIngestionRequest) -> ExtractionArtifact:
        return ExtractionArtifact(
            source=source,
            blocks=[
                ExtractedBlock(
                    kind="table" if source.artifact_type == "price-list" else "text",
                    text=self.by_source[source.source_id],
                    source=source,
                    parser=self.name,
                    page=1,
                )
            ],
        )


class IngestionE2ETest(unittest.TestCase):
    def test_public_coa_shape_extracts_supplier_names_and_certifications(self) -> None:
        source = DocumentIngestionRequest(
            source_id="lyreco-coa",
            artifact_type="coa",
            title="Public COA sample",
            retrieved_at="2026-07-05T00:00:00Z",
            url=PUBLIC_COA_URL,
            mime_hint="application/pdf",
        )

        job = JobService(ParserRouter([TextParser({"lyreco-coa": LYRECO_COA_TEXT})])).create([source])

        supplier_names = {supplier.name for supplier in job.result.observed_suppliers}
        certifications = {claim.value.lower() for claim in job.result.source_claims if claim.field == "certification"}
        self.assertEqual(job.status, "succeeded")
        self.assertIn("Rudolf Wild GmbH & Co. KG", supplier_names)
        self.assertIn("SPUMADOR SPA", supplier_names)
        self.assertIn("brc", certifications)
        self.assertTrue(all(claim.source.url == PUBLIC_COA_URL for claim in job.result.source_claims))

    def test_conflicting_vendor_claims_are_preserved_not_collapsed(self) -> None:
        sources = [
            DocumentIngestionRequest(
                source_id="quote-old",
                artifact_type="price-list",
                title="Harbor old price list",
                retrieved_at="2026-07-05T00:00:00Z",
                url="https://example.com/old.pdf",
                mime_hint="application/pdf",
            ),
            DocumentIngestionRequest(
                source_id="quote-new",
                artifact_type="price-list",
                title="Harbor new price list",
                retrieved_at="2026-07-05T00:00:00Z",
                url="https://example.com/new.pdf",
                mime_hint="application/pdf",
            ),
        ]

        job = JobService(ParserRouter([TextParser({"quote-old": PRICE_LIST_TEXT, "quote-new": PRICE_UPDATE_TEXT})])).create(sources)

        fields = [conflict.field for conflict in job.result.conflicts]
        self.assertIn("price", fields)
        self.assertIn("lead-time-text", fields)
        self.assertEqual(len(job.result.canonical_suppliers), 1)

    def test_http_contract_keeps_error_shape(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/ingestion/jobs",
            json={
                "session_id": "fixture",
                "sources": [
                    {
                        "source_id": "inline",
                        "artifact_type": "quote",
                        "title": "Inline quote",
                        "retrieved_at": "2026-07-05T00:00:00Z",
                        "reason": PRICE_LIST_TEXT,
                    }
                ],
            },
        )
        body = response.json()
        self.assertEqual(response.status_code, 202)
        self.assertEqual(client.get(f"/ingestion/jobs/{body['job_id']}").status_code, 200)
        self.assertEqual(client.get("/ingestion/jobs/missing").json(), {"error": "Job not found."})
        self.assertEqual(client.post("/ingestion/jobs", json={}).status_code, 400)


if __name__ == "__main__":
    unittest.main()
