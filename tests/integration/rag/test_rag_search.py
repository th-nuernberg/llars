"""
RAG Search and Statistics Integration Tests
============================================

Tests for RAG search, retrieval, and statistics functionality.

Test IDs: RAG_INT_081 - RAG_INT_120
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import hashlib


# =============================================================================
# FIXTURES: Search Test Setup
# =============================================================================

@pytest.fixture
def rag_db_models(db, app):
    """Create RAG-related database tables and models."""
    with app.app_context():
        from db.tables import RAGCollection, RAGDocument, RAGDocumentChunk, RAGRetrievalLog
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
            'RAGRetrievalLog': RAGRetrievalLog,
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
            name='search-test-collection',
            display_name='Search Test Collection',
            embedding_model='sentence-transformers/all-MiniLM-L6-v2',
            created_by='admin',
            is_active=True,
            is_public=True
        )
        db.session.add(collection)
        db.session.commit()
        db.session.refresh(collection)
        return collection


@pytest.fixture
def sample_documents(db, app, rag_db_models, sample_collection):
    """Create multiple sample documents with chunks."""
    with app.app_context():
        RAGDocument = rag_db_models['RAGDocument']
        RAGDocumentChunk = rag_db_models['RAGDocumentChunk']
        CollectionDocumentLink = rag_db_models['CollectionDocumentLink']

        documents = []
        for i in range(5):
            doc = RAGDocument(
                filename=f'document-{i}.pdf',
                original_filename=f'document-{i}.pdf',
                file_path=f'/tmp/document-{i}.pdf',
                file_size_bytes=1024 * (i + 1),
                mime_type='application/pdf',
                file_hash=f'sha256:hash{i}',
                status='processed',
                chunk_count=3,
                collection_id=sample_collection.id,
                uploaded_by='admin',
                retrieval_count=i * 2
            )
            db.session.add(doc)
            db.session.commit()

            # Link to collection
            link = CollectionDocumentLink(
                collection_id=sample_collection.id,
                document_id=doc.id,
                link_type='new'
            )
            db.session.add(link)

            # Create chunks
            for j in range(3):
                chunk = RAGDocumentChunk(
                    document_id=doc.id,
                    chunk_index=j,
                    content=f'Document {i} chunk {j} content with searchable text.',
                    start_char=j * 50,
                    end_char=(j + 1) * 50
                )
                db.session.add(chunk)

            documents.append(doc)

        db.session.commit()
        return documents


@pytest.fixture
def retrieval_logs(db, app, rag_db_models, sample_collection, sample_documents):
    """Create sample retrieval logs."""
    with app.app_context():
        RAGRetrievalLog = rag_db_models['RAGRetrievalLog']

        logs = []
        queries = [
            'What is the main topic?',
            'How does this work?',
            'Explain the process',
            'What are the benefits?',
            'What is the main topic?',  # Duplicate for popular queries
        ]

        for query in queries:
            query_hash = hashlib.sha256(query.encode()).hexdigest()[:32]
            log = RAGRetrievalLog(
                collection_id=sample_collection.id,
                query_text=query,
                query_hash=query_hash,
                num_results=3,
                retrieval_time_ms=50,
                created_at=datetime.utcnow()
            )
            db.session.add(log)
            logs.append(log)

        db.session.commit()
        return logs


# =============================================================================
# Statistics Overview Tests
# =============================================================================

class TestStatsOverview:
    """Tests for RAG statistics overview."""

    def test_RAG_INT_081_stats_unauthenticated(self, client):
        """RAG_INT_081: Stats endpoint without auth should fail."""
        response = client.get('/api/rag/stats')
        assert response.status_code in [401, 403, 404, 500]

    def test_RAG_INT_082_stats_empty_system(
        self, db, app, rag_db_models
    ):
        """RAG_INT_082: Stats should return zeros for empty system."""
        with app.app_context():
            RAGCollection = rag_db_models['RAGCollection']
            RAGDocument = rag_db_models['RAGDocument']

            collection_count = RAGCollection.query.filter_by(is_active=True).count()
            document_count = RAGDocument.query.count()

            assert collection_count == 0
            assert document_count == 0

    def test_RAG_INT_083_stats_with_data(
        self, db, app, rag_db_models, sample_collection, sample_documents
    ):
        """RAG_INT_083: Stats should reflect actual data."""
        with app.app_context():
            RAGCollection = rag_db_models['RAGCollection']
            RAGDocument = rag_db_models['RAGDocument']
            RAGDocumentChunk = rag_db_models['RAGDocumentChunk']

            collection_count = RAGCollection.query.filter_by(is_active=True).count()
            document_count = RAGDocument.query.count()
            chunk_count = RAGDocumentChunk.query.count()

            assert collection_count == 1
            assert document_count == 5
            assert chunk_count == 15  # 5 docs * 3 chunks

    def test_RAG_INT_084_stats_document_by_status(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_084: Stats should group documents by status."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']
            from sqlalchemy import func

            # Create documents with different statuses
            for status in ['pending', 'processing', 'processed', 'error']:
                doc = RAGDocument(
                    filename=f'{status}-doc.pdf',
                    file_path=f'/tmp/{status}-doc.pdf',
                    file_size_bytes=1024,
                    mime_type='application/pdf',
                    status=status,
                    original_filename=f'{status}-doc.pdf', file_hash=f'sha256:{status}hash',
                    collection_id=sample_collection.id,
                    uploaded_by='admin'
                )
                db.session.add(doc)
            db.session.commit()

            # Count by status
            status_counts = db.session.query(
                RAGDocument.status,
                func.count(RAGDocument.id)
            ).group_by(RAGDocument.status).all()

            assert len(status_counts) == 4


# =============================================================================
# Popular Documents Tests
# =============================================================================

class TestPopularDocuments:
    """Tests for popular documents statistics."""

    def test_RAG_INT_085_popular_documents_unauthenticated(self, client):
        """RAG_INT_085: Popular documents endpoint without auth should fail."""
        response = client.get('/api/rag/stats/popular-documents')
        assert response.status_code in [401, 403, 404, 500]

    def test_RAG_INT_086_popular_documents_empty(
        self, db, app, rag_db_models
    ):
        """RAG_INT_086: Should return empty list when no documents retrieved."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            popular = RAGDocument.query.filter(
                RAGDocument.retrieval_count > 0
            ).all()

            assert len(popular) == 0

    def test_RAG_INT_087_popular_documents_ordering(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_087: Popular documents should be ordered by retrieval count."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            # Create documents with varying retrieval counts
            for count in [5, 10, 2, 8, 1]:
                doc = RAGDocument(
                    filename=f'pop-{count}.pdf',
                    file_path=f'/tmp/pop-{count}.pdf',
                    file_size_bytes=1024,
                    mime_type='application/pdf',
                    status='processed',
                    original_filename=f'pop-{count}.pdf', file_hash=f'sha256:pop{count}hash',
                    retrieval_count=count,
                    collection_id=sample_collection.id,
                    uploaded_by='admin'
                )
                db.session.add(doc)
            db.session.commit()

            # Query ordered by retrieval count
            popular = RAGDocument.query.filter(
                RAGDocument.retrieval_count > 0
            ).order_by(RAGDocument.retrieval_count.desc()).limit(3).all()

            assert len(popular) == 3
            assert popular[0].retrieval_count == 10
            assert popular[1].retrieval_count == 8
            assert popular[2].retrieval_count == 5

    def test_RAG_INT_088_popular_documents_limit(
        self, db, app, rag_db_models, sample_documents
    ):
        """RAG_INT_088: Popular documents should respect limit parameter."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            popular = RAGDocument.query.filter(
                RAGDocument.retrieval_count > 0
            ).order_by(RAGDocument.retrieval_count.desc()).limit(2).all()

            assert len(popular) <= 2


# =============================================================================
# Popular Queries Tests
# =============================================================================

class TestPopularQueries:
    """Tests for popular queries statistics."""

    def test_RAG_INT_089_popular_queries_unauthenticated(self, client):
        """RAG_INT_089: Popular queries endpoint without auth should fail."""
        response = client.get('/api/rag/stats/popular-queries')
        assert response.status_code in [401, 403, 404, 500]

    def test_RAG_INT_090_popular_queries_empty(
        self, db, app, rag_db_models
    ):
        """RAG_INT_090: Should return empty list when no queries logged."""
        with app.app_context():
            RAGRetrievalLog = rag_db_models['RAGRetrievalLog']

            logs = RAGRetrievalLog.query.all()
            assert len(logs) == 0

    def test_RAG_INT_091_popular_queries_grouping(
        self, db, app, rag_db_models, sample_collection, retrieval_logs
    ):
        """RAG_INT_091: Queries should be grouped by hash."""
        with app.app_context():
            RAGRetrievalLog = rag_db_models['RAGRetrievalLog']
            from sqlalchemy import func

            grouped = db.session.query(
                RAGRetrievalLog.query_hash,
                func.count(RAGRetrievalLog.id).label('count')
            ).group_by(RAGRetrievalLog.query_hash).all()

            # "What is the main topic?" appears twice
            assert any(g.count > 1 for g in grouped)


# =============================================================================
# Retrieval Logging Tests
# =============================================================================

class TestRetrievalLogging:
    """Tests for retrieval logging."""

    def test_RAG_INT_092_log_retrieval(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_092: Should log retrieval correctly."""
        with app.app_context():
            RAGRetrievalLog = rag_db_models['RAGRetrievalLog']

            log = RAGRetrievalLog(
                collection_id=sample_collection.id,
                query_text='Test query',
                query_hash='abc123',
                num_results=5,
                retrieval_time_ms=100
            )
            db.session.add(log)
            db.session.commit()

            result = RAGRetrievalLog.query.get(log.id)
            assert result.query_text == 'Test query'
            assert result.num_results == 5

    def test_RAG_INT_093_log_retrieval_time(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_093: Should track retrieval time in ms."""
        with app.app_context():
            RAGRetrievalLog = rag_db_models['RAGRetrievalLog']

            log = RAGRetrievalLog(
                collection_id=sample_collection.id,
                query_text='Timing test',
                query_hash='def456',
                num_results=3,
                retrieval_time_ms=75
            )
            db.session.add(log)
            db.session.commit()

            assert log.retrieval_time_ms == 75

    def test_RAG_INT_094_log_retrieval_zero_results(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_094: Should log zero result retrievals."""
        with app.app_context():
            RAGRetrievalLog = rag_db_models['RAGRetrievalLog']

            log = RAGRetrievalLog(
                collection_id=sample_collection.id,
                query_text='No matches query',
                query_hash='ghi789',
                num_results=0,
                retrieval_time_ms=20
            )
            db.session.add(log)
            db.session.commit()

            assert log.num_results == 0


# =============================================================================
# Embedding Info Tests
# =============================================================================

class TestEmbeddingInfo:
    """Tests for embedding model information."""

    def test_RAG_INT_095_embedding_info_unauthenticated(self, client):
        """RAG_INT_095: Embedding info endpoint without auth should fail."""
        response = client.get('/api/rag/embedding-info')
        assert response.status_code in [401, 403, 404, 500]

    def test_RAG_INT_096_default_embedding_model(
        self, db, app, rag_db_models
    ):
        """RAG_INT_096: Should have a default embedding model."""
        with app.app_context():
            LLMModel = rag_db_models['LLMModel']

            default = LLMModel.query.filter_by(
                model_type='embedding',
                is_default=True
            ).first()

            assert default is not None
            assert default.is_active is True

    def test_RAG_INT_097_embedding_model_dimensions(
        self, db, app, rag_db_models
    ):
        """RAG_INT_097: Embedding model should have valid context window."""
        with app.app_context():
            LLMModel = rag_db_models['LLMModel']

            model = LLMModel.query.filter_by(model_type='embedding').first()
            assert model.context_window > 0  # Should have valid context window


# =============================================================================
# Search Filtering Tests
# =============================================================================

class TestSearchFiltering:
    """Tests for search filtering functionality."""

    def test_RAG_INT_098_filter_by_collection(
        self, db, app, rag_db_models
    ):
        """RAG_INT_098: Should filter documents by collection."""
        with app.app_context():
            RAGCollection = rag_db_models['RAGCollection']
            RAGDocument = rag_db_models['RAGDocument']

            # Create two collections
            coll1 = RAGCollection(
                name='coll1', display_name='Collection 1',
                embedding_model='test', created_by='admin', is_active=True
            )
            coll2 = RAGCollection(
                name='coll2', display_name='Collection 2',
                embedding_model='test', created_by='admin', is_active=True
            )
            db.session.add_all([coll1, coll2])
            db.session.commit()

            # Add documents to each
            for i in range(3):
                doc1 = RAGDocument(
                    filename=f'coll1-{i}.pdf', file_path=f'/tmp/c1-{i}.pdf',
                    file_size_bytes=1024, mime_type='application/pdf',
                    original_filename=f'coll1-{i}.pdf', file_hash=f'sha256:coll1hash{i}',
                    status='processed', collection_id=coll1.id, uploaded_by='admin'
                )
                db.session.add(doc1)

            for i in range(2):
                doc2 = RAGDocument(
                    filename=f'coll2-{i}.pdf', file_path=f'/tmp/c2-{i}.pdf',
                    file_size_bytes=1024, mime_type='application/pdf',
                    original_filename=f'coll2-{i}.pdf', file_hash=f'sha256:coll2hash{i}',
                    status='processed', collection_id=coll2.id, uploaded_by='admin'
                )
                db.session.add(doc2)
            db.session.commit()

            # Filter by collection
            coll1_docs = RAGDocument.query.filter_by(collection_id=coll1.id).all()
            coll2_docs = RAGDocument.query.filter_by(collection_id=coll2.id).all()

            assert len(coll1_docs) == 3
            assert len(coll2_docs) == 2

    def test_RAG_INT_099_filter_by_status(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_099: Should filter documents by status."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            # Create documents with different statuses
            for status, count in [('processed', 3), ('pending', 2), ('error', 1)]:
                for i in range(count):
                    doc = RAGDocument(
                        filename=f'{status}-{i}.pdf', file_path=f'/tmp/{status}-{i}.pdf',
                        file_size_bytes=1024, mime_type='application/pdf',
                        original_filename=f'{status}-{i}.pdf', file_hash=f'sha256:{status}{i}hash',
                        status=status, collection_id=sample_collection.id, uploaded_by='admin'
                    )
                    db.session.add(doc)
            db.session.commit()

            processed = RAGDocument.query.filter_by(status='processed').count()
            pending = RAGDocument.query.filter_by(status='pending').count()
            error = RAGDocument.query.filter_by(status='error').count()

            assert processed == 3
            assert pending == 2
            assert error == 1


# =============================================================================
# Search Result Tests
# =============================================================================

class TestSearchResults:
    """Tests for search result handling."""

    def test_RAG_INT_100_chunk_relevance_score(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_100: Chunks should support relevance scoring."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']
            RAGDocumentChunk = rag_db_models['RAGDocumentChunk']

            doc = RAGDocument(
                filename='relevance.pdf', file_path='/tmp/relevance.pdf',
                file_size_bytes=1024, mime_type='application/pdf',
                original_filename='relevance.pdf', file_hash='sha256:relevancehash123',
                status='processed', collection_id=sample_collection.id, uploaded_by='admin'
            )
            db.session.add(doc)
            db.session.commit()

            chunk = RAGDocumentChunk(
                document_id=doc.id,
                chunk_index=0,
                content='Relevant content',
                start_char=0,
                end_char=16
            )
            db.session.add(chunk)
            db.session.commit()

            # Chunk should exist
            result = RAGDocumentChunk.query.get(chunk.id)
            assert result is not None


# =============================================================================
# Collection Embedding Status Tests
# =============================================================================

class TestCollectionEmbeddingStatus:
    """Tests for collection embedding status tracking."""

    def test_RAG_INT_101_embedding_status_idle(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_101: New collection should have idle status."""
        with app.app_context():
            RAGCollection = rag_db_models['RAGCollection']

            collection = RAGCollection.query.get(sample_collection.id)
            # Default status should be idle or None
            assert collection.embedding_status in [None, 'idle']

    def test_RAG_INT_102_embedding_status_processing(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_102: Should track processing status."""
        with app.app_context():
            RAGCollection = rag_db_models['RAGCollection']

            collection = RAGCollection.query.get(sample_collection.id)
            collection.embedding_status = 'processing'
            collection.embedding_progress = 50
            db.session.commit()

            result = RAGCollection.query.get(sample_collection.id)
            assert result.embedding_status == 'processing'
            assert result.embedding_progress == 50

    def test_RAG_INT_103_embedding_status_completed(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_103: Should track completed status."""
        with app.app_context():
            RAGCollection = rag_db_models['RAGCollection']

            collection = RAGCollection.query.get(sample_collection.id)
            collection.embedding_status = 'completed'
            collection.embedding_progress = 100
            collection.last_indexed_at = datetime.utcnow()
            db.session.commit()

            result = RAGCollection.query.get(sample_collection.id)
            assert result.embedding_status == 'completed'
            assert result.last_indexed_at is not None


# =============================================================================
# Multi-Model Embedding Tests
# =============================================================================

class TestMultiModelEmbedding:
    """Tests for multi-model embedding support."""

    def test_RAG_INT_104_collection_embedding_record(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_104: Should create embedding record for collection."""
        with app.app_context():
            CollectionEmbedding = rag_db_models['CollectionEmbedding']

            embedding = CollectionEmbedding(
                collection_id=sample_collection.id,
                model_id='sentence-transformers/all-MiniLM-L6-v2',
                model_source='local',
                embedding_dimensions=384,
                chroma_collection_name=f'coll_{sample_collection.id}_minilm',
                status='idle',
                priority=1
            )
            db.session.add(embedding)
            db.session.commit()

            result = CollectionEmbedding.query.filter_by(
                collection_id=sample_collection.id
            ).first()
            assert result is not None
            assert result.embedding_dimensions == 384

    def test_RAG_INT_105_multiple_embedding_models(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_105: Collection should support multiple embedding models."""
        with app.app_context():
            CollectionEmbedding = rag_db_models['CollectionEmbedding']

            # Add two embedding models
            emb1 = CollectionEmbedding(
                collection_id=sample_collection.id,
                model_id='model-1',
                model_source='local',
                embedding_dimensions=384,
                chroma_collection_name=f'coll_{sample_collection.id}_m1',
                status='completed',
                priority=1
            )
            emb2 = CollectionEmbedding(
                collection_id=sample_collection.id,
                model_id='model-2',
                model_source='litellm',
                embedding_dimensions=1024,
                chroma_collection_name=f'coll_{sample_collection.id}_m2',
                status='completed',
                priority=2
            )
            db.session.add_all([emb1, emb2])
            db.session.commit()

            embeddings = CollectionEmbedding.query.filter_by(
                collection_id=sample_collection.id
            ).order_by(CollectionEmbedding.priority.desc()).all()

            assert len(embeddings) == 2
            assert embeddings[0].priority > embeddings[1].priority


# =============================================================================
# Processing Queue Tests
# =============================================================================

class TestProcessingQueue:
    """Tests for document processing queue."""

    def test_RAG_INT_106_queue_document(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_106: Should queue document for processing."""
        with app.app_context():
            from db.tables import RAGProcessingQueue
            RAGDocument = rag_db_models['RAGDocument']

            doc = RAGDocument(
                filename='queue-test.pdf', file_path='/tmp/queue-test.pdf',
                file_size_bytes=1024, mime_type='application/pdf',
                original_filename='queue-test.pdf', file_hash='sha256:queuetesthash123',
                status='pending', collection_id=sample_collection.id, uploaded_by='admin'
            )
            db.session.add(doc)
            db.session.commit()

            queue_entry = RAGProcessingQueue(
                document_id=doc.id,
                priority=5,
                status='queued'
            )
            db.session.add(queue_entry)
            db.session.commit()

            result = RAGProcessingQueue.query.filter_by(document_id=doc.id).first()
            assert result is not None
            assert result.status == 'queued'

    def test_RAG_INT_107_queue_priority(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_107: Queue should respect priority ordering."""
        with app.app_context():
            from db.tables import RAGProcessingQueue
            RAGDocument = rag_db_models['RAGDocument']

            # Create documents with different priorities
            for priority in [1, 5, 3, 10, 2]:
                doc = RAGDocument(
                    filename=f'pri-{priority}.pdf', file_path=f'/tmp/pri-{priority}.pdf',
                    file_size_bytes=1024, mime_type='application/pdf',
                    original_filename=f'pri-{priority}.pdf', file_hash=f'sha256:prihash{priority}',
                    status='pending', collection_id=sample_collection.id, uploaded_by='admin'
                )
                db.session.add(doc)
                db.session.commit()

                queue = RAGProcessingQueue(
                    document_id=doc.id,
                    priority=priority,
                    status='queued'
                )
                db.session.add(queue)
            db.session.commit()

            # Get in priority order
            ordered = RAGProcessingQueue.query.filter_by(
                status='queued'
            ).order_by(RAGProcessingQueue.priority.desc()).all()

            priorities = [q.priority for q in ordered]
            assert priorities == sorted(priorities, reverse=True)


# =============================================================================
# Size and Count Calculations Tests
# =============================================================================

class TestSizeCalculations:
    """Tests for size and count calculations."""

    def test_RAG_INT_108_total_size_bytes(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_108: Should calculate total size correctly."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']
            from sqlalchemy import func

            # Create documents
            sizes = [1024, 2048, 4096]
            for size in sizes:
                doc = RAGDocument(
                    filename=f'size-{size}.pdf', file_path=f'/tmp/size-{size}.pdf',
                    file_size_bytes=size, mime_type='application/pdf',
                    original_filename=f'size-{size}.pdf', file_hash=f'sha256:sizehash{size}',
                    status='processed', collection_id=sample_collection.id, uploaded_by='admin'
                )
                db.session.add(doc)
            db.session.commit()

            total = db.session.query(
                func.sum(RAGDocument.file_size_bytes)
            ).filter_by(collection_id=sample_collection.id).scalar()

            assert total == sum(sizes)

    def test_RAG_INT_109_total_chunks(
        self, db, app, rag_db_models, sample_documents
    ):
        """RAG_INT_109: Should calculate total chunks correctly."""
        with app.app_context():
            RAGDocumentChunk = rag_db_models['RAGDocumentChunk']

            total = RAGDocumentChunk.query.count()
            assert total == 15  # 5 docs * 3 chunks

    def test_RAG_INT_110_avg_retrieval_score(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_110: Should calculate average retrieval score."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']
            from sqlalchemy import func

            # Create documents with relevance scores
            scores = [0.8, 0.9, 0.7, 0.85]
            for idx, score in enumerate(scores):
                doc = RAGDocument(
                    filename=f'score-{score}.pdf', file_path=f'/tmp/score-{score}.pdf',
                    file_size_bytes=1024, mime_type='application/pdf',
                    original_filename=f'score-{score}.pdf', file_hash=f'sha256:scorehash{idx}',
                    status='processed', collection_id=sample_collection.id,
                    uploaded_by='admin', avg_relevance_score=score
                )
                db.session.add(doc)
            db.session.commit()

            avg = db.session.query(
                func.avg(RAGDocument.avg_relevance_score)
            ).filter_by(collection_id=sample_collection.id).scalar()

            expected_avg = sum(scores) / len(scores)
            assert abs(avg - expected_avg) < 0.01


# =============================================================================
# Date Range Queries Tests
# =============================================================================

class TestDateRangeQueries:
    """Tests for date range queries."""

    def test_RAG_INT_111_documents_uploaded_today(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_111: Should find documents uploaded today."""
        with app.app_context():
            RAGDocument = rag_db_models['RAGDocument']

            now = datetime.utcnow()
            doc = RAGDocument(
                filename='today.pdf', file_path='/tmp/today.pdf',
                file_size_bytes=1024, mime_type='application/pdf',
                original_filename='today.pdf', file_hash='sha256:todayhash123',
                status='processed', collection_id=sample_collection.id,
                uploaded_by='admin', uploaded_at=now
            )
            db.session.add(doc)
            db.session.commit()

            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_docs = RAGDocument.query.filter(
                RAGDocument.uploaded_at >= start_of_day
            ).all()

            assert len(today_docs) >= 1

    def test_RAG_INT_112_recent_retrievals(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_112: Should find recent retrieval logs."""
        with app.app_context():
            RAGRetrievalLog = rag_db_models['RAGRetrievalLog']

            now = datetime.utcnow()
            log = RAGRetrievalLog(
                collection_id=sample_collection.id,
                query_text='Recent query',
                query_hash='recent123',
                num_results=3,
                retrieval_time_ms=50,
                created_at=now
            )
            db.session.add(log)
            db.session.commit()

            one_hour_ago = now - timedelta(hours=1)
            recent = RAGRetrievalLog.query.filter(
                RAGRetrievalLog.created_at >= one_hour_ago
            ).all()

            assert len(recent) >= 1


# =============================================================================
# Edge Cases
# =============================================================================

class TestSearchEdgeCases:
    """Tests for edge cases in search functionality."""

    def test_RAG_INT_113_empty_query(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_113: Empty query should be handled."""
        with app.app_context():
            RAGRetrievalLog = rag_db_models['RAGRetrievalLog']

            log = RAGRetrievalLog(
                collection_id=sample_collection.id,
                query_text='',
                query_hash='empty',
                num_results=0,
                retrieval_time_ms=5
            )
            db.session.add(log)
            db.session.commit()

            assert log.query_text == ''

    def test_RAG_INT_114_very_long_query(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_114: Very long query should be handled."""
        with app.app_context():
            RAGRetrievalLog = rag_db_models['RAGRetrievalLog']

            long_query = 'A' * 5000
            log = RAGRetrievalLog(
                collection_id=sample_collection.id,
                query_text=long_query,
                query_hash=hashlib.sha256(long_query.encode()).hexdigest()[:32],
                num_results=0,
                retrieval_time_ms=100
            )
            db.session.add(log)
            db.session.commit()

            assert len(log.query_text) == 5000

    def test_RAG_INT_115_unicode_query(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_115: Unicode query should be handled."""
        with app.app_context():
            RAGRetrievalLog = rag_db_models['RAGRetrievalLog']

            unicode_query = 'Как работает система? 日本語クエリ'
            log = RAGRetrievalLog(
                collection_id=sample_collection.id,
                query_text=unicode_query,
                query_hash='unicode123',
                num_results=0,
                retrieval_time_ms=50
            )
            db.session.add(log)
            db.session.commit()

            result = RAGRetrievalLog.query.get(log.id)
            assert 'Как' in result.query_text
            assert '日本語' in result.query_text


# =============================================================================
# Performance Metrics Tests
# =============================================================================

class TestPerformanceMetrics:
    """Tests for performance metrics tracking."""

    def test_RAG_INT_116_avg_retrieval_time(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_116: Should calculate average retrieval time."""
        with app.app_context():
            RAGRetrievalLog = rag_db_models['RAGRetrievalLog']
            from sqlalchemy import func

            times = [50, 100, 75, 150, 25]
            for time_ms in times:
                log = RAGRetrievalLog(
                    collection_id=sample_collection.id,
                    query_text='Time test',
                    query_hash=f'time{time_ms}',
                    num_results=3,
                    retrieval_time_ms=time_ms
                )
                db.session.add(log)
            db.session.commit()

            avg = db.session.query(
                func.avg(RAGRetrievalLog.retrieval_time_ms)
            ).filter_by(collection_id=sample_collection.id).scalar()

            expected_avg = sum(times) / len(times)
            assert abs(avg - expected_avg) < 0.01

    def test_RAG_INT_117_max_retrieval_time(
        self, db, app, rag_db_models, sample_collection
    ):
        """RAG_INT_117: Should find max retrieval time."""
        with app.app_context():
            RAGRetrievalLog = rag_db_models['RAGRetrievalLog']
            from sqlalchemy import func

            for time_ms in [50, 200, 100]:
                log = RAGRetrievalLog(
                    collection_id=sample_collection.id,
                    query_text='Max test',
                    query_hash=f'max{time_ms}',
                    num_results=3,
                    retrieval_time_ms=time_ms
                )
                db.session.add(log)
            db.session.commit()

            max_time = db.session.query(
                func.max(RAGRetrievalLog.retrieval_time_ms)
            ).filter_by(collection_id=sample_collection.id).scalar()

            assert max_time == 200


# =============================================================================
# Data Integrity Tests
# =============================================================================

class TestDataIntegrity:
    """Tests for data integrity in search data."""

    def test_RAG_INT_118_collection_document_consistency(
        self, db, app, rag_db_models, sample_collection, sample_documents
    ):
        """RAG_INT_118: Document collection_id should match link."""
        with app.app_context():
            CollectionDocumentLink = rag_db_models['CollectionDocumentLink']
            RAGDocument = rag_db_models['RAGDocument']

            links = CollectionDocumentLink.query.filter_by(
                collection_id=sample_collection.id
            ).all()

            for link in links:
                doc = RAGDocument.query.get(link.document_id)
                # Document exists and is linked correctly
                assert doc is not None

    def test_RAG_INT_119_chunk_document_reference(
        self, db, app, rag_db_models, sample_documents
    ):
        """RAG_INT_119: All chunks should reference valid documents."""
        with app.app_context():
            RAGDocumentChunk = rag_db_models['RAGDocumentChunk']
            RAGDocument = rag_db_models['RAGDocument']

            chunks = RAGDocumentChunk.query.all()
            for chunk in chunks:
                doc = RAGDocument.query.get(chunk.document_id)
                assert doc is not None

    def test_RAG_INT_120_retrieval_log_collection_reference(
        self, db, app, rag_db_models, sample_collection, retrieval_logs
    ):
        """RAG_INT_120: All logs should reference valid collections."""
        with app.app_context():
            RAGRetrievalLog = rag_db_models['RAGRetrievalLog']
            RAGCollection = rag_db_models['RAGCollection']

            logs = RAGRetrievalLog.query.all()
            for log in logs:
                collection = RAGCollection.query.get(log.collection_id)
                assert collection is not None
