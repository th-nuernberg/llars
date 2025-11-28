from flask import Flask, request
from flask_socketio import SocketIO
from db.db import configure_database
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from socketio_handlers import configure_socket_routes
from routes import auth_blueprint, data_blueprint, judge_bp, oncoco_bp
import os

app = Flask(__name__)

# CORS configuration - restrict in production!
allowed_origins = os.environ.get('ALLOWED_ORIGINS', 'http://localhost,http://localhost:80,http://localhost:5173').split(',')
# Strip whitespace from origins
allowed_origins = [origin.strip() for origin in allowed_origins]
CORS(app, origins=allowed_origins, supports_credentials=True)

# Determine socket CORS settings based on environment
flask_env = os.environ.get('FLASK_ENV', 'production')
if flask_env == 'development':
    # Allow all origins in development for easier debugging
    socket_cors = '*'
else:
    socket_cors = allowed_origins

# SocketIO with increased timeouts for long-running LLM streams
# ping_timeout: How long to wait for pong before disconnecting (default: 20s)
# ping_interval: How often to send ping to keep connection alive (default: 25s)
# For LLM streaming, we need longer timeouts to prevent disconnections during generation
#
# async_mode options:
# - 'eventlet': Best performance but requires eventlet server and monkey-patching
# - 'gevent': Good performance, requires gevent server
# - 'threading': Works with any WSGI server, uses long-polling fallback for WebSocket
#
# For development with flask run, use 'threading' mode
# For production, use 'eventlet' or 'gevent' with appropriate server
socketio = SocketIO(
    app,
    cors_allowed_origins=socket_cors,
    async_mode='threading',  # Use threading for compatibility with flask run
    ping_timeout=120,  # 2 minutes - allow for long LLM responses
    ping_interval=30,  # Send ping every 30 seconds
    logger=flask_env == 'development',  # Enable logging in development
    engineio_logger=False
)

# Rate Limiting - Schützt vor Brute-Force und DoS
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",  # In production: Redis verwenden
)

# Exempt health check and judge session endpoints from rate limiting
@limiter.request_filter
def exempt_endpoints():
    """Exempt health check and high-frequency judge endpoints from rate limiting"""
    if not request.endpoint:
        return False
    # Exempt health checks
    if 'health_check' in request.endpoint:
        return True
    # Exempt judge session polling endpoints (queue, current, comparisons, workers)
    if request.path and '/api/judge/sessions/' in request.path:
        return True
    return False

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

# LLM-as-Judge routes
app.register_blueprint(judge_bp)

# OnCoCo Analysis routes
app.register_blueprint(oncoco_bp)

# Chatbot routes
from routes.chatbot.chatbot_routes import chatbot_blueprint
app.register_blueprint(chatbot_blueprint)

# Web Crawler routes
from routes.crawler.crawler_routes import crawler_blueprint, init_crawler_socketio
app.register_blueprint(crawler_blueprint)


# Configure all SocketIO event handlers
configure_socket_routes(socketio)

# Initialize Crawler service with SocketIO for live updates
# (Crawler events are registered in configure_socket_routes,
# this only injects the socketio instance into the crawler service)
init_crawler_socketio(socketio)

# Initialize Embedding Worker for background document processing
# The worker automatically processes pending documents and creates embeddings
from workers.embedding_worker import start_embedding_worker
start_embedding_worker(app)

if __name__ == '__main__':
    # Debug mode nur in development aktivieren
    debug_mode = os.environ.get('FLASK_ENV', 'production') == 'development'
    socketio.run(app, host='0.0.0.0', port=8081, debug=debug_mode)

