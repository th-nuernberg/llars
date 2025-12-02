"""KAIMO database models."""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db import db


class KaimoCase(db.Model):
    __tablename__ = 'kaimo_cases'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    status: Mapped[str] = mapped_column(
        db.Enum('draft', 'published', 'archived', name='kaimo_case_status'),
        nullable=False,
        default='draft'
    )
    icon: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)
    created_by: Mapped[str] = mapped_column(db.String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    documents = relationship('KaimoDocument', back_populates='case', cascade='all, delete-orphan')
    hints = relationship('KaimoHint', back_populates='case', cascade='all, delete-orphan')
    categories = relationship('KaimoCaseCategory', back_populates='case', cascade='all, delete-orphan')
    assessments = relationship('KaimoUserAssessment', back_populates='case', cascade='all, delete-orphan')
    permissions = relationship('KaimoCasePermission', back_populates='case', cascade='all, delete-orphan')
    ai_content = relationship('KaimoAIContent', back_populates='case', cascade='all, delete-orphan')


class KaimoDocument(db.Model):
    __tablename__ = 'kaimo_documents'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('kaimo_cases.id', ondelete='CASCADE'), nullable=False, index=True)
    title: Mapped[str] = mapped_column(db.String(255), nullable=False)
    content: Mapped[str] = mapped_column(db.Text, nullable=False)
    document_type: Mapped[str] = mapped_column(
        db.Enum('aktenvermerk', 'bericht', 'protokoll', 'sonstiges', name='kaimo_document_type'),
        nullable=False
    )
    document_date: Mapped[Optional[datetime]] = mapped_column(db.Date, nullable=True)
    sort_order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)

    case = relationship('KaimoCase', back_populates='documents')
    hints = relationship('KaimoHint', back_populates='source_document')


class KaimoCategory(db.Model):
    __tablename__ = 'kaimo_categories'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(db.String(10), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(db.String(20), nullable=True)
    sort_order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    is_default: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)

    subcategories = relationship('KaimoSubcategory', back_populates='category', cascade='all, delete-orphan')
    case_links = relationship('KaimoCaseCategory', back_populates='category', cascade='all, delete-orphan')


class KaimoSubcategory(db.Model):
    __tablename__ = 'kaimo_subcategories'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('kaimo_categories.id', ondelete='CASCADE'), nullable=False, index=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    is_default: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)

    category = relationship('KaimoCategory', back_populates='subcategories')

    __table_args__ = (
        db.UniqueConstraint('category_id', 'name', name='uq_subcategory_per_category'),
    )


class KaimoHint(db.Model):
    __tablename__ = 'kaimo_hints'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('kaimo_cases.id', ondelete='CASCADE'), nullable=False, index=True)
    document_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('kaimo_documents.id', ondelete='SET NULL'), nullable=True, index=True)
    content: Mapped[str] = mapped_column(db.Text, nullable=False)
    expected_category_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('kaimo_categories.id', ondelete='SET NULL'), nullable=True)
    expected_subcategory_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('kaimo_subcategories.id', ondelete='SET NULL'), nullable=True)
    expected_rating: Mapped[Optional[str]] = mapped_column(
        db.Enum('risk', 'resource', 'unclear', name='kaimo_hint_expected_rating'),
        nullable=True
    )
    sort_order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)

    case = relationship('KaimoCase', back_populates='hints')
    source_document = relationship('KaimoDocument', back_populates='hints')
    expected_category = relationship('KaimoCategory', foreign_keys=[expected_category_id])
    expected_subcategory = relationship('KaimoSubcategory', foreign_keys=[expected_subcategory_id])
    assignments = relationship('KaimoHintAssignment', back_populates='hint', cascade='all, delete-orphan')


class KaimoCaseCategory(db.Model):
    __tablename__ = 'kaimo_case_categories'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('kaimo_cases.id', ondelete='CASCADE'), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('kaimo_categories.id', ondelete='CASCADE'), nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(db.Integer, default=0, nullable=False)

    case = relationship('KaimoCase', back_populates='categories')
    category = relationship('KaimoCategory', back_populates='case_links')

    __table_args__ = (
        db.UniqueConstraint('case_id', 'category_id', name='uq_case_category'),
    )


class KaimoAIContent(db.Model):
    __tablename__ = 'kaimo_ai_content'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('kaimo_cases.id', ondelete='CASCADE'), nullable=False, index=True)
    content_type: Mapped[str] = mapped_column(
        db.Enum('summary', 'consequences', 'plausibility', name='kaimo_ai_content_type'),
        nullable=False
    )
    content: Mapped[str] = mapped_column(db.Text, nullable=False)
    is_generated: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)
    generated_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)

    case = relationship('KaimoCase', back_populates='ai_content')

    __table_args__ = (
        db.UniqueConstraint('case_id', 'content_type', name='uq_case_content_type'),
    )


class KaimoUserAssessment(db.Model):
    __tablename__ = 'kaimo_user_assessments'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('kaimo_cases.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    username: Mapped[str] = mapped_column(db.String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        db.Enum('in_progress', 'completed', name='kaimo_assessment_status'),
        nullable=False,
        default='in_progress'
    )
    final_verdict: Mapped[Optional[str]] = mapped_column(
        db.Enum('inconclusive', 'not_endangered', 'endangered', name='kaimo_final_verdict'),
        nullable=True
    )
    final_comment: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(db.Integer, nullable=True)

    case = relationship('KaimoCase', back_populates='assessments')
    assignments = relationship('KaimoHintAssignment', back_populates='assessment', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('case_id', 'user_id', name='uq_assessment_per_user_case'),
    )


class KaimoHintAssignment(db.Model):
    __tablename__ = 'kaimo_hint_assignments'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    assessment_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('kaimo_user_assessments.id', ondelete='CASCADE'), nullable=False, index=True)
    hint_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('kaimo_hints.id', ondelete='CASCADE'), nullable=False, index=True)
    assigned_category_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('kaimo_categories.id', ondelete='SET NULL'), nullable=True)
    assigned_subcategory_id: Mapped[Optional[int]] = mapped_column(db.Integer, db.ForeignKey('kaimo_subcategories.id', ondelete='SET NULL'), nullable=True)
    rating: Mapped[Optional[str]] = mapped_column(
        db.Enum('risk', 'resource', 'unclear', name='kaimo_assignment_rating'),
        nullable=True
    )
    assigned_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)

    assessment = relationship('KaimoUserAssessment', back_populates='assignments')
    hint = relationship('KaimoHint', back_populates='assignments')
    assigned_category = relationship('KaimoCategory', foreign_keys=[assigned_category_id])
    assigned_subcategory = relationship('KaimoSubcategory', foreign_keys=[assigned_subcategory_id])

    __table_args__ = (
        db.UniqueConstraint('assessment_id', 'hint_id', name='uq_assignment_per_hint_assessment'),
    )


class KaimoCasePermission(db.Model):
    __tablename__ = 'kaimo_case_permissions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('kaimo_cases.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True, index=True)
    group_name: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True, index=True)
    granted_by: Mapped[str] = mapped_column(db.String(255), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)

    case = relationship('KaimoCase', back_populates='permissions')

