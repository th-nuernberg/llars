"""Scenario and Rating database models."""

import json
from typing import Optional
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column, synonym
from db import db


class ScenarioRoles(Enum):
    OWNER = 'Owner'      # Szenario-Ersteller - kann bearbeiten, User verwalten, löschen
    RATER = 'Rater'      # Kann bewerten
    EVALUATOR = 'Evaluator'  # Kann an Evaluationen teilnehmen (ehemals Viewer)


class InvitationStatus(Enum):
    ACCEPTED = 'accepted'    # Einladung angenommen (Standard für neue Einladungen)
    REJECTED = 'rejected'    # Einladung abgelehnt - Szenario erscheint nicht mehr
    PENDING = 'pending'      # Optional: Einladung noch nicht beantwortet


class ProgressionStatus(Enum):
    NOT_STARTED = 'Not Started'
    PROGRESSING = 'Progressing'
    DONE = 'Done'


class FeatureFunctionType(db.Model):
    __tablename__ = 'feature_function_types'
    function_type_id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    name = mapped_column(db.String(255), unique=True)


class EvaluationItem(db.Model):
    """
    Generic evaluation item that can be rated, compared, labeled, or analyzed.

    Replaces the legacy EmailThread model. Supports multiple evaluation types:
    - rating: Likert/star scale evaluations
    - ranking: Sort/categorize items
    - comparison: A/B comparisons
    - labeling: Category assignment
    - authenticity: Fake/Real voting
    """
    __tablename__ = 'evaluation_items'
    item_id = mapped_column(db.Integer, primary_key=True)
    chat_id = mapped_column(db.Integer)
    institut_id = mapped_column(db.Integer)
    subject = mapped_column(db.String(255))
    sender = mapped_column(db.String(255))
    function_type_id = mapped_column(db.Integer, db.ForeignKey('feature_function_types.function_type_id'))

    # Backwards compatibility: thread_id is a synonym for item_id (for queries)
    thread_id = synonym('item_id')

    messages = db.relationship('Message', backref='evaluation_item')
    features = db.relationship('Feature', backref='evaluation_item')
    function_type = db.relationship('FeatureFunctionType', backref='evaluation_items')

    # Legacy backref names for backwards compatibility
    @property
    def email_thread(self):
        """Backwards compatibility alias."""
        return self

    __table_args__ = (
        db.UniqueConstraint('chat_id', 'institut_id', 'function_type_id', name='_chat_institut_function_uc'),
    )


# Backwards compatibility alias (deprecated)
EmailThread = EvaluationItem


class Message(db.Model):
    __tablename__ = 'messages'
    message_id = mapped_column(db.Integer, primary_key=True)
    item_id = mapped_column(db.Integer, db.ForeignKey('evaluation_items.item_id'))
    sender = mapped_column(db.String(255))
    content = mapped_column(db.TEXT)
    timestamp = mapped_column(db.DateTime)
    generated_by = mapped_column(db.String(255), default="Human")

    # Backwards compatibility: thread_id is a synonym for item_id (for queries)
    thread_id = synonym('item_id')


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
    item_id = mapped_column(db.Integer, db.ForeignKey('evaluation_items.item_id'))
    consulting_category_type_id = mapped_column(db.Integer, db.ForeignKey('consulting_category_types.id'))
    notes = mapped_column(db.String(255))
    timestamp = mapped_column(db.DateTime, default=datetime.utcnow)

    # Backwards compatibility: thread_id is a synonym for item_id (for queries)
    thread_id = synonym('item_id')


class Feature(db.Model):
    __tablename__ = 'features'
    feature_id = mapped_column(db.Integer, primary_key=True)
    item_id = mapped_column(db.Integer, db.ForeignKey('evaluation_items.item_id'))
    type_id = mapped_column(db.Integer, db.ForeignKey('feature_types.type_id'))
    llm_id = mapped_column(db.Integer, db.ForeignKey('llms.llm_id'))
    content = mapped_column(db.TEXT)

    feature_type = db.relationship('FeatureType', backref='features')
    llm = db.relationship('LLM', backref='features')

    # Backwards compatibility: thread_id is a synonym for item_id (for queries)
    thread_id = synonym('item_id')


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


class RatingScenarios(db.Model):
    __tablename__ = 'rating_scenarios'
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    scenario_name = mapped_column(db.String(255))
    function_type_id = mapped_column(db.Integer, db.ForeignKey('feature_function_types.function_type_id'))
    begin = mapped_column(db.DateTime, default=datetime.utcnow)
    end = mapped_column(db.DateTime, default=datetime.utcnow)
    timestamp = mapped_column(db.DateTime, default=datetime.utcnow)
    # Wer hat das Szenario erstellt (Username aus Authentik)
    created_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True, index=True)
    # Modellkonfiguration für Comparison-Szenarien
    llm1_model: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    llm2_model: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    # Generische, funktionsspezifische Szenario-Konfiguration (z.B. Fake/Echt, Comparison, zukünftige Evaluations)
    config_json: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)

    # Definiere die Beziehungen mit Cascade-Option
    scenario_users = db.relationship('ScenarioUsers', backref='rating_scenario', cascade="all, delete-orphan")
    scenario_items = db.relationship('ScenarioItems', backref='rating_scenario', cascade="all, delete-orphan")
    scenario_item_distribution = db.relationship('ScenarioItemDistribution', backref='rating_scenario', cascade="all, delete-orphan")
    # Comparison sessions (for comparison function type)
    comparison_sessions_rel = db.relationship('ComparisonSession', back_populates="scenario", cascade="all, delete-orphan", passive_deletes=True)

    # Backwards compatibility properties
    @property
    def scenario_threads(self):
        return self.scenario_items

    @property
    def scenario_thread_distribution(self):
        return self.scenario_item_distribution


class ScenarioUsers(db.Model):
    __tablename__ = 'scenario_users'
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    scenario_id = mapped_column(db.Integer, db.ForeignKey('rating_scenarios.id'))
    user_id = mapped_column(db.Integer, db.ForeignKey('users.id'))
    role = mapped_column(db.Enum(ScenarioRoles))
    # Einladungsstatus: accepted (default), rejected, pending
    invitation_status = mapped_column(
        db.Enum(InvitationStatus),
        default=InvitationStatus.ACCEPTED,
        nullable=False
    )
    # Zeitstempel für Einladung und Antwort
    invited_at = mapped_column(db.DateTime, default=datetime.utcnow, nullable=True)
    responded_at = mapped_column(db.DateTime, nullable=True)
    # Wer hat eingeladen (für Re-Invite Tracking)
    invited_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    user = db.relationship('User', backref='scenario_users')

    # Definiere den Unique Constraint für die Kombination von user_id und szenario_id
    __table_args__ = (
        db.UniqueConstraint('user_id', 'scenario_id', name='uix_user_szenario'),
    )


class ScenarioItems(db.Model):
    """Links EvaluationItems to Scenarios. Renamed from ScenarioThreads."""
    __tablename__ = 'scenario_items'
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    scenario_id = mapped_column(db.Integer, db.ForeignKey('rating_scenarios.id'))
    item_id = mapped_column(db.Integer, db.ForeignKey('evaluation_items.item_id'))
    item = db.relationship('EvaluationItem', backref='scenario_items')

    # Backwards compatibility: thread_id is a synonym for item_id (for queries)
    thread_id = synonym('item_id')

    __table_args__ = (
        db.UniqueConstraint('item_id', 'scenario_id', name='uix_item_scenario'),
    )

    # Backwards compatibility property for relationship
    @property
    def thread(self):
        return self.item


# Backwards compatibility alias
ScenarioThreads = ScenarioItems


class ScenarioItemDistribution(db.Model):
    """Distributes EvaluationItems to ScenarioUsers. Renamed from ScenarioThreadDistribution."""
    __tablename__ = 'scenario_item_distribution'
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    scenario_id = mapped_column(db.Integer, db.ForeignKey('rating_scenarios.id'))
    scenario_user_id = mapped_column(db.Integer, db.ForeignKey('scenario_users.id'))
    scenario_item_id = mapped_column(db.Integer, db.ForeignKey('scenario_items.id'))
    scenario_item = db.relationship('ScenarioItems', backref='distributions')
    scenario_user = db.relationship('ScenarioUsers', backref='item_distributions')

    # Backwards compatibility: scenario_thread_id is a synonym for scenario_item_id (for queries)
    scenario_thread_id = synonym('scenario_item_id')

    # Backwards compatibility property for relationship
    @property
    def scenario_thread(self):
        return self.scenario_item


# Backwards compatibility alias
ScenarioThreadDistribution = ScenarioItemDistribution



class UserMailHistoryRating(db.Model):
    __tablename__ = 'user_mailhistory_ratings'
    rating_id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(db.Integer, db.ForeignKey('users.id'))
    item_id = mapped_column(db.Integer, db.ForeignKey('evaluation_items.item_id'))
    counsellor_coherence_rating = mapped_column(db.Integer, nullable=True)
    client_coherence_rating = mapped_column(db.Integer, nullable=True)
    quality_rating = mapped_column(db.Integer, nullable=True)
    overall_rating = mapped_column(db.Integer, nullable=True)
    feedback = mapped_column(db.TEXT)
    status = mapped_column(db.Enum(ProgressionStatus), default=ProgressionStatus.NOT_STARTED)
    timestamp = mapped_column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='mail_ratings')
    evaluation_item = db.relationship('EvaluationItem', backref='mail_ratings')

    # Backwards compatibility: thread_id is a synonym for item_id (for queries)
    thread_id = synonym('item_id')

    # Backwards compatibility property for relationship
    @property
    def email_thread(self):
        return self.evaluation_item


class UserMessageRating(db.Model):
    __tablename__ = 'user_message_ratings'
    msg_rating_id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(db.Integer, db.ForeignKey('users.id'))
    item_id = mapped_column(db.Integer, db.ForeignKey('evaluation_items.item_id'))
    message_id = mapped_column(db.Integer, db.ForeignKey('messages.message_id'))
    rating = mapped_column(db.String(4), nullable=True)
    timestamp = mapped_column(db.DateTime, default=datetime.utcnow)

    # Backwards compatibility: thread_id is a synonym for item_id (for queries)
    thread_id = synonym('item_id')


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
    scenario = db.relationship("RatingScenarios", back_populates="comparison_sessions_rel")


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


class PromptCommit(db.Model):
    """Git-like commit history for UserPrompt collaborative editing."""
    __tablename__ = "prompt_commits"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    prompt_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("user_prompts.prompt_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_username: Mapped[str] = mapped_column(db.String(255), nullable=False)
    message: Mapped[str] = mapped_column(db.Text, nullable=False)
    # JSON object with per-user contribution stats: { users: [...], insertions, deletions, hasChanges }
    diff_summary: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)
    # Full prompt content at commit time (all blocks as JSON) for diff comparison
    content_snapshot: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    prompt = db.relationship("UserPrompt", backref=db.backref("commits", cascade="all, delete-orphan", lazy="selectin"))
