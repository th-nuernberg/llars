"""
LLM Access Service

Handles per-user/per-role visibility for LLM models.
"""

from typing import Any, Dict, List, Optional, Set

from db.database import db
from db.models.llm_model import LLMModel
from db.models.llm_model_permission import LLMModelPermission
from services.permission_service import PermissionService


class LLMAccessService:
    """Business logic for LLM model visibility."""

    ADMIN_PERMISSION = 'admin:system:configure'

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
    def _normalize_role_names(values: Any) -> List[str]:
        roles = LLMAccessService._normalize_strings(values)
        normalized: Set[str] = set()
        for role in roles:
            name = role.strip().lower()
            if not name:
                continue
            if name == 'viewer':
                name = 'evaluator'
            normalized.add(name)
        return sorted(normalized)

    @staticmethod
    def _get_user_role_names(username: Optional[str]) -> Set[str]:
        if not username:
            return set()
        roles = PermissionService.get_user_roles(username)
        role_names = set()
        for role in roles or []:
            name = (role.get('role_name') if isinstance(role, dict) else None) or ''
            if not name:
                continue
            role_names.add(name.strip().lower())
        return role_names

    @staticmethod
    def is_admin_user(username: Optional[str]) -> bool:
        if not username:
            return False
        return PermissionService.check_permission(username, LLMAccessService.ADMIN_PERMISSION)

    @staticmethod
    def user_can_access_model(username: Optional[str], model_id: Optional[str]) -> bool:
        if not username or not model_id:
            return False
        model = LLMModel.get_by_model_id(model_id)
        if not model or not model.is_active:
            return False
        if LLMAccessService.is_admin_user(username):
            return True

        permissions = (
            LLMModelPermission.query
            .filter_by(llm_model_id=model.id)
            .all()
        )
        if not permissions:
            return True

        allowed_usernames = {p.target_identifier for p in permissions if p.permission_type == 'user'}
        allowed_roles = {p.target_identifier for p in permissions if p.permission_type == 'role'}
        if username in allowed_usernames:
            return True

        user_roles = LLMAccessService._get_user_role_names(username)
        return bool(user_roles.intersection({r.lower() for r in allowed_roles}))

    @staticmethod
    def get_allowed_usernames(model_id: int) -> List[str]:
        rows = (
            LLMModelPermission.query
            .filter_by(llm_model_id=model_id, permission_type='user')
            .order_by(LLMModelPermission.target_identifier.asc())
            .all()
        )
        return [r.target_identifier for r in rows]

    @staticmethod
    def get_allowed_roles(model_id: int) -> List[str]:
        rows = (
            LLMModelPermission.query
            .filter_by(llm_model_id=model_id, permission_type='role')
            .order_by(LLMModelPermission.target_identifier.asc())
            .all()
        )
        return [r.target_identifier for r in rows]

    @staticmethod
    def set_model_access(
        model_id: int,
        *,
        usernames: Any = None,
        role_names: Any = None,
        granted_by: Optional[str] = None,
    ) -> Dict[str, List[str]]:
        model = LLMModel.query.get(model_id)
        if not model:
            raise ValueError('LLM model not found')

        normalized_users = LLMAccessService._normalize_strings(usernames)
        normalized_roles = LLMAccessService._normalize_role_names(role_names)

        existing = LLMModelPermission.query.filter_by(llm_model_id=model_id).all()
        for row in existing:
            db.session.delete(row)

        for username in normalized_users:
            db.session.add(LLMModelPermission(
                llm_model_id=model_id,
                permission_type='user',
                target_identifier=username,
                granted_by=granted_by
            ))

        for role_name in normalized_roles:
            db.session.add(LLMModelPermission(
                llm_model_id=model_id,
                permission_type='role',
                target_identifier=role_name,
                granted_by=granted_by
            ))

        db.session.commit()

        return {
            'allowed_usernames': normalized_users,
            'allowed_roles': normalized_roles
        }

    @staticmethod
    def get_accessible_models(
        username: Optional[str],
        *,
        active_only: bool = True,
        model_type: Optional[str] = None,
        vision_only: bool = False,
        reasoning_only: bool = False,
    ) -> List[LLMModel]:
        query = LLMModel.query
        if active_only:
            query = query.filter_by(is_active=True)
        if model_type:
            query = query.filter_by(model_type=model_type)
        if vision_only:
            query = query.filter_by(supports_vision=True)
        if reasoning_only:
            query = query.filter_by(supports_reasoning=True)

        models = query.order_by(LLMModel.is_default.desc(), LLMModel.display_name).all()

        if LLMAccessService.is_admin_user(username):
            return models

        if not models or not username:
            return []

        model_ids = [m.id for m in models]
        permissions = (
            LLMModelPermission.query
            .filter(LLMModelPermission.llm_model_id.in_(model_ids))
            .all()
        )

        allowed_usernames: Dict[int, Set[str]] = {mid: set() for mid in model_ids}
        allowed_roles: Dict[int, Set[str]] = {mid: set() for mid in model_ids}

        for perm in permissions:
            if perm.permission_type == 'user':
                allowed_usernames.setdefault(perm.llm_model_id, set()).add(perm.target_identifier)
            elif perm.permission_type == 'role':
                allowed_roles.setdefault(perm.llm_model_id, set()).add(perm.target_identifier)

        user_roles = LLMAccessService._get_user_role_names(username)
        accessible: List[LLMModel] = []
        for model in models:
            users = allowed_usernames.get(model.id, set())
            roles = allowed_roles.get(model.id, set())

            if not users and not roles:
                accessible.append(model)
                continue

            if username in users:
                accessible.append(model)
                continue

            if roles and user_roles.intersection({r.lower() for r in roles}):
                accessible.append(model)

        return accessible
