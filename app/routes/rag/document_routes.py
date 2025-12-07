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
from auth.auth_utils import AuthUtils
from services.rag.document_service import DocumentService

rag_document_bp = Blueprint('rag_document', __name__)


@rag_document_bp.route('/documents', methods=['GET'])
@require_permission('feature:rag:view')
def get_documents():
    """Get all documents with optional filters"""
    try:
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

    except Exception as e:
        current_app.logger.error(f"Error in get_documents: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@rag_document_bp.route('/documents/<int:document_id>', methods=['GET'])
@require_permission('feature:rag:view')
def get_document(document_id):
    """Get detailed document information"""
    try:
        document = DocumentService.get_document_by_id(document_id)
        if not document:
            return jsonify({'success': False, 'error': 'Document not found'}), 404

        return jsonify({
            'success': True,
            'document': DocumentService.serialize_document(document, include_details=True)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in get_document: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@rag_document_bp.route('/documents/<int:document_id>/content', methods=['GET'])
@require_permission('feature:rag:view')
def get_document_content(document_id):
    """
    Get the extracted text content of a document.
    Returns the combined text from all chunks.
    """
    try:
        document, full_content = DocumentService.get_document_content(document_id)
        if not document:
            return jsonify({'success': False, 'error': 'Document not found'}), 404

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

    except Exception as e:
        current_app.logger.error(f"Error in get_document_content: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@rag_document_bp.route('/documents/<int:document_id>/chunks', methods=['GET'])
@require_permission('feature:rag:view')
def get_document_chunks(document_id):
    """Get all chunks for a document"""
    try:
        document, chunks = DocumentService.get_document_chunks(document_id)
        if not document:
            return jsonify({'success': False, 'error': 'Document not found'}), 404

        return jsonify({
            'success': True,
            'document': {
                'id': document.id,
                'filename': document.filename,
                'chunk_count': document.chunk_count
            },
            'chunks': [DocumentService.serialize_chunk(c) for c in chunks]
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in get_document_chunks: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@rag_document_bp.route('/documents/<int:document_id>/download', methods=['GET'])
@require_permission('feature:rag:view')
def download_document(document_id):
    """Download document file"""
    try:
        document = DocumentService.get_document_by_id(document_id)
        if not document:
            return jsonify({'success': False, 'error': 'Document not found'}), 404

        if not os.path.exists(document.file_path):
            return jsonify({
                'success': False,
                'error': 'Document file not found on disk'
            }), 404

        return send_file(
            document.file_path,
            as_attachment=True,
            download_name=document.original_filename,
            mimetype=document.mime_type
        )

    except Exception as e:
        current_app.logger.error(f"Error in download_document: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@rag_document_bp.route('/documents/upload', methods=['POST'])
@require_permission('feature:rag:edit')
def upload_document():
    """Upload new document to RAG system"""
    try:
        # Get username from token
        username = AuthUtils.extract_username_without_validation()

        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

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
            status_code = 409 if 'existing_document_id' in result else 400
            return jsonify(result), status_code

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

    except Exception as e:
        current_app.logger.error(f"Error in upload_document: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@rag_document_bp.route('/documents/upload-multiple', methods=['POST'])
@require_permission('feature:rag:edit')
def upload_multiple_documents():
    """Upload multiple documents at once"""
    try:
        # Get username from token
        username = AuthUtils.extract_username_without_validation()

        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'No files provided'}), 400

        files = request.files.getlist('files')
        collection_id = request.form.get('collection_id', type=int)

        # Upload documents using service
        result = DocumentService.create_multiple_documents(
            files=files,
            uploaded_by=username,
            collection_id=collection_id
        )

        return jsonify(result), 201

    except Exception as e:
        current_app.logger.error(f"Error in upload_multiple_documents: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@rag_document_bp.route('/documents/<int:document_id>', methods=['PUT'])
@require_permission('feature:rag:edit')
def update_document(document_id):
    """Update document metadata"""
    try:
        data = request.get_json()
        success, error, document = DocumentService.update_document(document_id, data)

        if not success:
            status_code = 404 if error == 'Document not found' else 500
            return jsonify({'success': False, 'error': error}), status_code

        return jsonify({
            'success': True,
            'message': f"Document '{document.filename}' updated successfully"
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in update_document: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@rag_document_bp.route('/documents/<int:document_id>', methods=['DELETE'])
@require_permission('feature:rag:delete')
def delete_document(document_id):
    """Delete document and its file"""
    try:
        # Get document first for the filename
        document = DocumentService.get_document_by_id(document_id)
        if not document:
            return jsonify({'success': False, 'error': 'Document not found'}), 404

        filename = document.filename

        # Delete document using service
        success, error = DocumentService.delete_document(document_id)

        if not success:
            return jsonify({'success': False, 'error': error}), 500

        return jsonify({
            'success': True,
            'message': f"Document '{filename}' deleted successfully"
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in delete_document: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
