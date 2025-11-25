#tables.py
import json
from typing import Optional
from unittest.mock import DEFAULT

from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from enum import Enum

class UserGroup(db.Model):
    __tablename__ = 'user_groups'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(255), unique=True)

class User(db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(db.String(255))
    password_hash: Mapped[str] = mapped_column(db.String(255))
    api_key: Mapped[str] = mapped_column(db.String(36), unique=True)
    group_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('user_groups.id'), default=1)  # Default-Wert 1

    group = db.relationship('UserGroup', backref='users')


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class FeatureFunctionType(db.Model):
    __tablename__ = 'feature_function_types'
    function_type_id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    name = mapped_column(db.String(255), unique=True)


class EmailThread(db.Model):
    __tablename__ = 'email_threads'
    thread_id = mapped_column(db.Integer, primary_key=True)
    chat_id = mapped_column(db.Integer)
    institut_id = mapped_column(db.Integer)
    subject = mapped_column(db.String(255))
    sender = mapped_column(db.String(255))  # Neues Feld für den Sender
    function_type_id = mapped_column(db.Integer, db.ForeignKey('feature_function_types.function_type_id'))

    messages = db.relationship('Message', backref='email_thread')
    features = db.relationship('Feature', backref='email_thread')
    function_type = db.relationship('FeatureFunctionType', backref='email_threads')

    __table_args__ = (
        db.UniqueConstraint('chat_id', 'institut_id', 'function_type_id', name='_chat_institut_function_uc'),
    )


class Message(db.Model):
    __tablename__ = 'messages'
    message_id = mapped_column(db.Integer, primary_key=True)
    thread_id = mapped_column(db.Integer, db.ForeignKey('email_threads.thread_id'))
    sender = mapped_column(db.String(255))
    content = mapped_column(db.TEXT)
    timestamp = mapped_column(db.DateTime)
    generated_by = mapped_column(db.String(255), default="Human")


class LLM(db.Model):
    __tablename__ = 'llms'
    llm_id = mapped_column(db.Integer, primary_key=True)
    name = mapped_column(db.String(255), unique=True)


class FeatureType(db.Model):
    __tablename__ = 'feature_types'
    type_id = mapped_column(db.Integer, primary_key=True)
    name = mapped_column(db.String(255), unique=True)


class ConsultingCategoryType(db.Model):
    __tablename__ = 'consulting_category_types'
    id = mapped_column(db.Integer, primary_key=True)
    name = mapped_column(db.String(255), unique=True)
    description = mapped_column(db.String(255))


class UserConsultingCategorySelection(db.Model):
    __tablename__ = 'user_consulting_category_selection'
    id = mapped_column(db.Integer, primary_key=True)
    user_id = mapped_column(db.Integer, db.ForeignKey('users.id'))
    thread_id = mapped_column(db.Integer, db.ForeignKey('email_threads.thread_id'))
    consulting_category_type_id = mapped_column(db.Integer, db.ForeignKey('consulting_category_types.id'))
    notes = mapped_column(db.String(255))
    timestamp = mapped_column(db.DateTime, default=datetime.utcnow)


class Feature(db.Model):
    __tablename__ = 'features'
    feature_id = mapped_column(db.Integer, primary_key=True)
    thread_id = mapped_column(db.Integer, db.ForeignKey('email_threads.thread_id'))
    type_id = mapped_column(db.Integer, db.ForeignKey('feature_types.type_id'))
    llm_id = mapped_column(db.Integer, db.ForeignKey('llms.llm_id'))
    content = mapped_column(db.TEXT)

    feature_type = db.relationship('FeatureType', backref='features')
    llm = db.relationship('LLM', backref='features')


class UserFeatureRanking(db.Model):
    __tablename__ = 'user_feature_rankings'
    ranking_id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(db.Integer, db.ForeignKey('users.id'))
    feature_id = mapped_column(db.Integer, db.ForeignKey('features.feature_id'))
    ranking_content = mapped_column(db.Float)
    type_id = mapped_column(db.Integer, db.ForeignKey('feature_types.type_id'))  # Neuer Typ
    llm_id = mapped_column(db.Integer, db.ForeignKey('llms.llm_id'))
    bucket = mapped_column(db.String(20))  # Neuer Bucket (z.B. 'Gut', 'Mittel', 'Schlecht')

    user = db.relationship('User', backref='feature_rankings')
    feature = db.relationship('Feature', backref='user_rankings')
    feature_type = db.relationship('FeatureType', backref='user_rankings')  # Verknüpfung mit dem FeatureType
    llm = db.relationship('LLM', backref='user_rankings')



class UserFeatureRating(db.Model):
    __tablename__ = 'user_feature_ratings'
    rating_id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(db.Integer, db.ForeignKey('users.id'))
    feature_id = mapped_column(db.Integer, db.ForeignKey('features.feature_id'))
    rating_content = mapped_column(db.Float)
    edited_feature = mapped_column(db.TEXT)

    user = db.relationship('User', backref='feature_ratings')
    feature = db.relationship('Feature', backref='user_ratings')

class ScenarioRoles(Enum):
    VIEWER = 'Viewer'
    RATER = 'Rater'

class ProgressionStatus(Enum):
    NOT_STARTED = 'Not Started'
    PROGRESSING = 'Progressing'
    DONE = 'Done'

class RatingScenarios(db.Model):
    __tablename__ = 'rating_scenarios'
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    scenario_name = mapped_column(db.String(255))
    function_type_id = mapped_column(db.Integer, db.ForeignKey('feature_function_types.function_type_id'))
    begin = mapped_column(db.DateTime, default=datetime.utcnow)
    end = mapped_column(db.DateTime, default=datetime.utcnow)
    timestamp = mapped_column(db.DateTime, default=datetime.utcnow)
    # Modellkonfiguration für Comparison-Szenarien
    llm1_model: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    llm2_model: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    # Definiere die Beziehungen mit Cascade-Option
    scenario_users = db.relationship('ScenarioUsers', backref='rating_scenario', cascade="all, delete")
    scenario_threads = db.relationship('ScenarioThreads', backref='rating_scenario', cascade="all, delete")
    scenario_thread_distribution = db.relationship('ScenarioThreadDistribution', backref='rating_scenario', cascade="all, delete")

class ScenarioUsers(db.Model):
    __tablename__ = 'scenario_users'
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    scenario_id = mapped_column(db.Integer, db.ForeignKey('rating_scenarios.id'))
    user_id = mapped_column(db.Integer, db.ForeignKey('users.id'))
    role = mapped_column(db.Enum(ScenarioRoles))
    user = db.relationship('User', backref='scenario_users')

    # Definiere den Unique Constraint für die Kombination von user_id und szenario_id
    __table_args__ = (
        db.UniqueConstraint('user_id', 'scenario_id', name='uix_user_szenario'),
    )

class ScenarioThreads(db.Model):
    __tablename__ = 'scenario_threads'
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    scenario_id = mapped_column(db.Integer, db.ForeignKey('rating_scenarios.id'))
    thread_id = mapped_column(db.Integer, db.ForeignKey('email_threads.thread_id'))
    thread = db.relationship('EmailThread', backref='scenario_threads')

    # Definiere den Unique Constraint für die Kombination von user_id und szenario_id
    __table_args__ = (
        db.UniqueConstraint('thread_id', 'scenario_id', name='uix_thread_szenario'),
    )


class ScenarioThreadDistribution(db.Model):
    __tablename__ = 'scenario_thread_distribution'
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    scenario_id = mapped_column(db.Integer, db.ForeignKey('rating_scenarios.id'))
    scenario_user_id = mapped_column(db.Integer, db.ForeignKey('scenario_users.id'))
    scenario_thread_id = mapped_column(db.Integer, db.ForeignKey('scenario_threads.id'))
    scenario_thread = db.relationship('ScenarioThreads', backref='distributions')
    scenario_user = db.relationship('ScenarioUsers', backref='thread_distributions')



class UserMailHistoryRating(db.Model):
    __tablename__ = 'user_mailhistory_ratings'
    rating_id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(db.Integer, db.ForeignKey('users.id'))
    thread_id = mapped_column(db.Integer, db.ForeignKey('email_threads.thread_id'))
    counsellor_coherence_rating = mapped_column(db.Integer, nullable=True)
    client_coherence_rating = mapped_column(db.Integer, nullable=True)
    quality_rating = mapped_column(db.Integer, nullable=True)
    overall_rating = mapped_column(db.Integer, nullable=True)
    feedback = mapped_column(db.TEXT)  # Optionales Feld für textbasiertes Feedback
    status = mapped_column(db.Enum(ProgressionStatus), default=ProgressionStatus.NOT_STARTED)
    timestamp = mapped_column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='mail_ratings')
    email_thread = db.relationship('EmailThread', backref='mail_ratings')


class UserMessageRating(db.Model):
    __tablename__ = 'user_message_ratings'
    msg_rating_id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(db.Integer, db.ForeignKey('users.id'))
    thread_id = mapped_column(db.Integer, db.ForeignKey('email_threads.thread_id'))
    message_id = mapped_column(db.Integer, db.ForeignKey('messages.message_id'))
    rating = mapped_column(db.String(4), nullable=True)
    timestamp = mapped_column(db.DateTime, default=datetime.utcnow)

class UserPrompt(db.Model):
    __tablename__ = 'user_prompts'
    prompt_id = mapped_column(db.Integer, primary_key=True, autoincrement=True)  # Eindeutige ID für jedes Prompt
    user_id = mapped_column(db.Integer, db.ForeignKey('users.id'))  # Verknüpfung mit einem User
    name = mapped_column(db.String(255), nullable=False)  # Name des Prompts, vom User festgelegt
    content = mapped_column(db.JSON, nullable=False)  # Prompt-Inhalt im JSON-Format
    created_at = mapped_column(db.DateTime, default=datetime.utcnow)  # Zeitpunkt der Erstellung
    updated_at = mapped_column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Zeitpunkt der letzten Aktualisierung

    user = db.relationship('User', backref='prompts')  # Beziehung zu einem User

class UserPromptShare(db.Model):
    __tablename__ = 'user_prompt_shares'
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    prompt_id = mapped_column(db.Integer, db.ForeignKey('user_prompts.prompt_id'))
    shared_with_user_id = mapped_column(db.Integer, db.ForeignKey('users.id'))
    created_at = mapped_column(db.DateTime, default=datetime.utcnow)  # Zeitstempel hinzugefügt

    prompt = db.relationship('UserPrompt', backref='shared_users')
    shared_with_user = db.relationship('User', backref='shared_prompts')

class ComparisonSession(db.Model):
    __tablename__ = "comparison_sessions"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    scenario_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("rating_scenarios.id"), index=True)
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("users.id"), index=True)
    persona_json: Mapped[dict] = mapped_column(db.JSON, nullable=False)
    persona_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    messages: Mapped[list["ComparisonMessage"]] = db.relationship("ComparisonMessage", backref="session", cascade="all, delete-orphan", lazy="selectin")
    
    user = db.relationship("User", backref="comparison_sessions")
    scenario = db.relationship("RatingScenarios", backref="comparison_sessions")

class ComparisonMessage(db.Model):
    __tablename__ = "comparison_messages"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("comparison_sessions.id"), index=True)
    idx: Mapped[int] = mapped_column(db.Integer)
    type: Mapped[str] = mapped_column(db.String(20)) # "user" / "bot_pair"
    content: Mapped[str] = mapped_column(db.Text)
    selected: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True) # "llm1" / "llm2" / "tie" / null
    timestamp: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)

    def to_dict(self):
      content_data = self.content
      if self.type == 'bot_pair' and isinstance(self.content, str):
        try:
          content_data = json.loads(self.content)
        except json.JSONDecodeError:
          content_data = {'llm1': '', 'llm2': ''}

      return {
        'id': self.id,
        'idx': self.idx,
        'type': self.type,
        'content': content_data,
        'selected': self.selected,
        'timestamp': self.timestamp.isoformat()
      }


class ComparisonEvaluation(db.Model):
    __tablename__ = "comparison_evaluations"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey("comparison_messages.id"), index=True)
    user_selection: Mapped[str] = mapped_column(db.String(10))  # "llm1" / "llm2" / "tie"
    ai_selection: Mapped[str] = mapped_column(db.String(10))  # "llm1" / "llm2" / "tie"
    ai_reason: Mapped[str] = mapped_column(db.Text)
    user_justification: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    match_result: Mapped[bool] = mapped_column(db.Boolean)
    timestamp: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)

    message = db.relationship("ComparisonMessage", backref="evaluations")


# ============================================================================
# PERMISSION SYSTEM TABLES
# ============================================================================

class Permission(db.Model):
    """Defines available permissions in the system"""
    __tablename__ = 'permissions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    permission_key: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)


class Role(db.Model):
    """Collection of permissions (e.g., 'researcher', 'admin')"""
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)


class RolePermission(db.Model):
    """Maps permissions to roles"""
    __tablename__ = 'role_permissions'

    role_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    permission_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)

    role = db.relationship('Role', backref='permissions')
    permission = db.relationship('Permission')


class UserPermission(db.Model):
    """Direct user permissions (overrides role permissions)"""
    __tablename__ = 'user_permissions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    permission_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False)
    granted: Mapped[bool] = mapped_column(db.Boolean, default=True)  # TRUE = granted, FALSE = denied
    granted_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)

    permission = db.relationship('Permission')

    __table_args__ = (
        db.UniqueConstraint('username', 'permission_id', name='unique_user_permission'),
    )


class UserRole(db.Model):
    """Maps users to roles"""
    __tablename__ = 'user_roles'

    username: Mapped[str] = mapped_column(db.String(255), primary_key=True)
    role_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    assigned_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)

    role = db.relationship('Role', backref='users')


class PermissionAuditLog(db.Model):
    """Audit trail for all permission changes"""
    __tablename__ = 'permission_audit_log'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(db.String(50), nullable=False)  # GRANT, REVOKE, ROLE_ASSIGN, etc.
    admin_username: Mapped[str] = mapped_column(db.String(255), nullable=False)
    target_username: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    permission_key: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    role_name: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(db.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, index=True)


# ============================================================================
# RAG (RETRIEVAL-AUGMENTED GENERATION) SYSTEM TABLES
# ============================================================================

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


# ============================================================================
# LLM-AS-JUDGE SYSTEM TABLES
# ============================================================================

class PillarThread(db.Model):
    """Maps email threads to KIA pillars (1-5) for structured evaluation"""
    __tablename__ = 'pillar_threads'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('email_threads.thread_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    pillar_number: Mapped[int] = mapped_column(db.Integer, nullable=False)  # 1-5
    pillar_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)

    # Relationship
    thread = db.relationship('EmailThread', backref='pillar_assignments')

    __table_args__ = (
        db.UniqueConstraint('thread_id', 'pillar_number', name='unique_thread_pillar'),
        db.CheckConstraint('pillar_number >= 1 AND pillar_number <= 5', name='check_pillar_range'),
    )


class JudgeSessionStatus(Enum):
    """Status states for judge evaluation sessions"""
    CREATED = 'created'
    QUEUED = 'queued'
    RUNNING = 'running'
    PAUSED = 'paused'
    COMPLETED = 'completed'
    FAILED = 'failed'


class JudgeSession(db.Model):
    """LLM-as-Judge evaluation session orchestrating multiple comparisons"""
    __tablename__ = 'judge_sessions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    # Store Authentik username as string (not FK to users table)
    user_id: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    config_json: Mapped[dict] = mapped_column(db.JSON, nullable=False)  # LLM settings, prompts, etc.
    status: Mapped[str] = mapped_column(
        db.Enum(JudgeSessionStatus),
        default=JudgeSessionStatus.CREATED,
        nullable=False,
        index=True
    )
    total_comparisons: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    completed_comparisons: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    current_comparison_id: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    # Relationships
    comparisons = db.relationship('JudgeComparison', backref='session', cascade='all, delete-orphan')
    statistics = db.relationship('PillarStatistics', backref='session', cascade='all, delete-orphan')


class JudgeComparisonStatus(Enum):
    """Status states for individual pairwise comparisons"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'


class JudgeComparison(db.Model):
    """Individual pairwise comparison of two email threads within a session"""
    __tablename__ = 'judge_comparisons'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('judge_sessions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    thread_a_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('email_threads.thread_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    thread_b_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('email_threads.thread_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    pillar_a: Mapped[int] = mapped_column(db.Integer, nullable=False)  # 1-5
    pillar_b: Mapped[int] = mapped_column(db.Integer, nullable=False)  # 1-5
    position_order: Mapped[int] = mapped_column(db.Integer, nullable=False)  # 1 or 2 (for position bias mitigation)
    status: Mapped[str] = mapped_column(
        db.Enum(JudgeComparisonStatus),
        default=JudgeComparisonStatus.PENDING,
        nullable=False,
        index=True
    )
    queue_position: Mapped[int] = mapped_column(db.Integer, nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    # Relationships
    thread_a = db.relationship('EmailThread', foreign_keys=[thread_a_id], backref='comparisons_as_a')
    thread_b = db.relationship('EmailThread', foreign_keys=[thread_b_id], backref='comparisons_as_b')
    evaluations = db.relationship('JudgeEvaluation', backref='comparison', cascade='all, delete-orphan')

    __table_args__ = (
        db.CheckConstraint('pillar_a >= 1 AND pillar_a <= 5', name='check_pillar_a_range'),
        db.CheckConstraint('pillar_b >= 1 AND pillar_b <= 5', name='check_pillar_b_range'),
        db.CheckConstraint('position_order IN (1, 2)', name='check_position_order'),
    )


class JudgeWinner(Enum):
    """Winner designation for evaluation results"""
    A = 'A'
    B = 'B'
    TIE = 'TIE'


class JudgeEvaluation(db.Model):
    """LLM evaluation result for a single pairwise comparison"""
    __tablename__ = 'judge_evaluations'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    comparison_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('judge_comparisons.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        unique=True  # One evaluation per comparison
    )

    # Raw LLM Response
    raw_response: Mapped[str] = mapped_column(db.Text, nullable=False)
    evaluation_json: Mapped[dict] = mapped_column(db.JSON, nullable=False)  # Structured parsed response

    # Overall Result
    winner: Mapped[str] = mapped_column(db.Enum(JudgeWinner), nullable=False, index=True)

    # Individual Metrics (Thread A)
    counsellor_coherence_a: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    client_coherence_a: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    quality_a: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    empathy_a: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    authenticity_a: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    solution_orientation_a: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)

    # Individual Metrics (Thread B)
    counsellor_coherence_b: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    client_coherence_b: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    quality_b: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    empathy_b: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    authenticity_b: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    solution_orientation_b: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)

    # Analysis
    reasoning: Mapped[str] = mapped_column(db.Text, nullable=False)
    confidence: Mapped[float] = mapped_column(db.Float, nullable=False)
    position_variant: Mapped[int] = mapped_column(db.Integer, nullable=False)  # 1 or 2

    # Performance Metrics
    llm_latency_ms: Mapped[int] = mapped_column(db.Integer, nullable=False)
    token_count: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)


class PillarStatistics(db.Model):
    """Aggregated win/loss statistics for pillar-to-pillar comparisons"""
    __tablename__ = 'pillar_statistics'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('judge_sessions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    pillar_a: Mapped[int] = mapped_column(db.Integer, nullable=False)  # 1-5
    pillar_b: Mapped[int] = mapped_column(db.Integer, nullable=False)  # 1-5

    # Win Statistics
    wins_a: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    wins_b: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    ties: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)

    # Confidence Metrics
    avg_confidence: Mapped[float] = mapped_column(db.Float, default=0.0, nullable=False)

    # Timestamp
    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint('session_id', 'pillar_a', 'pillar_b', name='unique_session_pillar_pair'),
        db.CheckConstraint('pillar_a >= 1 AND pillar_a <= 5', name='check_stats_pillar_a_range'),
        db.CheckConstraint('pillar_b >= 1 AND pillar_b <= 5', name='check_stats_pillar_b_range'),
    )


# ============================================================================
# ONCOCO ANALYSIS SYSTEM TABLES
# ============================================================================

class OnCoCoAnalysisStatus(Enum):
    """Status states for OnCoCo analysis jobs"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'


class OnCoCoAnalysis(db.Model):
    """OnCoCo analysis job tracking and configuration"""
    __tablename__ = 'oncoco_analyses'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        db.Enum(OnCoCoAnalysisStatus),
        default=OnCoCoAnalysisStatus.PENDING,
        nullable=False,
        index=True
    )
    config_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)  # pillars, granularity etc.

    # Progress tracking
    total_threads: Mapped[int] = mapped_column(db.Integer, default=0)
    processed_threads: Mapped[int] = mapped_column(db.Integer, default=0)
    total_sentences: Mapped[int] = mapped_column(db.Integer, default=0)

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    # Relationships
    sentence_labels = db.relationship('OnCoCoSentenceLabel', backref='analysis', cascade='all, delete-orphan')
    pillar_statistics = db.relationship('OnCoCoPillarStatistics', backref='analysis', cascade='all, delete-orphan')
    transition_matrices = db.relationship('OnCoCoTransitionMatrix', backref='analysis', cascade='all, delete-orphan')


class OnCoCoSentenceLabel(db.Model):
    """Individual sentence classifications from OnCoCo model"""
    __tablename__ = 'oncoco_sentence_labels'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('oncoco_analyses.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    thread_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('email_threads.thread_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    message_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('messages.message_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    pillar_number: Mapped[int] = mapped_column(db.Integer, nullable=False, index=True)

    # Sentence info
    sentence_index: Mapped[int] = mapped_column(db.Integer, nullable=False)
    sentence_text: Mapped[str] = mapped_column(db.Text, nullable=False)
    role: Mapped[str] = mapped_column(db.String(20), nullable=False)  # 'Counselor' or 'Client'

    # Classification result
    label: Mapped[str] = mapped_column(db.String(50), nullable=False, index=True)
    label_level2: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True, index=True)  # Aggregated label
    confidence: Mapped[float] = mapped_column(db.Float, nullable=False)
    top_3_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)  # Top 3 predictions

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)

    # Relationships
    thread = db.relationship('EmailThread', backref='oncoco_labels')
    message = db.relationship('Message', backref='oncoco_labels')


class OnCoCoPillarStatistics(db.Model):
    """Aggregated statistics per pillar for an analysis"""
    __tablename__ = 'oncoco_pillar_statistics'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('oncoco_analyses.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    pillar_number: Mapped[int] = mapped_column(db.Integer, nullable=False, index=True)

    # Counts
    total_threads: Mapped[int] = mapped_column(db.Integer, default=0)
    total_messages: Mapped[int] = mapped_column(db.Integer, default=0)
    total_sentences: Mapped[int] = mapped_column(db.Integer, default=0)
    counselor_sentences: Mapped[int] = mapped_column(db.Integer, default=0)
    client_sentences: Mapped[int] = mapped_column(db.Integer, default=0)

    # Label distributions (JSON: {label: count, ...})
    label_distribution_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    label_distribution_level2_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)

    # Computed scores
    impact_factor_ratio: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    mi_score: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)  # Motivational Interviewing
    resource_activation_score: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)
    avg_confidence: Mapped[Optional[float]] = mapped_column(db.Float, nullable=True)

    # Timestamps
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('analysis_id', 'pillar_number', name='unique_analysis_pillar'),
    )


class OnCoCoTransitionMatrix(db.Model):
    """Transition matrices between labels for conversation flow analysis"""
    __tablename__ = 'oncoco_transition_matrices'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey('oncoco_analyses.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    pillar_number: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True, index=True)  # NULL = all pillars
    level: Mapped[int] = mapped_column(db.Integer, default=2, nullable=False)  # Aggregation level (2-5)

    # Matrix data: {from_label: {to_label: count, ...}, ...}
    matrix_counts_json: Mapped[dict] = mapped_column(db.JSON, nullable=False)
    matrix_probs_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)  # Normalized probabilities

    # Statistics
    total_transitions: Mapped[int] = mapped_column(db.Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('analysis_id', 'pillar_number', 'level', name='unique_analysis_pillar_level'),
    )