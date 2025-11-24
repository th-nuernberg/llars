from flask import Flask, request
from flask_socketio import SocketIO
from db.db import configure_database
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from socketio_handlers import configure_socket_routes
from routes import auth_blueprint, data_blueprint
from routes_websocket_prompt_eng import configure_websocket_prompt_eng
import os

app = Flask(__name__)

# CORS configuration - restrict in production!
allowed_origins = os.environ.get('ALLOWED_ORIGINS', 'http://localhost,http://localhost:80,http://localhost:5173').split(',')
CORS(app, origins=allowed_origins, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins=allowed_origins)

# Rate Limiting - Schützt vor Brute-Force und DoS
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",  # In production: Redis verwenden
)

# JWT Configuration (for legacy auth routes)
# TODO: Complete migration to Authentik and remove legacy JWT auth
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
jwt = JWTManager(app)

configure_database(app)

# Configure routes
# Legacy auth routes (still available for backwards compatibility)
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(data_blueprint, url_prefix='/api')

# Authentik authentication routes
from routes.authentik_routes import authentik_auth_blueprint
app.register_blueprint(authentik_auth_blueprint, url_prefix='/auth/authentik')


configure_socket_routes(socketio)
configure_websocket_prompt_eng(socketio)

if __name__ == '__main__':
    # Debug mode nur in development aktivieren
    debug_mode = os.environ.get('FLASK_ENV', 'production') == 'development'
    socketio.run(app, host='0.0.0.0', port=8081, debug=debug_mode)

