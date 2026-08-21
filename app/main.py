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
    Ermittelt die echte Client-IP hinter dem nginx Reverse Proxy — spoofing-resistent.

    Ohne diese Funktion sehen alle User wie eine einzige IP aus (nginx-Container-IP),
    und das Rate-Limit wird für ALLE User gemeinsam gezählt.

    SICHERHEIT: nginx hängt die echte Peer-IP RECHTS an einen ggf. vom Client
    mitgeschickten X-Forwarded-For an (`proxy_add_x_forwarded_for`). Würde man dem
    LINKEN (ersten) Element vertrauen, könnte ein Angreifer seine Rate-Limit-Bucket
    frei wählen, indem er einfach einen gefälschten X-Forwarded-For-Header schickt —
    und damit das Limit für Login-Brute-Force, Passwort-Reset-Mail-Flooding und DoS
    komplett umgehen. Korrekt ist die Adresse, die unser eigener vertrauenswürdiger
    Proxy beigesteuert hat: das `PROXY_FIX_X_FOR`-te Element VON RECHTS (Default 1 Hop
    → letztes Element). Die linken Einträge sind potenziell client-gefälscht und werden
    ignoriert. X-Real-IP wird von nginx mit `$remote_addr` überschrieben und ist daher
    ebenfalls nicht fälschbar.
    """
    # Anzahl der vertrauenswürdigen Proxy-Hops (mind. 1) — gespiegelt aus der
    # ProxyFix-Konfiguration oben, damit beide dieselbe Topologie annehmen.
    trusted_hops = max(proxy_fix_x_for, 1)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        parts = [p.strip() for p in forwarded_for.split(',') if p.strip()]
        if parts:
            # Von rechts zählen: nur die von unseren Proxies angehängten Einträge
            # sind vertrauenswürdig. Bei genau 1 Hop ist das das letzte Element.
            return parts[-min(trusted_hops, len(parts))]
    # X-Real-IP wird von nginx (überschreibend) gesetzt → nicht client-fälschbar.
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


# CI-/interne Anfragen vom Rate-Limit ausnehmen. Die nächtliche E2E-Suite testet
# die Staging-Instanz von einer EINZIGEN internen IP (Docker-Gateway/Loopback)
# gegen localhost:55080 und sprengt sonst das strikte Per-IP-Limit (500/h im
# Prod-Modus) → 429, was den ganzen Deploy blockiert (E2E-Timeout + smoke:staging
# 429). Echte Nutzer kommen über das öffentliche FH-Gateway mit ÖFFENTLICHEN IPs
# und bleiben unverändert limitiert. Spoofing-sicher: X-Real-IP/X-Forwarded-For
# sind nicht client-fälschbar (siehe _get_real_client_ip), eine öffentliche
# Quelle kann keine private IP vortäuschen.
@limiter.request_filter
def exempt_internal_ips():
    import ipaddress
    try:
        ip = ipaddress.ip_address(_get_real_client_ip())
    except (ValueError, TypeError):
        return False
    return ip.is_private or ip.is_loopback


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
    # Exempt the app-shell polling endpoints.
    #
    # INCIDENT 2026-07-29: these two are polled by the running SPA roughly
    # every 5s (usePermissions / useCommunicationAdmin), i.e. ~720 req/h per
    # user — well past the production default of 500/h per (IP, endpoint).
    # Once the budget was gone every request 429'd, `fetchPermissions()` never
    # set hasLoaded, the permission set stayed EMPTY, and the router guard
    # bounced raters out of permission-gated routes back to /login. Users
    # reported it as "I keep getting logged out" / "I can't log in at all" —
    # there was never a 401 involved (230x 429, 0x 401 for the worst-hit IP).
    #
    # Both are cheap, authenticated reads that the app cannot function
    # without, so rate-limiting them only ever breaks legitimate sessions;
    # they are useless as an attack surface (no writes, no enumeration).
    if path.startswith('/api/permissions/'):
        return True
    if path.startswith('/api/system/communication-status'):
        return True
    return False

# Flask Secret Key (required for session management and signed cookies)
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

# Session-Cookie-Härtung: Die Flask-Session trägt kurzlebigen Server-State.
# HTTPONLY blockt JS-Zugriff (XSS), SAMESITE=Lax mindert CSRF, SECURE erzwingt
# HTTPS-only-Übertragung (nur in Production, da Dev über http läuft).
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = not is_development

# JWT Configuration (for legacy auth routes)
# TODO: Complete migration to Authentik and remove legacy JWT auth
app.config['JWT_SECRET_KEY'] = _jwt_secret
jwt = JWTManager(app)

configure_database(app)

# Register all blueprints via central registry
register_all_blueprints(app)


# ---------------------------------------------------------------------------
# Dedicated, stricter rate limits on sensitive UNAUTHENTICATED endpoints.
# These stack on top of the global default_limits and target brute-force /
# email-bombing of the self-service password-reset flow.
#
# Applied here (after blueprint registration) rather than as @limiter.limit
# decorators in the route modules, because the limiter lives in main.py and the
# route files cannot import it at definition time without a circular import
# (mirrors the lazy `from main import socketio` pattern used elsewhere).
# Flask-Limiter keys decorator limits by the view function's qualified name, so
# applying limiter.limit(...) to the already-registered view object binds at
# request time. The per-IP key is only as good as _get_real_client_ip() — see
# the spoofing-resistant X-Forwarded-For handling above; the password-reset
# request route additionally enforces a per-account cooldown that no IP trick
# can bypass.
# ---------------------------------------------------------------------------
_pw_reset_request_limit = (
    "30 per hour;15 per 10 minutes" if is_development else "6 per hour;3 per 10 minutes"
)
_pw_reset_redeem_limit = "60 per hour" if is_development else "20 per hour"
# Public, account-creating referral endpoints: throttle to curb mass account
# creation / email-bombing / DoS on the unauthenticated POST /register and the
# write-triggering (click_count) GET /validate. Generous in dev.
_referral_register_limit = "60 per hour;20 per 10 minutes" if is_development else "20 per hour;6 per 10 minutes"
_referral_validate_limit = "300 per hour" if is_development else "120 per hour"
_SENSITIVE_ENDPOINT_LIMITS = {
    'auth.request_password_reset': _pw_reset_request_limit,
    'auth.perform_password_reset': _pw_reset_redeem_limit,
    'referral.register_via_referral': _referral_register_limit,
    'referral.validate_referral_link': _referral_validate_limit,
}
for _endpoint, _limit_spec in _SENSITIVE_ENDPOINT_LIMITS.items():
    _view = app.view_functions.get(_endpoint)
    if _view is not None:
        limiter.limit(_limit_spec)(_view)
    else:
        print(f"[Startup] WARN: rate-limit target endpoint not registered: {_endpoint}")


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


# Add metadata_json column to evaluation_items (introduced in 6f2acd61, never migrated).
def migrate_evaluation_item_metadata_column():
    """
    One-time migration: add metadata_json (JSON, nullable) to evaluation_items.
    Idempotent — no-op when the column already exists.
    See app/db/migrations/migrate_evaluation_items_metadata.py for details.
    """
    if _skip_startup_tasks():
        print("[Startup] Skipping evaluation_items metadata_json migration (LLARS_SKIP_STARTUP_TASKS=true)")
        return
    from db.migrations.migrate_evaluation_items_metadata import migrate_evaluation_item_metadata

    with app.app_context():
        try:
            result = migrate_evaluation_item_metadata()
            if result.get('column_added'):
                print("[Startup] Added metadata_json column to evaluation_items")
            else:
                print("[Startup] evaluation_items.metadata_json already exists — skipping")
        except Exception as e:
            print(f"[Startup] Error migrating evaluation_items.metadata_json: {e}")

if _should_run_one_time_startup_tasks():
    migrate_evaluation_item_metadata_column()


# Add span_id to the three labeling tables (conversation labeling, function_type 9).
def migrate_labeling_span_id_columns():
    """
    One-time migration: span_id + extended unique key on
    item_labeling_evaluations, labeling_copilot_logs, evaluation_item_timings.

    Purely additive (NOT NULL DEFAULT ''), so existing labeling study data keeps
    exactly the duplicate protection it had. Idempotent.
    See app/db/migrations/migrate_labeling_span_id.py for the full rationale.
    """
    if _skip_startup_tasks():
        print("[Startup] Skipping labeling span_id migration (LLARS_SKIP_STARTUP_TASKS=true)")
        return
    from db.migrations.migrate_labeling_span_id import migrate_labeling_span_id

    with app.app_context():
        try:
            result = migrate_labeling_span_id()
            if result.get('changed'):
                touched = [
                    t['table'] for t in result['tables']
                    if t['column_added'] or t['index_swapped']
                ]
                print(f"[Startup] Added span_id to: {', '.join(touched)}")
            else:
                print("[Startup] labeling span_id already present — skipping")
        except Exception as e:
            print(f"[Startup] Error migrating labeling span_id: {e}")

if _should_run_one_time_startup_tasks():
    migrate_labeling_span_id_columns()


# Add collect_email + collect_display_name flags to referral_links so
# study links can hide / skip those fields on the registration form.
def migrate_referral_link_collect_flags_column():
    """One-time migration: ``collect_email`` + ``collect_display_name``.
    Idempotent — no-op when both columns already exist.
    See app/db/migrations/migrate_referral_link_collect_flags.py."""
    if _skip_startup_tasks():
        print("[Startup] Skipping referral_links collect-flags migration (LLARS_SKIP_STARTUP_TASKS=true)")
        return
    from db.migrations.migrate_referral_link_collect_flags import migrate_referral_link_collect_flags
    with app.app_context():
        try:
            result = migrate_referral_link_collect_flags()
            if result.get('columns_added'):
                print(f"[Startup] referral_links — added {result['columns_added']}")
            else:
                print("[Startup] referral_links — collect-flag columns already present")
        except Exception as exc:
            print(f"[Startup] Error migrating referral_links collect-flags: {exc}")


if _should_run_one_time_startup_tasks():
    migrate_referral_link_collect_flags_column()


# Add collect_email_optional flag to referral_links so a link can offer
# an email field that is shown but not required (optional email at signup).
def migrate_collect_email_optional_column():
    """One-time migration: ``collect_email_optional``.
    Idempotent — no-op when the column already exists.
    See app/db/migrations/migrate_add_collect_email_optional.py."""
    if _skip_startup_tasks():
        print("[Startup] Skipping referral_links collect_email_optional migration (LLARS_SKIP_STARTUP_TASKS=true)")
        return
    from db.migrations.migrate_add_collect_email_optional import migrate_add_collect_email_optional
    with app.app_context():
        try:
            result = migrate_add_collect_email_optional()
            if result.get('columns_added'):
                print(f"[Startup] referral_links — added {result['columns_added']}")
            else:
                print("[Startup] referral_links — collect_email_optional already present")
        except Exception as exc:
            print(f"[Startup] Error migrating referral_links collect_email_optional: {exc}")


if _should_run_one_time_startup_tasks():
    migrate_collect_email_optional_column()


# Add click_count to referral_links so admins can see a funnel
# "X Aufrufe -> Y registriert" per link (page opens vs registrations).
def migrate_referral_click_count_column():
    """One-time migration: ``click_count``.
    Idempotent — no-op when the column already exists.
    See app/db/migrations/migrate_add_referral_click_count.py."""
    if _skip_startup_tasks():
        print("[Startup] Skipping referral_links click_count migration (LLARS_SKIP_STARTUP_TASKS=true)")
        return
    from db.migrations.migrate_add_referral_click_count import migrate_add_referral_click_count
    with app.app_context():
        try:
            result = migrate_add_referral_click_count()
            if result.get('columns_added'):
                print(f"[Startup] referral_links — added {result['columns_added']}")
            else:
                print("[Startup] referral_links — click_count already present")
        except Exception as exc:
            print(f"[Startup] Error migrating referral_links click_count: {exc}")


if _should_run_one_time_startup_tasks():
    migrate_referral_click_count_column()


# Add demo-enrollment + configurable signup columns to referral_links:
# target_scenario_ids / viewer_scenario_ids (multi-scenario auto-enroll +
# read-only viewer) and signup_mode (full | email | instant). Powers the
# IJCAI demo link. Idempotent.
def migrate_referral_link_demo_enrollment_columns():
    """One-time migration: target_scenario_ids, viewer_scenario_ids, signup_mode.
    Idempotent — no-op when columns already exist.
    See app/db/migrations/migrate_referral_link_demo_enrollment.py."""
    if _skip_startup_tasks():
        print("[Startup] Skipping referral_links demo-enrollment migration (LLARS_SKIP_STARTUP_TASKS=true)")
        return
    from db.migrations.migrate_referral_link_demo_enrollment import migrate_referral_link_demo_enrollment
    with app.app_context():
        try:
            result = migrate_referral_link_demo_enrollment()
            if result.get('columns_added'):
                print(f"[Startup] referral_links — added {result['columns_added']}")
            else:
                print("[Startup] referral_links — demo-enrollment columns already present")
        except Exception as exc:
            print(f"[Startup] Error migrating referral_links demo-enrollment: {exc}")


if _should_run_one_time_startup_tasks():
    migrate_referral_link_demo_enrollment_columns()


# Add demo-content provisioning to referral_links: provision_json says which
# prompts get cloned and which generation jobs get shared with everyone who
# registers through the link (IJCAI conference QR code). Idempotent.
def migrate_referral_link_provisioning_column():
    """One-time migration: provision_json.
    Idempotent — no-op when the column already exists.
    See app/db/migrations/migrate_referral_link_provisioning.py."""
    if _skip_startup_tasks():
        print("[Startup] Skipping referral_links provisioning migration (LLARS_SKIP_STARTUP_TASKS=true)")
        return
    from db.migrations.migrate_referral_link_provisioning import migrate_referral_link_provisioning
    with app.app_context():
        try:
            result = migrate_referral_link_provisioning()
            if result.get('columns_added'):
                print(f"[Startup] referral_links — added {result['columns_added']}")
            else:
                print("[Startup] referral_links — provision_json already present")
        except Exception as exc:
            print(f"[Startup] Error migrating referral_links provisioning: {exc}")


if _should_run_one_time_startup_tasks():
    migrate_referral_link_provisioning_column()


# Add a per-link badge color so a referral source keeps one consistent color
# everywhere it surfaces (scenario-team origin pills, legends, admin list).
def migrate_referral_link_color_column():
    """One-time migration: ``color``.
    Idempotent — no-op when the column already exists.
    See app/db/migrations/migrate_add_referral_link_color.py."""
    if _skip_startup_tasks():
        print("[Startup] Skipping referral_links color migration (LLARS_SKIP_STARTUP_TASKS=true)")
        return
    from db.migrations.migrate_add_referral_link_color import migrate_add_referral_link_color
    with app.app_context():
        try:
            result = migrate_add_referral_link_color()
            if result.get('columns_added'):
                print(f"[Startup] referral_links — added {result['columns_added']}")
            else:
                print("[Startup] referral_links — color already present")
        except Exception as exc:
            print(f"[Startup] Error migrating referral_links color: {exc}")


if _should_run_one_time_startup_tasks():
    migrate_referral_link_color_column()


# Create the password_reset_tokens table backing the self-service
# "Passwort vergessen?" flow on the login page.
def migrate_password_reset_tokens():
    """One-time migration: create ``password_reset_tokens``.
    Idempotent — no-op when the table already exists.
    See app/db/migrations/migrate_password_reset_tokens_table.py."""
    if _skip_startup_tasks():
        print("[Startup] Skipping password_reset_tokens migration (LLARS_SKIP_STARTUP_TASKS=true)")
        return
    from db.migrations.migrate_password_reset_tokens_table import migrate_password_reset_tokens_table
    with app.app_context():
        try:
            result = migrate_password_reset_tokens_table()
            if result.get('table_created'):
                print("[Startup] Created password_reset_tokens table")
            else:
                print("[Startup] password_reset_tokens table already exists — skipping")
        except Exception as exc:
            print(f"[Startup] Error migrating password_reset_tokens table: {exc}")


if _should_run_one_time_startup_tasks():
    migrate_password_reset_tokens()


# Create the Mail-Center tables (email_log + referral_invitation) backing the
# Admin Mail-Center: central mail audit log + invitation→acceptance tracking.
def migrate_mail_center():
    """One-time migration: create ``email_log`` + ``referral_invitation``.
    Idempotent — no-op when the tables already exist.
    See app/db/migrations/migrate_mail_center_tables.py."""
    if _skip_startup_tasks():
        print("[Startup] Skipping mail-center migration (LLARS_SKIP_STARTUP_TASKS=true)")
        return
    from db.migrations.migrate_mail_center_tables import migrate_mail_center_tables
    with app.app_context():
        try:
            result = migrate_mail_center_tables()
            created = result.get('created') or []
            if created:
                print(f"[Startup] Created Mail-Center tables: {', '.join(created)}")
            else:
                print("[Startup] Mail-Center tables already exist — skipping")
        except Exception as exc:
            print(f"[Startup] Error migrating Mail-Center tables: {exc}")


if _should_run_one_time_startup_tasks():
    migrate_mail_center()


# Add open/click tracking columns to email_log (Brevo webhook).
def migrate_email_log_tracking():
    """One-time migration: ``provider_message_id`` + ``opened_at`` + ``clicked_at``.
    Idempotent — no-op when all columns already exist.
    See app/db/migrations/migrate_add_email_log_tracking.py."""
    if _skip_startup_tasks():
        print("[Startup] Skipping email_log tracking migration (LLARS_SKIP_STARTUP_TASKS=true)")
        return
    from db.migrations.migrate_add_email_log_tracking import migrate_add_email_log_tracking
    with app.app_context():
        try:
            result = migrate_add_email_log_tracking()
            if result.get('columns_added') or result.get('index_added'):
                print(f"[Startup] email_log — added {result.get('columns_added')} "
                      f"(index_added={result.get('index_added')})")
            else:
                print("[Startup] email_log — tracking columns already present")
        except Exception as exc:
            print(f"[Startup] Error migrating email_log tracking columns: {exc}")


if _should_run_one_time_startup_tasks():
    migrate_email_log_tracking()


# Add the self_service_password_reset_enabled toggle to system_settings.
def migrate_self_service_password_reset_setting():
    """One-time migration: ``self_service_password_reset_enabled``.
    Idempotent — no-op when the column already exists.
    See app/db/migrations/migrate_add_self_service_password_reset_setting.py."""
    if _skip_startup_tasks():
        print("[Startup] Skipping self_service_password_reset_enabled migration (LLARS_SKIP_STARTUP_TASKS=true)")
        return
    from db.migrations.migrate_add_self_service_password_reset_setting import (
        migrate_add_self_service_password_reset_setting,
    )
    with app.app_context():
        try:
            result = migrate_add_self_service_password_reset_setting()
            if result.get('columns_added'):
                print(f"[Startup] system_settings — added {result['columns_added']}")
            else:
                print("[Startup] system_settings — self_service_password_reset_enabled already present")
        except Exception as exc:
            print(f"[Startup] Error migrating system_settings self_service_password_reset_enabled: {exc}")


if _should_run_one_time_startup_tasks():
    migrate_self_service_password_reset_setting()


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


if __name__ == '__main__':
    # Debug mode nur in development aktivieren
    debug_mode = os.environ.get('FLASK_ENV', 'production') == 'development'
    socketio.run(app, host='0.0.0.0', port=8081, debug=debug_mode)
