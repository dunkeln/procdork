from __future__ import annotations

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .contracts import CreateIngestionJobRequest, IngestionJob
from .service import JobService

load_dotenv(find_dotenv())

app = FastAPI(title="Procdork ingestion microservice", version="0.1.0")
service = JobService()


@app.post("/ingestion/jobs", response_model=IngestionJob, status_code=202)
def create_ingestion_job(request: CreateIngestionJobRequest) -> IngestionJob:
    return service.create(
        request.sources,
        session_id=request.session_id,
        turn_id=request.turn_id,
    )


@app.get("/ingestion/jobs/{job_id}", response_model=IngestionJob)
def get_ingestion_job(job_id: str) -> IngestionJob:
    job = service.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@app.exception_handler(HTTPException)
def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})


@app.exception_handler(RequestValidationError)
def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    missing = ", ".join(".".join(str(part) for part in error["loc"][1:]) for error in exc.errors())
    return JSONResponse(status_code=400, content={"error": f"Invalid request: {missing}"})
