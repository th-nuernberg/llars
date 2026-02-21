"""
Chatbot Access Service

Implements chatbot-level access control:
- Public chatbots are visible to all users with `feature:chatbots:view`
- Private chatbots require an explicit allowlist entry (username ↔ chatbot)
- Admins can always access (management override)
"""

from typing import List, Optional, Set, Any

from sqlalchemy import and_, or_, select

from db.database import db
from db.tables import Chatbot, ChatbotUserAccess, Role, UserRole, ChatbotCollection
from services.permission_service import PermissionService
from services.rag.access_service import RAGAccessService


class ChatbotAccessService:
    """Business logic for chatbot visibility and allowlist assignments."""

    @staticmethod
    def _normalize_strings(values: Any) -> List[str]:
        if not values:
            return []
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, (list, tuple, set)):
            return []
        return sorted({str(v).strip() for v in values if v and str(v).strip()})

    @staticmethod
    def _normalize_allowed_roles(value: Any) -> List[str]:
        if not value:
            return []
        if isinstance(value, dict):
            for key in ('roles', 'role_names', 'allowed_roles'):
                if key in value:
                    return ChatbotAccessService._normalize_strings(value.get(key))
            return []
        return ChatbotAccessService._normalize_strings(value)

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
    def user_is_owner(username: Optional[str], chatbot: Optional[Chatbot]) -> bool:
        if not username or not chatbot:
            return False
        return chatbot.created_by == username

    @staticmethod
    def user_can_manage_chatbot(username: Optional[str], chatbot: Optional[Chatbot]) -> bool:
        if not username or not chatbot:
            return False
        if ChatbotAccessService.is_admin_user(username):
            return True
        return ChatbotAccessService.user_is_owner(username, chatbot)

    @staticmethod
    def user_can_access_chatbot(username: Optional[str], chatbot: Optional[Chatbot]) -> bool:
        if not username or not chatbot:
            return False

        # Admin override
        if ChatbotAccessService.is_admin_user(username):
            return True

        # Owners can always access their own chatbots (even inactive)
        if ChatbotAccessService.user_is_owner(username, chatbot):
            return True

        # Only allow active chatbots for regular users
        if not chatbot.is_active:
            return False

        # Public chatbots are visible to all users
        if chatbot.is_public:
            return True

        # Role-based access for private chatbots
        allowed_roles = ChatbotAccessService._normalize_allowed_roles(chatbot.allowed_roles)
        if allowed_roles:
            user_roles = ChatbotAccessService._get_user_role_names(username)
            if user_roles.intersection(allowed_roles):
                return True

        # Private chatbots require explicit allowlist entry
        return (
            ChatbotUserAccess.query
            .filter_by(chatbot_id=chatbot.id, username=username)
            .first()
            is not None
        )

    @staticmethod
    def user_can_access_chatbot_id(username: Optional[str], chatbot_id: int) -> bool:
        chatbot = Chatbot.query.get(chatbot_id)
        return ChatbotAccessService.user_can_access_chatbot(username, chatbot)

    @staticmethod
    def get_accessible_chatbots(username: str, include_inactive: bool = False) -> List[Chatbot]:
        """
        Return chatbots visible to this user.

        Admin users get full list (optionally including inactive).
        Regular users get public chatbots + explicit allowlist, and only active unless include_inactive=True.
        """
        query = Chatbot.query

        if ChatbotAccessService.is_admin_user(username):
            if not include_inactive:
                query = query.filter(Chatbot.is_active == True)
            return query.order_by(Chatbot.created_at.desc()).all()

        if include_inactive:
            bots = query.order_by(Chatbot.created_at.desc()).all()
        else:
            bots = query.filter(Chatbot.is_active == True).order_by(Chatbot.created_at.desc()).all()

        allowed_user_rows = (
            ChatbotUserAccess.query
            .filter_by(username=username)
            .all()
        )
        allowed_chatbot_ids = {r.chatbot_id for r in allowed_user_rows}
        user_roles = ChatbotAccessService._get_user_role_names(username)

        result = []
        for bot in bots:
            is_owner = ChatbotAccessService.user_is_owner(username, bot)
            if is_owner:
                result.append(bot)
                continue
            if not bot.is_active:
                continue
            if bot.is_public:
                result.append(bot)
                continue
            if bot.id in allowed_chatbot_ids:
                result.append(bot)
                continue
            allowed_roles = ChatbotAccessService._normalize_allowed_roles(bot.allowed_roles)
            if allowed_roles and user_roles.intersection(allowed_roles):
                result.append(bot)
        return result

    @staticmethod
    def get_owned_chatbots(username: str) -> List[Chatbot]:
        if not username:
            return []
        return Chatbot.query.filter_by(created_by=username).order_by(Chatbot.created_at.desc()).all()

    @staticmethod
    def get_allowed_usernames_for_chatbot(chatbot_id: int) -> List[str]:
        rows = (
            ChatbotUserAccess.query
            .filter_by(chatbot_id=chatbot_id)
            .order_by(ChatbotUserAccess.username.asc())
            .all()
        )
        return [r.username for r in rows]

    @staticmethod
    def get_allowed_roles_for_chatbot(chatbot_id: int) -> List[str]:
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            return []
        return ChatbotAccessService._normalize_allowed_roles(chatbot.allowed_roles)

    @staticmethod
    def set_allowed_usernames_for_chatbot(chatbot_id: int, usernames: List[str], granted_by: Optional[str] = None) -> List[str]:
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            raise ValueError('Chatbot not found')

        normalized = ChatbotAccessService._normalize_strings(usernames)

        existing_rows = ChatbotUserAccess.query.filter_by(chatbot_id=chatbot_id).all()
        existing_usernames = {r.username for r in existing_rows}

        to_add = [u for u in normalized if u not in existing_usernames]
        to_remove = [r for r in existing_rows if r.username not in normalized]

        for row in to_remove:
            db.session.delete(row)

        for username in to_add:
            db.session.add(ChatbotUserAccess(
                chatbot_id=chatbot_id,
                username=username,
                granted_by=granted_by
            ))

        db.session.commit()
        return normalized

    @staticmethod
    def set_chatbot_access(
        chatbot_id: int,
        usernames: Optional[List[str]] = None,
        role_names: Optional[List[str]] = None,
        granted_by: Optional[str] = None,
    ) -> dict:
        """
        Replace both user and role allowlists for a chatbot in one transaction.

        Also synchronizes collection access:
        - Adds view-only access for new users/roles
        - Removes view-only access for removed users/roles (keeps elevated permissions)
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            raise ValueError('Chatbot not found')

        normalized_users = ChatbotAccessService._normalize_strings(usernames)
        normalized_roles = ChatbotAccessService._normalize_strings(role_names)

        # Get existing chatbot access
        existing_rows = ChatbotUserAccess.query.filter_by(chatbot_id=chatbot_id).all()
        existing_usernames = {r.username for r in existing_rows}
        existing_roles = set(ChatbotAccessService._normalize_allowed_roles(chatbot.allowed_roles))

        # Calculate what's being added and removed
        users_to_add = [u for u in normalized_users if u not in existing_usernames]
        users_to_remove = [r.username for r in existing_rows if r.username not in normalized_users]
        roles_to_add = [r for r in normalized_roles if r not in existing_roles]
        roles_to_remove = [r for r in existing_roles if r not in normalized_roles]

        # Update chatbot user access
        for row in existing_rows:
            if row.username not in normalized_users:
                db.session.delete(row)

        for username in users_to_add:
            db.session.add(ChatbotUserAccess(
                chatbot_id=chatbot_id,
                username=username,
                granted_by=granted_by
            ))

        chatbot.allowed_roles = normalized_roles or None

        # Synchronize collection access
        collection_links = ChatbotCollection.query.filter_by(chatbot_id=chatbot_id).all()
        shared_collections = []

        for link in collection_links:
            collection_id = link.collection_id
            shared_collections.append(collection_id)

            # Grant view access to new users/roles
            # This won't downgrade existing edit permissions
            if users_to_add or roles_to_add:
                RAGAccessService.ensure_collection_view_access(
                    collection_id=collection_id,
                    usernames=users_to_add,
                    role_names=roles_to_add,
                    granted_by=granted_by
                )

            # Remove view-only access from removed users/roles
            # This won't remove elevated permissions (edit, delete, share)
            if users_to_remove or roles_to_remove:
                RAGAccessService.remove_view_only_collection_access(
                    collection_id=collection_id,
                    usernames=users_to_remove,
                    role_names=roles_to_remove
                )

        db.session.commit()
        return {
            'allowed_usernames': normalized_users,
            'allowed_roles': normalized_roles,
            'shared_collections': shared_collections,
            'users_added': users_to_add,
            'users_removed': users_to_remove,
            'roles_added': roles_to_add,
            'roles_removed': roles_to_remove,
        }
