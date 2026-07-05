## Procdork Ingestion Service

FastAPI service for the live document ingestion tool used by `web/src/routes/api/chat/+server.ts`.

Run locally:

```sh
uv run uvicorn ingestion.api:app --host 127.0.0.1 --port 8000
```

Then point the web runtime at it:

```sh
INGESTION_SERVICE_URL=http://127.0.0.1:8000 npm run dev
```

Contract source of truth: `../web/openapi.yaml`.
