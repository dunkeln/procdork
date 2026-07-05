from ingestion.api import app

__all__ = ["app"]


def _demo() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post(
        "/ingestion/jobs",
        json={
            "session_id": "demo",
            "sources": [
                {
                    "source_id": "src_1",
                    "artifact_type": "quote",
                    "title": "Quote from Acme Foods",
                    "retrieved_at": "2026-07-05T00:00:00Z",
                    "reason": "Supplier: Acme Foods LLC\nMOQ: 500 kg\nLead time: 21 days\nKosher certified",
                }
            ],
        },
    )
    body = response.json()
    assert response.status_code == 202, body
    assert body["result"]["observed_suppliers"][0]["name"] == "Acme Foods LLC"
    assert {claim["field"] for claim in body["result"]["source_claims"]} >= {"moq", "lead-time-text", "certification"}


if __name__ == "__main__":
    _demo()
