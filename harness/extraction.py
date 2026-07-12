from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from typing import Callable

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


SourceReader = Callable[[str], tuple[bytes, str | None, str]]


def extract_source(
    source: str | SourcePointer,
    reader: SourceReader,
    source_type: str = "unknown",
) -> ExtractedSource:
    pointer = source if isinstance(source, SourcePointer) else source_pointer(source, source_type)
    payload, content_type, adapter_name = reader(pointer.uri)
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
