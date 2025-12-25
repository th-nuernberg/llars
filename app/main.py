from flask import Flask, request
from flask_socketio import SocketIO
from db.db import configure_database
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from socketio_handlers import configure_socket_routes
from routes.registry import register_all_blueprints
from services.api_metrics_service import create_metrics_middleware
import os

app = Flask(__name__)

# Initialize API metrics collection middleware
create_metrics_middleware(app)

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
socketio_async_mode = os.environ.get('SOCKETIO_ASYNC_MODE', 'threading')
socketio_allow_upgrades = socketio_async_mode != 'threading'
socketio_transports = None
if socketio_async_mode == 'threading':
    socketio_transports = ['polling']

socketio = SocketIO(
    app,
    cors_allowed_origins=socket_cors,
    async_mode=socketio_async_mode,
    ping_timeout=120,  # 2 minutes - allow for long LLM responses
    ping_interval=30,  # Send ping every 30 seconds
    allow_upgrades=socketio_allow_upgrades,
    transports=socketio_transports,
    # Keep Socket.IO/Engine.IO debug logs opt-in: enabling them can flood container logs and
    # can create feedback loops in the Docker Monitor when streaming backend logs.
    logger=str(os.environ.get('SOCKETIO_LOGGER', 'false')).lower() == 'true',
    engineio_logger=str(os.environ.get('ENGINEIO_LOGGER', 'false')).lower() == 'true'
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
    # Exempt email thread endpoints (frequently accessed by judge workers)
    if request.path and '/api/email_threads/' in request.path:
        return True
    # Exempt chatbot wizard endpoints (high-frequency polling/updates)
    if request.path and '/api/chatbots/' in request.path and '/wizard/' in request.path:
        return True
    # Exempt crawler job status polling endpoints
    if request.path and request.path.startswith('/api/crawler/jobs'):
        return True
    return False

# JWT Configuration (for legacy auth routes)
# TODO: Complete migration to Authentik and remove legacy JWT auth
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
jwt = JWTManager(app)

configure_database(app)

# Register all blueprints via central registry
register_all_blueprints(app)


# Configure all SocketIO event handlers
# IMPORTANT: Must be inside app_context so ChatManager -> RAGPipeline can query llm_models
with app.app_context():
    configure_socket_routes(socketio)

# Initialize Crawler service with SocketIO for live updates
# (Crawler events are registered in configure_socket_routes,
# this only injects the socketio instance into the crawler service)
from routes.crawler.crawler_routes import init_crawler_socketio
init_crawler_socketio(socketio)

# Initialize Embedding Worker for background document processing
# The worker automatically processes pending documents and creates embeddings
def _should_start_background_threads() -> bool:
    """
    Prevent duplicate background threads when the Flask reloader is active.

    In development, `flask run` spawns a reloader parent process and a child process.
    The child sets `WERKZEUG_RUN_MAIN=true`. Background threads must only start once.
    """
    if os.environ.get('FLASK_ENV', 'production') == 'development':
        return os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    return True


if _should_start_background_threads():
    from workers.embedding_worker import start_embedding_worker
    start_embedding_worker(app)

# Initialize Stale Job Detector for LLM-as-Judge
# Checks every 5 minutes for comparisons stuck in RUNNING state and resets them
    from services.judge.stale_job_detection import start_stale_job_detector
    start_stale_job_detector(app)

# Initialize KIA Auto-Sync for LLM-as-Judge
# Automatically syncs KIA data from GitLab if no pillar threads exist
    from services.judge.kia_auto_sync import start_kia_auto_sync
    start_kia_auto_sync(app)

# Fix missing chroma_collection_name for existing collections
# This is a one-time migration for collections created before the fix
def fix_missing_chroma_collection_names():
    """Set chroma_collection_name for collections where it's missing."""
    from db.tables import RAGCollection
    from db.db import db
    from db.models.llm_model import seed_default_models
    from rag_pipeline import RAGPipeline
    from services.rag.collection_embedding_service import sanitize_chroma_collection_name

    with app.app_context():
        try:
            seed_default_models()
            pipeline = RAGPipeline()
            collections = RAGCollection.query.filter(
                RAGCollection.chroma_collection_name.is_(None),
                RAGCollection.embedding_status == 'completed'
            ).all()

            for collection in collections:
                chroma_name = sanitize_chroma_collection_name(collection.name, pipeline.model_name)
                collection.chroma_collection_name = chroma_name
                print(f"[Startup] Fixed chroma_collection_name for collection '{collection.name}': {chroma_name}")

            if collections:
                db.session.commit()
                print(f"[Startup] Fixed {len(collections)} collections with missing chroma_collection_name")
        except Exception as e:
            print(f"[Startup] Error fixing chroma_collection_names: {e}")

fix_missing_chroma_collection_names()


# Seed default LLM models into the database
def seed_llm_models():
    """Seed default LLM models on startup."""
    from db.models.llm_model import seed_default_models

    with app.app_context():
        try:
            print("[Startup] Seeding LLM models...")
            seed_default_models()
            print("[Startup] LLM models seeded successfully")
        except Exception as e:
            print(f"[Startup] Error seeding LLM models: {e}")

seed_llm_models()

if __name__ == '__main__':
    # Debug mode nur in development aktivieren
    debug_mode = os.environ.get('FLASK_ENV', 'production') == 'development'
    socketio.run(app, host='0.0.0.0', port=8081, debug=debug_mode)
