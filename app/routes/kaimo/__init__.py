"""KAIMO Routes Module

Provides KAIMO admin and user panel API endpoints.
"""

from flask import Blueprint

# Main KAIMO blueprint
kaimo_bp = Blueprint('kaimo', __name__, url_prefix='/api/kaimo')

# Import sub-blueprints
from routes.kaimo.kaimo_admin_routes import kaimo_admin_bp
from routes.kaimo.kaimo_user_routes import kaimo_user_bp

# Register sub-blueprints
kaimo_bp.register_blueprint(kaimo_admin_bp)
kaimo_bp.register_blueprint(kaimo_user_bp)

__all__ = ['kaimo_bp']
