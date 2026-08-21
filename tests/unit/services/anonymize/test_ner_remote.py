"""
Unit Tests: Anonymize NER remote offload (ner_remote)
=====================================================

Covers the web-side client that offloads Flair/privacy-filter NER to the warm
worker container, including the graceful local-fallback paths.

Test IDs:
- NER_RMT_001: remote disabled -> returns None (caller falls back local)
- NER_RMT_002: no warm worker (no heartbeat) -> returns None
- NER_RMT_003: BLPOP timeout -> returns None
- NER_RMT_004: worker reports error -> returns None
- NER_RMT_005: success -> returns parsed spans
- NER_RMT_006: empty text -> returns None without touching redis
- NER_RMT_007: worker serialises EntityOccurrence -> span dicts
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from services.anonymize import ner_remote
from services.anonymize.ner_remote import (
    detect_ner_remote,
    NER_WORKER_ALIVE_KEY,
    DETECTOR_FLAIR,
)


class FakeRedis:
    """Minimal redis stand-in: configurable heartbeat + canned LPOP result."""

    def __init__(self, alive=b"ner-0", lpop_result=None):
        self._alive = alive
        self._lpop_result = lpop_result
        self.pushed = []

    def get(self, key):
        return self._alive if key == NER_WORKER_ALIVE_KEY else None

    def rpush(self, key, value):
        self.pushed.append((key, value))

    def expire(self, key, ttl):
        pass

    def set(self, key, value, ex=None):
        pass

    def lpop(self, key):
        # Return the canned result once, then None (mirrors a consumed list).
        v = self._lpop_result
        self._lpop_result = None
        return v


@pytest.fixture(autouse=True)
def _fast_poll(monkeypatch):
    # detect_ner_remote polls with time.sleep between LPOPs — no-op it so the
    # timeout test doesn't actually sleep.
    monkeypatch.setattr(ner_remote.time, "sleep", lambda *_a, **_k: None)


@pytest.fixture(autouse=True)
def _enable_remote(monkeypatch):
    # Most tests assume the feature flag is on; NER_RMT_001 overrides it.
    monkeypatch.setattr(ner_remote, "REMOTE_ENABLED", True)


def _use_redis(monkeypatch, fake):
    monkeypatch.setattr(ner_remote, "_redis", lambda: fake)


def test_ner_rmt_001_remote_disabled_returns_none(monkeypatch):
    monkeypatch.setattr(ner_remote, "REMOTE_ENABLED", False)
    assert detect_ner_remote("Max Mustermann", DETECTOR_FLAIR) is None


def test_ner_rmt_002_no_worker_alive_returns_none(monkeypatch):
    _use_redis(monkeypatch, FakeRedis(alive=None))
    assert detect_ner_remote("Max Mustermann", DETECTOR_FLAIR) is None


def test_ner_rmt_003_timeout_returns_none(monkeypatch):
    # Worker alive, but no result ever lands → poll loop exits at the deadline.
    _use_redis(monkeypatch, FakeRedis(alive=b"ner-0", lpop_result=None))
    assert detect_ner_remote("Max Mustermann", DETECTOR_FLAIR, timeout=0.05) is None


def test_ner_rmt_004_worker_error_returns_none(monkeypatch):
    fake = FakeRedis(alive=b"ner-0", lpop_result=json.dumps({"error": "boom"}))
    _use_redis(monkeypatch, fake)
    assert detect_ner_remote("Max Mustermann", DETECTOR_FLAIR, timeout=1) is None


def test_ner_rmt_005_success_returns_spans(monkeypatch):
    spans = [{"label": "PER", "start": 0, "end": 14, "text": "Max Mustermann"}]
    fake = FakeRedis(alive=b"ner-0", lpop_result=json.dumps({"spans": spans}))
    _use_redis(monkeypatch, fake)

    result = detect_ner_remote("Max Mustermann", DETECTOR_FLAIR, timeout=1)
    assert result == spans
    # A request was actually enqueued.
    assert fake.pushed and fake.pushed[0][0] == ner_remote.NER_REQUEST_LIST


def test_ner_rmt_006_empty_text_returns_none(monkeypatch):
    fake = FakeRedis(alive=b"ner-0", lpop_result=json.dumps({"spans": []}))
    _use_redis(monkeypatch, fake)
    assert detect_ner_remote("   ", DETECTOR_FLAIR) is None
    assert fake.pushed == []  # never touched redis


def test_ner_rmt_007_worker_serialises_entities(monkeypatch):
    from services.anonymize.anonymize_constants import EntityOccurrence

    fake_ents = [
        EntityOccurrence(label="PER", start=0, end=3, text="Max"),
        EntityOccurrence(label="LOC", start=8, end=14, text="Berlin"),
    ]
    with patch(
        "services.anonymize.anonymize_entity_detection.find_flair_ner",
        return_value=fake_ents,
    ):
        spans = ner_remote._detect_local_spans("Max in Berlin", DETECTOR_FLAIR)

    assert spans == [
        {"label": "PER", "start": 0, "end": 3, "text": "Max"},
        {"label": "LOC", "start": 8, "end": 14, "text": "Berlin"},
    ]
