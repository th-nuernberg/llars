"""
Leichtgewichtiges Per-User Rate-Limiting für Socket.IO-LLM-Streams.

Hintergrund (Pentest 2026-06-10): Alle ``/socket.io``-Pfade sind vom globalen
Flask-Limiter ausgenommen (``main.py`` exempt_endpoints), und genau dort laufen
die interaktiven LLM-Completions (``chat_stream``, ``test_prompt_stream``,
``chatbot:stream``). Ohne Cap kann ein einzelner authentifizierter Client
unbegrenzt teure LLM-Calls auslösen (Token-/Kosten-DoS, Worker-Sättigung).

Architektur-Entscheidung: In-Memory Sliding-Window statt Redis, weil LLARS in
Production mit **einem** Gunicorn-Gevent-Worker läuft (GUNICORN_WORKERS=1, siehe
MEMORY/socketio-multiworker) — ein prozesslokaler Zähler genügt und vermeidet
einen Redis-Roundtrip pro Chat-Chunk. Bei Multi-Worker-Betrieb müsste dies auf
einen geteilten Store umgestellt werden.

Das Limit ist bewusst großzügig: normale Nutzer (auch zügiges Tippen/Testen)
bleiben weit darunter; es greift erst bei skriptgesteuertem Missbrauch.
"""

import time
from collections import deque
from threading import Lock

# Default: max. 30 LLM-Stream-Starts pro 60s und Schlüssel (User bzw. Socket).
_WINDOW_SECONDS = 60
_MAX_EVENTS = 30

_events: dict[str, deque] = {}
_lock = Lock()  # unter gevent monkey-patched → greenlet-sicher


def allow_llm_event(key: str, max_events: int = _MAX_EVENTS, window: int = _WINDOW_SECONDS) -> bool:
    """
    Registriert ein LLM-Event für ``key`` und meldet, ob es erlaubt ist.

    Returns True, wenn innerhalb des Zeitfensters noch Budget frei ist (und zählt
    das Event), sonst False. Ein leerer Key wird durchgelassen (fail-open für
    fehlende Identität, da der Aufrufer dann ohnehin schon andere Gates hat).
    """
    if not key:
        return True
    now = time.monotonic()
    cutoff = now - window
    with _lock:
        dq = _events.get(key)
        if dq is None:
            dq = deque()
            _events[key] = dq
        # Alte Timestamps außerhalb des Fensters verwerfen
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= max_events:
            return False
        dq.append(now)
        return True
