"""
Public LLARS v1 API.

All routes mounted under ``/api/v1`` and authenticated via API key (or OAuth
bearer for browser-based callers). Scope enforcement is applied per route via
``@require_api_scope(...)`` — see ``app/auth/decorators.py`` for the scope
vocabulary and the OAuth fallback semantics.
"""

from flask import Blueprint

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")

# Side-effect imports register the routes onto the blueprint above.
# Keep these AFTER the blueprint definition so circular imports don't bite.
from . import scenarios_routes  # noqa: E402,F401
from . import scenario_items_routes  # noqa: E402,F401
from . import scenario_assessors_routes  # noqa: E402,F401
from . import scenario_referral_routes  # noqa: E402,F401
from . import scenario_copilot_routes  # noqa: E402,F401
from . import scenario_parts_routes  # noqa: E402,F401
from . import scenario_results_routes  # noqa: E402,F401
from . import chatbots_routes  # noqa: E402,F401
from . import chatbot_collections_routes  # noqa: E402,F401
from . import chatbot_access_routes  # noqa: E402,F401
from . import chatbot_conversations_routes  # noqa: E402,F401
from . import chatbot_chat_routes  # noqa: E402,F401
from . import chatbot_wizard_routes  # noqa: E402,F401

__all__ = ["api_v1_bp"]
