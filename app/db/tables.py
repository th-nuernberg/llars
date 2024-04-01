from . import db  # Importieren Sie db aus dem database-Paket
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(db.String(255))  # Länge für String hinzugefügt
    password_hash: Mapped[str] = mapped_column(db.String(255))  # Länge für String hinzugefügt

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class EmailThread(db.Model):
    __tablename__ = 'email_threads'
    thread_id = mapped_column(db.Integer, primary_key=True)
    chat_id = mapped_column(db.Integer)
    institut_id = mapped_column(db.Integer)
    subject = mapped_column(db.String(255))  # Länge für String hinzugefügt

    messages = db.relationship('Message', backref='email_thread')
    features = db.relationship('Feature', backref='email_thread')

class Message(db.Model):
    __tablename__ = 'messages'
    message_id = mapped_column(db.Integer, primary_key=True)
    thread_id = mapped_column(db.Integer, db.ForeignKey('email_threads.thread_id'))
    sender = mapped_column(db.String(255))  # Länge für String hinzugefügt
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
