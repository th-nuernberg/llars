"""User-related database models."""

from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.security import generate_password_hash, check_password_hash
from db import db


class UserGroup(db.Model):
    """Group model for organizing users."""
    __tablename__ = 'user_groups'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(255), unique=True)


class User(db.Model):
    """User model for authentication and authorization."""
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(db.String(255))
    password_hash: Mapped[str] = mapped_column(db.String(255))
    api_key: Mapped[str] = mapped_column(db.String(100), unique=True)
    group_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('user_groups.id'), default=1)

    group = db.relationship('UserGroup', backref='users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
