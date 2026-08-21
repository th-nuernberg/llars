# ner_remote.py
"""
Remote NER offload: run the heavy Flair / privacy-filter models in the dedicated
worker container instead of the gevent web tier.

WHY (see [[gunicorn-gevent-preload-pitfall]] memory):
- The web tier runs gunicorn + gevent. Loading the 2.2 GB Flair model there means
  a ~35 s cold load on the first /api/anonymize request per worker, and one model
  copy per worker → RAM creep toward the 12 GB cap.
- A gunicorn master preload to share the model copy-on-write breaks gevent
  (background greenlets stall, worker boot crashes via openai's lazy proxies).

SOLUTION:
- The `llars_worker` container (not under gevent, same image, already mounts the
  model dirs) loads the model ONCE and stays warm. It consumes NER jobs from a
  Redis list and writes spans back to a per-job result list.
- The web tier calls detect_ner_remote(), which is pure Redis I/O — gevent-friendly
  (redis-py sockets are monkey-patched, so BLPOP yields to the hub). The 2.2 GB
  model never loads in the web tier.
- GRACEFUL FALLBACK: if the remote is disabled, Redis is down, or no warm worker
  is alive (heartbeat missing) / the request times out, detect_ner_remote()
  returns None and the caller falls back to loading the model locally — i.e. never
  worse than the previous behaviour.

Protocol (Redis):
  request  -> RPUSH  anonymize:ner:requests        {job_id, text, detector}
  result   -> RPUSH  anonymize:ner:result:<job_id> {spans:[{label,start,end,text}]}
  liveness -> SET    anonymize:ner:worker:alive     <label>  EX heartbeat_ttl
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

# Redis keys / protocol
NER_REQUEST_LIST = "anonymize:ner:requests"
NER_RESULT_PREFIX = "anonymize:ner:result:"
NER_WORKER_ALIVE_KEY = "anonymize:ner:worker:alive"

# Tunables (env-overridable)
REMOTE_ENABLED = os.environ.get("ANONYMIZE_NER_REMOTE", "1").strip().lower() not in {"0", "false", "no"}
REMOTE_TIMEOUT = int(os.environ.get("ANONYMIZE_NER_REMOTE_TIMEOUT", "45"))  # web wait for a result (s)
RESULT_TTL = int(os.environ.get("ANONYMIZE_NER_RESULT_TTL", "120"))         # per-job result list TTL (s)
REQUEST_TTL = int(os.environ.get("ANONYMIZE_NER_REQUEST_TTL", "120"))       # request backlog TTL (s)
WORKER_HEARTBEAT_TTL = int(os.environ.get("ANONYMIZE_NER_HEARTBEAT_TTL", "30"))  # liveness key TTL (s)

# Detector identifiers exchanged over the wire.
DETECTOR_FLAIR = "flair"
DETECTOR_PRIVACY_FILTER = "privacy-filter"


def _redis():
    """Return the shared redis-py client (or None). Reuses the app's client."""
    try:
        from main import redis_client
        if redis_client is not None:
            return redis_client
    except Exception:
        pass
    try:
        from services.runtime_config import get_redis_client
        return get_redis_client()
    except Exception as e:  # pragma: no cover - redis optional in some envs
        logger.debug("[ner_remote] no redis client available: %s", e)
        return None


def worker_alive() -> bool:
    """True if a warm NER worker has published a recent heartbeat."""
    r = _redis()
    if r is None:
        return False
    try:
        return bool(r.get(NER_WORKER_ALIVE_KEY))
    except Exception:
        return False


def detect_ner_remote(text: str, detector: str, timeout: Optional[int] = None) -> Optional[list[dict]]:
    """
    Ask the warm worker to run NER and return span dicts, or None to signal the
    caller to fall back to a local model load.

    Returns None (fall back) when: remote disabled, no redis, no warm worker,
    timeout, or any error. Returns a (possibly empty) list of
    {label,start,end,text} on success.
    """
    if not REMOTE_ENABLED or not (text or "").strip():
        return None

    r = _redis()
    if r is None:
        return None

    # Only route to the worker if one is actually alive — otherwise skip straight
    # to local fallback instead of eating the full BLPOP timeout on every request.
    try:
        if not r.get(NER_WORKER_ALIVE_KEY):
            return None
    except Exception:
        return None

    job_id = uuid.uuid4().hex
    result_key = f"{NER_RESULT_PREFIX}{job_id}"
    payload = json.dumps({"job_id": job_id, "text": text, "detector": detector})

    try:
        r.rpush(NER_REQUEST_LIST, payload)
        r.expire(NER_REQUEST_LIST, REQUEST_TTL)
        # Poll the per-job result list with non-blocking LPOP instead of BLPOP:
        # the shared redis client has a socket_timeout shorter than a long BLPOP
        # block, so BLPOP would raise TimeoutError. Polling avoids that entirely
        # (time.sleep is gevent-patched in the web tier → yields the hub).
        deadline = time.monotonic() + (timeout or REMOTE_TIMEOUT)
        raw = None
        while time.monotonic() < deadline:
            raw = r.lpop(result_key)
            if raw is not None:
                break
            time.sleep(0.1)
        if raw is None:
            logger.warning("[ner_remote] timeout waiting for NER result (detector=%s) — falling back local", detector)
            return None
        data = json.loads(raw)
        if data.get("error"):
            logger.warning("[ner_remote] worker reported error: %s — falling back local", data.get("error"))
            return None
        spans = data.get("spans")
        return spans if isinstance(spans, list) else []
    except Exception as e:
        logger.warning("[ner_remote] remote NER failed (%s) — falling back local", e)
        return None


# ----------------------------------------------------------------------------
# Worker side (runs in the llars_worker container, NOT under gevent)
# ----------------------------------------------------------------------------

def _detect_local_spans(text: str, detector: str) -> list[dict]:
    """Run the actual model in-process (worker) and serialise spans."""
    if detector == DETECTOR_PRIVACY_FILTER:
        from .anonymize_privacy_filter_detection import find_privacy_filter_ner
        ents = find_privacy_filter_ner(text)
    else:
        from .anonymize_entity_detection import find_flair_ner
        ents = find_flair_ner(text)
    return [{"label": e.label, "start": e.start, "end": e.end, "text": e.text} for e in ents]


def run_ner_worker_loop(worker_label: str) -> None:
    """
    Blocking consumer loop for the worker container.

    Warms the Flair model once (so the first real request is fast), then BLPOPs
    NER jobs, runs the model, and pushes spans to the per-job result list. A
    heartbeat key is refreshed every iteration so the web tier knows a warm
    worker exists before routing to it.
    """
    r = _redis()
    if r is None:
        logger.error("[ner_worker %s] no redis client — NER offload disabled", worker_label)
        return

    # Warm the Flair model before announcing liveness, so the web tier only routes
    # here once inference is actually fast (no cold load on the first real job).
    try:
        from .anonymize_entity_detection import find_flair_ner
        logger.info("[ner_worker %s] warming Flair model ...", worker_label)
        find_flair_ner("Aufwärmen")
        logger.info("[ner_worker %s] Flair model warm — consuming NER jobs", worker_label)
    except Exception:
        logger.exception("[ner_worker %s] Flair warmup failed (will retry lazily per job)", worker_label)

    while True:
        try:
            # Announce liveness (short TTL → auto-clears if this worker dies).
            r.set(NER_WORKER_ALIVE_KEY, worker_label, ex=WORKER_HEARTBEAT_TTL)

            # Non-blocking LPOP poll (not BLPOP): the shared redis client's
            # socket_timeout is shorter than a blocking BLPOP wait, which would
            # raise TimeoutError every idle cycle. Poll + short sleep instead.
            raw = r.lpop(NER_REQUEST_LIST)
            if raw is None:
                time.sleep(0.5)
                continue
            req = json.loads(raw)
            job_id = req.get("job_id")
            text = req.get("text") or ""
            detector = req.get("detector") or DETECTOR_FLAIR
            if not job_id:
                continue

            result_key = f"{NER_RESULT_PREFIX}{job_id}"
            try:
                spans = _detect_local_spans(text, detector)
                r.rpush(result_key, json.dumps({"spans": spans}))
            except Exception as e:
                logger.exception("[ner_worker %s] detection failed for job %s", worker_label, job_id)
                r.rpush(result_key, json.dumps({"error": str(e)}))
            r.expire(result_key, RESULT_TTL)
        except Exception:
            logger.exception("[ner_worker %s] loop failure", worker_label)
            # Brief backoff to avoid hot-looping on a persistent redis error.
            time.sleep(1.0)
