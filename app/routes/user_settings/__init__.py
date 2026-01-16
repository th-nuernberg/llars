"""User Settings Routes Package."""

from flask import Blueprint

from .settings_routes import settings_bp
from .user_provider_routes import user_provider_bp
from .user_referral_routes import user_referral_bp

user_settings_bp = Blueprint('user_settings', __name__, url_prefix='/api/user')

# Register sub-blueprints
user_settings_bp.register_blueprint(settings_bp)
user_settings_bp.register_blueprint(user_provider_bp)
user_settings_bp.register_blueprint(user_referral_bp)
