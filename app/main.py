from flask import Flask, request
from flask_socketio import SocketIO
from db.database import configure_database
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from socketio_handlers import configure_socket_routes
from routes.registry import register_all_blueprints
from services.api_metrics_service import create_metrics_middleware
from services.runtime_config import get_redis_client, get_redis_url, get_runtime_role, is_web_runtime
from werkzeug.middleware.proxy_fix import ProxyFix
import logging
import re
import os


class _SocketIOAccessLogFilter(logging.Filter):
    """Suppress noisy Socket.IO polling access logs."""

    _socketio_path_pattern = re.compile(r'"\w+\s+/socket\.io/', re.IGNORECASE)

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            return True
        return not bool(self._socketio_path_pattern.search(message))


def _configure_access_log_filters() -> None:
    suppress_socketio_access_logs = str(
        os.environ.get('SUPPRESS_SOCKETIO_ACCESS_LOGS', 'true')
    ).lower() in ('1', 'true', 'yes', 'on')
    if not suppress_socketio_access_logs:
        return

    filter_instance = _SocketIOAccessLogFilter()
    for logger_name in ('werkzeug', 'gunicorn.access'):
        logger = logging.getLogger(logger_name)
        has_socketio_filter = any(
            isinstance(existing_filter, _SocketIOAccessLogFilter)
            for existing_filter in logger.filters
        )
        if not has_socketio_filter:
            logger.addFilter(filter_instance)

app = Flask(__name__)
_configure_access_log_filters()

# Limit upload size to 50 MB to prevent oversized file uploads
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Trust one reverse proxy hop (nginx) by default so request.remote_addr
# resolves to the actual client IP instead of the container network IP.
proxy_fix_x_for = int(os.environ.get('PROXY_FIX_X_FOR', '1'))
if proxy_fix_x_for > 0:
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=proxy_fix_x_for,
        x_proto=1,
        x_host=1,
        x_port=1,
    )

# Initialize API metrics collection middleware
create_metrics_middleware(app)

# Initialize Redis client for server-authoritative sessions (Wizard Sessions, etc.)
# Redis provides persistent session storage that survives browser closures and server restarts
redis_client = get_redis_client()

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


def _skip_startup_tasks() -> bool:
    if get_runtime_role() == 'standby':
        return True
    return os.environ.get('LLARS_SKIP_STARTUP_TASKS', '').lower() in ('1', 'true', 'yes')


def _should_run_one_time_startup_tasks() -> bool:
    if _skip_startup_tasks() or not is_web_runtime():
        return False
    if os.environ.get('FLASK_ENV', 'production') == 'development':
        return os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    return True

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

socketio_message_queue = os.environ.get('SOCKETIO_MESSAGE_QUEUE', '').strip() or None
if socketio_message_queue is None and socketio_async_mode != 'threading':
    socketio_message_queue = get_redis_url()

socketio = SocketIO(
    app,
    cors_allowed_origins=socket_cors,
    async_mode=socketio_async_mode,
    message_queue=socketio_message_queue,
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
# In development mode, use much higher limits to support E2E testing
is_development = os.environ.get('FLASK_ENV', 'production') == 'development'
rate_limit_defaults = ["10000 per day", "1000 per hour"] if is_development else ["5000 per day", "500 per hour"]
rate_limit_storage_uri = os.environ.get('RATE_LIMIT_STORAGE_URI', '').strip()
if not rate_limit_storage_uri:
    rate_limit_storage_uri = "memory://" if is_development else get_redis_url(
        db_override=int(os.environ.get('REDIS_RATE_LIMIT_DB', os.environ.get('REDIS_DB', 0)))
    )


def _get_real_client_ip():
    """
    Ermittelt die echte Client-IP hinter dem nginx Reverse Proxy.

    Ohne diese Funktion sehen alle User wie eine einzige IP aus (nginx-Container-IP),
    und das Rate-Limit wird für ALLE User gemeinsam gezählt.
    """
    # X-Forwarded-For: client, proxy1, proxy2 → erstes Element = echte Client-IP
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    # X-Real-IP wird von nginx gesetzt wenn konfiguriert
    real_ip = request.headers.get('X-Real-Ip')
    if real_ip:
        return real_ip.strip()
    return get_remote_address()


limiter = Limiter(
    app=app,
    key_func=_get_real_client_ip,
    default_limits=rate_limit_defaults,
    storage_uri=rate_limit_storage_uri,
)

# Exempt high-frequency and internal endpoints from rate limiting
@limiter.request_filter
def exempt_endpoints():
    """Exempt health check, Socket.IO, and high-frequency endpoints from rate limiting."""
    path = request.path or ''
    # Exempt Socket.IO / WebSocket endpoints (check path BEFORE endpoint)
    if path.startswith('/socket.io'):
        return True
    if not request.endpoint:
        return False
    # Exempt health checks and version endpoint
    if 'health_check' in request.endpoint:
        return True
    if request.endpoint == 'data_bp.get_version':
        return True
    # Exempt SSE (Server-Sent Events) streaming endpoints
    if path.startswith('/api/latex-collab/compile/'):
        return True
    # Exempt judge session polling (queue, current, comparisons, workers)
    if '/api/judge/sessions/' in path:
        return True
    # Exempt evaluation session endpoints (frequent polling during active evaluation)
    if path.startswith('/api/evaluation/'):
        return True
    # Exempt scenario endpoints (stats polling, pagination)
    if path.startswith('/api/scenarios/'):
        return True
    # Exempt generation endpoints (pagination, WebSocket polling)
    if path.startswith('/api/generation/'):
        return True
    # Exempt data import endpoints (bulk uploads)
    if path.startswith('/api/import/'):
        return True
    return False

# Flask Secret Key (required for session management, e.g. Zotero OAuth)
_DEFAULT_SECRET_KEY = 'dev-secret-key-change-in-production'
_flask_secret = os.environ.get('FLASK_SECRET_KEY', os.environ.get('JWT_SECRET_KEY', _DEFAULT_SECRET_KEY))
_jwt_secret = os.environ.get('JWT_SECRET_KEY', _DEFAULT_SECRET_KEY)

# Security: Refuse to start in production with default FLASK_SECRET_KEY
# (JWT_SECRET_KEY is legacy and will be removed after full Authentik migration)
if not is_development:
    if _flask_secret == _DEFAULT_SECRET_KEY:
        raise RuntimeError(
            "SECURITY ERROR: Default FLASK_SECRET_KEY detected in production! "
            "Set FLASK_SECRET_KEY to a unique, cryptographically random value. "
            "Example: python3 -c \"import secrets; print(secrets.token_hex(64))\""
        )
    _system_api_key = os.environ.get('SYSTEM_ADMIN_API_KEY', '')
    if _system_api_key and 'change-in-production' in _system_api_key.lower():
        raise RuntimeError(
            "SECURITY ERROR: Default SYSTEM_ADMIN_API_KEY detected in production! "
            "Set SYSTEM_ADMIN_API_KEY to a unique, cryptographically random value."
        )

app.secret_key = _flask_secret

# JWT Configuration (for legacy auth routes)
# TODO: Complete migration to Authentik and remove legacy JWT auth
app.config['JWT_SECRET_KEY'] = _jwt_secret
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
    if _skip_startup_tasks() or not is_web_runtime():
        return False
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
    if _skip_startup_tasks():
        print("[Startup] Skipping chroma collection name fix (LLARS_SKIP_STARTUP_TASKS=true)")
        return
    from db.tables import RAGCollection
    from db.database import db
    from services.rag.collection_embedding_service import sanitize_chroma_collection_name

    with app.app_context():
        try:
            collections = RAGCollection.query.filter(
                RAGCollection.chroma_collection_name.is_(None),
                RAGCollection.embedding_status == 'completed'
            ).all()

            if not collections:
                return

            from db.models.llm_model import seed_default_models
            from rag_pipeline import RAGPipeline

            seed_default_models()
            pipeline = RAGPipeline()

            for collection in collections:
                chroma_name = sanitize_chroma_collection_name(collection.name, pipeline.model_name)
                collection.chroma_collection_name = chroma_name
                print(f"[Startup] Fixed chroma_collection_name for collection '{collection.name}': {chroma_name}")

            if collections:
                db.session.commit()
                print(f"[Startup] Fixed {len(collections)} collections with missing chroma_collection_name")
        except Exception as e:
            print(f"[Startup] Error fixing chroma_collection_names: {e}")

if _should_run_one_time_startup_tasks():
    fix_missing_chroma_collection_names()


# Seed default LLM models into the database
def seed_llm_models():
    """Seed default LLM models on startup."""
    if _skip_startup_tasks():
        print("[Startup] Skipping LLM model seeding (LLARS_SKIP_STARTUP_TASKS=true)")
        return
    from db.models.llm_model import seed_default_models

    with app.app_context():
        try:
            print("[Startup] Seeding LLM models...")
            seed_default_models()
            print("[Startup] LLM models seeded successfully")
        except Exception as e:
            print(f"[Startup] Error seeding LLM models: {e}")

if _should_run_one_time_startup_tasks():
    seed_llm_models()


# Ensure LLM providers from environment variables (LiteLLM, OpenAI)
def ensure_llm_providers():
    """Create providers from env vars and link orphaned models."""
    if _skip_startup_tasks():
        print("[Startup] Skipping LLM provider setup (LLARS_SKIP_STARTUP_TASKS=true)")
        return
    from services.llm.llm_provider_service import LLMProviderService

    with app.app_context():
        try:
            created = LLMProviderService.ensure_env_providers()
            if created:
                print(f"[Startup] Created {created} LLM provider(s) from environment")
            else:
                # Even if no new providers created, link orphaned models
                LLMProviderService._link_orphaned_models()
                print("[Startup] LLM providers already configured")
        except Exception as e:
            print(f"[Startup] Error setting up LLM providers: {e}")

if _should_run_one_time_startup_tasks():
    ensure_llm_providers()


# Seed default field prompts for AI-assist features
def seed_field_prompts():
    """Seed default field prompts on startup."""
    if _skip_startup_tasks():
        print("[Startup] Skipping field prompt seeding (LLARS_SKIP_STARTUP_TASKS=true)")
        return
    from services.ai_assist import FieldPromptService

    with app.app_context():
        try:
            print("[Startup] Seeding field prompts...")
            created = FieldPromptService.seed_defaults()
            if created > 0:
                print(f"[Startup] Created {created} new field prompts")
            else:
                print("[Startup] Field prompts already exist")
        except Exception as e:
            print(f"[Startup] Error seeding field prompts: {e}")

if _should_run_one_time_startup_tasks():
    seed_field_prompts()


# Migrate plaintext API keys to argon2 hashes
def migrate_api_key_hashes():
    """
    One-time migration: hash any remaining plaintext API keys with argon2id.
    Idempotent — only processes users with api_key set but api_key_hash missing.
    """
    if _skip_startup_tasks():
        print("[Startup] Skipping API key hash migration (LLARS_SKIP_STARTUP_TASKS=true)")
        return
    from migrations.hash_api_keys import migrate_api_keys_to_hash
    from db.database import db

    with app.app_context():
        try:
            migrated = migrate_api_keys_to_hash(db)
            if migrated > 0:
                print(f"[Startup] Migrated {migrated} API keys from plaintext to argon2 hash")
            else:
                print("[Startup] No plaintext API keys to migrate")
        except Exception as e:
            print(f"[Startup] Error migrating API keys: {e}")

if _should_run_one_time_startup_tasks():
    migrate_api_key_hashes()


# Sync LLARS documentation to RAG collection for the chatbot
def sync_documentation_collection():
    """
    Synchronize MkDocs documentation with the LLARS-Documentation RAG collection.

    This enables the LLARS chatbot to answer questions about the system
    and provide direct links to relevant documentation pages.
    """
    if _skip_startup_tasks():
        print("[Startup] Skipping documentation sync (LLARS_SKIP_STARTUP_TASKS=true)")
        return

    from services.docs import MkDocsLoaderService

    with app.app_context():
        try:
            print("[Startup] Syncing LLARS documentation...")
            loader = MkDocsLoaderService()
            result = loader.sync_llars_documentation()

            if result.get('success'):
                print(f"[Startup] {result.get('message')}")
            else:
                print(f"[Startup] Documentation sync failed: {result.get('error')}")
        except Exception as e:
            print(f"[Startup] Error syncing documentation: {e}")


if _should_run_one_time_startup_tasks():
    sync_documentation_collection()


# Auto-start DB Price Agent scheduler for periodic price monitoring
def start_db_agent_scheduler():
    """Start the DB Agent background scheduler on boot."""
    if _skip_startup_tasks():
        print("[Startup] Skipping DB Agent scheduler (LLARS_SKIP_STARTUP_TASKS=true)")
        return
    from services.db_agent.db_agent_scheduler import start_scheduler
    try:
        started = start_scheduler(app)
        if started:
            print("[Startup] DB Agent scheduler started (6h interval)")
        else:
            print("[Startup] DB Agent scheduler already running")
    except Exception as e:
        print(f"[Startup] Error starting DB Agent scheduler: {e}")


if _should_start_background_threads():
    start_db_agent_scheduler()


if __name__ == '__main__':
    # Debug mode nur in development aktivieren
    debug_mode = os.environ.get('FLASK_ENV', 'production') == 'development'
    socketio.run(app, host='0.0.0.0', port=8081, debug=debug_mode)
