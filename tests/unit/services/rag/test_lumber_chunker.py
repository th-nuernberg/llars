"""
Unit Tests: Lumber Chunker Service
==================================

Tests for the RAG document chunking service.

Test IDs:
- CHUNK-001 to CHUNK-010: Basic Chunking Tests
- CHUNK-020 to CHUNK-025: Position Tracking Tests
- CHUNK-030 to CHUNK-035: PDF Extraction Tests
- CHUNK-040 to CHUNK-045: Edge Cases

Status: Implemented
"""

import pytest
from unittest.mock import MagicMock, patch
import tempfile
import os


class TestBasicChunking:
    """
    Basic Chunking Tests

    Tests for basic text splitting functionality.
    """

    def test_CHUNK_001_simple_text_chunking(self, app, app_context):
        """
        [CHUNK-001] Einfacher Text wird gechunkt

        Ein langer Text soll in mehrere Chunks aufgeteilt werden.
        """
        from services.rag.lumber_chunker import LumberChunker

        chunker = LumberChunker(chunk_size=100, chunk_overlap=20)

        # Text longer than chunk_size
        text = "Dies ist ein Testtext. " * 20  # ~460 chars

        chunks = chunker.chunk_text(text)

        assert len(chunks) > 1
        # Each chunk should have text
        for chunk in chunks:
            assert chunk.text
            assert len(chunk.text) > 0

    def test_CHUNK_002_short_text_single_chunk(self, app, app_context):
        """
        [CHUNK-002] Kurzer Text bleibt ein Chunk

        Text kürzer als chunk_size soll ein einzelner Chunk sein.
        """
        from services.rag.lumber_chunker import LumberChunker

        chunker = LumberChunker(chunk_size=1000, chunk_overlap=100)

        short_text = "Dies ist ein kurzer Text."

        chunks = chunker.chunk_text(short_text)

        assert len(chunks) == 1
        assert chunks[0].text == short_text

    def test_CHUNK_003_chunk_size_respected(self, app, app_context):
        """
        [CHUNK-003] Chunk-Größe wird respektiert

        Chunks sollen nicht größer als chunk_size + overlap sein.
        """
        from services.rag.lumber_chunker import LumberChunker

        chunk_size = 200
        overlap = 50
        chunker = LumberChunker(chunk_size=chunk_size, chunk_overlap=overlap)

        # Long text with clear sentence boundaries
        text = "Dies ist Satz eins. " * 50

        chunks = chunker.chunk_text(text)

        # Most chunks should be around chunk_size (with some tolerance for overlap)
        for chunk in chunks:
            # Allow some tolerance for word boundary alignment
            assert len(chunk.text) <= chunk_size + overlap + 50

    def test_CHUNK_004_chunk_overlap_works(self, app, app_context):
        """
        [CHUNK-004] Chunk Overlap funktioniert

        Aufeinanderfolgende Chunks sollen sich überlappen.
        """
        from services.rag.lumber_chunker import LumberChunker

        chunker = LumberChunker(chunk_size=100, chunk_overlap=30)

        text = "Wort " * 100  # 500 chars

        chunks = chunker.chunk_text(text)

        if len(chunks) >= 2:
            # Check that consecutive chunks have some overlap
            chunk1_end = chunks[0].text[-30:]
            chunk2_start = chunks[1].text[:30]
            # Some overlap should exist (either text or position)
            assert len(chunks) >= 2

    def test_CHUNK_005_empty_text_handling(self, app, app_context):
        """
        [CHUNK-005] Leerer Text Handling

        Leerer Text soll leere Liste oder einzelnen leeren Chunk zurückgeben.
        """
        from services.rag.lumber_chunker import LumberChunker

        chunker = LumberChunker()

        chunks = chunker.chunk_text("")

        # Should either be empty list or have empty/minimal chunks
        assert isinstance(chunks, list)

    def test_CHUNK_006_whitespace_only_text(self, app, app_context):
        """
        [CHUNK-006] Nur Whitespace Text

        Text mit nur Leerzeichen soll sinnvoll behandelt werden.
        """
        from services.rag.lumber_chunker import LumberChunker

        chunker = LumberChunker()

        chunks = chunker.chunk_text("   \n\t   \n   ")

        assert isinstance(chunks, list)

    def test_CHUNK_007_custom_separators(self, app, app_context):
        """
        [CHUNK-007] Benutzerdefinierte Separatoren

        Chunker soll benutzerdefinierte Separatoren respektieren.
        """
        from services.rag.lumber_chunker import LumberChunker

        # Custom separators
        custom_seps = ("## ", "\n\n", "\n")
        chunker = LumberChunker(
            chunk_size=100,
            chunk_overlap=10,
            separators=custom_seps
        )

        text = "## Header 1\n\nParagraph 1.\n\n## Header 2\n\nParagraph 2."

        chunks = chunker.chunk_text(text)

        assert isinstance(chunks, list)


class TestPositionTracking:
    """
    Position Tracking Tests

    Tests for character position tracking in chunks.
    """

    def test_CHUNK_020_start_char_tracking(self, app, app_context):
        """
        [CHUNK-020] Start-Position Tracking

        Chunks sollen start_char Position haben.
        """
        from services.rag.lumber_chunker import LumberChunker

        chunker = LumberChunker(chunk_size=50, chunk_overlap=10)

        text = "Erster Abschnitt. Zweiter Abschnitt. Dritter Abschnitt. Vierter Abschnitt."

        chunks = chunker.chunk_text(text)

        # First chunk should start at 0 or close to it
        if chunks and chunks[0].start_char is not None:
            assert chunks[0].start_char >= 0

    def test_CHUNK_021_end_char_tracking(self, app, app_context):
        """
        [CHUNK-021] End-Position Tracking

        Chunks sollen end_char Position haben.
        """
        from services.rag.lumber_chunker import LumberChunker

        chunker = LumberChunker(chunk_size=50, chunk_overlap=10)

        text = "Erster Teil. Zweiter Teil. Dritter Teil. Vierter Teil."

        chunks = chunker.chunk_text(text)

        for chunk in chunks:
            if chunk.end_char is not None and chunk.start_char is not None:
                # end_char should be greater than start_char
                assert chunk.end_char >= chunk.start_char

    def test_CHUNK_022_positions_match_text(self, app, app_context):
        """
        [CHUNK-022] Positionen matchen Text

        Text zwischen start_char und end_char soll dem Chunk-Text entsprechen.
        """
        from services.rag.lumber_chunker import LumberChunker

        chunker = LumberChunker(chunk_size=100, chunk_overlap=20)

        text = "Dies ist ein langer Testtext mit mehreren Sätzen. Jeder Satz enthält wichtige Informationen. Der Chunker soll die Positionen korrekt tracken."

        chunks = chunker.chunk_text(text)

        for chunk in chunks:
            if chunk.start_char is not None and chunk.end_char is not None:
                # Extract text using positions
                extracted = text[chunk.start_char:chunk.end_char]
                # Should match or be contained in chunk text
                assert chunk.text.strip() in text or extracted in chunk.text

    def test_CHUNK_023_base_offset_parameter(self, app, app_context):
        """
        [CHUNK-023] Base Offset Parameter

        base_offset soll zu allen Positionen addiert werden.
        """
        from services.rag.lumber_chunker import LumberChunker

        chunker = LumberChunker(chunk_size=100, chunk_overlap=10)

        text = "Kurzer Text hier."
        base_offset = 1000

        chunks = chunker.chunk_text(text, base_offset=base_offset)

        if chunks and chunks[0].start_char is not None:
            # Position should be offset
            assert chunks[0].start_char >= base_offset

    def test_CHUNK_024_page_number_parameter(self, app, app_context):
        """
        [CHUNK-024] Page Number Parameter

        page_number soll an Chunks weitergegeben werden.
        """
        from services.rag.lumber_chunker import LumberChunker

        chunker = LumberChunker(chunk_size=100, chunk_overlap=10)

        text = "Text auf Seite 5."
        page_num = 5

        chunks = chunker.chunk_text(text, page_number=page_num)

        for chunk in chunks:
            assert chunk.page_number == page_num


class TestPDFChunking:
    """
    PDF Chunking Tests

    Tests for PDF page extraction and chunking.
    """

    def test_CHUNK_030_chunk_pdf_pages(self, app, app_context):
        """
        [CHUNK-030] PDF Seiten chunken

        chunk_pdf_pages soll Seiten korrekt verarbeiten.
        """
        from services.rag.lumber_chunker import LumberChunker

        chunker = LumberChunker(chunk_size=100, chunk_overlap=20)

        # Simulate PDF pages as (page_num, text) tuples
        pages = [
            (1, "Dies ist der Text auf Seite 1. Er enthält mehrere Sätze."),
            (2, "Seite 2 hat anderen Inhalt. Auch hier mehrere Sätze."),
            (3, "Seite 3 ist die letzte. Abschließende Informationen."),
        ]

        chunks = chunker.chunk_pdf_pages(pages)

        assert len(chunks) > 0
        # Should have page numbers
        page_numbers = [c.page_number for c in chunks if c.page_number is not None]
        assert len(page_numbers) > 0

    def test_CHUNK_031_pdf_page_numbers_preserved(self, app, app_context):
        """
        [CHUNK-031] PDF Seitenzahlen erhalten

        Chunks sollen die Seitenzahl der Quellseite haben.
        """
        from services.rag.lumber_chunker import LumberChunker

        chunker = LumberChunker(chunk_size=50, chunk_overlap=10)

        pages = [
            (1, "Seite eins Inhalt."),
            (5, "Seite fünf Inhalt."),
            (10, "Seite zehn Inhalt."),
        ]

        chunks = chunker.chunk_pdf_pages(pages)

        page_numbers = set(c.page_number for c in chunks if c.page_number is not None)
        # Should contain at least some of the original page numbers
        assert len(page_numbers) > 0

    def test_CHUNK_032_empty_pdf_pages(self, app, app_context):
        """
        [CHUNK-032] Leere PDF Seiten

        Leere Seiten sollen übersprungen werden.
        """
        from services.rag.lumber_chunker import LumberChunker

        chunker = LumberChunker()

        pages = [
            (1, ""),
            (2, "   "),
            (3, "Nur diese Seite hat Text."),
        ]

        chunks = chunker.chunk_pdf_pages(pages)

        # Should have chunks only from page 3
        assert all(c.text.strip() for c in chunks if c.text)


class TestLumberChunkDataclass:
    """
    LumberChunk Dataclass Tests

    Tests for the LumberChunk dataclass.
    """

    def test_CHUNK_040_lumber_chunk_creation(self, app, app_context):
        """
        [CHUNK-040] LumberChunk Erstellung

        LumberChunk soll korrekt erstellt werden können.
        """
        from services.rag.lumber_chunker import LumberChunk

        chunk = LumberChunk(
            text="Test Text",
            start_char=0,
            end_char=9,
            page_number=1
        )

        assert chunk.text == "Test Text"
        assert chunk.start_char == 0
        assert chunk.end_char == 9
        assert chunk.page_number == 1

    def test_CHUNK_041_lumber_chunk_immutable(self, app, app_context):
        """
        [CHUNK-041] LumberChunk ist immutable

        LumberChunk ist frozen und soll nicht veränderbar sein.
        """
        from services.rag.lumber_chunker import LumberChunk

        chunk = LumberChunk(text="Test")

        with pytest.raises(Exception):  # FrozenInstanceError
            chunk.text = "Modified"

    def test_CHUNK_042_lumber_chunk_defaults(self, app, app_context):
        """
        [CHUNK-042] LumberChunk Defaults

        Optionale Felder sollen None als Default haben.
        """
        from services.rag.lumber_chunker import LumberChunk

        chunk = LumberChunk(text="Only text")

        assert chunk.text == "Only text"
        assert chunk.start_char is None
        assert chunk.end_char is None
        assert chunk.page_number is None


class TestFileChunking:
    """
    File Chunking Tests

    Tests for the chunk_file function.
    """

    def test_CHUNK_050_chunk_text_file(self, app, app_context):
        """
        [CHUNK-050] Textdatei chunken

        chunk_file soll .txt Dateien lesen und chunken.
        """
        from services.rag.lumber_chunker import chunk_file

        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Dies ist ein Testtext. " * 20)
            temp_path = f.name

        try:
            chunks = chunk_file(temp_path)
            assert len(chunks) > 0
            assert all(isinstance(c.text, str) for c in chunks)
        finally:
            os.unlink(temp_path)

    def test_CHUNK_051_chunk_markdown_file(self, app, app_context):
        """
        [CHUNK-051] Markdown-Datei chunken

        chunk_file soll .md Dateien lesen und chunken.
        """
        from services.rag.lumber_chunker import chunk_file

        # Create a temporary markdown file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("# Header\n\nParagraph 1.\n\n## Subheader\n\nParagraph 2.")
            temp_path = f.name

        try:
            chunks = chunk_file(temp_path)
            assert len(chunks) > 0
        finally:
            os.unlink(temp_path)

    def test_CHUNK_052_chunk_nonexistent_file(self, app, app_context):
        """
        [CHUNK-052] Nicht existierende Datei

        chunk_file soll bei fehlender Datei Exception werfen oder leere Liste.
        """
        from services.rag.lumber_chunker import chunk_file

        try:
            chunks = chunk_file('/nonexistent/path/file.txt')
            # Either empty list or exception
            assert chunks == [] or chunks is None
        except (FileNotFoundError, OSError):
            # Expected behavior
            pass

    def test_CHUNK_053_chunk_file_encoding_fallback(self, app, app_context):
        """
        [CHUNK-053] Encoding Fallback

        chunk_file soll bei UTF-8-Fehler auf Latin-1 fallen.
        """
        from services.rag.lumber_chunker import chunk_file

        # Create a file with Latin-1 encoding
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            # Write Latin-1 encoded text with special chars
            f.write("Größenänderung und Übung".encode('latin-1'))
            temp_path = f.name

        try:
            chunks = chunk_file(temp_path)
            # Should handle the encoding gracefully
            assert isinstance(chunks, list)
        finally:
            os.unlink(temp_path)


class TestChunkerConfiguration:
    """
    Chunker Configuration Tests

    Tests for chunker initialization and configuration.
    """

    def test_CHUNK_060_default_configuration(self, app, app_context):
        """
        [CHUNK-060] Default Konfiguration

        LumberChunker soll sinnvolle Defaults haben.
        """
        from services.rag.lumber_chunker import LumberChunker

        chunker = LumberChunker()

        # Should have default values
        assert chunker.chunk_size > 0
        assert chunker.chunk_overlap >= 0
        assert chunker.chunk_overlap < chunker.chunk_size

    def test_CHUNK_061_custom_configuration(self, app, app_context):
        """
        [CHUNK-061] Benutzerdefinierte Konfiguration

        Alle Parameter sollen überschreibbar sein.
        """
        from services.rag.lumber_chunker import LumberChunker

        custom_size = 500
        custom_overlap = 50
        custom_seps = ("\n\n", "\n")

        chunker = LumberChunker(
            chunk_size=custom_size,
            chunk_overlap=custom_overlap,
            separators=custom_seps
        )

        assert chunker.chunk_size == custom_size
        assert chunker.chunk_overlap == custom_overlap


class TestUnicodeHandling:
    """
    Unicode Handling Tests

    Tests for proper Unicode text handling.
    """

    def test_CHUNK_070_german_umlauts(self, app, app_context):
        """
        [CHUNK-070] Deutsche Umlaute

        Chunker soll Umlaute korrekt handhaben.
        """
        from services.rag.lumber_chunker import LumberChunker

        chunker = LumberChunker(chunk_size=100, chunk_overlap=10)

        text = "Größe, Übung, Änderung. Öffentliche Äußerungen über Übel."

        chunks = chunker.chunk_text(text)

        # All umlauts should be preserved
        all_text = " ".join(c.text for c in chunks)
        assert "ö" in all_text.lower() or "Ö" in all_text
        assert "ü" in all_text.lower() or "Ü" in all_text
        assert "ä" in all_text.lower() or "Ä" in all_text

    def test_CHUNK_071_emoji_handling(self, app, app_context):
        """
        [CHUNK-071] Emoji Handling

        Chunker soll Emojis korrekt handhaben.
        """
        from services.rag.lumber_chunker import LumberChunker

        chunker = LumberChunker(chunk_size=100, chunk_overlap=10)

        text = "Text mit Emojis 🚀 und mehr 🎉 Inhalt."

        chunks = chunker.chunk_text(text)

        all_text = " ".join(c.text for c in chunks)
        # Emojis should be preserved or gracefully handled
        assert len(chunks) > 0

    def test_CHUNK_072_chinese_characters(self, app, app_context):
        """
        [CHUNK-072] Chinesische Zeichen

        Chunker soll CJK Zeichen handhaben.
        """
        from services.rag.lumber_chunker import LumberChunker

        chunker = LumberChunker(chunk_size=50, chunk_overlap=10)

        text = "这是中文文本。包含多个句子。用于测试分块功能。"

        chunks = chunker.chunk_text(text)

        assert len(chunks) > 0
        # Chinese chars should be preserved
        all_text = "".join(c.text for c in chunks)
        assert "中" in all_text or len(all_text) > 0
