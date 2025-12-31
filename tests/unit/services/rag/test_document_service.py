"""
Unit Tests: Document Service
============================

Tests for the RAG document management service.

Test IDs:
- DOC-001 to DOC-010: Utility Method Tests
- DOC-020 to DOC-030: Document Retrieval Tests
- DOC-040 to DOC-055: Document Creation Tests
- DOC-060 to DOC-070: Document Modification Tests
- DOC-080 to DOC-090: Serialization Tests

Status: Implemented
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime
from io import BytesIO
import tempfile
import os


class TestUtilityMethods:
    """
    Utility Method Tests

    Tests for static utility functions.
    """

    def test_DOC_001_allowed_file_pdf(self, app, app_context):
        """
        [DOC-001] PDF Datei erlaubt

        PDF-Dateien sollen als erlaubt erkannt werden.
        """
        from services.rag.document_service import DocumentService

        assert DocumentService.allowed_file('document.pdf') is True
        assert DocumentService.allowed_file('DOCUMENT.PDF') is True

    def test_DOC_002_allowed_file_txt(self, app, app_context):
        """
        [DOC-002] TXT Datei erlaubt

        Text-Dateien sollen als erlaubt erkannt werden.
        """
        from services.rag.document_service import DocumentService

        assert DocumentService.allowed_file('readme.txt') is True
        assert DocumentService.allowed_file('notes.TXT') is True

    def test_DOC_003_allowed_file_markdown(self, app, app_context):
        """
        [DOC-003] Markdown Datei erlaubt

        Markdown-Dateien sollen als erlaubt erkannt werden.
        """
        from services.rag.document_service import DocumentService

        assert DocumentService.allowed_file('README.md') is True

    def test_DOC_004_allowed_file_docx(self, app, app_context):
        """
        [DOC-004] DOCX Datei erlaubt

        Word-Dokumente sollen als erlaubt erkannt werden.
        """
        from services.rag.document_service import DocumentService

        assert DocumentService.allowed_file('report.docx') is True
        assert DocumentService.allowed_file('letter.doc') is True

    def test_DOC_005_disallowed_file_types(self, app, app_context):
        """
        [DOC-005] Nicht erlaubte Dateitypen

        Executables und andere gefährliche Dateien sollen abgelehnt werden.
        """
        from services.rag.document_service import DocumentService

        assert DocumentService.allowed_file('virus.exe') is False
        assert DocumentService.allowed_file('script.js') is False
        assert DocumentService.allowed_file('image.png') is False
        assert DocumentService.allowed_file('archive.zip') is False

    def test_DOC_006_no_extension(self, app, app_context):
        """
        [DOC-006] Datei ohne Extension

        Dateien ohne Extension sollen abgelehnt werden.
        """
        from services.rag.document_service import DocumentService

        assert DocumentService.allowed_file('noextension') is False
        assert DocumentService.allowed_file('') is False

    def test_DOC_007_get_mime_type_pdf(self, app, app_context):
        """
        [DOC-007] MIME Type für PDF

        PDF soll application/pdf zurückgeben.
        """
        from services.rag.document_service import DocumentService

        assert DocumentService.get_mime_type('pdf') == 'application/pdf'
        assert DocumentService.get_mime_type('PDF') == 'application/pdf'

    def test_DOC_008_get_mime_type_text(self, app, app_context):
        """
        [DOC-008] MIME Type für Text

        TXT und MD sollen text/* zurückgeben.
        """
        from services.rag.document_service import DocumentService

        assert DocumentService.get_mime_type('txt') == 'text/plain'
        assert DocumentService.get_mime_type('md') == 'text/markdown'

    def test_DOC_009_get_mime_type_word(self, app, app_context):
        """
        [DOC-009] MIME Type für Word

        DOC/DOCX sollen korrekte MIME types zurückgeben.
        """
        from services.rag.document_service import DocumentService

        assert DocumentService.get_mime_type('docx') == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        assert DocumentService.get_mime_type('doc') == 'application/msword'

    def test_DOC_010_get_mime_type_unknown(self, app, app_context):
        """
        [DOC-010] MIME Type für unbekannte Extension

        Unbekannte Extensions sollen application/octet-stream zurückgeben.
        """
        from services.rag.document_service import DocumentService

        assert DocumentService.get_mime_type('xyz') == 'application/octet-stream'
        assert DocumentService.get_mime_type('unknown') == 'application/octet-stream'

    def test_DOC_011_get_file_hash(self, app, app_context):
        """
        [DOC-011] Datei-Hash berechnen

        SHA-256 Hash soll korrekt berechnet werden.
        """
        from services.rag.document_service import DocumentService

        # Create a temporary file with known content
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'test content for hashing')
            temp_path = f.name

        try:
            file_hash = DocumentService.get_file_hash(temp_path)

            # Verify hash is a valid SHA-256 hex string
            assert isinstance(file_hash, str)
            assert len(file_hash) == 64  # SHA-256 produces 64 hex chars
            assert all(c in '0123456789abcdef' for c in file_hash)
        finally:
            os.unlink(temp_path)

    def test_DOC_012_get_file_hash_consistency(self, app, app_context):
        """
        [DOC-012] Datei-Hash Konsistenz

        Gleicher Inhalt soll gleichen Hash produzieren.
        """
        from services.rag.document_service import DocumentService

        content = b'identical content'

        with tempfile.NamedTemporaryFile(delete=False) as f1:
            f1.write(content)
            path1 = f1.name

        with tempfile.NamedTemporaryFile(delete=False) as f2:
            f2.write(content)
            path2 = f2.name

        try:
            hash1 = DocumentService.get_file_hash(path1)
            hash2 = DocumentService.get_file_hash(path2)
            assert hash1 == hash2
        finally:
            os.unlink(path1)
            os.unlink(path2)


class TestDocumentRetrieval:
    """
    Document Retrieval Tests

    Tests for fetching documents from database.
    """

    def test_DOC_020_get_documents_empty(self, app, db, app_context):
        """
        [DOC-020] Leere Dokumentliste

        Bei leerer Datenbank soll leere Liste zurückgegeben werden.
        """
        from services.rag.document_service import DocumentService

        documents, pagination = DocumentService.get_documents()

        assert documents == []
        assert pagination['total'] == 0
        assert pagination['page'] == 1

    def test_DOC_021_get_documents_with_data(self, app, db, app_context):
        """
        [DOC-021] Dokumente abrufen

        Vorhandene Dokumente sollen korrekt abgerufen werden.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGCollection

        # Create test collection
        collection = RAGCollection(
            name='test-collection',
            display_name='Test Collection',
            description='Test',
            created_by='test_user',
            is_public=True
        )
        db.session.add(collection)
        db.session.flush()

        # Create test document
        doc = RAGDocument(
            filename='test.pdf',
            original_filename='test.pdf',
            file_path='/tmp/test.pdf',
            file_size_bytes=1024,
            mime_type='application/pdf',
            file_hash='abc123',
            title='Test Document',
            status='indexed',
            collection_id=collection.id,
            uploaded_by='test_user'
        )
        db.session.add(doc)
        db.session.commit()

        documents, pagination = DocumentService.get_documents()

        assert len(documents) == 1
        assert documents[0].title == 'Test Document'
        assert pagination['total'] == 1

    def test_DOC_022_get_documents_filter_collection(self, app, db, app_context):
        """
        [DOC-022] Dokumente nach Collection filtern

        Filter nach collection_id soll funktionieren.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGCollection

        # Create two collections
        coll1 = RAGCollection(name='coll1', display_name='Collection 1', created_by='test')
        coll2 = RAGCollection(name='coll2', display_name='Collection 2', created_by='test')
        db.session.add_all([coll1, coll2])
        db.session.flush()

        # Create documents in different collections
        doc1 = RAGDocument(
            filename='doc1.pdf', original_filename='doc1.pdf',
            file_path='/tmp/doc1.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash1',
            collection_id=coll1.id, uploaded_by='test'
        )
        doc2 = RAGDocument(
            filename='doc2.pdf', original_filename='doc2.pdf',
            file_path='/tmp/doc2.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash2',
            collection_id=coll2.id, uploaded_by='test'
        )
        db.session.add_all([doc1, doc2])
        db.session.commit()

        # Filter by collection
        documents, _ = DocumentService.get_documents(collection_id=coll1.id)
        assert len(documents) == 1
        assert documents[0].filename == 'doc1.pdf'

    def test_DOC_023_get_documents_filter_status(self, app, db, app_context):
        """
        [DOC-023] Dokumente nach Status filtern

        Filter nach status soll funktionieren.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        # Create documents with different statuses
        doc_pending = RAGDocument(
            filename='pending.pdf', original_filename='pending.pdf',
            file_path='/tmp/pending.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash1',
            status='pending', collection_id=collection.id, uploaded_by='test'
        )
        doc_indexed = RAGDocument(
            filename='indexed.pdf', original_filename='indexed.pdf',
            file_path='/tmp/indexed.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash2',
            status='indexed', collection_id=collection.id, uploaded_by='test'
        )
        db.session.add_all([doc_pending, doc_indexed])
        db.session.commit()

        # Filter by status
        documents, _ = DocumentService.get_documents(status='indexed')
        assert len(documents) == 1
        assert documents[0].status == 'indexed'

    def test_DOC_024_get_documents_search(self, app, db, app_context):
        """
        [DOC-024] Dokumente suchen

        Suche nach Titel/Dateiname/Beschreibung soll funktionieren.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        doc1 = RAGDocument(
            filename='report.pdf', original_filename='report.pdf',
            file_path='/tmp/report.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash1',
            title='Annual Report 2024',
            collection_id=collection.id, uploaded_by='test'
        )
        doc2 = RAGDocument(
            filename='notes.pdf', original_filename='notes.pdf',
            file_path='/tmp/notes.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash2',
            title='Meeting Notes',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add_all([doc1, doc2])
        db.session.commit()

        # Search by title
        documents, _ = DocumentService.get_documents(search='Report')
        assert len(documents) == 1
        assert documents[0].title == 'Annual Report 2024'

    def test_DOC_025_get_documents_pagination(self, app, db, app_context):
        """
        [DOC-025] Dokument-Paginierung

        Paginierung soll korrekt funktionieren.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        # Create 5 documents
        for i in range(5):
            doc = RAGDocument(
                filename=f'doc{i}.pdf', original_filename=f'doc{i}.pdf',
                file_path=f'/tmp/doc{i}.pdf', file_size_bytes=100,
                mime_type='application/pdf', file_hash=f'hash{i}',
                collection_id=collection.id, uploaded_by='test'
            )
            db.session.add(doc)
        db.session.commit()

        # Get first page (2 per page)
        docs_page1, pagination = DocumentService.get_documents(page=1, per_page=2)
        assert len(docs_page1) == 2
        assert pagination['total'] == 5
        assert pagination['pages'] == 3
        assert pagination['has_next'] is True
        assert pagination['has_prev'] is False

        # Get second page
        docs_page2, pagination2 = DocumentService.get_documents(page=2, per_page=2)
        assert len(docs_page2) == 2
        assert pagination2['has_prev'] is True

    def test_DOC_026_get_document_by_id(self, app, db, app_context):
        """
        [DOC-026] Einzelnes Dokument abrufen

        get_document_by_id soll korrektes Dokument zurückgeben.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='single.pdf', original_filename='single.pdf',
            file_path='/tmp/single.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='unique_hash',
            title='Single Document',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.commit()

        result = DocumentService.get_document_by_id(doc.id)
        assert result is not None
        assert result.title == 'Single Document'

    def test_DOC_027_get_document_by_id_not_found(self, app, db, app_context):
        """
        [DOC-027] Nicht existierendes Dokument

        Nicht existierende ID soll None zurückgeben.
        """
        from services.rag.document_service import DocumentService

        result = DocumentService.get_document_by_id(99999)
        assert result is None

    def test_DOC_028_get_document_content(self, app, db, app_context):
        """
        [DOC-028] Dokument-Inhalt abrufen

        get_document_content soll Dokument mit zusammengeführten Chunks zurückgeben.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGDocumentChunk, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='content.pdf', original_filename='content.pdf',
            file_path='/tmp/content.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_content',
            status='indexed',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.flush()

        # Add chunks
        chunk1 = RAGDocumentChunk(
            document_id=doc.id, chunk_index=0,
            content='First paragraph.', page_number=1
        )
        chunk2 = RAGDocumentChunk(
            document_id=doc.id, chunk_index=1,
            content='Second paragraph.', page_number=1
        )
        db.session.add_all([chunk1, chunk2])
        db.session.commit()

        result_doc, content = DocumentService.get_document_content(doc.id)

        assert result_doc is not None
        assert 'First paragraph.' in content
        assert 'Second paragraph.' in content

    def test_DOC_029_get_document_chunks(self, app, db, app_context):
        """
        [DOC-029] Dokument-Chunks abrufen

        get_document_chunks soll Liste aller Chunks zurückgeben.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGDocumentChunk, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='chunks.pdf', original_filename='chunks.pdf',
            file_path='/tmp/chunks.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_chunks',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.flush()

        # Add 3 chunks
        for i in range(3):
            chunk = RAGDocumentChunk(
                document_id=doc.id, chunk_index=i,
                content=f'Chunk {i} content', page_number=1
            )
            db.session.add(chunk)
        db.session.commit()

        result_doc, chunks = DocumentService.get_document_chunks(doc.id)

        assert result_doc is not None
        assert len(chunks) == 3
        assert chunks[0].chunk_index == 0
        assert chunks[2].chunk_index == 2


class TestDocumentCreation:
    """
    Document Creation Tests

    Tests for creating new documents.
    """

    def test_DOC_040_check_file_duplicate_none(self, app, db, app_context):
        """
        [DOC-040] Kein Duplikat gefunden

        Bei neuem Hash soll None zurückgegeben werden.
        """
        from services.rag.document_service import DocumentService

        result = DocumentService.check_file_duplicate('new_unique_hash_12345')
        assert result is None

    def test_DOC_041_check_file_duplicate_exists(self, app, db, app_context):
        """
        [DOC-041] Duplikat gefunden

        Bei vorhandenem Hash soll Dokument zurückgegeben werden.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        existing_hash = 'existing_file_hash_abcd'
        doc = RAGDocument(
            filename='existing.pdf', original_filename='existing.pdf',
            file_path='/tmp/existing.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash=existing_hash,
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.commit()

        result = DocumentService.check_file_duplicate(existing_hash)
        assert result is not None
        assert result.filename == 'existing.pdf'

    def test_DOC_042_get_default_collection(self, app, db, app_context):
        """
        [DOC-042] Default Collection abrufen

        get_default_collection soll 'general' Collection zurückgeben.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGCollection

        # Create default collection
        general = RAGCollection(
            name='general',
            display_name='General Collection',
            created_by='system'
        )
        db.session.add(general)
        db.session.commit()

        result = DocumentService.get_default_collection()
        assert result is not None
        assert result.name == 'general'

    def test_DOC_043_get_default_collection_not_exists(self, app, db, app_context):
        """
        [DOC-043] Default Collection nicht vorhanden

        Ohne 'general' Collection soll None zurückgegeben werden.
        """
        from services.rag.document_service import DocumentService

        result = DocumentService.get_default_collection()
        assert result is None

    def test_DOC_044_create_document_no_file(self, app, db, app_context):
        """
        [DOC-044] Dokument ohne Datei erstellen

        Leere Datei soll Fehler zurückgeben.
        """
        from services.rag.document_service import DocumentService

        result = DocumentService.create_document(
            file=None,
            uploaded_by='test_user'
        )

        assert result['success'] is False
        assert 'No file provided' in result['error']

    def test_DOC_045_create_document_disallowed_type(self, app, db, app_context):
        """
        [DOC-045] Dokument mit nicht erlaubtem Typ

        Nicht erlaubte Dateitypen sollen Fehler zurückgeben.
        """
        from services.rag.document_service import DocumentService
        from werkzeug.datastructures import FileStorage

        # Create mock file with disallowed extension
        mock_file = MagicMock(spec=FileStorage)
        mock_file.filename = 'malware.exe'

        result = DocumentService.create_document(
            file=mock_file,
            uploaded_by='test_user'
        )

        assert result['success'] is False
        assert 'File type not allowed' in result['error']

    def test_DOC_046_create_document_too_large(self, app, db, app_context):
        """
        [DOC-046] Dokument zu groß

        Dateien über MAX_FILE_SIZE sollen abgelehnt werden.
        """
        from services.rag.document_service import DocumentService, MAX_FILE_SIZE
        from werkzeug.datastructures import FileStorage

        mock_file = MagicMock(spec=FileStorage)
        mock_file.filename = 'large.pdf'

        # Simulate large file
        mock_file.seek = MagicMock()
        mock_file.tell = MagicMock(return_value=MAX_FILE_SIZE + 1)

        result = DocumentService.create_document(
            file=mock_file,
            uploaded_by='test_user'
        )

        assert result['success'] is False
        assert 'too large' in result['error']

    def test_DOC_047_create_document_success(self, app, db, app_context):
        """
        [DOC-047] Dokument erfolgreich erstellen

        Valide Datei soll erfolgreich erstellt werden.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGCollection
        from werkzeug.datastructures import FileStorage

        # Create collection
        collection = RAGCollection(
            name='general',
            display_name='General',
            created_by='test'
        )
        db.session.add(collection)
        db.session.commit()

        # Create mock file
        content = b'Test PDF content'
        mock_file = MagicMock(spec=FileStorage)
        mock_file.filename = 'test_upload.pdf'
        mock_file.seek = MagicMock()
        mock_file.tell = MagicMock(return_value=len(content))
        mock_file.save = MagicMock()

        with patch('services.rag.document_service.os.makedirs'):
            with patch('services.rag.document_service.DocumentService.get_file_hash', return_value='unique_hash_test'):
                with patch('services.rag.document_service.os.path.exists', return_value=True):
                    result = DocumentService.create_document(
                        file=mock_file,
                        uploaded_by='test_user',
                        title='Uploaded Document',
                        description='Test upload'
                    )

        assert result['success'] is True
        assert result['document'] is not None
        assert result['document'].title == 'Uploaded Document'

    def test_DOC_048_create_document_duplicate(self, app, db, app_context):
        """
        [DOC-048] Duplikat-Dokument ablehnen

        Bereits vorhandene Datei soll abgelehnt werden.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGCollection, RAGDocument
        from werkzeug.datastructures import FileStorage

        # Create existing document
        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        existing = RAGDocument(
            filename='existing.pdf', original_filename='existing.pdf',
            file_path='/tmp/existing.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='duplicate_hash',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(existing)
        db.session.commit()

        # Try to upload duplicate
        mock_file = MagicMock(spec=FileStorage)
        mock_file.filename = 'new_file.pdf'
        mock_file.seek = MagicMock()
        mock_file.tell = MagicMock(return_value=100)
        mock_file.save = MagicMock()

        with patch('services.rag.document_service.os.makedirs'):
            with patch('services.rag.document_service.DocumentService.get_file_hash', return_value='duplicate_hash'):
                with patch('services.rag.document_service.os.remove'):
                    result = DocumentService.create_document(
                        file=mock_file,
                        uploaded_by='test_user'
                    )

        assert result['success'] is False
        assert 'Duplicate' in result['error']
        assert 'existing_document_id' in result


class TestDocumentModification:
    """
    Document Modification Tests

    Tests for updating and deleting documents.
    """

    def test_DOC_060_update_document_success(self, app, db, app_context):
        """
        [DOC-060] Dokument erfolgreich aktualisieren

        Metadaten sollen erfolgreich aktualisiert werden.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='update.pdf', original_filename='update.pdf',
            file_path='/tmp/update.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_update',
            title='Original Title',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.commit()

        with patch('services.chatbot.lexical_index.LexicalSearchIndex'):
            success, error, updated_doc = DocumentService.update_document(
                document_id=doc.id,
                data={'title': 'Updated Title', 'description': 'New description'}
            )

        assert success is True
        assert error is None
        assert updated_doc.title == 'Updated Title'
        assert updated_doc.description == 'New description'

    def test_DOC_061_update_document_not_found(self, app, db, app_context):
        """
        [DOC-061] Nicht existierendes Dokument aktualisieren

        Update auf nicht existierende ID soll fehlschlagen.
        """
        from services.rag.document_service import DocumentService

        success, error, doc = DocumentService.update_document(
            document_id=99999,
            data={'title': 'New Title'}
        )

        assert success is False
        assert 'not found' in error.lower()
        assert doc is None

    def test_DOC_062_update_document_forbidden_fields(self, app, db, app_context):
        """
        [DOC-062] Nicht erlaubte Felder ignorieren

        Nicht erlaubte Felder sollen ignoriert werden.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='forbidden.pdf', original_filename='forbidden.pdf',
            file_path='/tmp/forbidden.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_forbidden',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.commit()

        original_hash = doc.file_hash

        with patch('services.chatbot.lexical_index.LexicalSearchIndex'):
            success, _, updated_doc = DocumentService.update_document(
                document_id=doc.id,
                data={
                    'file_hash': 'hacked_hash',  # Should be ignored
                    'title': 'Valid Update'
                }
            )

        assert success is True
        assert updated_doc.file_hash == original_hash  # Unchanged
        assert updated_doc.title == 'Valid Update'

    def test_DOC_063_delete_document_success(self, app, db, app_context):
        """
        [DOC-063] Dokument erfolgreich löschen

        Dokument und Datei sollen gelöscht werden.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(
            name='test', display_name='Test', created_by='test',
            document_count=1, total_size_bytes=100
        )
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='delete_me.pdf', original_filename='delete_me.pdf',
            file_path='/tmp/delete_me.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_delete',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.commit()

        doc_id = doc.id

        with patch('services.rag.document_service.os.path.exists', return_value=True):
            with patch('services.rag.document_service.os.remove') as mock_remove:
                with patch('services.chatbot.lexical_index.LexicalSearchIndex'):
                    success, error = DocumentService.delete_document(doc_id)

        assert success is True
        assert error is None
        mock_remove.assert_called_once()

        # Verify document is deleted
        assert RAGDocument.query.get(doc_id) is None

    def test_DOC_064_delete_document_not_found(self, app, db, app_context):
        """
        [DOC-064] Nicht existierendes Dokument löschen

        Delete auf nicht existierende ID soll fehlschlagen.
        """
        from services.rag.document_service import DocumentService

        success, error = DocumentService.delete_document(99999)

        assert success is False
        assert 'not found' in error.lower()

    def test_DOC_065_delete_document_updates_collection_stats(self, app, db, app_context):
        """
        [DOC-065] Collection-Statistiken nach Delete aktualisieren

        Nach Delete sollen Collection-Statistiken aktualisiert werden.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(
            name='test', display_name='Test', created_by='test',
            document_count=5, total_size_bytes=5000
        )
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='stats.pdf', original_filename='stats.pdf',
            file_path='/tmp/stats.pdf', file_size_bytes=1000,
            mime_type='application/pdf', file_hash='hash_stats',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.commit()

        doc_id = doc.id
        collection_id = collection.id

        with patch('services.rag.document_service.os.path.exists', return_value=True):
            with patch('services.rag.document_service.os.remove'):
                with patch('services.chatbot.lexical_index.LexicalSearchIndex'):
                    DocumentService.delete_document(doc_id)

        # Reload collection
        updated_collection = RAGCollection.query.get(collection_id)
        assert updated_collection.document_count == 4
        assert updated_collection.total_size_bytes == 4000


class TestSerialization:
    """
    Serialization Tests

    Tests for document and chunk serialization.
    """

    def test_DOC_080_serialize_document_basic(self, app, db, app_context):
        """
        [DOC-080] Dokument-Serialisierung Basis

        Basis-Serialisierung soll alle wichtigen Felder enthalten.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGCollection
        from datetime import datetime

        collection = RAGCollection(name='test', display_name='Test Collection', created_by='test')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='serialize.pdf', original_filename='serialize.pdf',
            file_path='/tmp/serialize.pdf', file_size_bytes=2048,
            mime_type='application/pdf', file_hash='hash_serialize',
            title='Serialization Test',
            description='Test document',
            status='indexed',
            collection_id=collection.id, uploaded_by='test_user',
            uploaded_at=datetime(2024, 1, 15, 10, 30, 0)
        )
        db.session.add(doc)
        db.session.commit()

        result = DocumentService.serialize_document(doc)

        assert result['id'] == doc.id
        assert result['filename'] == 'serialize.pdf'
        assert result['title'] == 'Serialization Test'
        assert result['file_size_bytes'] == 2048
        assert result['file_size_mb'] == 0.0  # 2048 bytes = ~0.002 MB rounded
        assert result['status'] == 'indexed'
        assert result['collection_name'] == 'Test Collection'
        assert result['uploaded_by'] == 'test_user'

    def test_DOC_081_serialize_document_with_details(self, app, db, app_context):
        """
        [DOC-081] Dokument-Serialisierung mit Details

        include_details=True soll zusätzliche Felder enthalten.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='details.pdf', original_filename='original_details.pdf',
            file_path='/tmp/details.pdf', file_size_bytes=1024,
            mime_type='application/pdf', file_hash='hash_details',
            keywords='test, details, serialization',
            is_public=True,
            source_url='https://example.com/doc.pdf',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.commit()

        result = DocumentService.serialize_document(doc, include_details=True)

        assert 'original_filename' in result
        assert result['original_filename'] == 'original_details.pdf'
        assert 'file_path' in result
        assert 'file_hash' in result
        assert 'keywords' in result
        assert result['keywords'] == 'test, details, serialization'
        assert 'is_public' in result
        assert result['is_public'] is True
        assert 'source_url' in result
        assert result['source_url'] == 'https://example.com/doc.pdf'

    def test_DOC_082_serialize_document_no_collection(self, app, db, app_context):
        """
        [DOC-082] Dokument ohne Collection serialisieren

        Dokument ohne Collection soll collection_name=None haben.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument

        doc = RAGDocument(
            filename='orphan.pdf', original_filename='orphan.pdf',
            file_path='/tmp/orphan.pdf', file_size_bytes=512,
            mime_type='application/pdf', file_hash='hash_orphan',
            collection_id=None, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.commit()

        result = DocumentService.serialize_document(doc)

        assert result['collection_id'] is None
        assert result['collection_name'] is None

    def test_DOC_083_serialize_chunk(self, app, db, app_context):
        """
        [DOC-083] Chunk-Serialisierung

        Chunk soll korrekt serialisiert werden.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGDocumentChunk, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='chunk_test.pdf', original_filename='chunk_test.pdf',
            file_path='/tmp/chunk_test.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_chunk_test',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.flush()

        chunk = RAGDocumentChunk(
            document_id=doc.id,
            chunk_index=0,
            content='This is the chunk content.',
            page_number=1,
            start_char=0,
            end_char=26,
            retrieval_count=5
        )
        db.session.add(chunk)
        db.session.commit()

        result = DocumentService.serialize_chunk(chunk)

        assert result['id'] == chunk.id
        assert result['chunk_index'] == 0
        assert result['content'] == 'This is the chunk content.'
        assert result['page_number'] == 1
        assert result['start_char'] == 0
        assert result['end_char'] == 26
        assert result['retrieval_count'] == 5

    def test_DOC_084_serialize_chunk_with_image(self, app, db, app_context):
        """
        [DOC-084] Chunk mit Bild serialisieren

        Chunk mit eingebettetem Bild soll Bild-Infos enthalten.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGDocumentChunk, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='image_chunk.pdf', original_filename='image_chunk.pdf',
            file_path='/tmp/image_chunk.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_image_chunk',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.flush()

        chunk = RAGDocumentChunk(
            document_id=doc.id,
            chunk_index=0,
            content='Chunk with image',
            has_image=True,
            image_path='/app/data/rag/images/img1.png',
            image_url='https://example.com/img1.png',
            image_alt_text='Test image',
            image_mime_type='image/png'
        )
        db.session.add(chunk)
        db.session.commit()

        result = DocumentService.serialize_chunk(chunk)

        assert result['has_image'] is True
        assert result['image_path'] == '/app/data/rag/images/img1.png'
        assert result['image_url'] == 'https://example.com/img1.png'
        assert result['image_alt_text'] == 'Test image'
        assert result['image_mime_type'] == 'image/png'


class TestAccessControl:
    """
    Access Control Tests

    Tests for document access control integration.
    """

    def test_DOC_090_get_document_with_access_check(self, app, db, app_context):
        """
        [DOC-090] Dokument mit Zugriffskontrolle abrufen

        Zugriffskontrolle soll bei username-Parameter angewendet werden.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='owner')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='access.pdf', original_filename='access.pdf',
            file_path='/tmp/access.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_access',
            collection_id=collection.id, uploaded_by='owner'
        )
        db.session.add(doc)
        db.session.commit()

        # Mock access service to deny access
        with patch('services.rag.access_service.RAGAccessService') as MockAccess:
            MockAccess.can_view_document.return_value = False

            result = DocumentService.get_document_by_id(
                doc.id,
                username='unauthorized_user',
                access='view'
            )

            assert result is None

    def test_DOC_091_get_document_owner_access(self, app, db, app_context):
        """
        [DOC-091] Dokument-Besitzer hat Zugriff

        Besitzer soll immer Zugriff haben.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='owner')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='owner_access.pdf', original_filename='owner_access.pdf',
            file_path='/tmp/owner_access.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_owner_access',
            collection_id=collection.id, uploaded_by='owner'
        )
        db.session.add(doc)
        db.session.commit()

        # Mock access service to grant access
        with patch('services.rag.access_service.RAGAccessService') as MockAccess:
            MockAccess.can_view_document.return_value = True

            result = DocumentService.get_document_by_id(
                doc.id,
                username='owner',
                access='view'
            )

            assert result is not None
            assert result.uploaded_by == 'owner'

    def test_DOC_092_update_document_forbidden(self, app, db, app_context):
        """
        [DOC-092] Dokument-Update ohne Berechtigung

        Update ohne Berechtigung soll Forbidden zurückgeben.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='owner')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='forbidden_update.pdf', original_filename='forbidden_update.pdf',
            file_path='/tmp/forbidden_update.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_forbidden_update',
            collection_id=collection.id, uploaded_by='owner'
        )
        db.session.add(doc)
        db.session.commit()

        with patch('services.rag.access_service.RAGAccessService') as MockAccess:
            MockAccess.can_edit_document.return_value = False

            success, error, _ = DocumentService.update_document(
                document_id=doc.id,
                data={'title': 'Hacked Title'},
                username='hacker'
            )

            assert success is False
            assert error == 'Forbidden'

    def test_DOC_093_delete_document_forbidden(self, app, db, app_context):
        """
        [DOC-093] Dokument-Delete ohne Berechtigung

        Delete ohne Berechtigung soll Forbidden zurückgeben.
        """
        from services.rag.document_service import DocumentService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='owner')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='forbidden_delete.pdf', original_filename='forbidden_delete.pdf',
            file_path='/tmp/forbidden_delete.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_forbidden_delete',
            collection_id=collection.id, uploaded_by='owner'
        )
        db.session.add(doc)
        db.session.commit()

        with patch('services.rag.access_service.RAGAccessService') as MockAccess:
            MockAccess.can_delete_document.return_value = False

            success, error = DocumentService.delete_document(
                document_id=doc.id,
                username='hacker'
            )

            assert success is False
            assert error == 'Forbidden'
