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
import os
import redis

app = Flask(__name__)

# Initialize API metrics collection middleware
create_metrics_middleware(app)

# Initialize Redis client for server-authoritative sessions (Wizard Sessions, etc.)
# Redis provides persistent session storage that survives browser closures and server restarts
redis_client = redis.Redis(
    host=os.environ.get('REDIS_HOST', 'llars-redis'),
    port=int(os.environ.get('REDIS_PORT', 6379)),
    db=int(os.environ.get('REDIS_DB', 0)),
    decode_responses=True,  # Return strings instead of bytes
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)

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
    return os.environ.get('LLARS_SKIP_STARTUP_TASKS', '').lower() in ('1', 'true', 'yes')

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
# In development mode, use much higher limits to support E2E testing
is_development = os.environ.get('FLASK_ENV', 'production') == 'development'
rate_limit_defaults = ["10000 per day", "1000 per hour"] if is_development else ["200 per day", "50 per hour"]

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=rate_limit_defaults,
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
    # Exempt LaTeX compile status + SyncTeX endpoints (frequently polled)
    if request.path and request.path.startswith('/api/latex-collab/compile/'):
        return True
    # Exempt data import endpoints (bulk uploads can exceed normal limits)
    if request.path and request.path.startswith('/api/import/'):
        return True
    return False

# Flask Secret Key (required for session management, e.g. Zotero OAuth)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.environ.get('JWT_SECRET_KEY', 'dev-secret-key-change-in-production'))

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
    if _skip_startup_tasks():
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

seed_llm_models()


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

seed_field_prompts()


# Auto-start LLM evaluations for scenarios with configured evaluators
def start_pending_llm_evaluations():
    """
    Start LLM evaluations for all scenarios that have pending evaluations.

    This runs on startup to ensure LLM evaluators process any threads that
    haven't been evaluated yet. Runs in background threads to not block startup.
    """
    if _skip_startup_tasks():
        print("[Startup] Skipping LLM evaluation startup (LLARS_SKIP_STARTUP_TASKS=true)")
        return

    import json
    import threading
    from db.database import db
    from db.models import (
        RatingScenarios, ScenarioThreads, LLMTaskResult,
        ComparisonSession, FeatureFunctionType
    )

    def _run_pending_evaluations():
        with app.app_context():
            try:
                # Find all scenarios with LLM evaluators configured
                scenarios = RatingScenarios.query.filter(
                    RatingScenarios.config_json.isnot(None)
                ).all()

                scenarios_to_process = []
                for scenario in scenarios:
                    config = scenario.config_json
                    if isinstance(config, str):
                        try:
                            config = json.loads(config)
                        except (json.JSONDecodeError, TypeError):
                            continue
                    if not isinstance(config, dict):
                        continue

                    llm_evaluators = config.get('llm_evaluators') or config.get('selected_llms') or []
                    if not llm_evaluators:
                        continue

                    # Get function type to handle comparison scenarios differently
                    function_type = FeatureFunctionType.query.filter_by(
                        function_type_id=scenario.function_type_id
                    ).first()
                    function_name = function_type.name if function_type else None

                    # For comparison scenarios, use ComparisonSessions
                    if function_name == "comparison":
                        comparison_sessions = ComparisonSession.query.filter_by(
                            scenario_id=scenario.id
                        ).all()
                        all_ids = {cs.id for cs in comparison_sessions}
                    else:
                        # For other scenarios, use ScenarioThreads
                        scenario_threads = ScenarioThreads.query.filter_by(
                            scenario_id=scenario.id
                        ).all()
                        all_ids = {st.thread_id for st in scenario_threads}

                    if not all_ids:
                        continue

                    scenarios_to_process.append({
                        'scenario': scenario,
                        'llm_evaluators': llm_evaluators,
                        'all_ids': all_ids,
                        'is_comparison': function_name == "comparison",
                    })

                if not scenarios_to_process:
                    print("[Startup] No scenarios with pending LLM evaluations")
                    return

                print(f"[Startup] Checking {len(scenarios_to_process)} scenarios for pending LLM evaluations...")

                from services.llm.llm_ai_task_runner import LLMAITaskRunner

                total_started = 0
                for item in scenarios_to_process:
                    scenario = item['scenario']
                    llm_evaluators = item['llm_evaluators']
                    all_ids = item['all_ids']

                    for model_id in llm_evaluators:
                        # Get IDs that already have successful results
                        completed_rows = db.session.query(LLMTaskResult.thread_id).filter(
                            LLMTaskResult.scenario_id == scenario.id,
                            LLMTaskResult.model_id == model_id,
                            LLMTaskResult.payload_json.isnot(None),
                            LLMTaskResult.error.is_(None),
                        ).all()
                        completed_ids = {row[0] for row in completed_rows if row[0]}

                        # Find IDs that need evaluation
                        pending_ids = list(all_ids - completed_ids)

                        if pending_ids:
                            id_type = "sessions" if item['is_comparison'] else "threads"
                            print(
                                f"[Startup] Starting LLM evaluation: scenario={scenario.id} "
                                f"({scenario.scenario_name}), model={model_id}, "
                                f"pending_{id_type}={len(pending_ids)}/{len(all_ids)}"
                            )
                            LLMAITaskRunner.run_for_scenario_async(
                                scenario.id,
                                model_ids=[model_id],
                                thread_ids=pending_ids,  # Works for both threads and session IDs
                            )
                            total_started += 1

                if total_started > 0:
                    print(f"[Startup] Started {total_started} LLM evaluation tasks")
                else:
                    print("[Startup] All LLM evaluations are up to date")

            except Exception as e:
                print(f"[Startup] Error starting LLM evaluations: {e}")

    # Run in background thread after a short delay to let other services initialize
    def _delayed_start():
        import time
        time.sleep(5)  # Wait 5 seconds for other services to be ready
        _run_pending_evaluations()

    # Start background thread - skip only if LLARS_SKIP_STARTUP_TASKS is set
    # For Docker/Gunicorn, we always want to run this (unlike embedding worker which
    # has special handling for Flask reloader)
    thread = threading.Thread(target=_delayed_start, daemon=True)
    thread.start()
    print("[Startup] LLM evaluation checker scheduled")


start_pending_llm_evaluations()


if __name__ == '__main__':
    # Debug mode nur in development aktivieren
    debug_mode = os.environ.get('FLASK_ENV', 'production') == 'development'
    socketio.run(app, host='0.0.0.0', port=8081, debug=debug_mode)
