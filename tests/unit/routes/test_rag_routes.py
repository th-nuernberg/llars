"""
Route Tests for RAG Collection & Document API
================================================

Tests for app/routes/rag/collection_routes.py and document_routes.py.
Covers: Collection CRUD, document management, auth checks.

Uses real blueprints with mocked OIDC token validation.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


def _create_collection_in_db(db_instance, name='test-coll', display_name='Test Collection',
                             created_by='admin', is_public=False):
    """Helper: insert a RAG collection directly into the DB."""
    from db.models.rag import RAGCollection

    coll = RAGCollection(
        name=name,
        display_name=display_name,
        description='A test collection',
        embedding_model='test-embed',
        chunk_size=1500,
        chunk_overlap=300,
        retrieval_k=4,
        is_public=is_public,
        created_by=created_by,
    )
    db_instance.session.add(coll)
    db_instance.session.commit()
    return coll


def _create_document_in_db(db_instance, collection_id, filename='test.pdf',
                           uploaded_by='admin'):
    """Helper: insert a RAG document directly into the DB."""
    from db.models.rag import RAGDocument, CollectionDocumentLink

    import hashlib
    file_hash = hashlib.sha256(f'{filename}-{collection_id}'.encode()).hexdigest()

    doc = RAGDocument(
        collection_id=collection_id,
        filename=filename,
        original_filename=filename,
        title=filename,
        file_path='/tmp/test-file.pdf',
        file_size_bytes=1024,
        file_hash=file_hash,
        mime_type='application/pdf',
        uploaded_by=uploaded_by,
        status='completed',
    )
    db_instance.session.add(doc)
    db_instance.session.commit()

    # Create collection-document link
    link = CollectionDocumentLink(
        collection_id=collection_id,
        document_id=doc.id,
        link_type='new',
    )
    db_instance.session.add(link)
    db_instance.session.commit()
    return doc


# ---------------------------------------------------------------------------
# List Collections
# ---------------------------------------------------------------------------

class TestListCollections:
    """Tests for GET /api/rag/collections"""

    def test_ROUTE_RAG_COLL_LIST_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/rag/collections')
        assert response.status_code == 401

    def test_ROUTE_RAG_COLL_LIST_002_forbidden_no_permission(self, auth_researcher, real_app):
        """Researcher lacks feature:rag:view permission."""
        with real_app.app_context():
            response = auth_researcher.get('/api/rag/collections')
            assert response.status_code == 403

    def test_ROUTE_RAG_COLL_LIST_003_success_admin(self, auth_admin, real_app):
        with real_app.app_context():
            _create_collection_in_db(real_app.db, name='list-coll-1',
                                     display_name='List Coll 1')
            response = auth_admin.get('/api/rag/collections')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert isinstance(data['collections'], list)

    def test_ROUTE_RAG_COLL_LIST_004_success_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            _create_collection_in_db(real_app.db, name='list-coll-eval',
                                     display_name='Eval Collection', is_public=True)
            response = auth_user.get('/api/rag/collections')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# Get Collection
# ---------------------------------------------------------------------------

class TestGetCollection:
    """Tests for GET /api/rag/collections/<id>"""

    def test_ROUTE_RAG_COLL_GET_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/rag/collections/1')
        assert response.status_code == 401

    def test_ROUTE_RAG_COLL_GET_002_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/rag/collections/99999')
            assert response.status_code == 404

    def test_ROUTE_RAG_COLL_GET_003_success_admin(self, auth_admin, real_app):
        with real_app.app_context():
            coll = _create_collection_in_db(real_app.db, name='get-coll',
                                            display_name='Get Coll')
            response = auth_admin.get(f'/api/rag/collections/{coll.id}')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['collection']['display_name'] == 'Get Coll'
            assert 'documents' in data['collection']

    def test_ROUTE_RAG_COLL_GET_004_forbidden_private(self, auth_user, real_app):
        with real_app.app_context():
            coll = _create_collection_in_db(real_app.db, name='priv-coll',
                                            display_name='Private', is_public=False,
                                            created_by='someone_else')
            response = auth_user.get(f'/api/rag/collections/{coll.id}')
            assert response.status_code == 403

    def test_ROUTE_RAG_COLL_GET_005_success_public(self, auth_user, real_app):
        with real_app.app_context():
            coll = _create_collection_in_db(real_app.db, name='pub-coll',
                                            display_name='Public', is_public=True)
            response = auth_user.get(f'/api/rag/collections/{coll.id}')
            assert response.status_code == 200


# ---------------------------------------------------------------------------
# Create Collection
# ---------------------------------------------------------------------------

class TestCreateCollection:
    """Tests for POST /api/rag/collections"""

    def test_ROUTE_RAG_COLL_CREATE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/rag/collections', json={
            'name': 'new-coll', 'display_name': 'New Coll'
        })
        assert response.status_code == 401

    def test_ROUTE_RAG_COLL_CREATE_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.post('/api/rag/collections', json={
                'name': 'eval-coll', 'display_name': 'Eval Coll'
            })
            assert response.status_code == 403

    def test_ROUTE_RAG_COLL_CREATE_003_missing_name(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/rag/collections', json={
                'display_name': 'No Name'
            })
            assert response.status_code == 400

    def test_ROUTE_RAG_COLL_CREATE_004_missing_display_name(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/rag/collections', json={
                'name': 'no-display'
            })
            assert response.status_code == 400

    @patch('services.chatbot_activity_service.ChatbotActivityService.log_collection_created')
    def test_ROUTE_RAG_COLL_CREATE_005_success(self, mock_log, auth_admin, real_app):
        with real_app.app_context():
            # Seed a default embedding model
            from db.models.llm_model import LLMModel
            model = LLMModel(
                model_id='test-embed-model',
                display_name='Test Embed',
                provider='test',
                model_type=LLMModel.MODEL_TYPE_EMBEDDING,
                is_active=True,
                is_default=True,
                context_window=8192,
                max_output_tokens=4096,
            )
            real_app.db.session.add(model)
            real_app.db.session.commit()

            response = auth_admin.post('/api/rag/collections', json={
                'name': 'brand-new-coll',
                'display_name': 'Brand New Collection',
                'description': 'Test description',
            })
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True
            assert data['collection']['name'] == 'brand-new-coll'

    @patch('services.chatbot_activity_service.ChatbotActivityService.log_collection_created')
    def test_ROUTE_RAG_COLL_CREATE_006_duplicate_name(self, mock_log, auth_admin, real_app):
        with real_app.app_context():
            # Seed embedding model
            from db.models.llm_model import LLMModel
            if not LLMModel.query.filter_by(model_id='test-embed-model-dup').first():
                model = LLMModel(
                    model_id='test-embed-model-dup',
                    display_name='Test Embed Dup',
                    provider='test',
                    model_type=LLMModel.MODEL_TYPE_EMBEDDING,
                    is_active=True,
                    is_default=True,
                    context_window=8192,
                    max_output_tokens=4096,
                )
                real_app.db.session.add(model)
                real_app.db.session.commit()

            # Create first
            auth_admin.post('/api/rag/collections', json={
                'name': 'dup-coll',
                'display_name': 'Dup Collection 1',
            })
            # Attempt duplicate
            response = auth_admin.post('/api/rag/collections', json={
                'name': 'dup-coll',
                'display_name': 'Dup Collection 2',
            })
            assert response.status_code == 409


# ---------------------------------------------------------------------------
# Update Collection
# ---------------------------------------------------------------------------

class TestUpdateCollection:
    """Tests for PUT /api/rag/collections/<id>"""

    def test_ROUTE_RAG_COLL_UPDATE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.put('/api/rag/collections/1',
                               json={'display_name': 'Updated'})
        assert response.status_code == 401

    def test_ROUTE_RAG_COLL_UPDATE_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.put('/api/rag/collections/1',
                                     json={'display_name': 'Updated'})
            assert response.status_code == 403

    def test_ROUTE_RAG_COLL_UPDATE_003_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.put('/api/rag/collections/99999',
                                      json={'display_name': 'Updated'})
            assert response.status_code == 404

    @patch('services.chatbot_activity_service.ChatbotActivityService.log_collection_updated')
    def test_ROUTE_RAG_COLL_UPDATE_004_success(self, mock_log, auth_admin, real_app):
        with real_app.app_context():
            coll = _create_collection_in_db(real_app.db, name='update-coll',
                                            display_name='Update Me')
            response = auth_admin.put(f'/api/rag/collections/{coll.id}',
                                       json={'display_name': 'Updated Collection',
                                             'description': 'New description'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True

    def test_ROUTE_RAG_COLL_UPDATE_005_forbidden_other_user(self, auth_user, real_app):
        with real_app.app_context():
            coll = _create_collection_in_db(real_app.db, name='other-coll',
                                            display_name='Other User Coll',
                                            created_by='someone_else',
                                            is_public=False)
            response = auth_user.put(f'/api/rag/collections/{coll.id}',
                                      json={'display_name': 'Hacked'})
            assert response.status_code == 403


# ---------------------------------------------------------------------------
# Delete Collection
# ---------------------------------------------------------------------------

class TestDeleteCollection:
    """Tests for DELETE /api/rag/collections/<id>"""

    def test_ROUTE_RAG_COLL_DELETE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.delete('/api/rag/collections/1')
        assert response.status_code == 401

    def test_ROUTE_RAG_COLL_DELETE_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.delete('/api/rag/collections/1')
            assert response.status_code == 403

    def test_ROUTE_RAG_COLL_DELETE_003_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.delete('/api/rag/collections/99999')
            assert response.status_code == 404

    @patch('services.chatbot_activity_service.ChatbotActivityService.log_collection_deleted')
    def test_ROUTE_RAG_COLL_DELETE_004_success_empty(self, mock_log, auth_admin, real_app):
        with real_app.app_context():
            coll = _create_collection_in_db(real_app.db, name='delete-coll',
                                            display_name='Delete Me')
            response = auth_admin.delete(f'/api/rag/collections/{coll.id}')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True

    def test_ROUTE_RAG_COLL_DELETE_005_has_docs_without_force(self, auth_admin, real_app):
        with real_app.app_context():
            coll = _create_collection_in_db(real_app.db, name='del-docs-coll',
                                            display_name='Has Docs')
            _create_document_in_db(real_app.db, coll.id, filename='doc1.pdf')
            response = auth_admin.delete(f'/api/rag/collections/{coll.id}')
            assert response.status_code == 400

    @patch('services.chatbot_activity_service.ChatbotActivityService.log_collection_deleted')
    def test_ROUTE_RAG_COLL_DELETE_006_force_with_docs(self, mock_log, auth_admin, real_app):
        with real_app.app_context():
            coll = _create_collection_in_db(real_app.db, name='del-force-coll',
                                            display_name='Force Delete')
            _create_document_in_db(real_app.db, coll.id, filename='doc2.pdf')
            response = auth_admin.delete(f'/api/rag/collections/{coll.id}?force=true')
            assert response.status_code == 200


# ---------------------------------------------------------------------------
# List Documents
# ---------------------------------------------------------------------------

class TestListDocuments:
    """Tests for GET /api/rag/documents"""

    def test_ROUTE_RAG_DOC_LIST_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/rag/documents')
        assert response.status_code == 401

    def test_ROUTE_RAG_DOC_LIST_002_forbidden_researcher(self, auth_researcher, real_app):
        with real_app.app_context():
            response = auth_researcher.get('/api/rag/documents')
            assert response.status_code == 403

    def test_ROUTE_RAG_DOC_LIST_003_success_admin(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/rag/documents')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert isinstance(data['documents'], list)

    def test_ROUTE_RAG_DOC_LIST_004_success_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/rag/documents')
            assert response.status_code == 200


# ---------------------------------------------------------------------------
# Get Document
# ---------------------------------------------------------------------------

class TestGetDocument:
    """Tests for GET /api/rag/documents/<id>"""

    def test_ROUTE_RAG_DOC_GET_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/rag/documents/1')
        assert response.status_code == 401

    def test_ROUTE_RAG_DOC_GET_002_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/rag/documents/99999')
            assert response.status_code == 404


# ---------------------------------------------------------------------------
# Upload Document
# ---------------------------------------------------------------------------

class TestUploadDocument:
    """Tests for POST /api/rag/documents/upload"""

    def test_ROUTE_RAG_DOC_UPLOAD_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/rag/documents/upload')
        assert response.status_code == 401

    def test_ROUTE_RAG_DOC_UPLOAD_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.post('/api/rag/documents/upload')
            assert response.status_code == 403

    def test_ROUTE_RAG_DOC_UPLOAD_003_no_file(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/rag/documents/upload')
            assert response.status_code == 400


# ---------------------------------------------------------------------------
# Update Document
# ---------------------------------------------------------------------------

class TestUpdateDocument:
    """Tests for PUT /api/rag/documents/<id>"""

    def test_ROUTE_RAG_DOC_UPDATE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.put('/api/rag/documents/1',
                               json={'title': 'Updated Title'})
        assert response.status_code == 401

    def test_ROUTE_RAG_DOC_UPDATE_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.put('/api/rag/documents/1',
                                     json={'title': 'Updated'})
            assert response.status_code == 403


# ---------------------------------------------------------------------------
# Delete Document
# ---------------------------------------------------------------------------

class TestDeleteDocument:
    """Tests for DELETE /api/rag/documents/<id>"""

    def test_ROUTE_RAG_DOC_DELETE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.delete('/api/rag/documents/1')
        assert response.status_code == 401

    def test_ROUTE_RAG_DOC_DELETE_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.delete('/api/rag/documents/1')
            assert response.status_code == 403

    def test_ROUTE_RAG_DOC_DELETE_003_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.delete('/api/rag/documents/99999')
            assert response.status_code == 404


# ---------------------------------------------------------------------------
# Collection Access
# ---------------------------------------------------------------------------

class TestCollectionAccess:
    """Tests for GET/PUT /api/rag/collections/<id>/access"""

    def test_ROUTE_RAG_ACCESS_001_get_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/rag/collections/1/access')
        assert response.status_code == 401

    def test_ROUTE_RAG_ACCESS_002_get_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/rag/collections/99999/access')
            assert response.status_code == 404

    def test_ROUTE_RAG_ACCESS_003_get_success(self, auth_admin, real_app):
        with real_app.app_context():
            coll = _create_collection_in_db(real_app.db, name='access-coll',
                                            display_name='Access Coll')
            response = auth_admin.get(f'/api/rag/collections/{coll.id}/access')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True

    def test_ROUTE_RAG_ACCESS_004_set_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.put('/api/rag/collections/1/access',
                               json={'usernames': []})
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Embedding Status
# ---------------------------------------------------------------------------

class TestEmbeddingStatus:
    """Tests for GET /api/rag/collections/<id>/embed/status"""

    def test_ROUTE_RAG_EMBED_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/rag/collections/1/embed/status')
        assert response.status_code == 401

    def test_ROUTE_RAG_EMBED_002_not_found(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/rag/collections/99999/embed/status')
            assert response.status_code == 404
