"""
Unit Tests für WizardSessionService

Testet:
- Session CRUD (Create, Read, Update, Delete)
- Status-Transitionen mit Zeiterfassung
- Progress-Updates (Crawl, Embedding)
- Time-Tracking
- Wizard-Data-Management
- User-Session-Management
"""

import pytest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'app'))


# =============================================================================
# Mock Redis Client Fixture
# =============================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis client with in-memory storage."""
    storage = {}
    sets = {}

    class MockRedis:
        def hset(self, key, mapping=None, **kwargs):
            if key not in storage:
                storage[key] = {}
            if mapping:
                storage[key].update(mapping)
            storage[key].update(kwargs)

        def hgetall(self, key):
            return storage.get(key, {})

        def hget(self, key, field):
            return storage.get(key, {}).get(field)

        def exists(self, key):
            return key in storage

        def delete(self, *keys):
            for key in keys:
                storage.pop(key, None)
                sets.pop(key, None)

        def expire(self, key, ttl):
            pass  # No-op for tests

        def sadd(self, key, *values):
            if key not in sets:
                sets[key] = set()
            sets[key].update(str(v) for v in values)

        def srem(self, key, *values):
            if key in sets:
                for v in values:
                    sets[key].discard(str(v))

        def smembers(self, key):
            return sets.get(key, set())

    return MockRedis()


@pytest.fixture
def wizard_service(mock_redis):
    """Create WizardSessionService with mock Redis."""
    from services.wizard.wizard_session_service import WizardSessionService
    return WizardSessionService(mock_redis)


# =============================================================================
# Session CRUD Tests
# =============================================================================

class TestWizardSessionCreate:
    """Tests für create_session."""

    def test_WIZ_001_create_session_basic(self, wizard_service):
        """WIZ-001: Neue Session erstellen."""
        session = wizard_service.create_session(
            chatbot_id=1,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        assert session['chatbot_id'] == 1
        assert session['user_id'] == 100
        assert session['username'] == "testuser"
        assert session['source_url'] == "https://example.com"
        assert session['build_status'] == 'draft'
        assert session['current_step'] == 1

    def test_WIZ_002_create_session_with_config(self, wizard_service):
        """WIZ-002: Session mit Crawler-Config erstellen."""
        config = {'max_pages': 100, 'depth': 3}

        session = wizard_service.create_session(
            chatbot_id=2,
            user_id=100,
            username="testuser",
            source_url="https://example.com",
            crawler_config=config
        )

        assert session['crawler_config'] == config

    def test_WIZ_003_create_session_with_wizard_data(self, wizard_service):
        """WIZ-003: Session mit Wizard-Data erstellen."""
        wizard_data = {'name': 'Test Bot', 'color': '#FF0000'}

        session = wizard_service.create_session(
            chatbot_id=3,
            user_id=100,
            username="testuser",
            source_url="https://example.com",
            wizard_data=wizard_data
        )

        assert session['wizard_data'] == wizard_data

    def test_WIZ_004_create_session_timestamps(self, wizard_service):
        """WIZ-004: Timestamps werden gesetzt."""
        session = wizard_service.create_session(
            chatbot_id=4,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        assert session['created_at'] is not None
        assert session['last_activity_at'] is not None
        assert session['crawl_started_at'] is None
        assert session['embed_started_at'] is None

    def test_WIZ_005_create_session_initial_elapsed_times(self, wizard_service):
        """WIZ-005: Elapsed times sind initial 0."""
        session = wizard_service.create_session(
            chatbot_id=5,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        assert session['elapsed_crawl_time'] == 0.0
        assert session['elapsed_embed_time'] == 0.0


class TestWizardSessionGet:
    """Tests für get_session."""

    def test_WIZ_010_get_session_existing(self, wizard_service):
        """WIZ-010: Existierende Session abrufen."""
        wizard_service.create_session(
            chatbot_id=10,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        session = wizard_service.get_session(10)

        assert session is not None
        assert session['chatbot_id'] == 10

    def test_WIZ_011_get_session_not_found(self, wizard_service):
        """WIZ-011: Nicht existierende Session gibt None."""
        with patch.object(wizard_service, '_recover_from_db', return_value=None):
            session = wizard_service.get_session(999)

        assert session is None

    def test_WIZ_012_get_session_recovery_from_db(self, wizard_service):
        """WIZ-012: Session wird aus DB wiederhergestellt."""
        mock_session = {
            'chatbot_id': 12,
            'user_id': 100,
            'build_status': 'crawling'
        }

        with patch.object(wizard_service, '_recover_from_db', return_value=mock_session):
            session = wizard_service.get_session(12)

        assert session is not None
        assert session['build_status'] == 'crawling'


class TestWizardSessionUpdate:
    """Tests für update_session."""

    def test_WIZ_020_update_session_simple(self, wizard_service):
        """WIZ-020: Einfaches Session-Update."""
        wizard_service.create_session(
            chatbot_id=20,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        result = wizard_service.update_session(20, {'build_status': 'crawling'})

        assert result is True
        session = wizard_service.get_session(20)
        assert session['build_status'] == 'crawling'

    def test_WIZ_021_update_session_not_found(self, wizard_service):
        """WIZ-021: Update auf nicht existierende Session."""
        result = wizard_service.update_session(999, {'build_status': 'crawling'})

        assert result is False

    def test_WIZ_022_update_session_dict_serialization(self, wizard_service):
        """WIZ-022: Dict-Werte werden serialisiert."""
        wizard_service.create_session(
            chatbot_id=22,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        config = {'setting': 'value'}
        result = wizard_service.update_session(22, {'crawler_config': config})

        assert result is True
        session = wizard_service.get_session(22)
        assert session['crawler_config'] == config

    def test_WIZ_023_update_session_last_activity(self, wizard_service):
        """WIZ-023: last_activity_at wird automatisch aktualisiert."""
        wizard_service.create_session(
            chatbot_id=23,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        original_session = wizard_service.get_session(23)
        original_activity = original_session['last_activity_at']

        # Small delay to ensure different timestamp
        import time
        time.sleep(0.01)

        wizard_service.update_session(23, {'build_status': 'crawling'})
        updated_session = wizard_service.get_session(23)

        assert updated_session['last_activity_at'] != original_activity


class TestWizardSessionDelete:
    """Tests für delete_session."""

    def test_WIZ_030_delete_session(self, wizard_service):
        """WIZ-030: Session löschen."""
        wizard_service.create_session(
            chatbot_id=30,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        result = wizard_service.delete_session(30)

        assert result is True
        with patch.object(wizard_service, '_recover_from_db', return_value=None):
            session = wizard_service.get_session(30)
        assert session is None

    def test_WIZ_031_delete_session_cleans_user_sessions(self, wizard_service):
        """WIZ-031: User-Sessions werden aufgeräumt."""
        wizard_service.create_session(
            chatbot_id=31,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        wizard_service.delete_session(31)

        user_sessions = wizard_service.get_user_sessions(100)
        chatbot_ids = [s['chatbot_id'] for s in user_sessions]
        assert 31 not in chatbot_ids


# =============================================================================
# Status Transition Tests
# =============================================================================

class TestWizardStatusTransition:
    """Tests für transition_status."""

    def test_WIZ_040_transition_draft_to_crawling(self, wizard_service):
        """WIZ-040: Transition von draft zu crawling."""
        wizard_service.create_session(
            chatbot_id=40,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        session = wizard_service.transition_status(40, 'crawling')

        assert session['build_status'] == 'crawling'
        assert session['current_step'] == 2
        assert session['crawl_started_at'] is not None

    def test_WIZ_041_transition_crawling_to_embedding(self, wizard_service):
        """WIZ-041: Transition von crawling zu embedding."""
        wizard_service.create_session(
            chatbot_id=41,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )
        wizard_service.transition_status(41, 'crawling')

        session = wizard_service.transition_status(41, 'embedding')

        assert session['build_status'] == 'embedding'
        assert session['current_step'] == 3
        assert session['embed_started_at'] is not None

    def test_WIZ_042_transition_to_ready(self, wizard_service):
        """WIZ-042: Transition zu ready."""
        wizard_service.create_session(
            chatbot_id=42,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        session = wizard_service.transition_status(42, 'ready')

        assert session['build_status'] == 'ready'
        assert session['current_step'] == 5

    def test_WIZ_043_transition_to_error(self, wizard_service):
        """WIZ-043: Transition zu error mit Message."""
        wizard_service.create_session(
            chatbot_id=43,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        session = wizard_service.transition_status(
            43, 'error',
            error_message="Crawl failed",
            error_source="crawl"
        )

        assert session['build_status'] == 'error'
        assert session['error_message'] == "Crawl failed"
        assert session['error_source'] == "crawl"

    def test_WIZ_044_transition_to_paused(self, wizard_service):
        """WIZ-044: Transition zu paused."""
        wizard_service.create_session(
            chatbot_id=44,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )
        wizard_service.transition_status(44, 'crawling')

        session = wizard_service.transition_status(44, 'paused')

        assert session['build_status'] == 'paused'
        assert session['paused_at'] is not None

    def test_WIZ_045_transition_invalid_status(self, wizard_service):
        """WIZ-045: Ungültiger Status wird abgelehnt."""
        wizard_service.create_session(
            chatbot_id=45,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        session = wizard_service.transition_status(45, 'invalid_status')

        assert session is None

    def test_WIZ_046_transition_clears_error_on_valid_status(self, wizard_service):
        """WIZ-046: Error wird bei Statuswechsel gelöscht."""
        wizard_service.create_session(
            chatbot_id=46,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )
        wizard_service.transition_status(46, 'error', error_message="Test error")

        session = wizard_service.transition_status(46, 'draft')

        assert session['error_message'] is None or session['error_message'] == ''

    def test_WIZ_047_transition_not_found(self, wizard_service):
        """WIZ-047: Transition auf nicht existierende Session."""
        with patch.object(wizard_service, '_recover_from_db', return_value=None):
            session = wizard_service.transition_status(999, 'crawling')

        assert session is None


class TestWizardStatusToStep:
    """Tests für STATUS_TO_STEP Mapping."""

    def test_WIZ_050_status_draft_step_1(self, wizard_service):
        """WIZ-050: draft -> Step 1."""
        from services.wizard.wizard_session_service import WizardSessionService
        assert WizardSessionService.STATUS_TO_STEP['draft'] == 1

    def test_WIZ_051_status_crawling_step_2(self, wizard_service):
        """WIZ-051: crawling -> Step 2."""
        from services.wizard.wizard_session_service import WizardSessionService
        assert WizardSessionService.STATUS_TO_STEP['crawling'] == 2

    def test_WIZ_052_status_embedding_step_3(self, wizard_service):
        """WIZ-052: embedding -> Step 3."""
        from services.wizard.wizard_session_service import WizardSessionService
        assert WizardSessionService.STATUS_TO_STEP['embedding'] == 3

    def test_WIZ_053_status_configuring_step_4(self, wizard_service):
        """WIZ-053: configuring -> Step 4."""
        from services.wizard.wizard_session_service import WizardSessionService
        assert WizardSessionService.STATUS_TO_STEP['configuring'] == 4

    def test_WIZ_054_status_ready_step_5(self, wizard_service):
        """WIZ-054: ready -> Step 5."""
        from services.wizard.wizard_session_service import WizardSessionService
        assert WizardSessionService.STATUS_TO_STEP['ready'] == 5

    def test_WIZ_055_status_error_step_none(self, wizard_service):
        """WIZ-055: error -> Step None."""
        from services.wizard.wizard_session_service import WizardSessionService
        assert WizardSessionService.STATUS_TO_STEP['error'] is None


# =============================================================================
# Progress Updates Tests
# =============================================================================

class TestWizardProgressUpdates:
    """Tests für Progress-Updates."""

    def test_WIZ_060_update_crawl_progress(self, wizard_service):
        """WIZ-060: Crawl-Progress aktualisieren."""
        wizard_service.create_session(
            chatbot_id=60,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        wizard_service.update_crawl_progress(60, {
            'pages_crawled': 10,
            'total_pages': 50,
            'crawl_stage': 'crawling'
        })

        progress = wizard_service.get_progress(60)

        assert progress['pages_crawled'] == 10
        assert progress['total_pages'] == 50
        assert progress['crawl_stage'] == 'crawling'

    def test_WIZ_061_update_embedding_progress(self, wizard_service):
        """WIZ-061: Embedding-Progress aktualisieren."""
        wizard_service.create_session(
            chatbot_id=61,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        wizard_service.update_embedding_progress(61, {
            'chunks_processed': 100,
            'total_chunks': 500,
            'embedding_progress': 20
        })

        progress = wizard_service.get_progress(61)

        assert progress['chunks_processed'] == 100
        assert progress['total_chunks'] == 500
        assert progress['embedding_progress'] == 20

    def test_WIZ_062_get_progress_empty(self, wizard_service):
        """WIZ-062: Progress für Session ohne Progress-Daten."""
        wizard_service.create_session(
            chatbot_id=62,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        progress = wizard_service.get_progress(62)

        assert progress == {}

    def test_WIZ_063_progress_converts_numeric_strings(self, wizard_service):
        """WIZ-063: Numerische Strings werden konvertiert."""
        wizard_service.create_session(
            chatbot_id=63,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        wizard_service.update_crawl_progress(63, {
            'pages_crawled': 10,
            'progress_percent': 25.5
        })

        progress = wizard_service.get_progress(63)

        assert isinstance(progress['pages_crawled'], int)
        assert isinstance(progress['progress_percent'], float)


# =============================================================================
# Time Tracking Tests
# =============================================================================

class TestWizardTimeTracking:
    """Tests für Time-Tracking."""

    def test_WIZ_070_elapsed_time_initial(self, wizard_service):
        """WIZ-070: Initiale Elapsed-Time ist 0."""
        wizard_service.create_session(
            chatbot_id=70,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        elapsed = wizard_service.get_elapsed_time(70)

        assert elapsed['crawl'] == 0
        assert elapsed['embed'] == 0
        assert elapsed['total'] == 0

    def test_WIZ_071_elapsed_time_not_found(self, wizard_service):
        """WIZ-071: Elapsed-Time für nicht existierende Session."""
        with patch.object(wizard_service, '_recover_from_db', return_value=None):
            elapsed = wizard_service.get_elapsed_time(999)

        assert elapsed == {'crawl': 0, 'embed': 0, 'total': 0}

    def test_WIZ_072_elapsed_time_accumulated(self, wizard_service):
        """WIZ-072: Akkumulierte Zeit wird berechnet."""
        wizard_service.create_session(
            chatbot_id=72,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        # Set elapsed times directly
        wizard_service.update_session(72, {
            'elapsed_crawl_time': '30.5',
            'elapsed_embed_time': '20.0'
        })

        elapsed = wizard_service.get_elapsed_time(72)

        assert elapsed['crawl'] == 30.5
        assert elapsed['embed'] == 20.0
        assert elapsed['total'] == 50.5

    def test_WIZ_073_pause_timers(self, wizard_service):
        """WIZ-073: Timer pausieren."""
        wizard_service.create_session(
            chatbot_id=73,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )
        wizard_service.transition_status(73, 'crawling')

        wizard_service.pause_timers(73)

        session = wizard_service.get_session(73)
        assert session['build_status'] == 'paused'

    def test_WIZ_074_resume_timers_to_crawling(self, wizard_service):
        """WIZ-074: Timer zu crawling fortsetzen."""
        wizard_service.create_session(
            chatbot_id=74,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )
        wizard_service.transition_status(74, 'paused')

        # Set progress indicating crawling was active
        wizard_service.update_crawl_progress(74, {'crawl_stage': 'crawling'})

        wizard_service.resume_timers(74)

        session = wizard_service.get_session(74)
        assert session['build_status'] == 'crawling'

    def test_WIZ_075_resume_timers_to_embedding(self, wizard_service):
        """WIZ-075: Timer zu embedding fortsetzen."""
        wizard_service.create_session(
            chatbot_id=75,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )
        wizard_service.transition_status(75, 'paused')

        # Set progress indicating embedding was active
        wizard_service.update_embedding_progress(75, {'embedding_progress': 50})

        wizard_service.resume_timers(75)

        session = wizard_service.get_session(75)
        assert session['build_status'] == 'embedding'


# =============================================================================
# Wizard Data Tests
# =============================================================================

class TestWizardDataManagement:
    """Tests für Wizard-Data-Management."""

    def test_WIZ_080_update_wizard_data(self, wizard_service):
        """WIZ-080: Wizard-Data aktualisieren."""
        wizard_service.create_session(
            chatbot_id=80,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        result = wizard_service.update_wizard_data(80, {'name': 'Test Bot'})

        assert result is True
        data = wizard_service.get_wizard_data(80)
        assert data['name'] == 'Test Bot'

    def test_WIZ_081_update_wizard_data_merge(self, wizard_service):
        """WIZ-081: Wizard-Data wird gemerged."""
        wizard_service.create_session(
            chatbot_id=81,
            user_id=100,
            username="testuser",
            source_url="https://example.com",
            wizard_data={'name': 'Initial'}
        )

        wizard_service.update_wizard_data(81, {'color': '#FF0000'})

        data = wizard_service.get_wizard_data(81)
        assert data['name'] == 'Initial'
        assert data['color'] == '#FF0000'

    def test_WIZ_082_update_wizard_data_not_found(self, wizard_service):
        """WIZ-082: Update auf nicht existierende Session."""
        with patch.object(wizard_service, '_recover_from_db', return_value=None):
            result = wizard_service.update_wizard_data(999, {'name': 'Test'})

        assert result is False

    def test_WIZ_083_get_wizard_data_empty(self, wizard_service):
        """WIZ-083: Wizard-Data für Session ohne Data."""
        wizard_service.create_session(
            chatbot_id=83,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        data = wizard_service.get_wizard_data(83)

        assert data == {}

    def test_WIZ_084_get_wizard_data_not_found(self, wizard_service):
        """WIZ-084: Wizard-Data für nicht existierende Session."""
        with patch.object(wizard_service, '_recover_from_db', return_value=None):
            data = wizard_service.get_wizard_data(999)

        assert data == {}


# =============================================================================
# User Session Management Tests
# =============================================================================

class TestWizardUserSessions:
    """Tests für User-Session-Management."""

    def test_WIZ_090_get_user_sessions_empty(self, wizard_service):
        """WIZ-090: User ohne Sessions."""
        sessions = wizard_service.get_user_sessions(999)

        assert sessions == []

    def test_WIZ_091_get_user_sessions_single(self, wizard_service):
        """WIZ-091: User mit einer Session."""
        wizard_service.create_session(
            chatbot_id=91,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )

        sessions = wizard_service.get_user_sessions(100)

        assert len(sessions) == 1
        assert sessions[0]['chatbot_id'] == 91

    def test_WIZ_092_get_user_sessions_multiple(self, wizard_service):
        """WIZ-092: User mit mehreren Sessions."""
        wizard_service.create_session(
            chatbot_id=92,
            user_id=100,
            username="testuser",
            source_url="https://example1.com"
        )
        wizard_service.create_session(
            chatbot_id=93,
            user_id=100,
            username="testuser",
            source_url="https://example2.com"
        )

        sessions = wizard_service.get_user_sessions(100)

        assert len(sessions) == 2
        chatbot_ids = [s['chatbot_id'] for s in sessions]
        assert 92 in chatbot_ids
        assert 93 in chatbot_ids

    def test_WIZ_093_get_resumable_session_none(self, wizard_service):
        """WIZ-093: Keine resumable Session."""
        wizard_service.create_session(
            chatbot_id=94,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )
        wizard_service.transition_status(94, 'ready')

        session = wizard_service.get_resumable_session(100)

        assert session is None

    def test_WIZ_094_get_resumable_session_found(self, wizard_service):
        """WIZ-094: Resumable Session gefunden."""
        wizard_service.create_session(
            chatbot_id=95,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )
        wizard_service.transition_status(95, 'crawling')

        session = wizard_service.get_resumable_session(100)

        assert session is not None
        assert session['chatbot_id'] == 95
        assert session['build_status'] == 'crawling'

    def test_WIZ_095_get_resumable_excludes_error(self, wizard_service):
        """WIZ-095: Error-Sessions sind nicht resumable."""
        wizard_service.create_session(
            chatbot_id=96,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )
        wizard_service.transition_status(96, 'error', error_message="Test error")

        session = wizard_service.get_resumable_session(100)

        assert session is None


# =============================================================================
# Deserialization Tests
# =============================================================================

class TestWizardDeserialization:
    """Tests für _deserialize_session."""

    def test_WIZ_100_deserialize_chatbot_id(self, wizard_service):
        """WIZ-100: chatbot_id wird zu int."""
        session = wizard_service._deserialize_session({
            'chatbot_id': '123'
        })

        assert session['chatbot_id'] == 123

    def test_WIZ_101_deserialize_user_id_int(self, wizard_service):
        """WIZ-101: user_id als int."""
        session = wizard_service._deserialize_session({
            'user_id': '456'
        })

        assert session['user_id'] == 456

    def test_WIZ_102_deserialize_user_id_string(self, wizard_service):
        """WIZ-102: user_id als String (username)."""
        session = wizard_service._deserialize_session({
            'user_id': 'testuser'
        })

        assert session['user_id'] == 'testuser'

    def test_WIZ_103_deserialize_json_fields(self, wizard_service):
        """WIZ-103: JSON-Felder werden geparsed."""
        session = wizard_service._deserialize_session({
            'crawler_config': '{"max_pages": 100}',
            'wizard_data': '{"name": "Test"}'
        })

        assert session['crawler_config'] == {'max_pages': 100}
        assert session['wizard_data'] == {'name': 'Test'}

    def test_WIZ_104_deserialize_elapsed_times(self, wizard_service):
        """WIZ-104: Elapsed times werden zu float."""
        session = wizard_service._deserialize_session({
            'elapsed_crawl_time': '30.5',
            'elapsed_embed_time': '20.0'
        })

        assert session['elapsed_crawl_time'] == 30.5
        assert session['elapsed_embed_time'] == 20.0

    def test_WIZ_105_deserialize_empty_values(self, wizard_service):
        """WIZ-105: Leere Werte werden zu None."""
        session = wizard_service._deserialize_session({
            'error_message': '',
            'crawl_started_at': ''
        })

        assert session['error_message'] is None
        assert session['crawl_started_at'] is None


# =============================================================================
# Constants and Configuration Tests
# =============================================================================

class TestWizardConstants:
    """Tests für Service-Konstanten."""

    def test_WIZ_110_valid_statuses(self):
        """WIZ-110: Alle gültigen Status sind definiert."""
        from services.wizard.wizard_session_service import WizardSessionService

        expected = {'draft', 'crawling', 'embedding', 'configuring', 'ready', 'error', 'paused'}
        assert WizardSessionService.VALID_STATUSES == expected

    def test_WIZ_111_ttl_abandoned(self):
        """WIZ-111: TTL für abandoned Sessions."""
        from services.wizard.wizard_session_service import WizardSessionService

        assert WizardSessionService.TTL_ABANDONED == 604800  # 7 days

    def test_WIZ_112_key_session_template(self):
        """WIZ-112: Session-Key-Template."""
        from services.wizard.wizard_session_service import WizardSessionService

        key = WizardSessionService.KEY_SESSION.format(chatbot_id=123)
        assert key == "wizard:session:123"

    def test_WIZ_113_key_progress_template(self):
        """WIZ-113: Progress-Key-Template."""
        from services.wizard.wizard_session_service import WizardSessionService

        key = WizardSessionService.KEY_PROGRESS.format(chatbot_id=123)
        assert key == "wizard:session:123:progress"

    def test_WIZ_114_key_user_sessions_template(self):
        """WIZ-114: User-Sessions-Key-Template."""
        from services.wizard.wizard_session_service import WizardSessionService

        key = WizardSessionService.KEY_USER_SESSIONS.format(user_id=456)
        assert key == "wizard:user:456:sessions"

    def test_WIZ_115_key_active(self):
        """WIZ-115: Active-Sessions-Key."""
        from services.wizard.wizard_session_service import WizardSessionService

        assert WizardSessionService.KEY_ACTIVE == "wizard:active"


# =============================================================================
# Integration Tests
# =============================================================================

class TestWizardIntegration:
    """Integration Tests für vollständige Workflows."""

    def test_WIZ_120_complete_wizard_workflow(self, wizard_service):
        """WIZ-120: Vollständiger Wizard-Workflow."""
        # 1. Create session
        session = wizard_service.create_session(
            chatbot_id=120,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )
        assert session['build_status'] == 'draft'

        # 2. Start crawling
        session = wizard_service.transition_status(120, 'crawling')
        assert session['build_status'] == 'crawling'
        assert session['current_step'] == 2

        # 3. Update crawl progress
        wizard_service.update_crawl_progress(120, {
            'pages_crawled': 50,
            'total_pages': 100
        })

        # 4. Transition to embedding
        session = wizard_service.transition_status(120, 'embedding')
        assert session['build_status'] == 'embedding'
        assert session['current_step'] == 3

        # 5. Update embedding progress
        wizard_service.update_embedding_progress(120, {
            'chunks_processed': 500,
            'total_chunks': 1000
        })

        # 6. Transition to configuring
        session = wizard_service.transition_status(120, 'configuring')
        assert session['build_status'] == 'configuring'
        assert session['current_step'] == 4

        # 7. Update wizard data
        wizard_service.update_wizard_data(120, {
            'name': 'My Chatbot',
            'color': '#FF0000'
        })

        # 8. Complete wizard
        session = wizard_service.transition_status(120, 'ready')
        assert session['build_status'] == 'ready'
        assert session['current_step'] == 5

    def test_WIZ_121_pause_and_resume_workflow(self, wizard_service):
        """WIZ-121: Pause und Resume Workflow."""
        # Create and start crawling
        wizard_service.create_session(
            chatbot_id=121,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )
        wizard_service.transition_status(121, 'crawling')
        wizard_service.update_crawl_progress(121, {'crawl_stage': 'crawling'})

        # Pause
        wizard_service.pause_timers(121)
        session = wizard_service.get_session(121)
        assert session['build_status'] == 'paused'

        # Resume
        wizard_service.resume_timers(121)
        session = wizard_service.get_session(121)
        assert session['build_status'] == 'crawling'

    def test_WIZ_122_error_recovery_workflow(self, wizard_service):
        """WIZ-122: Error und Recovery Workflow."""
        # Create and start crawling
        wizard_service.create_session(
            chatbot_id=122,
            user_id=100,
            username="testuser",
            source_url="https://example.com"
        )
        wizard_service.transition_status(122, 'crawling')

        # Error occurs
        wizard_service.transition_status(
            122, 'error',
            error_message="Connection timeout",
            error_source="crawl"
        )
        session = wizard_service.get_session(122)
        assert session['build_status'] == 'error'
        assert session['error_message'] == "Connection timeout"

        # Retry - go back to draft
        session = wizard_service.transition_status(122, 'draft')
        assert session['build_status'] == 'draft'
        assert session['error_message'] is None or session['error_message'] == ''
