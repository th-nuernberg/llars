"""RAG (Retrieval-Augmented Generation) database models."""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from db import db


class RAGCollection(db.Model):
    """Collections for organizing RAG documents (e.g., General, Specialized, Training)"""
    __tablename__ = 'rag_collections'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)  # Emoji or icon name
    color: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)  # Hex color for UI

    # Configuration
    embedding_model: Mapped[str] = mapped_column(db.String(255), nullable=False, default='sentence-transformers/all-MiniLM-L6-v2')
    chunk_size: Mapped[int] = mapped_column(db.Integer, default=1000)
    chunk_overlap: Mapped[int] = mapped_column(db.Integer, default=200)
    retrieval_k: Mapped[int] = mapped_column(db.Integer, default=4)  # Number of docs to retrieve

    # Statistics
    document_count: Mapped[int] = mapped_column(db.Integer, default=0)
    total_chunks: Mapped[int] = mapped_column(db.Integer, default=0)
    total_size_bytes: Mapped[int] = mapped_column(db.BigInteger, default=0)

    # ChromaDB
    chroma_collection_name: Mapped[Optional[str]] = mapped_column(db.String(255), unique=True, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, index=True)

    # Permissions
    is_public: Mapped[bool] = mapped_column(db.Boolean, default=True)
    created_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    last_indexed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    # Relationships (n:m via CollectionDocumentLink)
    document_links = db.relationship('CollectionDocumentLink', back_populates='collection', cascade='all, delete-orphan')


class CollectionDocumentLink(db.Model):
    """
    Linking table for n:m relationship between Collections and Documents.

    A document can be linked to multiple collections, and a collection can contain
    multiple documents. When the same content (by hash) is found during crawling,
    it is only "linked" to the collection rather than creating a duplicate.

    Link types:
    - 'new': Document was newly created for this collection
    - 'linked': Document already existed and was linked to this collection
    """
    __tablename__ = 'collection_document_links'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    collection_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('rag_collections.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    document_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('rag_documents.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Link type: 'new' (newly created) or 'linked' (already existed)
    link_type: Mapped[str] = mapped_column(
        db.String(20),
        default='new',
        nullable=False
    )

    # Source information
    source_url: Mapped[Optional[str]] = mapped_column(db.String(2048), nullable=True)
    crawl_job_id: Mapped[Optional[str]] = mapped_column(db.String(36), nullable=True, index=True)

    # Timestamps
    linked_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    linked_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    # Relationships
    collection = db.relationship('RAGCollection', back_populates='document_links')
    document = db.relationship('RAGDocument', back_populates='collection_links')

    __table_args__ = (
        db.UniqueConstraint('collection_id', 'document_id', name='unique_collection_document'),
    )


class RAGDocument(db.Model):
    """Documents stored in RAG system with full metadata tracking"""
    __tablename__ = 'rag_documents'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(db.String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(db.String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(db.BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(db.String(100), nullable=False)
    file_hash: Mapped[str] = mapped_column(db.String(64), unique=True, nullable=False, index=True)  # SHA-256

    # Metadata
    title: Mapped[Optional[str]] = mapped_column(db.String(512), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    language: Mapped[str] = mapped_column(db.String(10), default='de')
    keywords: Mapped[Optional[str]] = mapped_column(db.JSON, nullable=True)  # Array of tags

    # Processing Status
    status: Mapped[str] = mapped_column(
        db.String(20),
        default='pending',
        nullable=False,
        index=True
    )  # pending, processing, indexed, failed, archived
    processing_error: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # Collections
    collection_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('rag_collections.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    # Embedding Info
    embedding_model: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    chunk_count: Mapped[int] = mapped_column(db.Integer, default=0)
    vector_ids: Mapped[Optional[str]] = mapped_column(db.JSON, nullable=True)  # Array of ChromaDB vector IDs

    # Statistics
    upload_count: Mapped[int] = mapped_column(db.Integer, default=0)  # Times re-uploaded
    retrieval_count: Mapped[int] = mapped_column(db.Integer, default=0)  # Times retrieved in RAG queries
    last_retrieved_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    avg_relevance_score: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)

    # Permissions
    is_public: Mapped[bool] = mapped_column(db.Boolean, default=True)
    uploaded_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True, index=True)

    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    indexed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    archived_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    # Relationships
    collection = db.relationship('RAGCollection', backref='documents')
    chunks = db.relationship('RAGDocumentChunk', backref='document', cascade='all, delete-orphan')
    versions = db.relationship('RAGDocumentVersion', backref='document', cascade='all, delete-orphan')
    permissions = db.relationship('RAGDocumentPermission', backref='document', cascade='all, delete-orphan')
    # n:m relationship to collections via CollectionDocumentLink
    collection_links = db.relationship('CollectionDocumentLink', back_populates='document', cascade='all, delete-orphan')


class RAGDocumentChunk(db.Model):
    """Individual chunks of documents with their embeddings"""
    __tablename__ = 'rag_document_chunks'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('rag_documents.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    chunk_index: Mapped[int] = mapped_column(db.Integer, nullable=False)

    # Content
    content: Mapped[str] = mapped_column(db.Text, nullable=False)
    content_hash: Mapped[Optional[str]] = mapped_column(db.String(64), nullable=True)  # MD5 of content

    # Metadata
    page_number: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    start_char: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)
    end_char: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    # Vector
    vector_id: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True, index=True)  # ChromaDB vector ID

    # Statistics
    retrieval_count: Mapped[int] = mapped_column(db.Integer, default=0)
    avg_relevance_score: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    last_retrieved_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('document_id', 'chunk_index', name='unique_doc_chunk'),
    )


class RAGDocumentVersion(db.Model):
    """Version history for documents"""
    __tablename__ = 'rag_document_versions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('rag_documents.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    version_number: Mapped[int] = mapped_column(db.Integer, nullable=False)

    # File Info
    file_path: Mapped[str] = mapped_column(db.String(512), nullable=False)
    file_hash: Mapped[str] = mapped_column(db.String(64), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(db.BigInteger, nullable=False)

    # Changes
    change_description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    changed_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('document_id', 'version_number', name='unique_doc_version'),
    )


class RAGRetrievalLog(db.Model):
    """Logs all RAG retrieval queries for analytics"""
    __tablename__ = 'rag_retrieval_logs'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    # Query Info
    query_text: Mapped[str] = mapped_column(db.Text, nullable=False)
    query_hash: Mapped[Optional[str]] = mapped_column(db.String(64), nullable=True, index=True)  # MD5 for caching
    username: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    # Retrieval Info
    collection_id: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        db.ForeignKey('rag_collections.id', ondelete='SET NULL'),
        nullable=True
    )
    retrieved_document_ids: Mapped[Optional[str]] = mapped_column(db.JSON, nullable=True)  # Array of doc IDs
    relevance_scores: Mapped[Optional[str]] = mapped_column(db.JSON, nullable=True)  # Array of scores
    num_results: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    # Performance
    retrieval_time_ms: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    # Feedback (optional)
    user_feedback: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)  # helpful, not_helpful, irrelevant
    feedback_comment: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False, index=True)

    # Relationship
    collection = db.relationship('RAGCollection', backref='retrieval_logs')


class RAGDocumentPermission(db.Model):
    """Granular permissions for individual documents"""
    __tablename__ = 'rag_document_permissions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('rag_documents.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Permission Type
    permission_type: Mapped[str] = mapped_column(db.String(20), nullable=False)  # user, role
    target_identifier: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)  # username or role_name

    # Access Level
    can_view: Mapped[bool] = mapped_column(db.Boolean, default=True)
    can_edit: Mapped[bool] = mapped_column(db.Boolean, default=False)
    can_delete: Mapped[bool] = mapped_column(db.Boolean, default=False)
    can_share: Mapped[bool] = mapped_column(db.Boolean, default=False)

    # Granted By
    granted_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('document_id', 'permission_type', 'target_identifier', name='unique_doc_permission'),
    )


class RAGProcessingQueue(db.Model):
    """Queue for background document processing"""
    __tablename__ = 'rag_processing_queue'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('rag_documents.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Processing Info
    priority: Mapped[int] = mapped_column(db.Integer, default=0, index=True)  # Higher = more urgent
    status: Mapped[str] = mapped_column(db.String(20), default='queued', nullable=False, index=True)  # queued, processing, completed, failed

    # Worker Info
    worker_id: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    # Progress
    progress_percent: Mapped[int] = mapped_column(db.Integer, default=0)
    current_step: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    # Error Handling
    error_message: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(db.Integer, default=0)
    max_retries: Mapped[int] = mapped_column(db.Integer, default=3)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship
    document = db.relationship('RAGDocument', backref='processing_queue')
