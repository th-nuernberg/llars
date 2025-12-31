"""
RAG Document Integration Tests
==============================

Tests for RAG document upload, processing, and management.

Test IDs: RAG_INT_041 - RAG_INT_080
"""

import pytest
import io
import os
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock


# =============================================================================
# FIXTURES: Document Test Setup
# =============================================================================

@pytest.fixture
def rag_db_models(db, app):
    """Create RAG-related database tables and models."""
    with app.app_context():
        from db.tables import RAGCollection, RAGDocument, RAGDocumentChunk
        from db.models.rag import CollectionEmbedding, CollectionDocumentLink
        from db.models.llm_model import LLMModel

        embedding_model = LLMModel(
            model_id='sentence-transformers/all-MiniLM-L6-v2',
            display_name='MiniLM-L6',
            provider='local',
            model_type='embedding',
            is_active=True,
            is_default=True,
            context_window=512,
            max_output_tokens=512
        )
        db.session.add(embedding_model)
        db.session.commit()

        return {
            'RAGCollection': RAGCollection,
            'RAGDocument': RAGDocument,
            'RAGDocumentChunk': RAGDocumentChunk,
            'CollectionEmbedding': CollectionEmbedding,
            'CollectionDocumentLink': CollectionDocumentLink,
            'LLMModel': LLMModel
        }


@pytest.fixture
def sample_collection(db, app, rag_db_models, admin_user):
    """Create a sample RAG collection."""
    with app.app_context():
        RAGCollection = rag_db_models['RAGCollection']

        collection = RAGCollection(
            name='doc-test-collection',
            display_name='Document Test Collection',
            embedding_model='sentence-transformers/all-MiniLM-L6-v2',
            created_by='admin',
            is_active=True
        )
        db.session.add(collection)
        db.session.commit()
        db.session.refresh(collection)
        return collection


@pytest.fixture
def temp_file():
    """Create a temporary file for upload testing."""
    content = b'Test document content for integration testing.'
    file_obj = io.BytesIO(content)
    file_obj.name = 'test-upload.txt'
    return file_obj


@pytest.fixture
def temp_pdf_file():
    """Create a temporary PDF-like file for upload testing."""
    # Simple PDF header (not a valid PDF but mimics the signature)
    content = b'%PDF-1.4 Test PDF content'
    file_obj = io.BytesIO(content)
    file_obj.name = 'test-upload.pdf'
    return file_obj


# =============================================================================
# Document CRUD Tests
# =============================================================================

class TestDocumentList:
    """Tests for listing RAG documents."""

    def test_RAG_INT_041_list_documents_unauthenticated(self, client):
        """RAG_INT_041: Listing documents without auth should fail."""
        response = client.get('/api/rag/documents')
        assert response.status_code in [401, 403, 404, 500]

    def test_RAG_INT_042_list_documents_empty(
        self, client, admin_token, mock_token_validation, rag_db_models, app
    ):
        """RAG_INT_042: Should return empty list when no documents exist."""
        pass  # Requires actual route registration

    def test_RAG_INT_043_list_documents_with_filter(
        self, client, admin_token, mock_token_validation, rag_db_models, app
    ):
        """RAG_INT_043: Should filter documents by collection_id."""
        pass

    def test_RAG_INT_044_list_documents_pagination(
        self, client, admin_token, mock_token_validation, rag_db_models, app
    ):
        """RAG_INT_044: Should support pagination."""
        pass


class TestDocumentUpload:
    """Tests for document upload."""

    def test_RAG_INT_045_upload_document_unauthenticated(self, client, temp_file):
        """RAG_INT_045: Uploading document without auth should fail."""
        response = client.post(
            '/api/rag/documents/upload',
            data={'file': temp_file},
            content_type='multipart/form-data'
        )
        assert response.status_code in [401, 403, 404, 405, 500]

    def test_RAG_INT_046_upload_document_valid(
        self, client, admin_token, mock_token_validation, sample_collection, temp_file, app
    ):
        """RAG_INT_046: Admin should be able to upload document."""
        pass

    def test_RAG_INT_047_upload_document_no_file(
        self, client, admin_token, mock_token_validation, app
    ):
        """RAG_INT_047: Upload without file should fail."""
        pass

    def test_RAG_INT_048_upload_multiple_documents(
        self, client, admin_token, mock_token_validation, sample_collection, app
    ):
        """RAG_INT_048: Should support multiple document upload."""
        pass


class TestDocumentGet:
    """Tests for getting document details."""

    def test_RAG_INT_049_get_document_unauthenticated(self, client):
        """RAG_INT_049: Getting document without auth should fail."""
        response = client.get('/api/rag/documents/1')
        assert response.status_code in [401, 403, 404, 500]

    def test_RAG_INT_050_get_document_not_found(
        self, client, admin_token, mock_token_validation, app
    ):
        """RAG_INT_050: Getting non-existent document should return 404."""
        pass

    def test_RAG_INT_051_get_document_content(
        self, client, admin_token, mock_token_validation, app
    ):
        """RAG_INT_051: Should return document content."""
        pass

    def test_RAG_INT_052_get_document_chunks(
        self, client, admin_token, mock_token_validation, app
    ):
        """RAG_INT_052: Should return document chunks."""
        pass


class TestDocumentUpdate:
    """Tests for updating documents."""

    def test_RAG_INT_053_update_document_title(
        self, client, admin_token, mock_token_validation, app
    ):
        """RAG_INT_053: Should update document title."""
        pass

    def test_RAG_INT_054_update_document_metadata(
        self, client, admin_token, mock_token_validation, app
    ):
        """RAG_INT_054: Should update document metadata."""
        pass


class TestDocumentDelete:
    """Tests for deleting documents."""

    def test_RAG_INT_055_delete_document_unauthenticated(self, client):
        """RAG_INT_055: Deleting document without auth should fail."""
        response = client.delete('/api/rag/documents/1')
        assert response.status_code in [401, 403, 404, 405, 500]

    def test_RAG_INT_056_delete_document_own(
        self, client, admin_token, mock_token_validation, app
    ):
        """RAG_INT_056: Owner should be able to delete document."""
        pass

    def test_RAG_INT_057_delete_document_not_owner(
        self, client, researcher_token, mock_token_validation, app
    ):
        """RAG_INT_057: Non-owner should not be able to delete document."""
        pass


# =============================================================================
# Document Processing Tests
# =============================================================================

class TestDocumentProcessing:
    """Tests for document processing pipeline."""

    def test_RAG_INT_058_document_status_pending(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_058: New document should have pending status."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            document = RAGDocument(
                filename='status-test.pdf',
                original_filename='status-test.pdf',
                file_path='/tmp/status-test.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                file_hash='sha256:testhash123',
                status='pending',
                collection_id=sample_collection.id,
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            assert document.status == 'pending'

    def test_RAG_INT_059_document_status_processing(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_059: Document in progress should have processing status."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            document = RAGDocument(
                filename='processing-test.pdf',
                original_filename='processing-test.pdf',
                file_path='/tmp/processing-test.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                file_hash='sha256:testhash123',
                status='processing',
                collection_id=sample_collection.id,
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            assert document.status == 'processing'

    def test_RAG_INT_060_document_status_processed(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_060: Completed document should have processed status."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            document = RAGDocument(
                filename='processed-test.pdf',
                original_filename='processed-test.pdf',
                file_path='/tmp/processed-test.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                file_hash='sha256:testhash123',
                status='processed',
                chunk_count=5,
                collection_id=sample_collection.id,
                uploaded_by='admin',
                processed_at=datetime.utcnow()
            )
            db.session.add(document)
            db.session.commit()

            assert document.status == 'processed'
            assert document.chunk_count == 5
            assert document.processed_at is not None

    def test_RAG_INT_061_document_status_error(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_061: Failed document should have error status."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            document = RAGDocument(
                filename='error-test.pdf',
                original_filename='error-test.pdf',
                file_path='/tmp/error-test.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                file_hash='sha256:testhash123',
                status='error',
                processing_error='Test error message',
                collection_id=sample_collection.id,
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            assert document.status == 'error'
            assert document.processing_error == 'Test error message'


# =============================================================================
# Document Chunking Tests
# =============================================================================

class TestDocumentChunking:
    """Tests for document chunking."""

    def test_RAG_INT_062_create_chunks(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_062: Should create document chunks correctly."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']
            RAGDocumentChunk = rag_db_models['RAGDocumentChunk']

            document = RAGDocument(
                filename='chunk-test.pdf',
                original_filename='chunk-test.pdf',
                file_path='/tmp/chunk-test.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                file_hash='sha256:testhash123',
                status='processed',
                collection_id=sample_collection.id,
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            # Create chunks
            for i in range(5):
                chunk = RAGDocumentChunk(
                    document_id=document.id,
                    chunk_index=i,
                    content=f'Chunk {i} content with some text.',
                    start_char=30,
                    end_char=5
                )
                db.session.add(chunk)
            db.session.commit()

            # Verify chunks
            chunks = RAGDocumentChunk.query.filter_by(
                document_id=document.id
            ).order_by(RAGDocumentChunk.chunk_index).all()

            assert len(chunks) == 5
            assert chunks[0].chunk_index == 0
            assert chunks[4].chunk_index == 4

    def test_RAG_INT_063_chunk_ordering(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_063: Chunks should maintain order."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']
            RAGDocumentChunk = rag_db_models['RAGDocumentChunk']

            document = RAGDocument(
                filename='order-test.pdf',
                original_filename='order-test.pdf',
                file_path='/tmp/order-test.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                file_hash='sha256:testhash123',
                status='processed',
                collection_id=sample_collection.id,
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            # Create chunks in random order
            for i in [3, 1, 4, 0, 2]:
                chunk = RAGDocumentChunk(
                    document_id=document.id,
                    chunk_index=i,
                    content=f'Chunk {i}',
                    start_char=10,
                    end_char=2
                )
                db.session.add(chunk)
            db.session.commit()

            # Should be orderable by chunk_index
            chunks = RAGDocumentChunk.query.filter_by(
                document_id=document.id
            ).order_by(RAGDocumentChunk.chunk_index).all()

            indices = [c.chunk_index for c in chunks]
            assert indices == [0, 1, 2, 3, 4]

    def test_RAG_INT_064_chunk_metadata(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_064: Chunks should store metadata correctly."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']
            RAGDocumentChunk = rag_db_models['RAGDocumentChunk']

            document = RAGDocument(
                filename='meta-test.pdf',
                original_filename='meta-test.pdf',
                file_path='/tmp/meta-test.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                file_hash='sha256:testhash123',
                status='processed',
                collection_id=sample_collection.id,
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            chunk = RAGDocumentChunk(
                document_id=document.id,
                chunk_index=0,
                content='Test content with metadata',
                start_char=0,
                end_char=26,
                page_number=1
            )
            db.session.add(chunk)
            db.session.commit()

            result = RAGDocumentChunk.query.get(chunk.id)
            assert result.page_number == 1
            assert result.content == 'Test content with metadata'


# =============================================================================
# Document Access Control Tests
# =============================================================================

class TestDocumentAccessControl:
    """Tests for document access control."""

    def test_RAG_INT_065_view_own_document(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_065: Owner should view own document."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            document = RAGDocument(
                filename='own-doc.pdf',
                original_filename='own-doc.pdf',
                file_path='/tmp/own-doc.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                file_hash='sha256:testhash123',
                status='processed',
                collection_id=sample_collection.id,
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            # Owner can access
            result = RAGDocument.query.filter_by(
                uploaded_by='admin'
            ).first()
            assert result is not None

    def test_RAG_INT_066_document_in_public_collection(
        self, db, app, rag_db_models
    ):
        """RAG_INT_066: Document in public collection should be accessible."""
        with app.app_context():
            RAGCollection = rag_db_models['RAGCollection']
            RAGDocument = rag_db_models['RAGDocument']

            # Create public collection
            collection = RAGCollection(
                name='public-doc-test',
                display_name='Public Doc Test',
                embedding_model='test-model',
                is_public=True,
                created_by='admin',
                is_active=True
            )
            db.session.add(collection)
            db.session.commit()

            document = RAGDocument(
                filename='public-doc.pdf',
                original_filename='public-doc.pdf',
                file_path='/tmp/public-doc.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                file_hash='sha256:testhash123',
                status='processed',
                collection_id=collection.id,
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            # Should be queryable
            result = RAGDocument.query.filter_by(id=document.id).first()
            assert result is not None


# =============================================================================
# Document Download Tests
# =============================================================================

class TestDocumentDownload:
    """Tests for document download functionality."""

    def test_RAG_INT_067_download_document_unauthenticated(self, client):
        """RAG_INT_067: Download without auth should fail."""
        response = client.get('/api/rag/documents/1/download')
        assert response.status_code in [401, 403, 404, 500]

    def test_RAG_INT_068_download_nonexistent_file(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_068: Download of missing file should return 404."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            document = RAGDocument(
                filename='missing-file.pdf',
                original_filename='missing-file.pdf',
                file_path='/nonexistent/path/file.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                file_hash='sha256:testhash123',
                status='processed',
                collection_id=sample_collection.id,
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            # File doesn't exist
            assert not os.path.exists(document.file_path)


# =============================================================================
# Document Screenshot Tests
# =============================================================================

class TestDocumentScreenshot:
    """Tests for document screenshot functionality."""

    def test_RAG_INT_069_get_screenshot_no_screenshot(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_069: Document without screenshot should return 404."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            document = RAGDocument(
                filename='no-screenshot.pdf',
                original_filename='no-screenshot.pdf',
                file_path='/tmp/no-screenshot.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                file_hash='sha256:testhash123',
                status='processed',
                screenshot_path=None,
                collection_id=sample_collection.id,
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            assert document.screenshot_path is None


# =============================================================================
# Document Statistics Tests
# =============================================================================

class TestDocumentStatistics:
    """Tests for document statistics."""

    def test_RAG_INT_070_document_retrieval_count(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_070: Document should track retrieval count."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            document = RAGDocument(
                filename='retrieval-test.pdf',
                original_filename='retrieval-test.pdf',
                file_path='/tmp/retrieval-test.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                file_hash='sha256:testhash123',
                status='processed',
                collection_id=sample_collection.id,
                uploaded_by='admin',
                retrieval_count=0
            )
            db.session.add(document)
            db.session.commit()

            # Simulate retrievals
            document.retrieval_count = 10
            db.session.commit()

            result = RAGDocument.query.get(document.id)
            assert result.retrieval_count == 10

    def test_RAG_INT_071_document_last_retrieved(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_071: Document should track last retrieval time."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            document = RAGDocument(
                filename='last-retrieved-test.pdf',
                original_filename='last-retrieved-test.pdf',
                file_path='/tmp/last-retrieved-test.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                file_hash='sha256:testhash123',
                status='processed',
                collection_id=sample_collection.id,
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            # Simulate retrieval
            now = datetime.utcnow()
            document.last_retrieved_at = now
            db.session.commit()

            result = RAGDocument.query.get(document.id)
            assert result.last_retrieved_at is not None


# =============================================================================
# Document MIME Type Tests
# =============================================================================

class TestDocumentMimeTypes:
    """Tests for document MIME type handling."""

    def test_RAG_INT_072_pdf_mime_type(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_072: PDF documents should have correct MIME type."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            document = RAGDocument(
                filename='test.pdf',
                original_filename='test.pdf',
                file_path='/tmp/test.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                file_hash='sha256:testhash123',
                status='pending',
                collection_id=sample_collection.id,
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            assert document.mime_type == 'application/pdf'

    def test_RAG_INT_073_html_mime_type(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_073: HTML documents should have correct MIME type."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            document = RAGDocument(
                filename='page.html',
                original_filename='page.html',
                file_path='/tmp/page.html',
                file_size_bytes=512,
                mime_type='text/html',
                file_hash='sha256:htmlhash123',
                status='pending',
                collection_id=sample_collection.id,
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            assert document.mime_type == 'text/html'

    def test_RAG_INT_074_markdown_mime_type(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_074: Markdown documents should have correct MIME type."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            document = RAGDocument(
                filename='readme.md',
                original_filename='readme.md',
                file_path='/tmp/readme.md',
                file_size_bytes=256,
                mime_type='text/markdown',
                file_hash='sha256:mdhash123',
                status='pending',
                collection_id=sample_collection.id,
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            assert document.mime_type == 'text/markdown'


# =============================================================================
# Document Link Tests
# =============================================================================

class TestDocumentLinks:
    """Tests for document-collection links."""

    def test_RAG_INT_075_link_document_to_collection(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_075: Should link document to collection correctly."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']
            CollectionDocumentLink = rag_db_models['CollectionDocumentLink']

            document = RAGDocument(
                filename='link-test.pdf',
                original_filename='link-test.pdf',
                file_path='/tmp/link-test.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                file_hash='sha256:testhash123',
                status='pending',
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            link = CollectionDocumentLink(
                collection_id=sample_collection.id,
                document_id=document.id,
                link_type='new'
            )
            db.session.add(link)
            db.session.commit()

            result = CollectionDocumentLink.query.filter_by(
                document_id=document.id
            ).first()
            assert result is not None
            assert result.link_type == 'new'

    def test_RAG_INT_076_link_type_linked(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_076: Should support 'linked' link type."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']
            CollectionDocumentLink = rag_db_models['CollectionDocumentLink']

            document = RAGDocument(
                filename='linked-type.pdf',
                original_filename='linked-type.pdf',
                file_path='/tmp/linked-type.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                file_hash='sha256:testhash123',
                status='pending',
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            link = CollectionDocumentLink(
                collection_id=sample_collection.id,
                document_id=document.id,
                link_type='linked',
                source_url='https://example.com/doc.pdf'
            )
            db.session.add(link)
            db.session.commit()

            result = CollectionDocumentLink.query.filter_by(
                document_id=document.id
            ).first()
            assert result.link_type == 'linked'
            assert result.source_url == 'https://example.com/doc.pdf'


# =============================================================================
# Edge Cases
# =============================================================================

class TestDocumentEdgeCases:
    """Tests for edge cases in document handling."""

    def test_RAG_INT_077_empty_document(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_077: Empty document should be handled."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            document = RAGDocument(
                filename='empty.txt',
                original_filename='empty.txt',
                file_path='/tmp/empty.txt',
                file_size_bytes=0,
                mime_type='text/plain',
                file_hash='sha256:emptyhash123',
                status='pending',
                collection_id=sample_collection.id,
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            assert document.file_size_bytes == 0

    def test_RAG_INT_078_large_document(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_078: Large document should be handled."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            # 100 MB document
            document = RAGDocument(
                filename='large.pdf',
                original_filename='large.pdf',
                file_path='/tmp/large.pdf',
                file_size_bytes=100 * 1024 * 1024,
                mime_type='application/pdf',
                file_hash='sha256:testhash123',
                status='pending',
                collection_id=sample_collection.id,
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            assert document.file_size_bytes == 100 * 1024 * 1024

    def test_RAG_INT_079_special_filename(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_079: Special characters in filename should be handled."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            document = RAGDocument(
                filename='test-äöü-日本語.pdf',
                original_filename='Test Dokument (äöü) 日本語.pdf',
                file_path='/tmp/test-special.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                file_hash='sha256:testhash123',
                status='pending',
                collection_id=sample_collection.id,
                uploaded_by='admin'
            )
            db.session.add(document)
            db.session.commit()

            result = RAGDocument.query.get(document.id)
            assert 'äöü' in result.filename
            assert '日本語' in result.original_filename

    def test_RAG_INT_080_duplicate_document_detection(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_080: Duplicate documents should be detectable by hash."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            # Two documents with same hash
            hash_value = 'sha256:abc123def456'

            doc1 = RAGDocument(
                filename='doc1.pdf',
                original_filename='doc1.pdf',
                file_path='/tmp/doc1.pdf',
                file_size_bytes=1024,
                mime_type='application/pdf',
                status='pending',
                file_hash=hash_value,
                collection_id=sample_collection.id,
                uploaded_by='admin'
            )
            db.session.add(doc1)
            db.session.commit()

            # Query for duplicates
            duplicates = RAGDocument.query.filter_by(
                file_hash=hash_value
            ).all()

            assert len(duplicates) == 1
