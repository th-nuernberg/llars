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
from datetime import datetime
from werkzeug.utils import secure_filename
import jwt
import os
import hashlib
import uuid
from decorators.permission_decorator import require_permission
from db.tables import (
    RAGCollection, RAGDocument, RAGDocumentChunk,
    RAGProcessingQueue
)
from db.db import db
from sqlalchemy import desc

rag_document_bp = Blueprint('rag_document', __name__)

# File upload configuration
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md', 'docx', 'doc'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
RAG_DOCS_PATH = '/app/rag_docs'


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_hash(file_path):
    """Calculate SHA-256 hash of file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


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

        # Build query
        query = RAGDocument.query

        if collection_id:
            query = query.filter_by(collection_id=collection_id)
        if status:
            query = query.filter_by(status=status)
        if search:
            query = query.filter(
                db.or_(
                    RAGDocument.filename.ilike(f'%{search}%'),
                    RAGDocument.title.ilike(f'%{search}%'),
                    RAGDocument.description.ilike(f'%{search}%')
                )
            )

        # Order by upload date (newest first)
        query = query.order_by(desc(RAGDocument.uploaded_at))

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        documents = pagination.items

        return jsonify({
            'success': True,
            'documents': [{
                'id': d.id,
                'filename': d.filename,
                'title': d.title,
                'description': d.description,
                'file_size_bytes': d.file_size_bytes,
                'file_size_mb': round(d.file_size_bytes / (1024*1024), 2),
                'mime_type': d.mime_type,
                'status': d.status,
                'collection_id': d.collection_id,
                'collection_name': d.collection.display_name if d.collection else None,
                'chunk_count': d.chunk_count,
                'retrieval_count': d.retrieval_count,
                'avg_relevance_score': d.avg_relevance_score,
                'language': d.language,
                'author': d.author,
                'uploaded_by': d.uploaded_by,
                'uploaded_at': d.uploaded_at.isoformat() if d.uploaded_at else None,
                'indexed_at': d.indexed_at.isoformat() if d.indexed_at else None,
                'last_retrieved_at': d.last_retrieved_at.isoformat() if d.last_retrieved_at else None
            } for d in documents],
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in get_documents: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@rag_document_bp.route('/documents/<int:document_id>', methods=['GET'])
@require_permission('feature:rag:view')
def get_document(document_id):
    """Get detailed document information"""
    try:
        document = RAGDocument.query.get_or_404(document_id)

        return jsonify({
            'success': True,
            'document': {
                'id': document.id,
                'filename': document.filename,
                'original_filename': document.original_filename,
                'title': document.title,
                'description': document.description,
                'author': document.author,
                'language': document.language,
                'keywords': document.keywords,
                'file_path': document.file_path,
                'file_size_bytes': document.file_size_bytes,
                'file_size_mb': round(document.file_size_bytes / (1024*1024), 2),
                'file_hash': document.file_hash,
                'mime_type': document.mime_type,
                'status': document.status,
                'processing_error': document.processing_error,
                'collection_id': document.collection_id,
                'collection_name': document.collection.display_name if document.collection else None,
                'embedding_model': document.embedding_model,
                'chunk_count': document.chunk_count,
                'retrieval_count': document.retrieval_count,
                'avg_relevance_score': document.avg_relevance_score,
                'last_retrieved_at': document.last_retrieved_at.isoformat() if document.last_retrieved_at else None,
                'is_public': document.is_public,
                'uploaded_by': document.uploaded_by,
                'uploaded_at': document.uploaded_at.isoformat() if document.uploaded_at else None,
                'processed_at': document.processed_at.isoformat() if document.processed_at else None,
                'indexed_at': document.indexed_at.isoformat() if document.indexed_at else None,
                'archived_at': document.archived_at.isoformat() if document.archived_at else None
            }
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
        document = RAGDocument.query.get_or_404(document_id)

        # Get all chunks ordered by index
        chunks = RAGDocumentChunk.query.filter_by(
            document_id=document_id
        ).order_by(RAGDocumentChunk.chunk_index).all()

        # Combine chunk content
        full_content = "\n\n".join([c.content for c in chunks])

        # If no chunks, try to extract from file directly
        if not full_content and document.status != 'indexed':
            full_content = "[Dokument wurde noch nicht verarbeitet. Bitte warten Sie, bis die Indexierung abgeschlossen ist.]"

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
        document = RAGDocument.query.get_or_404(document_id)
        chunks = RAGDocumentChunk.query.filter_by(
            document_id=document_id
        ).order_by(RAGDocumentChunk.chunk_index).all()

        return jsonify({
            'success': True,
            'document': {
                'id': document.id,
                'filename': document.filename,
                'chunk_count': document.chunk_count
            },
            'chunks': [{
                'id': c.id,
                'chunk_index': c.chunk_index,
                'content': c.content,
                'page_number': c.page_number,
                'start_char': c.start_char,
                'end_char': c.end_char,
                'retrieval_count': c.retrieval_count,
                'avg_relevance_score': c.avg_relevance_score,
                'last_retrieved_at': c.last_retrieved_at.isoformat() if c.last_retrieved_at else None
            } for c in chunks]
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in get_document_chunks: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@rag_document_bp.route('/documents/<int:document_id>/download', methods=['GET'])
@require_permission('feature:rag:view')
def download_document(document_id):
    """Download document file"""
    try:
        document = RAGDocument.query.get_or_404(document_id)

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
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        username = decoded_token.get('preferred_username')

        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400

        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning

        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)} MB'
            }), 400

        # Get additional metadata from form
        collection_id = request.form.get('collection_id', type=int)
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        author = request.form.get('author', '')
        language = request.form.get('language', 'de')

        # Ensure RAG docs directory exists
        os.makedirs(RAG_DOCS_PATH, exist_ok=True)

        # Generate unique filename
        original_filename = secure_filename(file.filename)
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        file_path = os.path.join(RAG_DOCS_PATH, unique_filename)

        # Save file temporarily to calculate hash
        file.save(file_path)
        file_hash = get_file_hash(file_path)

        # Check for duplicate file
        existing_doc = RAGDocument.query.filter_by(file_hash=file_hash).first()
        if existing_doc:
            # Remove the just uploaded file
            os.remove(file_path)
            return jsonify({
                'success': False,
                'error': f"Duplicate file detected. This file already exists as '{existing_doc.filename}'",
                'existing_document_id': existing_doc.id
            }), 409

        # Determine MIME type
        mime_types = {
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'md': 'text/markdown',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'doc': 'application/msword'
        }
        mime_type = mime_types.get(ext, 'application/octet-stream')

        # Get default collection if none specified
        if not collection_id:
            default_collection = RAGCollection.query.filter_by(name='general').first()
            if default_collection:
                collection_id = default_collection.id

        # Create document entry
        new_doc = RAGDocument(
            filename=unique_filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size_bytes=file_size,
            mime_type=mime_type,
            file_hash=file_hash,
            title=title or original_filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' '),
            description=description,
            author=author,
            language=language,
            status='pending',  # Will be processed by background job
            collection_id=collection_id,
            is_public=True,
            uploaded_by=username,
            uploaded_at=datetime.now()
        )

        db.session.add(new_doc)
        db.session.flush()  # Get the ID

        # Add to processing queue
        queue_entry = RAGProcessingQueue(
            document_id=new_doc.id,
            priority=5,  # Normal priority
            status='queued',
            created_at=datetime.now()
        )
        db.session.add(queue_entry)

        # Update collection statistics
        if new_doc.collection:
            new_doc.collection.document_count += 1
            new_doc.collection.total_size_bytes += file_size

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f"Document '{original_filename}' uploaded successfully",
            'document': {
                'id': new_doc.id,
                'filename': new_doc.filename,
                'original_filename': new_doc.original_filename,
                'file_size_mb': round(file_size / (1024*1024), 2),
                'status': new_doc.status,
                'collection_id': new_doc.collection_id
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        # Clean up file if it was saved
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        current_app.logger.error(f"Error in upload_document: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@rag_document_bp.route('/documents/upload-multiple', methods=['POST'])
@require_permission('feature:rag:edit')
def upload_multiple_documents():
    """Upload multiple documents at once"""
    try:
        # Get username from token
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        username = decoded_token.get('preferred_username')

        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No files provided'
            }), 400

        files = request.files.getlist('files')
        collection_id = request.form.get('collection_id', type=int)

        # Get default collection if none specified
        if not collection_id:
            default_collection = RAGCollection.query.filter_by(name='general').first()
            if default_collection:
                collection_id = default_collection.id

        os.makedirs(RAG_DOCS_PATH, exist_ok=True)

        results = {
            'uploaded': [],
            'skipped': [],
            'errors': []
        }

        for file in files:
            if file.filename == '':
                continue

            if not allowed_file(file.filename):
                results['errors'].append({
                    'filename': file.filename,
                    'error': 'File type not allowed'
                })
                continue

            try:
                # Check file size
                file.seek(0, 2)
                file_size = file.tell()
                file.seek(0)

                if file_size > MAX_FILE_SIZE:
                    results['errors'].append({
                        'filename': file.filename,
                        'error': f'File too large (max {MAX_FILE_SIZE // (1024*1024)} MB)'
                    })
                    continue

                # Generate unique filename
                original_filename = secure_filename(file.filename)
                ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
                unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
                file_path = os.path.join(RAG_DOCS_PATH, unique_filename)

                # Save and hash
                file.save(file_path)
                file_hash = get_file_hash(file_path)

                # Check for duplicate
                existing_doc = RAGDocument.query.filter_by(file_hash=file_hash).first()
                if existing_doc:
                    os.remove(file_path)
                    results['skipped'].append({
                        'filename': file.filename,
                        'reason': f"Duplicate of '{existing_doc.filename}'"
                    })
                    continue

                # Determine MIME type
                mime_types = {
                    'pdf': 'application/pdf',
                    'txt': 'text/plain',
                    'md': 'text/markdown',
                    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'doc': 'application/msword'
                }
                mime_type = mime_types.get(ext, 'application/octet-stream')

                # Create document
                new_doc = RAGDocument(
                    filename=unique_filename,
                    original_filename=original_filename,
                    file_path=file_path,
                    file_size_bytes=file_size,
                    mime_type=mime_type,
                    file_hash=file_hash,
                    title=original_filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' '),
                    language='de',
                    status='pending',
                    collection_id=collection_id,
                    is_public=True,
                    uploaded_by=username,
                    uploaded_at=datetime.now()
                )

                db.session.add(new_doc)
                db.session.flush()

                # Add to processing queue
                queue_entry = RAGProcessingQueue(
                    document_id=new_doc.id,
                    priority=5,
                    status='queued',
                    created_at=datetime.now()
                )
                db.session.add(queue_entry)

                results['uploaded'].append({
                    'id': new_doc.id,
                    'filename': original_filename,
                    'file_size_mb': round(file_size / (1024*1024), 2)
                })

            except Exception as e:
                results['errors'].append({
                    'filename': file.filename,
                    'error': str(e)
                })

        # Update collection statistics
        if collection_id and results['uploaded']:
            collection = RAGCollection.query.get(collection_id)
            if collection:
                collection.document_count += len(results['uploaded'])
                total_size = sum(d['file_size_mb'] * 1024 * 1024 for d in results['uploaded'])
                collection.total_size_bytes += int(total_size)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f"Uploaded {len(results['uploaded'])} documents",
            'results': results
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in upload_multiple_documents: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@rag_document_bp.route('/documents/<int:document_id>', methods=['PUT'])
@require_permission('feature:rag:edit')
def update_document(document_id):
    """Update document metadata"""
    try:
        document = RAGDocument.query.get_or_404(document_id)
        data = request.get_json()

        # Update allowed fields
        if 'title' in data:
            document.title = data['title']
        if 'description' in data:
            document.description = data['description']
        if 'author' in data:
            document.author = data['author']
        if 'language' in data:
            document.language = data['language']
        if 'keywords' in data:
            document.keywords = data['keywords']
        if 'collection_id' in data:
            document.collection_id = data['collection_id']
        if 'is_public' in data:
            document.is_public = data['is_public']

        document.updated_at = datetime.now()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f"Document '{document.filename}' updated successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in update_document: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@rag_document_bp.route('/documents/<int:document_id>', methods=['DELETE'])
@require_permission('feature:rag:delete')
def delete_document(document_id):
    """Delete document and its file"""
    try:
        document = RAGDocument.query.get_or_404(document_id)

        # Delete file from filesystem
        if os.path.exists(document.file_path):
            os.remove(document.file_path)

        # Update collection statistics
        if document.collection:
            document.collection.document_count -= 1
            document.collection.total_size_bytes -= document.file_size_bytes

        # Database will cascade delete chunks, versions, permissions, queue entries
        db.session.delete(document)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f"Document '{document.filename}' deleted successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in delete_document: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
