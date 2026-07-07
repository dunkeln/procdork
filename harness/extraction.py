from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from mimetypes import guess_type
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field


class HarnessModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class SourcePointer(HarnessModel):
    source_id: str
    source_type: str
    uri: str
    retrieved_at: datetime
    content_type: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    adapter_name: str = "unknown"


class ExtractedSource(HarnessModel):
    source: SourcePointer
    payload: bytes


def extract_source(source: str | SourcePointer, source_type: str = "unknown") -> ExtractedSource:
    pointer = source if isinstance(source, SourcePointer) else source_pointer(source, source_type)
    payload, content_type, adapter_name = read_source(pointer.uri)
    return ExtractedSource(
        payload=payload,
        source=pointer.model_copy(
            update={
                "content_type": content_type,
                "adapter_name": adapter_name,
                "retrieved_at": datetime.now(UTC),
            }
        ),
    )


def source_pointer(uri: str, source_type: str = "unknown", metadata: dict[str, str] | None = None) -> SourcePointer:
    return SourcePointer(
        source_id=f"src_{sha256(uri.encode()).hexdigest()[:12]}",
        source_type=source_type,
        uri=uri,
        retrieved_at=datetime.now(UTC),
        metadata=metadata or {},
    )


def read_source(source: str) -> tuple[bytes, str | None, str]:
    parsed = urlparse(source)
    if parsed.scheme in {"http", "https"}:
        request = Request(source, headers={"user-agent": "procdork-harness/0.1"})
        with urlopen(request, timeout=30) as response:
            return response.read(), response.headers.get_content_type(), "url"

    if parsed.scheme and parsed.scheme != "file":
        raise ValueError(f"unsupported source scheme: {parsed.scheme}")

    path = Path(parsed.path if parsed.scheme == "file" else source).expanduser()
    return path.read_bytes(), guess_type(path.name)[0], "local_file"
