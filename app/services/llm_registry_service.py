"""
LLM Model Registry Service.

Central "table of truth" for resolving display metadata (name, color,
provider name) for any model_id.  Used by stats, provenance, and evaluation
endpoints so the frontend receives consistent formatting hints.
"""

from __future__ import annotations

from typing import Any, Dict, List

from db.database import db
from db.models.llm_model import LLMModel
from db.models.user_llm_provider import UserLLMProvider


def resolve_model_registry(model_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Resolve display metadata for a list of model IDs.

    Returns a dict keyed by *model_id* with values::

        {
            "display_name": str,   # best-effort human-readable name
            "color": str,          # stable hex color
            "user_provider_name": str | None,  # e.g. "IONOS" for user-provider models
        }

    The function batch-loads DB models and user-provider rows to avoid N+1
    queries.
    """
    if not model_ids:
        return {}

    unique_ids = list(dict.fromkeys(model_ids))  # deduplicate, preserve order

    # 1. Batch-load Global / seeded LLM models from DB
    db_models = LLMModel.query.filter(LLMModel.model_id.in_(unique_ids)).all()
    db_map: Dict[str, LLMModel] = {m.model_id: m for m in db_models}

    # 2. Collect user-provider DB IDs for batch-load
    user_provider_ids: set[int] = set()
    for mid in unique_ids:
        if mid.startswith('user-provider:'):
            parts = mid.split(':')
            if len(parts) >= 2 and parts[1].isdigit():
                user_provider_ids.add(int(parts[1]))

    # 3. Batch-load UserLLMProvider rows
    provider_map: Dict[int, UserLLMProvider] = {}
    if user_provider_ids:
        providers = (
            db.session.query(UserLLMProvider)
            .filter(UserLLMProvider.id.in_(user_provider_ids))
            .all()
        )
        provider_map = {p.id: p for p in providers}

    # 4. Build registry
    registry: Dict[str, Dict[str, Any]] = {}
    for mid in unique_ids:
        if mid in db_map:
            m = db_map[mid]
            registry[mid] = {
                'display_name': m.display_name,
                'color': m.color or LLMModel.generate_color(mid),
                'user_provider_name': None,
            }
        elif mid.startswith('user-provider:'):
            parts = mid.split(':')
            provider_name = None
            if len(parts) >= 2 and parts[1].isdigit():
                provider = provider_map.get(int(parts[1]))
                provider_name = provider.name if provider else None
            registry[mid] = {
                'display_name': mid,
                'color': LLMModel.generate_color(mid),
                'user_provider_name': provider_name,
            }
        else:
            registry[mid] = {
                'display_name': mid,
                'color': LLMModel.generate_color(mid),
                'user_provider_name': None,
            }

    return registry
