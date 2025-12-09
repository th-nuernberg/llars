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
    handle_api_errors, NotFoundError, ValidationError, ConflictError
)
from auth.auth_utils import AuthUtils
from services.rag.document_service import DocumentService

rag_document_bp = Blueprint('rag_document', __name__)


@rag_document_bp.route('/documents', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_documents():
    """Get all documents with optional filters"""
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
        per_page=per_page
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
    document = DocumentService.get_document_by_id(document_id)
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
    document, full_content = DocumentService.get_document_content(document_id)
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
    document, chunks = DocumentService.get_document_chunks(document_id)
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
    document = DocumentService.get_document_by_id(document_id)
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

    return jsonify(result), 201


@rag_document_bp.route('/documents/<int:document_id>', methods=['PUT'])
@require_permission('feature:rag:edit')
@handle_api_errors(logger_name='rag')
def update_document(document_id):
    """Update document metadata"""
    data = request.get_json()
    success, error, document = DocumentService.update_document(document_id, data)

    if not success:
        if error == 'Document not found':
            raise NotFoundError(error)
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
    document = DocumentService.get_document_by_id(document_id)
    if not document:
        raise NotFoundError(f'Document with ID {document_id} not found')

    filename = document.filename

    # Delete document using service
    success, error = DocumentService.delete_document(document_id)

    if not success:
        raise ValidationError(error)

    return jsonify({
        'success': True,
        'message': f"Document '{filename}' deleted successfully"
    }), 200


@rag_document_bp.route('/documents/<int:document_id>/screenshot', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='rag')
def get_document_screenshot(document_id):
    """Get screenshot image for a document"""
    document = DocumentService.get_document_by_id(document_id)
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

    if not chunk.image_path:
        raise NotFoundError('No image available for this chunk')

    if not os.path.exists(chunk.image_path):
        raise NotFoundError('Image file not found on disk')

    return send_file(
        chunk.image_path,
        mimetype=chunk.image_mime_type or 'image/png'
    )
