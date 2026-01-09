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

from db.database import db
from db.models.rag import (
    RAGDocument,
    RAGDocumentPermission,
    RAGCollection,
    RAGCollectionPermission,
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
        from flask import g, has_request_context

        if getattr(g, 'is_system_api_key', False):
            return True

        if PermissionService.check_permission(username, 'admin:permissions:manage'):
            return True

        if not has_request_context():
            return False

        try:
            from auth.oidc_validator import get_token_from_request, validate_token, has_role

            token = get_token_from_request()
            if not token:
                return False
            payload = validate_token(token)
            if not payload:
                return False
            return has_role(payload, 'admin')
        except Exception:
            return False

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
    def _collection_permission_flag_clause(access: str):
        if access == 'delete':
            return RAGCollectionPermission.can_delete.is_(True)
        if access == 'edit':
            return or_(
                RAGCollectionPermission.can_edit.is_(True),
                RAGCollectionPermission.can_delete.is_(True)
            )
        if access == 'share':
            return RAGCollectionPermission.can_share.is_(True)
        return or_(
            RAGCollectionPermission.can_view.is_(True),
            RAGCollectionPermission.can_edit.is_(True),
            RAGCollectionPermission.can_delete.is_(True)
        )

    @staticmethod
    def _collection_permission_exists_clause(username: str, role_names: Set[str], access: str):
        flag_clause = RAGAccessService._collection_permission_flag_clause(access)
        targets = [and_(
            RAGCollectionPermission.permission_type == 'user',
            RAGCollectionPermission.target_identifier == username
        )]
        if role_names:
            targets.append(and_(
                RAGCollectionPermission.permission_type == 'role',
                RAGCollectionPermission.target_identifier.in_(sorted(role_names))
            ))
        return exists(
            select(1).where(and_(
                RAGCollectionPermission.collection_id == RAGCollection.id,
                or_(*targets),
                flag_clause
            ))
        )

    @staticmethod
    def _collection_permission_ids_subquery(username: str, role_names: Set[str], access: str):
        flag_clause = RAGAccessService._collection_permission_flag_clause(access)
        targets = [and_(
            RAGCollectionPermission.permission_type == 'user',
            RAGCollectionPermission.target_identifier == username
        )]
        if role_names:
            targets.append(and_(
                RAGCollectionPermission.permission_type == 'role',
                RAGCollectionPermission.target_identifier.in_(sorted(role_names))
            ))
        return select(RAGCollectionPermission.collection_id).where(and_(
            or_(*targets),
            flag_clause
        ))

    @staticmethod
    def _collection_permission_clause_for_document(username: str, role_names: Set[str], access: str):
        collection_ids = RAGAccessService._collection_permission_ids_subquery(username, role_names, access).subquery()
        collection_id_select = select(collection_ids.c.collection_id)

        linked_exists = exists(
            select(1).select_from(CollectionDocumentLink).where(and_(
                CollectionDocumentLink.document_id == RAGDocument.id,
                CollectionDocumentLink.collection_id.in_(collection_id_select)
            ))
        )

        return or_(
            RAGDocument.collection_id.in_(collection_id_select),
            linked_exists
        )

    @staticmethod
    def _has_collection_permission(username: str, collection_id: int, access: str) -> bool:
        role_names = RAGAccessService._get_user_role_names(username)
        flag_clause = RAGAccessService._collection_permission_flag_clause(access)
        targets = [and_(
            RAGCollectionPermission.permission_type == 'user',
            RAGCollectionPermission.target_identifier == username
        )]
        if role_names:
            targets.append(and_(
                RAGCollectionPermission.permission_type == 'role',
                RAGCollectionPermission.target_identifier.in_(sorted(role_names))
            ))

        permission_exists = exists(
            select(1).where(and_(
                RAGCollectionPermission.collection_id == collection_id,
                or_(*targets),
                flag_clause
            ))
        )
        return db.session.execute(select(permission_exists)).scalar() is True

    @staticmethod
    def _has_collection_permission_for_linked_document(username: str, document_id: int, access: str) -> bool:
        role_names = RAGAccessService._get_user_role_names(username)
        collection_ids = RAGAccessService._collection_permission_ids_subquery(username, role_names, access).subquery()
        collection_id_select = select(collection_ids.c.collection_id)

        permission_exists = exists(
            select(1).select_from(CollectionDocumentLink).where(and_(
                CollectionDocumentLink.document_id == document_id,
                CollectionDocumentLink.collection_id.in_(collection_id_select)
            ))
        )
        return db.session.execute(select(permission_exists)).scalar() is True

    @staticmethod
    def apply_document_access_filter(query, username: Optional[str], access: str = 'view'):
        if not username:
            return query.filter(False)
        if RAGAccessService.is_admin_user(username):
            return query

        role_names = RAGAccessService._get_user_role_names(username)
        permission_exists = RAGAccessService._permission_exists_clause(username, role_names, access)

        collection_permission = RAGAccessService._collection_permission_clause_for_document(
            username, role_names, access
        )

        clauses = [
            RAGDocument.uploaded_by == username,
            permission_exists,
            collection_permission
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
        if document.collection_id and RAGAccessService._has_collection_permission(username, document.collection_id, 'view'):
            return True
        if RAGAccessService._has_collection_permission_for_linked_document(username, document.id, 'view'):
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
        if document.collection_id and RAGAccessService._has_collection_permission(username, document.collection_id, 'edit'):
            return True
        if RAGAccessService._has_collection_permission_for_linked_document(username, document.id, 'edit'):
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
        if document.collection_id and RAGAccessService._has_collection_permission(username, document.collection_id, 'delete'):
            return True
        if RAGAccessService._has_collection_permission_for_linked_document(username, document.id, 'delete'):
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
        if document.collection_id and RAGAccessService._has_collection_permission(username, document.collection_id, 'share'):
            return True
        if RAGAccessService._has_collection_permission_for_linked_document(username, document.id, 'share'):
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

        role_names = RAGAccessService._get_user_role_names(username)
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

        collection_permission_exists = RAGAccessService._collection_permission_exists_clause(
            username, role_names, 'view'
        )

        return query.filter(or_(
            RAGCollection.created_by == username,
            RAGCollection.is_public.is_(True),
            has_accessible_doc,
            collection_permission_exists
        ))

    @staticmethod
    def can_view_collection(username: Optional[str], collection: Optional[RAGCollection]) -> bool:
        if not username or not collection:
            return False
        if RAGAccessService.is_admin_user(username):
            return True
        if collection.created_by == username or collection.is_public:
            return True
        if RAGAccessService._has_collection_permission(username, collection.id, 'view'):
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
        if collection.created_by == username:
            return True
        return RAGAccessService._has_collection_permission(username, collection.id, 'edit')

    @staticmethod
    def can_delete_collection(username: Optional[str], collection: Optional[RAGCollection]) -> bool:
        if not username or not collection:
            return False
        if RAGAccessService.is_admin_user(username):
            return True
        if collection.created_by == username:
            return True
        return RAGAccessService._has_collection_permission(username, collection.id, 'delete')

    @staticmethod
    def can_share_collection(username: Optional[str], collection: Optional[RAGCollection]) -> bool:
        if not username or not collection:
            return False
        if RAGAccessService.is_admin_user(username):
            return True
        if collection.created_by == username:
            return True
        return RAGAccessService._has_collection_permission(username, collection.id, 'share')

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

    @staticmethod
    def get_collection_permissions(collection_id: int) -> dict:
        rows = (
            RAGCollectionPermission.query
            .filter_by(collection_id=collection_id)
            .order_by(RAGCollectionPermission.permission_type, RAGCollectionPermission.target_identifier)
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
    def ensure_collection_view_access(
        collection_id: int,
        usernames=None,
        role_names=None,
        granted_by: Optional[str] = None
    ) -> dict:
        """
        Ensure users/roles have at least view access to a collection.
        This ADDS permissions without removing or downgrading existing ones.

        Use this when chatbots are shared - it won't overwrite existing edit permissions.
        """
        usernames = RAGAccessService._normalize_strings(usernames)
        role_names = RAGAccessService._normalize_strings(role_names)

        existing = RAGCollectionPermission.query.filter_by(collection_id=collection_id).all()
        existing_map = {(r.permission_type, r.target_identifier): r for r in existing}

        added_users = []
        added_roles = []

        # Add permissions for users who don't have any
        for username in usernames:
            key = ('user', username)
            if key not in existing_map:
                db.session.add(RAGCollectionPermission(
                    collection_id=collection_id,
                    permission_type='user',
                    target_identifier=username,
                    can_view=True,
                    can_edit=False,
                    can_delete=False,
                    can_share=False,
                    granted_by=granted_by
                ))
                added_users.append(username)

        # Add permissions for roles who don't have any
        for role_name in role_names:
            key = ('role', role_name)
            if key not in existing_map:
                db.session.add(RAGCollectionPermission(
                    collection_id=collection_id,
                    permission_type='role',
                    target_identifier=role_name,
                    can_view=True,
                    can_edit=False,
                    can_delete=False,
                    can_share=False,
                    granted_by=granted_by
                ))
                added_roles.append(role_name)

        if added_users or added_roles:
            db.session.commit()

        return {
            'added_users': added_users,
            'added_roles': added_roles,
            'already_had_access': {
                'users': [u for u in usernames if u not in added_users],
                'roles': [r for r in role_names if r not in added_roles]
            }
        }

    @staticmethod
    def remove_view_only_collection_access(
        collection_id: int,
        usernames=None,
        role_names=None
    ) -> dict:
        """
        Remove view-only access from a collection for specified users/roles.
        ONLY removes permissions that are view-only (can_view=True but can_edit/can_delete/can_share=False).
        Keeps any elevated permissions (edit, delete, share).

        Use this when chatbot sharing is removed.
        """
        usernames = RAGAccessService._normalize_strings(usernames)
        role_names = RAGAccessService._normalize_strings(role_names)

        existing = RAGCollectionPermission.query.filter_by(collection_id=collection_id).all()
        removed_users = []
        removed_roles = []

        for perm in existing:
            should_check = False
            if perm.permission_type == 'user' and perm.target_identifier in usernames:
                should_check = True
            elif perm.permission_type == 'role' and perm.target_identifier in role_names:
                should_check = True

            if should_check:
                # Only remove if it's view-only (no elevated permissions)
                if perm.can_view and not perm.can_edit and not perm.can_delete and not perm.can_share:
                    if perm.permission_type == 'user':
                        removed_users.append(perm.target_identifier)
                    else:
                        removed_roles.append(perm.target_identifier)
                    db.session.delete(perm)

        if removed_users or removed_roles:
            db.session.commit()

        return {
            'removed_users': removed_users,
            'removed_roles': removed_roles
        }

    @staticmethod
    def get_chatbot_required_access(collection_id: int) -> dict:
        """
        Get users/roles who need collection access because a chatbot using
        this collection is shared with them.

        Returns: {'users': [username, ...], 'roles': [role_name, ...], 'chatbots': [{id, name}, ...]}
        """
        from db.tables import Chatbot, ChatbotUserAccess, ChatbotCollection

        # Find chatbots using this collection
        chatbot_links = ChatbotCollection.query.filter_by(collection_id=collection_id).all()
        chatbot_ids = [link.chatbot_id for link in chatbot_links]

        if not chatbot_ids:
            return {'users': [], 'roles': [], 'chatbots': []}

        chatbots = Chatbot.query.filter(Chatbot.id.in_(chatbot_ids)).all()
        required_users = set()
        required_roles = set()
        chatbot_info = []

        for chatbot in chatbots:
            chatbot_info.append({'id': chatbot.id, 'name': chatbot.name})

            # Get users with access to this chatbot
            user_access = ChatbotUserAccess.query.filter_by(chatbot_id=chatbot.id).all()
            for access in user_access:
                required_users.add(access.username)

            # Get roles with access to this chatbot
            if chatbot.allowed_roles:
                if isinstance(chatbot.allowed_roles, list):
                    required_roles.update(chatbot.allowed_roles)
                elif isinstance(chatbot.allowed_roles, str):
                    required_roles.add(chatbot.allowed_roles)

        return {
            'users': sorted(required_users),
            'roles': sorted(required_roles),
            'chatbots': chatbot_info
        }

    @staticmethod
    def set_collection_permissions(
        collection_id: int,
        usernames=None,
        role_names=None,
        granted_by: Optional[str] = None,
        access: Optional[dict] = None,
        skip_chatbot_check: bool = False
    ) -> dict:
        usernames = RAGAccessService._normalize_strings(usernames)
        role_names = RAGAccessService._normalize_strings(role_names)

        # Check if we're removing access from users/roles who need it for chatbot access
        if not skip_chatbot_check:
            required = RAGAccessService.get_chatbot_required_access(collection_id)
            missing_users = [u for u in required['users'] if u not in usernames]
            missing_roles = [r for r in required['roles'] if r not in role_names]

            if missing_users or missing_roles:
                chatbot_names = ', '.join([c['name'] for c in required['chatbots']])
                error_parts = []
                if missing_users:
                    error_parts.append(f"User: {', '.join(missing_users)}")
                if missing_roles:
                    error_parts.append(f"Rollen: {', '.join(missing_roles)}")
                raise ValueError(
                    f"Collection-Zugriff kann nicht entfernt werden für {' und '.join(error_parts)} - "
                    f"Chatbot(s) '{chatbot_names}' sind mit diesen Usern/Rollen geteilt. "
                    f"Entferne zuerst den Chatbot-Zugriff."
                )
        access = access or {}
        can_view = bool(access.get('can_view', True))
        can_edit = bool(access.get('can_edit', True))
        can_delete = bool(access.get('can_delete', False))
        can_share = bool(access.get('can_share', False))

        existing = RAGCollectionPermission.query.filter_by(collection_id=collection_id).all()
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
                db.session.add(RAGCollectionPermission(
                    collection_id=collection_id,
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

    @staticmethod
    def set_collection_permissions_batch(
        collection_id: int,
        user_permissions: list = None,
        role_names: list = None,
        granted_by: Optional[str] = None
    ) -> dict:
        """
        Set collection permissions with individual access levels per user.

        Args:
            collection_id: Collection ID
            user_permissions: List of dicts with keys:
                - target: username
                - can_view: bool (default True)
                - can_edit: bool (default False)
                - can_delete: bool (default False)
                - can_share: bool (default False)
            role_names: List of role names (all get view-only access)
            granted_by: Username who granted the permission

        Returns:
            Dict with saved permissions
        """
        user_permissions = user_permissions or []
        role_names = RAGAccessService._normalize_strings(role_names)

        # Validate and normalize user permissions
        normalized_users = []
        for up in user_permissions:
            if not up.get('target'):
                continue
            normalized_users.append({
                'target': str(up['target']).strip(),
                'can_view': bool(up.get('can_view', True)),
                'can_edit': bool(up.get('can_edit', False)),
                'can_delete': bool(up.get('can_delete', False)),
                'can_share': bool(up.get('can_share', False))
            })

        usernames = [u['target'] for u in normalized_users]

        # Check chatbot requirements
        required = RAGAccessService.get_chatbot_required_access(collection_id)
        missing_users = [u for u in required['users'] if u not in usernames]
        missing_roles = [r for r in required['roles'] if r not in role_names]

        if missing_users or missing_roles:
            chatbot_names = ', '.join([c['name'] for c in required['chatbots']])
            error_parts = []
            if missing_users:
                error_parts.append(f"User: {', '.join(missing_users)}")
            if missing_roles:
                error_parts.append(f"Rollen: {', '.join(missing_roles)}")
            raise ValueError(
                f"Collection-Zugriff kann nicht entfernt werden für {' und '.join(error_parts)} - "
                f"Chatbot(s) '{chatbot_names}' sind mit diesen Usern/Rollen geteilt."
            )

        # Get existing permissions
        existing = RAGCollectionPermission.query.filter_by(collection_id=collection_id).all()
        existing_map = {(r.permission_type, r.target_identifier): r for r in existing}

        # Build target sets for cleanup
        target_sets = {
            'user': set(usernames),
            'role': set(role_names)
        }

        # Create lookup for user permissions
        user_perm_map = {u['target']: u for u in normalized_users}

        # Update or delete existing
        for row in existing:
            key = (row.permission_type, row.target_identifier)
            if row.permission_type == 'user':
                if row.target_identifier in user_perm_map:
                    up = user_perm_map[row.target_identifier]
                    row.can_view = up['can_view']
                    row.can_edit = up['can_edit']
                    row.can_delete = up['can_delete']
                    row.can_share = up['can_share']
                    row.granted_by = granted_by
                else:
                    db.session.delete(row)
            elif row.permission_type == 'role':
                if row.target_identifier in role_names:
                    row.can_view = True
                    row.can_edit = False
                    row.can_delete = False
                    row.can_share = False
                    row.granted_by = granted_by
                else:
                    db.session.delete(row)

        # Add new user permissions
        for up in normalized_users:
            key = ('user', up['target'])
            if key not in existing_map:
                db.session.add(RAGCollectionPermission(
                    collection_id=collection_id,
                    permission_type='user',
                    target_identifier=up['target'],
                    can_view=up['can_view'],
                    can_edit=up['can_edit'],
                    can_delete=up['can_delete'],
                    can_share=up['can_share'],
                    granted_by=granted_by
                ))

        # Add new role permissions
        for role_name in role_names:
            key = ('role', role_name)
            if key not in existing_map:
                db.session.add(RAGCollectionPermission(
                    collection_id=collection_id,
                    permission_type='role',
                    target_identifier=role_name,
                    can_view=True,
                    can_edit=False,
                    can_delete=False,
                    can_share=False,
                    granted_by=granted_by
                ))

        db.session.commit()
        return {
            'users': normalized_users,
            'roles': [{'target': r, 'can_view': True, 'can_edit': False} for r in role_names]
        }
