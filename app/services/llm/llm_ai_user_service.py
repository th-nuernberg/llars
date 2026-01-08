"""
LLM AI User Service

Creates and manages AI "users" bound to LLM models for scenario assignments.
"""

from __future__ import annotations

import logging
import secrets
from typing import Any, Dict, List, Optional
from uuid import uuid4

from db.database import db
from db.models import User, UserGroup
from db.models.llm_model import LLMModel
from services.llm.llm_access_service import LLMAccessService
from services.user_profile_service import pick_collab_color

logger = logging.getLogger(__name__)


class LLMAIUserService:
    """Sync AI users with available LLM models."""

    USERNAME_PREFIX = "ai:"
    GROUP_NAME = "AI"

    @staticmethod
    def _build_username(model: LLMModel) -> str:
        return f"{LLMAIUserService.USERNAME_PREFIX}{model.model_id}"

    @staticmethod
    def _get_or_create_group() -> UserGroup:
        group = UserGroup.query.filter_by(name=LLMAIUserService.GROUP_NAME).first()
        if group:
            return group
        group = UserGroup(name=LLMAIUserService.GROUP_NAME)
        db.session.add(group)
        db.session.commit()
        return group

    @staticmethod
    def sync_ai_users(include_inactive_models: bool = False) -> int:
        models_query = LLMModel.query.filter_by(model_type=LLMModel.MODEL_TYPE_LLM)
        if not include_inactive_models:
            models_query = models_query.filter_by(is_active=True)
        models = models_query.all()

        existing_users = User.query.filter_by(is_ai=True).all()
        by_model_id = {u.llm_model_id: u for u in existing_users if u.llm_model_id}

        group = LLMAIUserService._get_or_create_group()
        created = 0
        updated_any = False

        for model in models:
            ai_user = by_model_id.get(model.model_id)
            username = LLMAIUserService._build_username(model)
            if ai_user is None:
                ai_user = User(
                    username=username,
                    api_key=str(uuid4()),
                    group=group,
                    is_active=True,
                    is_ai=True,
                    llm_model_id=model.model_id,
                    collab_color=pick_collab_color(),
                )
                ai_user.set_password(secrets.token_urlsafe(24))
                db.session.add(ai_user)
                created += 1
                continue

            updated = False
            if ai_user.username != username:
                ai_user.username = username
                updated = True
            if not ai_user.is_active:
                ai_user.is_active = True
                updated = True
            if ai_user.llm_model_id != model.model_id:
                ai_user.llm_model_id = model.model_id
                updated = True
            if ai_user.group_id != group.id:
                ai_user.group = group
                updated = True
            if updated:
                db.session.add(ai_user)
                updated_any = True

        if created or updated_any:
            db.session.commit()
        return created

    @staticmethod
    def list_ai_users_for_username(username: Optional[str]) -> List[Dict[str, Any]]:
        LLMAIUserService.sync_ai_users()

        models = LLMModel.query.filter_by(model_type=LLMModel.MODEL_TYPE_LLM).all()
        model_map = {m.model_id: m for m in models}

        ai_users = User.query.filter_by(is_ai=True, is_active=True).all()
        result: List[Dict[str, Any]] = []

        for user in ai_users:
            model_id = user.llm_model_id
            if not model_id:
                continue
            model = model_map.get(model_id)
            if not model or not model.is_active:
                continue
            if username and not LLMAccessService.user_can_access_model(username, model_id):
                continue
            result.append({
                "id": user.id,
                "username": user.username,
                "is_ai": True,
                "llm_model_id": model.model_id,
                "llm_display_name": model.display_name,
                "provider": model.provider,
                "provider_id": model.provider_id,
            })

        result.sort(key=lambda item: (item.get("llm_display_name") or item.get("username")))
        return result

    @staticmethod
    def get_ai_user_model_id(user_id: int) -> Optional[str]:
        if not user_id:
            return None
        user = User.query.filter_by(id=user_id, is_ai=True).first()
        return user.llm_model_id if user else None
