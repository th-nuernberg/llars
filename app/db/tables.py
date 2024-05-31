from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(db.String(255))
    password_hash: Mapped[str] = mapped_column(db.String(255))
    api_key: Mapped[str] = mapped_column(db.String(36), unique=True)

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


class LLM(db.Model):
    __tablename__ = 'llms'
    llm_id = mapped_column(db.Integer, primary_key=True)
    name = mapped_column(db.String(255), unique=True)


class FeatureType(db.Model):
    __tablename__ = 'feature_types'
    type_id = mapped_column(db.Integer, primary_key=True)
    name = mapped_column(db.String(255), unique=True)


class Feature(db.Model):
    __tablename__ = 'features'
    feature_id = mapped_column(db.Integer, primary_key=True)
    thread_id = mapped_column(db.Integer, db.ForeignKey('email_threads.thread_id'))
    type_id = mapped_column(db.Integer, db.ForeignKey('feature_types.type_id'))
    llm_id = mapped_column(db.Integer, db.ForeignKey('llms.llm_id'))
    value = mapped_column(db.TEXT)

    feature_type = db.relationship('FeatureType', backref='features')
    llm = db.relationship('LLM', backref='features')


class UserFeatureRanking(db.Model):
    __tablename__ = 'user_feature_rankings'
    ranking_id = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(db.Integer, db.ForeignKey('users.id'))
    feature_id = mapped_column(db.Integer, db.ForeignKey('features.feature_id'))
    ranking_value = mapped_column(db.Float)
    type_id = mapped_column(db.Integer, db.ForeignKey('feature_types.type_id'))
    llm_id = mapped_column(db.Integer, db.ForeignKey('llms.llm_id'))

    user = db.relationship('User', backref='feature_rankings')
    feature = db.relationship('Feature', backref='user_rankings')
    feature_type = db.relationship('FeatureType', backref='user_rankings')
    llm = db.relationship('LLM', backref='user_rankings')
