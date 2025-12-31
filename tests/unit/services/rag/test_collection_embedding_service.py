"""
Unit Tests: Collection Embedding Service
========================================

Tests for the RAG collection embedding orchestration service.

Test IDs:
- CEMB-001 to CEMB-015: Helper Function Tests
- CEMB-020 to CEMB-035: Service Method Tests
- CEMB-040 to CEMB-055: Status Management Tests
- CEMB-060 to CEMB-070: Edge Cases and Error Handling

Status: Implemented
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime
import hashlib
import threading
import time


class TestHelperFunctions:
    """
    Helper Function Tests

    Tests for utility functions.
    """

    def test_CEMB_001_sanitize_chroma_metadata_basic(self, app, app_context):
        """
        [CEMB-001] Sanitize Metadata Basis

        Primitive Werte sollen durchgelassen werden.
        """
        from services.rag.collection_embedding_service import sanitize_chroma_metadata

        metadata = {
            'string_val': 'test',
            'int_val': 42,
            'float_val': 3.14,
            'bool_val': True
        }

        result = sanitize_chroma_metadata(metadata)

        assert result['string_val'] == 'test'
        assert result['int_val'] == 42
        assert result['float_val'] == 3.14
        assert result['bool_val'] is True

    def test_CEMB_002_sanitize_chroma_metadata_none_removed(self, app, app_context):
        """
        [CEMB-002] Sanitize Metadata None entfernen

        None-Werte sollen entfernt werden.
        """
        from services.rag.collection_embedding_service import sanitize_chroma_metadata

        metadata = {
            'valid': 'value',
            'none_val': None,
            'also_valid': 123
        }

        result = sanitize_chroma_metadata(metadata)

        assert 'valid' in result
        assert 'none_val' not in result
        assert 'also_valid' in result

    def test_CEMB_003_sanitize_chroma_metadata_complex_to_string(self, app, app_context):
        """
        [CEMB-003] Sanitize Metadata komplexe Typen zu String

        Komplexe Typen sollen zu String konvertiert werden.
        """
        from services.rag.collection_embedding_service import sanitize_chroma_metadata

        metadata = {
            'list_val': [1, 2, 3],
            'dict_val': {'nested': 'dict'},
            'datetime_val': datetime(2024, 1, 15)
        }

        result = sanitize_chroma_metadata(metadata)

        assert result['list_val'] == '[1, 2, 3]'
        assert 'nested' in result['dict_val']
        assert '2024' in result['datetime_val']

    def test_CEMB_004_sanitize_chroma_metadata_empty(self, app, app_context):
        """
        [CEMB-004] Sanitize Metadata leer

        Leere oder None Eingabe soll leeres Dict zurückgeben.
        """
        from services.rag.collection_embedding_service import sanitize_chroma_metadata

        assert sanitize_chroma_metadata(None) == {}
        assert sanitize_chroma_metadata({}) == {}

    def test_CEMB_005_sanitize_collection_name_basic(self, app, app_context):
        """
        [CEMB-005] Sanitize Collection Name Basis

        Einfacher Name soll korrekt formatiert werden.
        """
        from services.rag.collection_embedding_service import sanitize_chroma_collection_name

        result = sanitize_chroma_collection_name('my_collection', 'model/name')

        assert result.startswith('llars_')
        assert 'my_collection' in result
        assert '/' not in result  # Slashes should be replaced

    def test_CEMB_006_sanitize_collection_name_special_chars(self, app, app_context):
        """
        [CEMB-006] Sanitize Collection Name Sonderzeichen

        Sonderzeichen sollen durch Unterstriche ersetzt werden.
        """
        from services.rag.collection_embedding_service import sanitize_chroma_collection_name

        result = sanitize_chroma_collection_name('test@collection!', 'model#name')

        assert '@' not in result
        assert '!' not in result
        assert '#' not in result
        # Should only contain alphanumeric, underscore, hyphen
        import re
        assert re.match(r'^[a-zA-Z0-9_-]+$', result)

    def test_CEMB_007_sanitize_collection_name_length_limit(self, app, app_context):
        """
        [CEMB-007] Sanitize Collection Name Längenlimit

        Lange Namen sollen auf 63 Zeichen gekürzt werden.
        """
        from services.rag.collection_embedding_service import sanitize_chroma_collection_name

        long_name = 'a' * 100
        long_model = 'b' * 100

        result = sanitize_chroma_collection_name(long_name, long_model)

        assert len(result) <= 63

    def test_CEMB_008_sanitize_collection_name_min_length(self, app, app_context):
        """
        [CEMB-008] Sanitize Collection Name Mindestlänge

        Kurze Namen sollen mindestens 3 Zeichen haben.
        """
        from services.rag.collection_embedding_service import sanitize_chroma_collection_name

        result = sanitize_chroma_collection_name('a', 'b')

        assert len(result) >= 3

    def test_CEMB_009_sanitize_collection_name_no_leading_trailing(self, app, app_context):
        """
        [CEMB-009] Sanitize Collection Name ohne führende/trailing Zeichen

        Name soll nicht mit _ oder - beginnen/enden.
        """
        from services.rag.collection_embedding_service import sanitize_chroma_collection_name

        result = sanitize_chroma_collection_name('_test_', '-model-')

        assert not result.startswith('_')
        assert not result.startswith('-')
        assert not result.endswith('_')
        assert not result.endswith('-')

    def test_CEMB_010_retry_on_deadlock_success(self, app, app_context):
        """
        [CEMB-010] Retry Decorator erfolgreich

        Funktion ohne Deadlock soll normal ausgeführt werden.
        """
        from services.rag.collection_embedding_service import retry_on_deadlock

        call_count = 0

        @retry_on_deadlock(max_retries=3)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return 'success'

        result = successful_func()

        assert result == 'success'
        assert call_count == 1

    def test_CEMB_011_retry_on_deadlock_retry(self, app, db, app_context):
        """
        [CEMB-011] Retry Decorator mit Retry

        Bei Deadlock soll retry versucht werden.
        """
        from services.rag.collection_embedding_service import retry_on_deadlock
        from sqlalchemy.exc import OperationalError

        call_count = 0

        @retry_on_deadlock(max_retries=3, delay=0.01)
        def deadlock_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OperationalError('statement', {}, Exception('Deadlock found'))
            return 'success'

        result = deadlock_then_success()

        assert result == 'success'
        assert call_count == 3

    def test_CEMB_012_retry_on_deadlock_max_retries(self, app, db, app_context):
        """
        [CEMB-012] Retry Decorator Max Retries erreicht

        Nach max_retries soll Exception geworfen werden.
        """
        from services.rag.collection_embedding_service import retry_on_deadlock
        from sqlalchemy.exc import OperationalError

        @retry_on_deadlock(max_retries=2, delay=0.01)
        def always_deadlock():
            raise OperationalError('statement', {}, Exception('Deadlock found'))

        with pytest.raises(OperationalError):
            always_deadlock()


class TestServiceMethods:
    """
    Service Method Tests

    Tests for CollectionEmbeddingService methods.
    """

    def test_CEMB_020_start_embedding_collection_not_found(self, app, db, app_context):
        """
        [CEMB-020] Start Embedding Collection nicht gefunden

        Nicht existierende Collection soll Fehler zurückgeben.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService

        service = CollectionEmbeddingService(app)
        result = service.start_embedding(99999)

        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_CEMB_021_start_embedding_already_processing(self, app, db, app_context):
        """
        [CEMB-021] Start Embedding bereits in Bearbeitung

        Collection in Bearbeitung soll Nachricht zurückgeben.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService
        from db.tables import RAGCollection

        collection = RAGCollection(
            name='processing_test',
            display_name='Processing Test',
            created_by='test',
            embedding_status='processing'
        )
        db.session.add(collection)
        db.session.commit()

        service = CollectionEmbeddingService(app)
        # Simulate active job
        service._active_jobs[collection.id] = MagicMock()

        result = service.start_embedding(collection.id)

        assert result['success'] is True
        assert 'already processing' in result['message'].lower()

    def test_CEMB_022_pause_embedding_success(self, app, db, app_context):
        """
        [CEMB-022] Pause Embedding erfolgreich

        Laufende Embedding soll pausiert werden können.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService
        from db.tables import RAGCollection

        collection = RAGCollection(
            name='pause_test',
            display_name='Pause Test',
            created_by='test',
            embedding_status='processing'
        )
        db.session.add(collection)
        db.session.commit()

        service = CollectionEmbeddingService(app)
        service._stop_events[collection.id] = threading.Event()

        result = service.pause_embedding(collection.id)

        assert result['success'] is True
        assert service._stop_events[collection.id].is_set()

    def test_CEMB_023_pause_embedding_not_processing(self, app, db, app_context):
        """
        [CEMB-023] Pause Embedding nicht in Bearbeitung

        Nicht laufende Embedding soll Fehler zurückgeben.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService
        from db.tables import RAGCollection

        collection = RAGCollection(
            name='idle_test',
            display_name='Idle Test',
            created_by='test',
            embedding_status='idle'
        )
        db.session.add(collection)
        db.session.commit()

        service = CollectionEmbeddingService(app)
        result = service.pause_embedding(collection.id)

        assert result['success'] is False

    def test_CEMB_024_get_status_not_found(self, app, db, app_context):
        """
        [CEMB-024] Get Status Collection nicht gefunden

        Nicht existierende Collection soll Fehler zurückgeben.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService

        service = CollectionEmbeddingService(app)
        result = service.get_status(99999)

        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_CEMB_025_get_status_success(self, app, db, app_context):
        """
        [CEMB-025] Get Status erfolgreich

        Status soll korrekte Informationen zurückgeben.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService
        from db.tables import RAGCollection

        collection = RAGCollection(
            name='status_test',
            display_name='Status Test',
            created_by='test',
            embedding_status='completed',
            embedding_progress=100,
            total_chunks=50
        )
        db.session.add(collection)
        db.session.commit()

        service = CollectionEmbeddingService(app)
        result = service.get_status(collection.id)

        assert result['success'] is True
        assert result['status'] == 'completed'
        assert result['progress'] == 100
        assert result['total_chunks'] == 50
        assert result['name'] == 'status_test'

    def test_CEMB_026_hash_content(self, app, app_context):
        """
        [CEMB-026] Hash Content

        Content Hash soll SHA-256 sein.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService

        service = CollectionEmbeddingService(app)
        content = "Test content for hashing"

        result = service._hash_content(content)
        expected = hashlib.sha256(content.encode('utf-8')).hexdigest()

        assert result == expected
        assert len(result) == 64

    def test_CEMB_027_hash_content_unicode(self, app, app_context):
        """
        [CEMB-027] Hash Content Unicode

        Unicode Content soll korrekt gehasht werden.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService

        service = CollectionEmbeddingService(app)
        content = "Größe Übung 日本語 🎉"

        result = service._hash_content(content)

        assert len(result) == 64
        # Same content should produce same hash
        assert result == service._hash_content(content)


class TestStatusManagement:
    """
    Status Management Tests

    Tests for document and collection status updates.
    """

    def test_CEMB_040_update_document_status_indexed(self, app, db, app_context):
        """
        [CEMB-040] Document Status auf indexed setzen

        Status 'indexed' soll timestamps setzen.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='status.pdf', original_filename='status.pdf',
            file_path='/tmp/status.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_status',
            status='processing',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.commit()

        service = CollectionEmbeddingService(app)
        service._update_document_status(doc.id, 'indexed', chunk_count=10)

        # Reload document
        updated_doc = RAGDocument.query.get(doc.id)
        assert updated_doc.status == 'indexed'
        assert updated_doc.processed_at is not None
        assert updated_doc.indexed_at is not None

    def test_CEMB_041_update_document_status_failed(self, app, db, app_context):
        """
        [CEMB-041] Document Status auf failed setzen

        Status 'failed' soll Error speichern.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService
        from db.tables import RAGDocument, RAGCollection

        collection = RAGCollection(name='test', display_name='Test', created_by='test')
        db.session.add(collection)
        db.session.flush()

        doc = RAGDocument(
            filename='fail.pdf', original_filename='fail.pdf',
            file_path='/tmp/fail.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_fail',
            status='processing',
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.commit()

        service = CollectionEmbeddingService(app)
        service._update_document_status(doc.id, 'failed', 'Test error message')

        updated_doc = RAGDocument.query.get(doc.id)
        assert updated_doc.status == 'failed'
        assert updated_doc.processing_error == 'Test error message'

    def test_CEMB_042_update_document_status_not_found(self, app, db, app_context):
        """
        [CEMB-042] Document Status nicht gefunden

        Nicht existierendes Document soll keine Exception werfen.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService

        service = CollectionEmbeddingService(app)
        # Should not raise
        service._update_document_status(99999, 'indexed')

    def test_CEMB_043_complete_collection(self, app, db, app_context):
        """
        [CEMB-043] Collection als completed markieren

        _complete_collection soll Status und Progress setzen.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService
        from db.tables import RAGCollection

        collection = RAGCollection(
            name='complete_test',
            display_name='Complete Test',
            created_by='test',
            embedding_status='processing',
            embedding_progress=50
        )
        db.session.add(collection)
        db.session.commit()

        service = CollectionEmbeddingService(app)

        # The emit is in a try/except, so it will fail silently in tests
        service._complete_collection(collection.id, 100, 10)

        updated = RAGCollection.query.get(collection.id)
        assert updated.embedding_status == 'completed'
        assert updated.embedding_progress == 100
        assert updated.total_chunks == 100
        assert updated.last_indexed_at is not None

    def test_CEMB_044_set_collection_error(self, app, db, app_context):
        """
        [CEMB-044] Collection Error setzen

        _set_collection_error soll Status und Error speichern.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService
        from db.tables import RAGCollection

        collection = RAGCollection(
            name='error_test',
            display_name='Error Test',
            created_by='test',
            embedding_status='processing'
        )
        db.session.add(collection)
        db.session.commit()

        service = CollectionEmbeddingService(app)

        # The emit is in a try/except, so it will fail silently in tests
        service._set_collection_error(collection.id, 'Test error')

        updated = RAGCollection.query.get(collection.id)
        assert updated.embedding_status == 'failed'
        assert updated.embedding_error == 'Test error'

    def test_CEMB_045_set_collection_error_truncation(self, app, db, app_context):
        """
        [CEMB-045] Collection Error Kürzung

        Lange Errors sollen auf 1000 Zeichen gekürzt werden.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService
        from db.tables import RAGCollection

        collection = RAGCollection(
            name='truncate_test',
            display_name='Truncate Test',
            created_by='test',
            embedding_status='processing'
        )
        db.session.add(collection)
        db.session.commit()

        service = CollectionEmbeddingService(app)
        long_error = 'x' * 2000

        # The emit is in a try/except, so it will fail silently in tests
        service._set_collection_error(collection.id, long_error)

        updated = RAGCollection.query.get(collection.id)
        assert len(updated.embedding_error) <= 1000


class TestCollectionEmbeddingRecord:
    """
    CollectionEmbedding Record Tests

    Tests for CollectionEmbedding database records.
    """

    def test_CEMB_050_complete_updates_embedding_record(self, app, db, app_context):
        """
        [CEMB-050] Complete aktualisiert CollectionEmbedding Record

        CollectionEmbedding Record soll auf completed gesetzt werden.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService
        from db.tables import RAGCollection
        from db.models.rag import CollectionEmbedding

        collection = RAGCollection(
            name='record_test',
            display_name='Record Test',
            created_by='test',
            embedding_status='processing'
        )
        db.session.add(collection)
        db.session.flush()

        # Create CollectionEmbedding record
        coll_embedding = CollectionEmbedding(
            collection_id=collection.id,
            model_id='test/model',
            model_source='local',
            embedding_dimensions=384,
            chroma_collection_name='llars_record_test',
            status='processing',
            progress=50
        )
        db.session.add(coll_embedding)
        db.session.commit()

        service = CollectionEmbeddingService(app)

        # The emit is in a try/except, so it will fail silently in tests
        service._complete_collection(collection.id, 100, 10)

        updated_record = CollectionEmbedding.query.filter_by(
            collection_id=collection.id
        ).first()
        assert updated_record.status == 'completed'
        assert updated_record.progress == 100
        assert updated_record.chunk_count == 100
        assert updated_record.completed_at is not None

    def test_CEMB_051_error_updates_embedding_record(self, app, db, app_context):
        """
        [CEMB-051] Error aktualisiert CollectionEmbedding Record

        CollectionEmbedding Record soll auf failed gesetzt werden.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService
        from db.tables import RAGCollection
        from db.models.rag import CollectionEmbedding

        collection = RAGCollection(
            name='error_record_test',
            display_name='Error Record Test',
            created_by='test',
            embedding_status='processing'
        )
        db.session.add(collection)
        db.session.flush()

        coll_embedding = CollectionEmbedding(
            collection_id=collection.id,
            model_id='test/model',
            model_source='local',
            embedding_dimensions=384,
            chroma_collection_name='llars_error_record_test',
            status='processing'
        )
        db.session.add(coll_embedding)
        db.session.commit()

        service = CollectionEmbeddingService(app)

        # The emit is in a try/except, so it will fail silently in tests
        service._set_collection_error(collection.id, 'Test error')

        updated_record = CollectionEmbedding.query.filter_by(
            collection_id=collection.id
        ).first()
        assert updated_record.status == 'failed'
        assert updated_record.error_message == 'Test error'


class TestGlobalService:
    """
    Global Service Tests

    Tests for the global service instance.
    """

    def test_CEMB_060_get_collection_embedding_service(self, app, app_context):
        """
        [CEMB-060] Global Service abrufen

        get_collection_embedding_service soll Service zurückgeben.
        """
        import services.rag.collection_embedding_service as module

        # Reset global instance
        module._embedding_service = None

        service = module.get_collection_embedding_service()

        assert service is not None
        assert isinstance(service, module.CollectionEmbeddingService)

    def test_CEMB_061_get_collection_embedding_service_singleton(self, app, app_context):
        """
        [CEMB-061] Global Service Singleton

        Mehrfache Aufrufe sollen gleiche Instanz zurückgeben.
        """
        import services.rag.collection_embedding_service as module

        # Reset global instance
        module._embedding_service = None

        service1 = module.get_collection_embedding_service()
        service2 = module.get_collection_embedding_service()

        assert service1 is service2


class TestEdgeCases:
    """
    Edge Case Tests

    Tests for unusual inputs and edge cases.
    """

    def test_CEMB_070_sanitize_collection_name_consecutive_underscores(self, app, app_context):
        """
        [CEMB-070] Sanitize Collection Name konsekutive Unterstriche

        Mehrfache Unterstriche sollen zu einem reduziert werden.
        """
        from services.rag.collection_embedding_service import sanitize_chroma_collection_name

        result = sanitize_chroma_collection_name('test___name', 'model___name')

        assert '___' not in result
        assert '__' not in result

    def test_CEMB_071_sanitize_metadata_all_none(self, app, app_context):
        """
        [CEMB-071] Sanitize Metadata alle Werte None

        Alle None-Werte sollen leeres Dict ergeben.
        """
        from services.rag.collection_embedding_service import sanitize_chroma_metadata

        metadata = {
            'key1': None,
            'key2': None,
            'key3': None
        }

        result = sanitize_chroma_metadata(metadata)
        assert result == {}

    def test_CEMB_072_get_status_with_documents(self, app, db, app_context):
        """
        [CEMB-072] Get Status mit Dokumenten

        Status soll Dokumentzählung enthalten.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService
        from db.tables import RAGCollection, RAGDocument, CollectionDocumentLink

        collection = RAGCollection(
            name='docs_test',
            display_name='Docs Test',
            created_by='test',
            embedding_status='completed'
        )
        db.session.add(collection)
        db.session.flush()

        # Add documents
        for i in range(3):
            doc = RAGDocument(
                filename=f'doc{i}.pdf', original_filename=f'doc{i}.pdf',
                file_path=f'/tmp/doc{i}.pdf', file_size_bytes=100,
                mime_type='application/pdf', file_hash=f'hash_doc{i}',
                status='indexed' if i < 2 else 'pending',
                collection_id=collection.id, uploaded_by='test'
            )
            db.session.add(doc)
            db.session.flush()

            link = CollectionDocumentLink(
                collection_id=collection.id,
                document_id=doc.id
            )
            db.session.add(link)

        db.session.commit()

        service = CollectionEmbeddingService(app)
        result = service.get_status(collection.id)

        assert result['success'] is True
        assert result['documents_total'] == 3
        assert result['documents_indexed'] == 2

    def test_CEMB_073_start_embedding_recovers_stuck_docs(self, app, db, app_context):
        """
        [CEMB-073] Start Embedding recovered stuck Documents

        Documents im Status 'processing' sollen zurückgesetzt werden.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService
        from db.tables import RAGCollection, RAGDocument, CollectionDocumentLink

        collection = RAGCollection(
            name='stuck_test',
            display_name='Stuck Test',
            created_by='test',
            embedding_status='idle'
        )
        db.session.add(collection)
        db.session.flush()

        # Add stuck document
        doc = RAGDocument(
            filename='stuck.pdf', original_filename='stuck.pdf',
            file_path='/tmp/stuck.pdf', file_size_bytes=100,
            mime_type='application/pdf', file_hash='hash_stuck',
            status='processing',  # Stuck in processing
            collection_id=collection.id, uploaded_by='test'
        )
        db.session.add(doc)
        db.session.flush()

        link = CollectionDocumentLink(
            collection_id=collection.id,
            document_id=doc.id
        )
        db.session.add(link)
        db.session.commit()

        service = CollectionEmbeddingService(app)

        # Mock the background thread to prevent actual processing
        with patch.object(service, '_process_collection'):
            with patch('flask.current_app._get_current_object', return_value=app):
                result = service.start_embedding(collection.id)

        # Document should be reset to pending
        updated_doc = RAGDocument.query.get(doc.id)
        assert updated_doc.status == 'pending'

    def test_CEMB_074_hash_content_empty(self, app, app_context):
        """
        [CEMB-074] Hash Content leer

        Leerer Content soll validen Hash produzieren.
        """
        from services.rag.collection_embedding_service import CollectionEmbeddingService

        service = CollectionEmbeddingService(app)
        result = service._hash_content('')

        assert len(result) == 64
        # Empty string hash
        expected = hashlib.sha256(b'').hexdigest()
        assert result == expected
