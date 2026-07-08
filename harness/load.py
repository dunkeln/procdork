from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import json
from mimetypes import guess_extension
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from extraction import ExtractedSource, HarnessModel, SourcePointer
from olap import connect_duckdb


class LoadedArtifact(HarnessModel):
    artifact_id: str
    source: SourcePointer
    storage_uri: str
    sha256: str
    bytes: int
    loaded_at: datetime


def load_raw(extracted: ExtractedSource, storage_root: Path | str = "data/lake") -> LoadedArtifact:
    digest = sha256(extracted.payload).hexdigest()
    key = object_key(extracted.source.source_type, digest, extracted.source.uri, extracted.source.content_type)
    destination = Path(storage_root) / key
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(extracted.payload)
    return LoadedArtifact(
        artifact_id=f"art_{digest[:12]}",
        source=extracted.source,
        storage_uri=f"local://{key}",
        sha256=digest,
        bytes=len(extracted.payload),
        loaded_at=datetime.now(UTC),
    )


def append_manifest(artifact: LoadedArtifact, manifest_path: Path | str = "data/manifest.jsonl") -> None:
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as manifest:
        manifest.write(json.dumps(artifact.model_dump(mode="json"), sort_keys=True) + "\n")


def load_manifest_duckdb(artifact: LoadedArtifact, db_path: Path | str | None = None) -> None:
    with connect_duckdb(db_path) as con:
        con.execute(
            """
            create table if not exists raw_manifest (
                artifact_id varchar,
                source_id varchar,
                source_type varchar,
                source_uri varchar,
                source_retrieved_at timestamptz,
                source_content_type varchar,
                source_adapter_name varchar,
                source_metadata json,
                storage_uri varchar,
                sha256 varchar,
                bytes ubigint,
                loaded_at timestamptz
            )
            """
        )
        con.execute(
            """
            insert into raw_manifest values (?, ?, ?, ?, ?, ?, ?, ?::json, ?, ?, ?, ?)
            """,
            [
                artifact.artifact_id,
                artifact.source.source_id,
                artifact.source.source_type,
                artifact.source.uri,
                artifact.source.retrieved_at,
                artifact.source.content_type,
                artifact.source.adapter_name,
                json.dumps(artifact.source.metadata, sort_keys=True),
                artifact.storage_uri,
                artifact.sha256,
                artifact.bytes,
                artifact.loaded_at,
            ],
        )


def object_key(source_type: str, digest: str, source: str, content_type: str | None) -> str:
    suffix = PurePosixPath(urlparse(source).path).suffix or guess_extension(content_type or "") or ".bin"
    return f"raw/{safe_segment(source_type)}/{digest[:2]}/{digest}{suffix}"


def safe_segment(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value.lower()).strip("-") or "unknown"
