"""
DocumentService

Handles all database operations for RAG documents.
Separates business logic from HTTP handling in routes.
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import os
import hashlib
import uuid
import logging

from db.database import db
from db.models.rag import (
    RAGDocument,
    RAGDocumentChunk,
    RAGCollection,
    RAGProcessingQueue,
    CollectionDocumentLink
)
from sqlalchemy import desc, or_

logger = logging.getLogger(__name__)

# File upload configuration
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md', 'docx', 'doc'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
RAG_DOCS_PATH = '/app/data/rag/uploads'


class DocumentService:
    """Service for managing RAG documents"""

    @staticmethod
    def allowed_file(filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @staticmethod
    def get_file_hash(file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @staticmethod
    def get_mime_type(extension: str) -> str:
        """Get MIME type for file extension"""
        mime_types = {
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'md': 'text/markdown',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'doc': 'application/msword'
        }
        return mime_types.get(extension.lower(), 'application/octet-stream')

    @staticmethod
    def get_documents(
        collection_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
        username: Optional[str] = None
    ) -> Tuple[List[RAGDocument], Dict[str, Any]]:
        """
        Get all documents with optional filters.

        Returns:
            Tuple of (documents list, pagination dict)
        """
        query = RAGDocument.query
        if username:
            from services.rag.access_service import RAGAccessService
            query = RAGAccessService.apply_document_access_filter(query, username, access='view')

        # Apply filters
        if collection_id:
            query = query.filter_by(collection_id=collection_id)
        if status:
            query = query.filter_by(status=status)
        if search:
            query = query.filter(
                or_(
                    RAGDocument.filename.ilike(f'%{search}%'),
                    RAGDocument.title.ilike(f'%{search}%'),
                    RAGDocument.description.ilike(f'%{search}%')
                )
            )

        # Order by upload date (newest first)
        query = query.order_by(desc(RAGDocument.uploaded_at))

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        pagination_info = {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }

        return pagination.items, pagination_info

    @staticmethod
    def get_document_by_id(document_id: int, username: Optional[str] = None, access: str = 'view') -> Optional[RAGDocument]:
        """Get a single document by ID, optionally enforcing access."""
        document = RAGDocument.query.get(document_id)
        if not document or not username:
            return document
        from services.rag.access_service import RAGAccessService
        if access == 'edit' and not RAGAccessService.can_edit_document(username, document):
            return None
        if access == 'delete' and not RAGAccessService.can_delete_document(username, document):
            return None
        if access == 'share' and not RAGAccessService.can_share_document(username, document):
            return None
        if access == 'view' and not RAGAccessService.can_view_document(username, document):
            return None
        return document

    @staticmethod
    def get_document_content(document_id: int, username: Optional[str] = None) -> Tuple[Optional[RAGDocument], str]:
        """
        Get document with its full text content from chunks.

        Returns:
            Tuple of (document, content_text)
        """
        document = DocumentService.get_document_by_id(document_id, username=username, access='view')
        if not document:
            return None, ""

        # Get all chunks ordered by index
        chunks = RAGDocumentChunk.query.filter_by(
            document_id=document_id
        ).order_by(RAGDocumentChunk.chunk_index).all()

        # Combine chunk content
        full_content = "\n\n".join([c.content for c in chunks])

        # If no chunks, check processing status
        if not full_content and document.status != 'indexed':
            full_content = "[Dokument wurde noch nicht verarbeitet. Bitte warten Sie, bis die Indexierung abgeschlossen ist.]"

        return document, full_content

    @staticmethod
    def get_document_chunks(document_id: int, username: Optional[str] = None) -> Tuple[Optional[RAGDocument], List[RAGDocumentChunk]]:
        """
        Get document with all its chunks.

        Returns:
            Tuple of (document, chunks_list)
        """
        document = DocumentService.get_document_by_id(document_id, username=username, access='view')
        if not document:
            return None, []

        chunks = RAGDocumentChunk.query.filter_by(
            document_id=document_id
        ).order_by(RAGDocumentChunk.chunk_index).all()

        return document, chunks

    @staticmethod
    def check_file_duplicate(file_hash: str) -> Optional[RAGDocument]:
        """Check if a file with the same hash already exists"""
        return RAGDocument.query.filter_by(file_hash=file_hash).first()

    @staticmethod
    def get_default_collection() -> Optional[RAGCollection]:
        """Get the default 'general' collection"""
        return RAGCollection.query.filter_by(name='general').first()

    @staticmethod
    def create_document(
        file: FileStorage,
        uploaded_by: str,
        collection_id: Optional[int] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        author: Optional[str] = None,
        language: str = 'de'
    ) -> Dict[str, Any]:
        """
        Create a new document from uploaded file.

        Returns:
            Dict with 'success', 'document', 'error' keys
        """
        try:
            # Validate file
            if not file or file.filename == '':
                return {'success': False, 'error': 'No file provided'}

            if not DocumentService.allowed_file(file.filename):
                return {
                    'success': False,
                    'error': f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
                }

            # Check file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning

            if file_size > MAX_FILE_SIZE:
                return {
                    'success': False,
                    'error': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)} MB'
                }

            # Ensure RAG docs directory exists
            os.makedirs(RAG_DOCS_PATH, exist_ok=True)

            # Generate unique filename
            original_filename = secure_filename(file.filename)
            ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
            file_path = os.path.join(RAG_DOCS_PATH, unique_filename)

            # Save file temporarily to calculate hash
            file.save(file_path)
            file_hash = DocumentService.get_file_hash(file_path)

            # Check for duplicate file
            existing_doc = DocumentService.check_file_duplicate(file_hash)
            if existing_doc:
                # Remove the just uploaded file
                os.remove(file_path)
                return {
                    'success': False,
                    'error': f"Duplicate file detected. This file already exists as '{existing_doc.filename}'",
                    'existing_document_id': existing_doc.id
                }

            # Get MIME type
            mime_type = DocumentService.get_mime_type(ext)

            # Get default collection if none specified
            if not collection_id:
                default_collection = DocumentService.get_default_collection()
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
                is_public=False,  # Inherit visibility from collection
                uploaded_by=uploaded_by,
                uploaded_at=datetime.now()
            )

            db.session.add(new_doc)
            db.session.flush()  # Get the ID

            # Create collection-document link (n:m relationship)
            if collection_id:
                link = CollectionDocumentLink(
                    collection_id=collection_id,
                    document_id=new_doc.id,
                    link_type='new',
                    linked_at=datetime.now()
                )
                db.session.add(link)

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

            return {
                'success': True,
                'message': f"Document '{original_filename}' uploaded successfully",
                'document': new_doc
            }

        except Exception as e:
            db.session.rollback()
            # Clean up file if it was saved
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            logger.error(f"Error creating document: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def create_multiple_documents(
        files: List[FileStorage],
        uploaded_by: str,
        collection_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create multiple documents from uploaded files.

        Returns:
            Dict with 'success', 'uploaded', 'skipped', 'errors' keys
        """
        # Get default collection if none specified
        if not collection_id:
            default_collection = DocumentService.get_default_collection()
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

            if not DocumentService.allowed_file(file.filename):
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
                file_hash = DocumentService.get_file_hash(file_path)

                # Check for duplicate
                existing_doc = DocumentService.check_file_duplicate(file_hash)
                if existing_doc:
                    os.remove(file_path)
                    results['skipped'].append({
                        'filename': file.filename,
                        'reason': f"Duplicate of '{existing_doc.filename}'"
                    })
                    continue

                # Get MIME type
                mime_type = DocumentService.get_mime_type(ext)

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
                    is_public=False,  # Inherit visibility from collection
                    uploaded_by=uploaded_by,
                    uploaded_at=datetime.now()
                )

                db.session.add(new_doc)
                db.session.flush()

                # Create collection-document link (n:m relationship)
                if collection_id:
                    link = CollectionDocumentLink(
                        collection_id=collection_id,
                        document_id=new_doc.id,
                        link_type='new',
                        linked_at=datetime.now()
                    )
                    db.session.add(link)

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
                    'file_size_bytes': file_size,
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

        # Determine success based on results
        uploaded_count = len(results['uploaded'])
        error_count = len(results['errors'])
        skipped_count = len(results['skipped'])

        # If nothing was uploaded and there were errors, it's a failure
        if uploaded_count == 0 and error_count > 0:
            error_messages = [f"{e['filename']}: {e['error']}" for e in results['errors']]
            return {
                'success': False,
                'message': f"Upload fehlgeschlagen: {'; '.join(error_messages)}",
                'error': results['errors'][0]['error'] if results['errors'] else 'Unbekannter Fehler',
                'results': results
            }

        # Partial success - some uploaded, some failed
        if uploaded_count > 0 and (error_count > 0 or skipped_count > 0):
            return {
                'success': True,
                'message': f"{uploaded_count} Dokument(e) hochgeladen, {skipped_count} übersprungen, {error_count} Fehler",
                'results': results
            }

        # Full success
        return {
            'success': True,
            'message': f"{uploaded_count} Dokument(e) erfolgreich hochgeladen",
            'results': results
        }

    @staticmethod
    def update_document(
        document_id: int,
        data: Dict[str, Any],
        username: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[RAGDocument]]:
        """
        Update document metadata.

        Returns:
            Tuple of (success, error_message, document)
        """
        try:
            document = RAGDocument.query.get(document_id)
            if not document:
                return False, 'Document not found', None
            if username:
                from services.rag.access_service import RAGAccessService
                if not RAGAccessService.can_edit_document(username, document):
                    return False, 'Forbidden', None

            if username and 'collection_id' in data and data.get('collection_id'):
                from services.rag.access_service import RAGAccessService
                collection = RAGCollection.query.get(data.get('collection_id'))
                if collection and not RAGAccessService.can_edit_collection(username, collection):
                    return False, 'Forbidden', None

            # Update allowed fields
            allowed_fields = ['title', 'description', 'author', 'language', 'keywords', 'collection_id', 'is_public']
            for field in allowed_fields:
                if field in data:
                    setattr(document, field, data[field])

            document.updated_at = datetime.now()
            db.session.commit()

            try:
                from services.chatbot.lexical_index import LexicalSearchIndex
                LexicalSearchIndex.reindex_document(document.id)
            except Exception as exc:
                logger.warning(f"[DocumentService] Lexical index update failed for doc {document.id}: {exc}")

            return True, None, document

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating document {document_id}: {str(e)}")
            return False, str(e), None

    @staticmethod
    def delete_document(document_id: int, username: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Delete document and its file.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            document = RAGDocument.query.get(document_id)
            if not document:
                return False, 'Document not found'
            if username:
                from services.rag.access_service import RAGAccessService
                if not RAGAccessService.can_delete_document(username, document):
                    return False, 'Forbidden'

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

            try:
                from services.chatbot.lexical_index import LexicalSearchIndex
                LexicalSearchIndex.remove_document(document_id)
            except Exception as exc:
                logger.warning(f"[DocumentService] Lexical index removal failed for doc {document_id}: {exc}")

            return True, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False, str(e)

    @staticmethod
    def serialize_document(document: RAGDocument, include_details: bool = False) -> Dict[str, Any]:
        """
        Serialize document to JSON-compatible dict.

        Args:
            document: The document to serialize
            include_details: Include extended details (for single document view)
        """
        base_data = {
            'id': document.id,
            'filename': document.filename,
            'title': document.title,
            'description': document.description,
            'file_size_bytes': document.file_size_bytes,
            'file_size_mb': round(document.file_size_bytes / (1024*1024), 2),
            'mime_type': document.mime_type,
            'status': document.status,
            'collection_id': document.collection_id,
            'collection_name': document.collection.display_name if document.collection else None,
            'chunk_count': document.chunk_count,
            'retrieval_count': document.retrieval_count,
            'avg_relevance_score': document.avg_relevance_score,
            'language': document.language,
            'author': document.author,
            'uploaded_by': document.uploaded_by,
            'uploaded_at': document.uploaded_at.isoformat() if document.uploaded_at else None,
            'indexed_at': document.indexed_at.isoformat() if document.indexed_at else None,
            'last_retrieved_at': document.last_retrieved_at.isoformat() if document.last_retrieved_at else None
        }

        if include_details:
            screenshot_url = document.screenshot_url
            if document.screenshot_path and not screenshot_url:
                screenshot_url = f"/api/rag/documents/{document.id}/screenshot"

            base_data.update({
                'original_filename': document.original_filename,
                'keywords': document.keywords,
                'file_path': document.file_path,
                'file_hash': document.file_hash,
                'processing_error': document.processing_error,
                'embedding_model': document.embedding_model,
                'is_public': document.is_public,
                'processed_at': document.processed_at.isoformat() if document.processed_at else None,
                'archived_at': document.archived_at.isoformat() if document.archived_at else None,
                # Screenshot info for web-crawled documents
                'screenshot_path': document.screenshot_path,
                'screenshot_url': screenshot_url,
                'has_screenshot': bool(document.screenshot_path),
                # Source URL for web-crawled documents
                'source_url': document.source_url
            })

        return base_data

    @staticmethod
    def serialize_chunk(chunk: RAGDocumentChunk) -> Dict[str, Any]:
        """Serialize chunk to JSON-compatible dict"""
        return {
            'id': chunk.id,
            'chunk_index': chunk.chunk_index,
            'content': chunk.content,
            'page_number': chunk.page_number,
            'start_char': chunk.start_char,
            'end_char': chunk.end_char,
            'retrieval_count': chunk.retrieval_count,
            'avg_relevance_score': chunk.avg_relevance_score,
            'last_retrieved_at': chunk.last_retrieved_at.isoformat() if chunk.last_retrieved_at else None,
            # Image info for chunks with embedded images
            'has_image': chunk.has_image,
            'image_path': chunk.image_path,
            'image_url': chunk.image_url,
            'image_alt_text': chunk.image_alt_text,
            'image_mime_type': chunk.image_mime_type
        }
