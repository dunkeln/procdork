from __future__ import annotations

import os
import unittest
from pathlib import Path

from dotenv import load_dotenv
from fastapi.testclient import TestClient

from app import app
import ingestion.api as api
from ingestion.service import JobService
from ingestion.vendors import ParserRouter, UnstructuredParser
from tests.fixtures import PUBLIC_COA_URL


class IngestionLiveE2ETest(unittest.TestCase):
    def test_http_job_uses_real_unstructured_and_extracts_public_coa(self) -> None:
        load_dotenv(Path(__file__).resolve().parents[2] / ".env")
        if os.getenv("RUN_LIVE_E2E") != "1":
            self.skipTest("set RUN_LIVE_E2E=1 to call real vendors")

        old_service = api.service
        api.service = JobService(ParserRouter([UnstructuredParser()]))
        try:
            client = TestClient(app)
            create = client.post(
                "/ingestion/jobs",
                json={
                    "session_id": "live-smoke",
                    "sources": [
                        {
                            "source_id": "live-lyreco-coa",
                            "artifact_type": "coa",
                            "title": "Public COA sample",
                            "retrieved_at": "2026-07-05T00:00:00Z",
                            "url": PUBLIC_COA_URL,
                            "mime_hint": "application/pdf",
                        }
                    ],
                },
            )
            body = create.json()
            fetched = client.get(f"/ingestion/jobs/{body['job_id']}")
        finally:
            api.service = old_service

        self.assertEqual(202, create.status_code)
        self.assertEqual(200, fetched.status_code)
        self.assertEqual("succeeded", body["status"])
        self.assertIsNone(body["error"])
        self.assertIn("Rudolf Wild GmbH & Co. KG", {supplier["name"] for supplier in body["result"]["observed_suppliers"]})
        self.assertIn("SPUMADOR SPA", {supplier["name"] for supplier in body["result"]["observed_suppliers"]})
        self.assertIn("brc", {claim["value"].lower() for claim in body["result"]["source_claims"] if claim["field"] == "certification"})


if __name__ == "__main__":
    unittest.main()
