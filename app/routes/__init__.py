from flask import Blueprint

# Blueprint erstellen
auth_blueprint = Blueprint('auth', __name__)
data_blueprint = Blueprint('data', __name__)

from . import mail_rating, routes, RankingRoutes, RatingRoutes, UserPromptRoutes, LLMComparisonRoutes, PermissionRoutes
from .rag import RAGRoutes