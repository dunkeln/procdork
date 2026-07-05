from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .contracts import DocumentIngestionRequest

BlockKind = Literal["text", "table", "metadata"]


@dataclass
class ExtractedBlock:
    kind: BlockKind
    text: str
    source: DocumentIngestionRequest
    parser: str
    page: int | None = None
    row: int | None = None


@dataclass
class ExtractionArtifact:
    source: DocumentIngestionRequest
    blocks: list[ExtractedBlock] = field(default_factory=list)
    parsers_attempted: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(block.text for block in self.blocks if block.text)
