# Gunicorn configuration for LLARS Production
# https://docs.gunicorn.org/en/stable/settings.html

import os

# Server socket
bind = '0.0.0.0:8081'
backlog = 2048

# Worker processes
# Multiple gevent workers let LLARS spread request and Socket.IO load across CPU cores.
# CPU-heavy work is offloaded to dedicated backend workers, so the web tier stays responsive.
# Auto-scale to CPU count: cpu_count * 2 + 1 (Gunicorn recommendation), capped at 25.
# Override via GUNICORN_WORKERS env var (e.g. on low-memory dev machines).
def _auto_workers() -> int:
    env_val = os.environ.get('GUNICORN_WORKERS', '').strip()
    if env_val:
        return max(1, int(env_val))
    try:
        cpu_count = len(os.sched_getaffinity(0))
    except AttributeError:
        cpu_count = os.cpu_count() or 4
    return min(cpu_count * 2 + 1, 25)

workers = _auto_workers()

# Worker class: gevent-websocket for real WebSocket support
# This provides better Docker DNS compatibility than eventlet
worker_class = 'geventwebsocket.gunicorn.workers.GeventWebSocketWorker'

# Worker timeout (seconds) - increased for long LLM operations
timeout = 300  # 5 minutes for long-running LLM requests
graceful_timeout = 30
keepalive = 5

# Restart workers after this many requests (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '-'  # stdout
errorlog = '-'   # stderr
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'llars-backend'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (handled by nginx)
keyfile = None
certfile = None

# Hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    pass

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    pass

def worker_int(worker):
    """Called when a worker received SIGINT or SIGQUIT."""
    pass

def worker_abort(worker):
    """Called when a worker received SIGABRT (timeout)."""
    pass
