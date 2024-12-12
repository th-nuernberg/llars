from unittest.mock import DEFAULT

from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Mapped, mapped_column
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
    function_type_id = mapped_column(db.Integer, db.ForeignKey('feature_function_types.function_type_id'))
    begin_date = mapped_column(db.DateTime, default=datetime.utcnow)
    end_time = mapped_column(db.DateTime, default=datetime.utcnow)
    timestamp = mapped_column(db.DateTime, default=datetime.utcnow)

class ScenarioUsers(db.Model):
    __tablename__ = 'scenario_users'
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    scenario_id = mapped_column(db.Integer, db.ForeignKey('rating_scenarios.id'))
    user_id = mapped_column(db.Integer, db.ForeignKey('users.id'))
    role = mapped_column(db.Enum(ScenarioRoles))

class ScenarioThreads(db.Model):
    __tablename__ = 'scenario_threads'
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    scenario_id = mapped_column(db.Integer, db.ForeignKey('rating_scenarios.id'))
    thread_id = mapped_column(db.Integer, db.ForeignKey('email_threads.thread_id'))


class ScenarioThreadDistribution(db.Model):
    __tablename__ = 'scenario_thread_distribution'
    id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    scenario_id = mapped_column(db.Integer, db.ForeignKey('rating_scenarios.id'))
    user_id = mapped_column(db.Integer, db.ForeignKey('users.id'))
    thread_id = mapped_column(db.Integer, db.ForeignKey('email_threads.thread_id'))
    status = mapped_column(db.Enum(ProgressionStatus))


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
