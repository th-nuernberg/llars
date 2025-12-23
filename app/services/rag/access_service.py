"""
RAG Access Service

Provides document/collection-level access checks based on:
- Admin override
- Ownership (uploaded_by / created_by)
- Public flags
- Explicit permissions (rag_document_permissions)
"""

from typing import Optional, Set, List

from sqlalchemy import and_, or_, select, exists

from db.db import db
from db.models.rag import (
    RAGDocument,
    RAGDocumentPermission,
    RAGCollection,
    CollectionDocumentLink,
)
from db.tables import Role, UserRole
from services.permission_service import PermissionService


class RAGAccessService:
    """Business logic for RAG document/collection access."""

    @staticmethod
    def _normalize_strings(values) -> List[str]:
        if not values:
            return []
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, (list, tuple, set)):
            return []
        return sorted({str(v).strip() for v in values if v and str(v).strip()})

    @staticmethod
    def _get_user_role_names(username: Optional[str]) -> Set[str]:
        if not username:
            return set()
        rows = db.session.execute(
            select(Role.role_name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.username == username)
        ).scalars().all()
        return set(rows or [])

    @staticmethod
    def is_admin_user(username: Optional[str]) -> bool:
        if not username:
            return False
        return PermissionService.check_permission(username, 'admin:permissions:manage')

    @staticmethod
    def _permission_flag_clause(access: str):
        if access == 'delete':
            return RAGDocumentPermission.can_delete.is_(True)
        if access == 'edit':
            return or_(
                RAGDocumentPermission.can_edit.is_(True),
                RAGDocumentPermission.can_delete.is_(True)
            )
        if access == 'share':
            return RAGDocumentPermission.can_share.is_(True)
        return or_(
            RAGDocumentPermission.can_view.is_(True),
            RAGDocumentPermission.can_edit.is_(True),
            RAGDocumentPermission.can_delete.is_(True)
        )

    @staticmethod
    def _permission_exists_clause(username: str, role_names: Set[str], access: str):
        flag_clause = RAGAccessService._permission_flag_clause(access)
        targets = [and_(
            RAGDocumentPermission.permission_type == 'user',
            RAGDocumentPermission.target_identifier == username
        )]
        if role_names:
            targets.append(and_(
                RAGDocumentPermission.permission_type == 'role',
                RAGDocumentPermission.target_identifier.in_(sorted(role_names))
            ))
        return exists(
            select(1).where(and_(
                RAGDocumentPermission.document_id == RAGDocument.id,
                or_(*targets),
                flag_clause
            ))
        )

    @staticmethod
    def apply_document_access_filter(query, username: Optional[str], access: str = 'view'):
        if not username:
            return query.filter(False)
        if RAGAccessService.is_admin_user(username):
            return query

        role_names = RAGAccessService._get_user_role_names(username)
        permission_exists = RAGAccessService._permission_exists_clause(username, role_names, access)

        clauses = [
            RAGDocument.uploaded_by == username,
            permission_exists
        ]
        if access == 'view':
            clauses.insert(0, RAGDocument.is_public.is_(True))

        return query.filter(or_(*clauses))

    @staticmethod
    def can_view_document(username: Optional[str], document: Optional[RAGDocument]) -> bool:
        if not username or not document:
            return False
        if RAGAccessService.is_admin_user(username):
            return True
        if document.uploaded_by == username:
            return True
        if document.is_public:
            return True
        role_names = RAGAccessService._get_user_role_names(username)
        permission_exists = RAGAccessService._permission_exists_clause(username, role_names, 'view')
        return db.session.execute(select(permission_exists)).scalar() is True

    @staticmethod
    def can_edit_document(username: Optional[str], document: Optional[RAGDocument]) -> bool:
        if not username or not document:
            return False
        if RAGAccessService.is_admin_user(username):
            return True
        if document.uploaded_by == username:
            return True
        role_names = RAGAccessService._get_user_role_names(username)
        permission_exists = RAGAccessService._permission_exists_clause(username, role_names, 'edit')
        return db.session.execute(select(permission_exists)).scalar() is True

    @staticmethod
    def can_delete_document(username: Optional[str], document: Optional[RAGDocument]) -> bool:
        if not username or not document:
            return False
        if RAGAccessService.is_admin_user(username):
            return True
        if document.uploaded_by == username:
            return True
        role_names = RAGAccessService._get_user_role_names(username)
        permission_exists = RAGAccessService._permission_exists_clause(username, role_names, 'delete')
        return db.session.execute(select(permission_exists)).scalar() is True

    @staticmethod
    def can_share_document(username: Optional[str], document: Optional[RAGDocument]) -> bool:
        if not username or not document:
            return False
        if RAGAccessService.is_admin_user(username):
            return True
        if document.uploaded_by == username:
            return True
        role_names = RAGAccessService._get_user_role_names(username)
        permission_exists = RAGAccessService._permission_exists_clause(username, role_names, 'share')
        return db.session.execute(select(permission_exists)).scalar() is True

    @staticmethod
    def apply_collection_view_filter(query, username: Optional[str]):
        if not username:
            return query.filter(False)
        if RAGAccessService.is_admin_user(username):
            return query

        doc_ids = select(RAGDocument.id)
        doc_ids = RAGAccessService.apply_document_access_filter(
            RAGDocument.query, username, access='view'
        ).with_entities(RAGDocument.id)
        doc_ids_subq = doc_ids.subquery()

        has_accessible_doc = exists(
            select(1).select_from(CollectionDocumentLink).where(and_(
                CollectionDocumentLink.collection_id == RAGCollection.id,
                CollectionDocumentLink.document_id.in_(select(doc_ids_subq.c.id))
            ))
        )

        return query.filter(or_(
            RAGCollection.created_by == username,
            RAGCollection.is_public.is_(True),
            has_accessible_doc
        ))

    @staticmethod
    def can_view_collection(username: Optional[str], collection: Optional[RAGCollection]) -> bool:
        if not username or not collection:
            return False
        if RAGAccessService.is_admin_user(username):
            return True
        if collection.created_by == username or collection.is_public:
            return True

        doc_ids = select(RAGDocument.id)
        doc_ids = RAGAccessService.apply_document_access_filter(
            RAGDocument.query, username, access='view'
        ).with_entities(RAGDocument.id)
        doc_ids_subq = doc_ids.subquery()

        return db.session.execute(
            select(
                exists(
                    select(1).select_from(CollectionDocumentLink).where(and_(
                        CollectionDocumentLink.collection_id == collection.id,
                        CollectionDocumentLink.document_id.in_(select(doc_ids_subq.c.id))
                    ))
                )
            )
        ).scalar() is True

    @staticmethod
    def can_edit_collection(username: Optional[str], collection: Optional[RAGCollection]) -> bool:
        if not username or not collection:
            return False
        if RAGAccessService.is_admin_user(username):
            return True
        return collection.created_by == username

    @staticmethod
    def can_delete_collection(username: Optional[str], collection: Optional[RAGCollection]) -> bool:
        return RAGAccessService.can_edit_collection(username, collection)

    @staticmethod
    def get_document_permissions(document_id: int) -> dict:
        rows = (
            RAGDocumentPermission.query
            .filter_by(document_id=document_id)
            .order_by(RAGDocumentPermission.permission_type, RAGDocumentPermission.target_identifier)
            .all()
        )
        users = []
        roles = []
        for row in rows:
            payload = {
                'target': row.target_identifier,
                'can_view': row.can_view,
                'can_edit': row.can_edit,
                'can_delete': row.can_delete,
                'can_share': row.can_share,
                'granted_by': row.granted_by,
                'granted_at': row.granted_at.isoformat() if row.granted_at else None
            }
            if row.permission_type == 'role':
                roles.append(payload)
            else:
                users.append(payload)
        return {'users': users, 'roles': roles}

    @staticmethod
    def set_document_permissions(
        document_id: int,
        usernames=None,
        role_names=None,
        granted_by: Optional[str] = None,
        access: Optional[dict] = None
    ) -> dict:
        usernames = RAGAccessService._normalize_strings(usernames)
        role_names = RAGAccessService._normalize_strings(role_names)
        access = access or {}
        can_view = bool(access.get('can_view', True))
        can_edit = bool(access.get('can_edit', True))
        can_delete = bool(access.get('can_delete', False))
        can_share = bool(access.get('can_share', False))

        existing = RAGDocumentPermission.query.filter_by(document_id=document_id).all()
        existing_map = {(r.permission_type, r.target_identifier): r for r in existing}
        target_sets = {
            'user': set(usernames),
            'role': set(role_names)
        }

        for row in existing:
            if row.permission_type not in target_sets or row.target_identifier not in target_sets[row.permission_type]:
                db.session.delete(row)
                continue
            row.can_view = can_view
            row.can_edit = can_edit
            row.can_delete = can_delete
            row.can_share = can_share
            row.granted_by = granted_by

        for perm_type, targets in target_sets.items():
            for identifier in targets:
                key = (perm_type, identifier)
                if key in existing_map:
                    continue
                db.session.add(RAGDocumentPermission(
                    document_id=document_id,
                    permission_type=perm_type,
                    target_identifier=identifier,
                    can_view=can_view,
                    can_edit=can_edit,
                    can_delete=can_delete,
                    can_share=can_share,
                    granted_by=granted_by
                ))

        db.session.commit()
        return {
            'usernames': usernames,
            'role_names': role_names,
            'access': {
                'can_view': can_view,
                'can_edit': can_edit,
                'can_delete': can_delete,
                'can_share': can_share
            }
        }
