from flask import Blueprint

# Blueprint erstellen
auth_blueprint = Blueprint('auth', __name__)
data_blueprint = Blueprint('data', __name__)

from . import MailRatingRoutes, ScenarioRoutes, routes, RankingRoutes, RatingRoutes, UserPromptRoutes