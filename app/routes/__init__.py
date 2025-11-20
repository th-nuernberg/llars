from flask import Blueprint

# Blueprint erstellen
auth_blueprint = Blueprint('auth', __name__)
data_blueprint = Blueprint('data', __name__)

# Import route modules
from . import routes, RankingRoutes, RatingRoutes, UserPromptRoutes

# Import refactored scenario modules
from .scenarios import scenario_crud, scenario_management, scenario_resources, scenario_stats

# Import refactored mail rating modules
from .mail_rating import mail_rating_threads, mail_rating_history, mail_rating_messages, mail_rating_stats