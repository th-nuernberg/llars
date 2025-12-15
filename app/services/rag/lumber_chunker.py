"""
LumberChunker

Chunking utilities for RAG documents with optional PDF page support.

Goals:
- Produce stable, readable chunks using a recursive splitter
- Track chunk offsets (start/end char) for later inspection in the UI
- Preserve PDF page numbers when possible
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple
import logging
import os


logger = logging.getLogger(__name__)


DEFAULT_SEPARATORS: Sequence[str] = ("# ", "## ", "\n\n", "\n", ". ", "! ", "? ")


@dataclass(frozen=True)
class LumberChunk:
    text: str
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    page_number: Optional[int] = None


class LumberChunker:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[Sequence[str]] = None,
    ):
        self.chunk_size = int(chunk_size)
        self.chunk_overlap = int(chunk_overlap)
        self.separators = list(separators) if separators else list(DEFAULT_SEPARATORS)

    def chunk_text(
        self,
        text: str,
        *,
        page_number: Optional[int] = None,
        base_offset: int = 0,
    ) -> List[LumberChunk]:
        if not text:
            return []

        pieces = _split_text_recursive(
            text,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
        )

        return _attach_positions(
            text,
            pieces,
            chunk_overlap=self.chunk_overlap,
            page_number=page_number,
            base_offset=base_offset,
        )

    def chunk_pdf_pages(self, pages: Sequence[Tuple[int, str]]) -> List[LumberChunk]:
        chunks: List[LumberChunk] = []
        offset = 0

        for page_number, page_text in pages:
            page_chunks = self.chunk_text(
                page_text or "",
                page_number=page_number,
                base_offset=offset,
            )
            chunks.extend(page_chunks)
            offset += len(page_text or "") + 2  # implicit separator between pages

        return chunks


def chunk_file(
    file_path: str,
    mime_type: Optional[str] = None,
    *,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separators: Optional[Sequence[str]] = None,
) -> List[LumberChunk]:
    """
    Load a file and return chunks.

    For PDFs we extract text per page and preserve page numbers.
    For text-like files we read as UTF-8 with a latin-1 fallback.
    """
    mime_type = (mime_type or "").lower()
    ext = os.path.splitext(file_path)[1].lower()

    chunker = LumberChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
    )

    if mime_type == "application/pdf" or ext == ".pdf":
        pages = _extract_pdf_pages(file_path)
        return chunker.chunk_pdf_pages(pages)

    text = _read_text_file(file_path)
    return chunker.chunk_text(text)


def _read_text_file(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin-1", errors="replace") as f:
            return f.read()
    except Exception as e:
        logger.error(f"[LumberChunker] Failed to read file {file_path}: {e}")
        return ""


def _extract_pdf_pages(file_path: str) -> List[Tuple[int, str]]:
    try:
        import fitz  # PyMuPDF
    except Exception as e:
        logger.error(f"[LumberChunker] PyMuPDF not available for PDF extraction: {e}")
        return []

    pages: List[Tuple[int, str]] = []
    try:
        doc = fitz.open(file_path)
        for idx in range(doc.page_count):
            page = doc.load_page(idx)
            pages.append((idx + 1, page.get_text("text") or ""))
        doc.close()
    except Exception as e:
        logger.error(f"[LumberChunker] Failed to extract PDF text {file_path}: {e}")
        return []

    return pages


def _split_text_recursive(
    text: str,
    *,
    chunk_size: int,
    chunk_overlap: int,
    separators: Sequence[str],
) -> List[str]:
    """
    Use LangChain's RecursiveCharacterTextSplitter when available.
    Falls back to a naive fixed-size splitter if import fails.
    """
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=list(separators),
        )
        return splitter.split_text(text)
    except Exception as e:
        logger.warning(f"[LumberChunker] Falling back to naive splitter: {e}")

    # Naive fallback
    if chunk_size <= 0:
        return [text]

    chunks: List[str] = []
    step = max(1, chunk_size - max(0, chunk_overlap))
    for start in range(0, len(text), step):
        chunk = text[start : start + chunk_size]
        if chunk:
            chunks.append(chunk)
    return chunks


def _attach_positions(
    original: str,
    pieces: Sequence[str],
    *,
    chunk_overlap: int,
    page_number: Optional[int],
    base_offset: int,
) -> List[LumberChunk]:
    chunks: List[LumberChunk] = []

    cursor = 0
    for piece in pieces:
        idx = original.find(piece, cursor)
        if idx == -1:
            idx = original.find(piece)

        if idx == -1:
            chunks.append(LumberChunk(text=piece, start_char=None, end_char=None, page_number=page_number))
            continue

        start = base_offset + idx
        end = start + len(piece)
        chunks.append(LumberChunk(text=piece, start_char=start, end_char=end, page_number=page_number))

        advance = max(1, len(piece) - max(0, chunk_overlap))
        cursor = idx + advance

    return chunks

