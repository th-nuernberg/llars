"""
RAG Document Management Routes

Provides API endpoints for managing RAG documents.
All routes are protected with appropriate permissions.

Routes:
    GET    /api/rag/documents                  - List all documents (with filters)
    GET    /api/rag/documents/<id>             - Get document details
    GET    /api/rag/documents/<id>/content     - Get document text content
    GET    /api/rag/documents/<id>/chunks      - Get document chunks
    GET    /api/rag/documents/<id>/download    - Download document file
    POST   /api/rag/documents/upload           - Upload new document
    POST   /api/rag/documents/upload-multiple  - Upload multiple documents
    PUT    /api/rag/documents/<id>             - Update document metadata
    DELETE /api/rag/documents/<id>             - Delete document
"""

from flask import Blueprint, request, jsonify, current_app, send_file
import os
from decorators.permission_decorator import require_permission
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError, ForbiddenError
)
from auth.auth_utils import AuthUtils
from services.rag.document_service import DocumentService
from services.rag.access_service import RAGAccessService
from services.chatbot_activity_service import ChatbotActivityService
from db.tables import RAGCollection

rag_document_bp = Blueprint('rag_document', __name__)


@rag_document_bp.route('/documents', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_documents():
    """Get all documents with optional filters"""
    username = AuthUtils.extract_username_without_validation()
    # Query parameters for filtering
    collection_id = request.args.get('collection_id', type=int)
    status = request.args.get('status')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    # Get documents from service
    documents, pagination_info = DocumentService.get_documents(
        collection_id=collection_id,
        status=status,
        search=search,
        page=page,
        per_page=per_page,
        username=username
    )

    return jsonify({
        'success': True,
        'documents': [DocumentService.serialize_document(d) for d in documents],
        'pagination': pagination_info
    }), 200


@rag_document_bp.route('/documents/<int:document_id>', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_document(document_id):
    """Get detailed document information"""
    username = AuthUtils.extract_username_without_validation()
    document = DocumentService.get_document_by_id(document_id, username=username, access='view')
    if not document:
        raise NotFoundError(f'Document with ID {document_id} not found')

    return jsonify({
        'success': True,
        'document': DocumentService.serialize_document(document, include_details=True)
    }), 200


@rag_document_bp.route('/documents/<int:document_id>/content', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_document_content(document_id):
    """
    Get the extracted text content of a document.
    Returns the combined text from all chunks.
    """
    username = AuthUtils.extract_username_without_validation()
    document, full_content = DocumentService.get_document_content(document_id, username=username)
    if not document:
        raise NotFoundError(f'Document with ID {document_id} not found')

    return jsonify({
        'success': True,
        'document': {
            'id': document.id,
            'filename': document.filename,
            'title': document.title,
            'status': document.status,
            'chunk_count': document.chunk_count
        },
        'content': full_content,
        'content_length': len(full_content)
    }), 200


@rag_document_bp.route('/documents/<int:document_id>/chunks', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_document_chunks(document_id):
    """Get all chunks for a document"""
    username = AuthUtils.extract_username_without_validation()
    document, chunks = DocumentService.get_document_chunks(document_id, username=username)
    if not document:
        raise NotFoundError(f'Document with ID {document_id} not found')

    return jsonify({
        'success': True,
        'document': {
            'id': document.id,
            'filename': document.filename,
            'chunk_count': document.chunk_count
        },
        'chunks': [DocumentService.serialize_chunk(c) for c in chunks]
    }), 200


@rag_document_bp.route('/documents/<int:document_id>/download', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def download_document(document_id):
    """Download document file"""
    username = AuthUtils.extract_username_without_validation()
    document = DocumentService.get_document_by_id(document_id, username=username, access='view')
    if not document:
        raise NotFoundError(f'Document with ID {document_id} not found')

    if not os.path.exists(document.file_path):
        raise NotFoundError('Document file not found on disk')

    return send_file(
        document.file_path,
        as_attachment=True,
        download_name=document.original_filename,
        mimetype=document.mime_type
    )


@rag_document_bp.route('/documents/upload', methods=['POST'])
@require_permission('feature:rag:edit')
@handle_api_errors(logger_name='rag')
def upload_document():
    """Upload new document to RAG system"""
    # Get username from token
    username = AuthUtils.extract_username_without_validation()

    # Check if file was uploaded
    if 'file' not in request.files:
        raise ValidationError('No file provided')

    file = request.files['file']

    # Get additional metadata from form
    collection_id = request.form.get('collection_id', type=int)
    title = request.form.get('title', '')
    description = request.form.get('description', '')
    author = request.form.get('author', '')
    language = request.form.get('language', 'de')

    # Create document using service
    result = DocumentService.create_document(
        file=file,
        uploaded_by=username,
        collection_id=collection_id,
        title=title,
        description=description,
        author=author,
        language=language
    )

    if not result['success']:
        if 'existing_document_id' in result:
            raise ConflictError(result.get('error', 'Document already exists'), details=result)
        else:
            raise ValidationError(result.get('error', 'Failed to upload document'))

    # Serialize document for response
    doc = result['document']

    # Log activity
    collection_name = None
    if collection_id:
        collection = RAGCollection.query.get(collection_id)
        collection_name = collection.display_name if collection else None

    ChatbotActivityService.log_document_uploaded(
        document_id=doc.id,
        filename=doc.original_filename or doc.filename,
        username=username,
        collection_id=collection_id,
        collection_name=collection_name,
        file_size_bytes=doc.file_size_bytes,
        mime_type=doc.mime_type
    )

    return jsonify({
        'success': True,
        'message': result['message'],
        'document': {
            'id': doc.id,
            'filename': doc.filename,
            'original_filename': doc.original_filename,
            'file_size_mb': round(doc.file_size_bytes / (1024*1024), 2),
            'status': doc.status,
            'collection_id': doc.collection_id
        }
    }), 201


@rag_document_bp.route('/documents/upload-multiple', methods=['POST'])
@require_permission('feature:rag:edit')
@handle_api_errors(logger_name='rag')
def upload_multiple_documents():
    """Upload multiple documents at once"""
    # Get username from token
    username = AuthUtils.extract_username_without_validation()

    if 'files' not in request.files:
        raise ValidationError('No files provided')

    files = request.files.getlist('files')
    collection_id = request.form.get('collection_id', type=int)

    # Upload documents using service
    result = DocumentService.create_multiple_documents(
        files=files,
        uploaded_by=username,
        collection_id=collection_id
    )

    # Log activity for successful uploads
    if result.get('success') and result.get('uploaded'):
        collection_name = None
        if collection_id:
            collection = RAGCollection.query.get(collection_id)
            collection_name = collection.display_name if collection else None

        uploaded_docs = result['uploaded']
        document_ids = [d.get('id') for d in uploaded_docs if d.get('id')]
        filenames = [d.get('filename') or d.get('original_filename') for d in uploaded_docs]
        total_size = sum(d.get('file_size_bytes', 0) for d in uploaded_docs)

        if len(document_ids) == 1:
            # Single document - use single log
            ChatbotActivityService.log_document_uploaded(
                document_id=document_ids[0],
                filename=filenames[0] if filenames else 'unknown',
                username=username,
                collection_id=collection_id,
                collection_name=collection_name,
                file_size_bytes=total_size
            )
        elif len(document_ids) > 1:
            # Multiple documents - use batch log
            ChatbotActivityService.log_documents_uploaded(
                document_ids=document_ids,
                filenames=filenames,
                username=username,
                collection_id=collection_id,
                collection_name=collection_name,
                total_size_bytes=total_size
            )

    return jsonify(result), 201


@rag_document_bp.route('/documents/<int:document_id>', methods=['PUT'])
@require_permission('feature:rag:edit')
@handle_api_errors(logger_name='rag')
def update_document(document_id):
    """Update document metadata"""
    data = request.get_json()
    username = AuthUtils.extract_username_without_validation()
    success, error, document = DocumentService.update_document(document_id, data, username=username)

    if not success:
        if error == 'Document not found':
            raise NotFoundError(error)
        if error == 'Forbidden':
            raise ForbiddenError('Keine Berechtigung für dieses Dokument')
        else:
            raise ValidationError(error)

    return jsonify({
        'success': True,
        'message': f"Document '{document.filename}' updated successfully"
    }), 200


@rag_document_bp.route('/documents/<int:document_id>', methods=['DELETE'])
@require_permission('feature:rag:delete')
@handle_api_errors(logger_name='rag')
def delete_document(document_id):
    """Delete document and its file"""
    # Get document first for the filename
    username = AuthUtils.extract_username_without_validation()
    document = DocumentService.get_document_by_id(document_id)
    if not document:
        raise NotFoundError(f'Document with ID {document_id} not found')
    if not RAGAccessService.can_delete_document(username, document):
        raise ForbiddenError('Keine Berechtigung für dieses Dokument')

    # Store info before deletion
    filename = document.original_filename or document.filename
    collection_id = document.collection_id

    # Delete document using service
    success, error = DocumentService.delete_document(document_id, username=username)

    if not success:
        if error == 'Forbidden':
            raise ForbiddenError('Keine Berechtigung für dieses Dokument')
        raise ValidationError(error)

    # Log activity
    ChatbotActivityService.log_document_deleted(
        document_id=document_id,
        filename=filename,
        username=username,
        collection_id=collection_id
    )

    return jsonify({
        'success': True,
        'message': f"Document '{filename}' deleted successfully"
    }), 200


@rag_document_bp.route('/documents/<int:document_id>/screenshot', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_document_screenshot(document_id):
    """Get screenshot image for a document"""
    username = AuthUtils.extract_username_without_validation()
    document = DocumentService.get_document_by_id(document_id, username=username, access='view')
    if not document:
        raise NotFoundError(f'Document with ID {document_id} not found')

    if not document.screenshot_path:
        raise NotFoundError('No screenshot available for this document')

    if not os.path.exists(document.screenshot_path):
        raise NotFoundError('Screenshot file not found on disk')

    return send_file(
        document.screenshot_path,
        mimetype='image/png'
    )


@rag_document_bp.route('/chunks/<int:chunk_id>/image', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_chunk_image(chunk_id):
    """Get image for a chunk"""
    from db.models.rag import RAGDocumentChunk

    chunk = RAGDocumentChunk.query.get(chunk_id)
    if not chunk:
        raise NotFoundError(f'Chunk with ID {chunk_id} not found')
    username = AuthUtils.extract_username_without_validation()
    if not RAGAccessService.can_view_document(username, chunk.document):
        raise ForbiddenError('Keine Berechtigung für dieses Dokument')

    if not chunk.image_path:
        raise NotFoundError('No image available for this chunk')

    if not os.path.exists(chunk.image_path):
        raise NotFoundError('Image file not found on disk')

    return send_file(
        chunk.image_path,
        mimetype=chunk.image_mime_type or 'image/png'
    )


@rag_document_bp.route('/documents/<int:document_id>/access', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_document_access(document_id):
    """Get document access assignments (owner/admin)."""
    username = AuthUtils.extract_username_without_validation()
    document = DocumentService.get_document_by_id(document_id)
    if not document:
        raise NotFoundError(f'Document with ID {document_id} not found')
    if not RAGAccessService.can_share_document(username, document):
        raise ForbiddenError('Keine Berechtigung für dieses Dokument')

    access = RAGAccessService.get_document_permissions(document_id)
    return jsonify({'success': True, 'document_id': document_id, **access}), 200


@rag_document_bp.route('/documents/<int:document_id>/access', methods=['PUT'])
@require_permission('feature:rag:share')
@handle_api_errors(logger_name='rag')
def set_document_access(document_id):
    """Replace document access assignments (owner/admin)."""
    username = AuthUtils.extract_username_without_validation()
    document = DocumentService.get_document_by_id(document_id)
    if not document:
        raise NotFoundError(f'Document with ID {document_id} not found')
    if not RAGAccessService.can_share_document(username, document):
        raise ForbiddenError('Keine Berechtigung für dieses Dokument')

    data = request.get_json() or {}
    usernames = data.get('usernames') or data.get('users') or []
    role_names = data.get('role_names') or data.get('roles') or []
    access = data.get('access') or {}

    result = RAGAccessService.set_document_permissions(
        document_id=document_id,
        usernames=usernames,
        role_names=role_names,
        granted_by=username,
        access=access
    )
    return jsonify({'success': True, 'document_id': document_id, **result}), 200
