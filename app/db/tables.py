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