from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Protocol

import httpx

from .artifacts import ExtractedBlock, ExtractionArtifact
from .contracts import DocumentIngestionRequest
from .util import env, filename

DOC_TYPES = {"coa", "sds", "spec-sheet", "certificate", "price-list", "quote", "email-thread"}
DOC_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".csv", ".xls", ".doc"}


class Parser(Protocol):
    name: str

    def parse(self, source: DocumentIngestionRequest) -> ExtractionArtifact: ...


class ParserRouter:
    def __init__(self, parsers: list[Parser] | None = None) -> None:
        self.parsers = parsers or [LlamaParseParser(), UnstructuredParser()]

    def extract(self, source: DocumentIngestionRequest) -> ExtractionArtifact:
        artifact = ExtractionArtifact(source=source)
        if not should_parse_document(source):
            artifact.blocks.extend(pointer_blocks(source, "pointer"))
            return artifact
        if not source.url:
            artifact.errors.append("source has no URL; used pointer metadata only")
            artifact.blocks.extend(pointer_blocks(source, "pointer"))
            return artifact

        for parser in self._ordered_parsers(source):
            artifact.parsers_attempted.append(parser.name)
            parsed = parser.parse(source)
            artifact.errors.extend(parsed.errors)
            if parsed.blocks:
                artifact.blocks.extend(parsed.blocks)
                return artifact

        artifact.blocks.extend(pointer_blocks(source, "pointer"))
        return artifact

    def _ordered_parsers(self, source: DocumentIngestionRequest) -> list[Parser]:
        if wants_layout_parser(source):
            return self.parsers
        return list(reversed(self.parsers))


class LlamaParseParser:
    name = "llamaparse"

    def parse(self, source: DocumentIngestionRequest) -> ExtractionArtifact:
        artifact = ExtractionArtifact(source=source)
        key = env("LLAMA_CLOUD_API_KEY", "LLAMAINDEX")
        if not key:
            artifact.errors.append("LLAMA_CLOUD_API_KEY not configured")
            return artifact
        try:
            from llama_cloud import LlamaCloud

            result = LlamaCloud(api_key=key).parsing.parse(
                tier="agentic",
                version="latest",
                source_url=str(source.url),
                expand=["text", "markdown", "items"],
                timeout=120,
            )
            for text in result_texts(result):
                artifact.blocks.append(ExtractedBlock(kind="text", text=text[:100_000], source=source, parser=self.name))
            for table in result_tables(result):
                artifact.blocks.append(ExtractedBlock(kind="table", text=table[:100_000], source=source, parser=self.name))
        except Exception as exc:
            artifact.errors.append(f"LlamaParse failed: {exc.__class__.__name__}")
        return artifact


class UnstructuredParser:
    name = "unstructured"

    def parse(self, source: DocumentIngestionRequest) -> ExtractionArtifact:
        artifact = ExtractionArtifact(source=source)
        key = env("UNSTRUCTURED_API_KEY", "UNSTRUCTURED")
        if not key:
            artifact.errors.append("UNSTRUCTURED_API_KEY not configured")
            return artifact
        try:
            from unstructured_client import UnstructuredClient
            from unstructured_client.models.operations.partition import PartitionRequest
            from unstructured_client.models.shared.partition_parameters import Files, PartitionParameters

            response = httpx.get(str(source.url), timeout=30, follow_redirects=True)
            response.raise_for_status()
            client = UnstructuredClient(api_key_auth=key)
            partition = client.general.partition(
                request=PartitionRequest(
                    partition_parameters=PartitionParameters(
                        files=Files(content=response.content, file_name=filename(str(source.url)), content_type=source.mime_hint),
                        strategy="hi_res",
                        pdf_infer_table_structure=True,
                    )
                ),
                timeout_ms=120_000,
            )
            for element in partition_elements(partition):
                text = element_text(element)
                if text:
                    artifact.blocks.append(
                        ExtractedBlock(
                            kind="table" if element_category(element).lower() == "table" else "text",
                            text=text[:100_000],
                            source=source,
                            parser=self.name,
                            page=element_page(element),
                        )
                    )
        except Exception as exc:
            artifact.errors.append(f"Unstructured failed: {exc.__class__.__name__}")
        return artifact


def should_parse_document(source: DocumentIngestionRequest) -> bool:
    if source.mime_hint and any(kind in source.mime_hint for kind in ["pdf", "word", "sheet", "csv", "excel"]):
        return True
    if source.artifact_type in DOC_TYPES:
        return True
    if source.url and PurePosixPath(str(source.url).split("?", 1)[0]).suffix.lower() in DOC_EXTENSIONS:
        return True
    return False


def wants_layout_parser(source: DocumentIngestionRequest) -> bool:
    if source.mime_hint and any(kind in source.mime_hint for kind in ["pdf", "sheet", "excel", "spreadsheet"]):
        return True
    if source.artifact_type in {"coa", "spec-sheet", "certificate", "price-list", "supplier-questionnaire"}:
        return True
    return bool(source.url and PurePosixPath(str(source.url).split("?", 1)[0]).suffix.lower() in {".pdf", ".xlsx", ".xls"})


def pointer_blocks(source: DocumentIngestionRequest, parser: str) -> list[ExtractedBlock]:
    text = "\n".join(part for part in [source.title, source.reason, str(source.url or "")] if part)
    return [ExtractedBlock(kind="metadata", text=text, source=source, parser=parser)] if text else []


def result_texts(result: Any) -> list[str]:
    return [
        text
        for text in [
            getattr(result, "text", None),
            getattr(result, "text_full", None),
            getattr(result, "markdown", None),
            getattr(result, "markdown_full", None),
        ]
        if text
    ]


def result_tables(result: Any) -> list[str]:
    items = getattr(result, "items", None)
    pages = getattr(items, "pages", None) if items else None
    tables: list[str] = []
    for page in pages or []:
        for item in getattr(page, "items", []) or []:
            text = str(getattr(item, "md", "") or getattr(item, "text", ""))
            if text and "table" in str(getattr(item, "type", "")).lower():
                tables.append(text)
    return tables


def partition_elements(partition: Any) -> list[Any]:
    return getattr(partition, "elements", None) or getattr(partition, "partition_response", None) or []


def element_text(element: Any) -> str:
    if isinstance(element, dict):
        return str(element.get("text", ""))
    return str(getattr(element, "text", ""))


def element_category(element: Any) -> str:
    if isinstance(element, dict):
        return str(element.get("type", element.get("category", "")))
    return str(getattr(element, "type", getattr(element, "category", "")))


def element_page(element: Any) -> int | None:
    metadata = element.get("metadata", {}) if isinstance(element, dict) else getattr(element, "metadata", None)
    page = metadata.get("page_number") if isinstance(metadata, dict) else getattr(metadata, "page_number", None)
    return int(page) if page else None
