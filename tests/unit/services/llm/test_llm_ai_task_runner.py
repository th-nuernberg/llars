"""
LLMAITaskRunner Unit Tests
==========================

Tests for the LLM AI Task Runner's core safety mechanisms,
payload validation, and orchestration logic.

The LLMAITaskRunner has 6 anti-DDoS layers (see class docstring).
These tests verify each layer independently:
- Lock mechanism (layer 1): prevents duplicate parallel execution
- Permanent failure detection (layer 2): skips unrecoverable errors
- Circuit breaker (layer 5): aborts after consecutive failures
- Total failure cap (layer 6): tested indirectly via run_for_scenario

Additionally tests payload validators for all evaluation types,
model ID resolution from scenario config, JSON parsing with
markdown fence stripping, error storage, and the main orchestration
entry point (run_for_scenario).

Tests are split into pure-logic (no DB) and DB-dependent groups.
DB tests use the app/db/app_context fixtures from conftest.py.
"""

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from services.llm.llm_ai_task_runner import (
    LLMAITaskRunner,
    LLMNonRetryableError,
    LLMResponseError,
)


# ============================================================
# Autouse fixture: clear class-level lock state between tests
# ============================================================
@pytest.fixture(autouse=True)
def clear_active_locks():
    """
    Reset LLMAITaskRunner._active_locks between tests to prevent state leakage.

    _active_locks is a class-level set shared across all tests in the process.
    Without this fixture, a test that acquires a lock but fails before releasing
    it would cause all subsequent tests for that (scenario, model) pair to fail.
    """
    LLMAITaskRunner._active_locks.clear()
    yield
    LLMAITaskRunner._active_locks.clear()


# ============================================================
# TestLockMechanism (TASK_LOCK_001-006)
# ============================================================
class TestLockMechanism:
    """Test the thread-safe lock for (scenario_id, model_id) deduplication.

    This lock (layer 1 of anti-DDoS) prevents duplicate parallel execution
    of the same evaluation task. It was added after race conditions caused
    100% CPU and server crashes (see commits b70e670d, e16d4a30).

    The lock uses a threading.Lock guard around a set of (scenario_id, model_id)
    tuples, with _try_acquire using add-if-absent and _release using discard
    (safe for non-held keys).
    """

    def test_TASK_LOCK_001_try_acquire_first_call_returns_true(self):
        """First acquisition of a lock should succeed."""
        assert LLMAITaskRunner._try_acquire(1, "model-a") is True

    def test_TASK_LOCK_002_try_acquire_duplicate_returns_false(self):
        """Second acquisition of the same lock should fail (already held)."""
        LLMAITaskRunner._try_acquire(1, "model-a")
        assert LLMAITaskRunner._try_acquire(1, "model-a") is False

    def test_TASK_LOCK_003_release_makes_lock_available(self):
        """Releasing a lock should allow re-acquisition."""
        LLMAITaskRunner._try_acquire(1, "model-a")
        LLMAITaskRunner._release(1, "model-a")
        assert LLMAITaskRunner._try_acquire(1, "model-a") is True

    def test_TASK_LOCK_004_is_running_reflects_lock_state(self):
        """is_running should accurately reflect whether a lock is held."""
        assert LLMAITaskRunner.is_running(1, "model-a") is False
        LLMAITaskRunner._try_acquire(1, "model-a")
        assert LLMAITaskRunner.is_running(1, "model-a") is True
        LLMAITaskRunner._release(1, "model-a")
        assert LLMAITaskRunner.is_running(1, "model-a") is False

    def test_TASK_LOCK_005_concurrent_acquire_only_one_wins(self):
        """10 threads race to acquire the same lock -- exactly 1 should win.

        Validates that the threading.Lock guard around _active_locks prevents
        race conditions when multiple triggers fire simultaneously (e.g.
        server startup + user opening scenario page).
        """
        results = []

        def try_lock():
            results.append(LLMAITaskRunner._try_acquire(99, "race-model"))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(try_lock) for _ in range(10)]
            for f in futures:
                f.result()

        assert results.count(True) == 1
        assert results.count(False) == 9

    def test_TASK_LOCK_006_release_unheld_lock_is_noop(self):
        """Releasing a lock that was never acquired should not raise.

        Uses set.discard() internally which is safe for missing keys.
        This matters because finally blocks always call _release.
        """
        LLMAITaskRunner._release(999, "nonexistent")
        assert LLMAITaskRunner.is_running(999, "nonexistent") is False


# ============================================================
# TestPermanentFailureDetection (TASK_PERM_001-013)
# ============================================================
class TestPermanentFailureDetection:
    """Test classification of stored error strings as permanent failures.

    Layer 2 of anti-DDoS: permanent failures (401/403/404/422 and auth-related
    keywords) are skipped by auto-start paths (server startup, scenario GET).
    Only the manual "Start/Retry" button can clear these error records and retry.

    _is_permanent_failure checks STORED error strings from the DB, while
    _is_non_retryable_error checks LIVE exceptions during API calls. They use
    different code sets: permanent includes 404/422, non-retryable only 401/403.
    """

    def test_TASK_PERM_001_http_401(self):
        """401 Unauthorized is always permanent (invalid API key)."""
        assert LLMAITaskRunner._is_permanent_failure("Error code: 401") is True

    def test_TASK_PERM_002_http_403(self):
        """403 Forbidden is always permanent (no model access)."""
        assert LLMAITaskRunner._is_permanent_failure("Error code: 403") is True

    def test_TASK_PERM_003_http_404(self):
        """404 Not Found is permanent (model doesn't exist)."""
        assert LLMAITaskRunner._is_permanent_failure("Error code: 404") is True

    def test_TASK_PERM_004_http_422(self):
        """422 Unprocessable Entity is permanent (bad request format)."""
        assert LLMAITaskRunner._is_permanent_failure("status_code=422 bad request") is True

    def test_TASK_PERM_005_keyword_unauthorized(self):
        """'unauthorized' keyword in error string triggers permanent failure."""
        assert LLMAITaskRunner._is_permanent_failure("Request unauthorized") is True

    def test_TASK_PERM_006_keyword_forbidden(self):
        """'forbidden' keyword in error string triggers permanent failure."""
        assert LLMAITaskRunner._is_permanent_failure("Access forbidden for this model") is True

    def test_TASK_PERM_007_keyword_authentication(self):
        """'authentication' keyword in error string triggers permanent failure."""
        assert LLMAITaskRunner._is_permanent_failure("Authentication failed") is True

    def test_TASK_PERM_008_keyword_invalid_api_key(self):
        """'invalid api key' keyword triggers permanent failure."""
        assert LLMAITaskRunner._is_permanent_failure("Invalid api key provided") is True

    def test_TASK_PERM_009_keyword_invalid_api_key_underscore(self):
        """'invalid_api_key' (underscore variant) triggers permanent failure."""
        assert LLMAITaskRunner._is_permanent_failure("invalid_api_key") is True

    def test_TASK_PERM_010_empty_string_returns_false(self):
        """Empty error string is not a permanent failure."""
        assert LLMAITaskRunner._is_permanent_failure("") is False

    def test_TASK_PERM_011_none_returns_false(self):
        """None error string is not a permanent failure."""
        assert LLMAITaskRunner._is_permanent_failure(None) is False

    def test_TASK_PERM_012_rate_limit_not_permanent(self):
        """429 rate limit is transient -- should be retried on next auto-start."""
        assert LLMAITaskRunner._is_permanent_failure("Error code: 429 rate limited") is False

    def test_TASK_PERM_013_server_error_not_permanent(self):
        """500 server error is transient -- should be retried on next auto-start."""
        assert LLMAITaskRunner._is_permanent_failure("Error code: 500 internal server error") is False


# ============================================================
# TestNonRetryableError (TASK_NR_001-005)
# ============================================================
class TestNonRetryableError:
    """Test classification of live exceptions as non-retryable.

    _is_non_retryable_error checks live exceptions during API calls
    and only triggers for 401/403 (unlike _is_permanent_failure which
    also includes 404/422). Non-retryable errors raise LLMNonRetryableError
    immediately without retrying within _request_json.
    """

    def test_TASK_NR_001_status_code_attribute_401(self):
        """Exception with status_code=401 attribute is non-retryable."""
        exc = Exception("Auth error")
        exc.status_code = 401
        assert LLMAITaskRunner._is_non_retryable_error(exc) is True

    def test_TASK_NR_002_status_code_attribute_403(self):
        """Exception with status_code=403 attribute is non-retryable."""
        exc = Exception("Forbidden")
        exc.status_code = 403
        assert LLMAITaskRunner._is_non_retryable_error(exc) is True

    def test_TASK_NR_003_error_code_in_string(self):
        """'Error code: 401' in exception string is non-retryable."""
        exc = Exception("Error code: 401 Unauthorized")
        assert LLMAITaskRunner._is_non_retryable_error(exc) is True

    def test_TASK_NR_004_status_code_in_string(self):
        """'status_code=403' in exception string is non-retryable."""
        exc = Exception("Response status_code=403")
        assert LLMAITaskRunner._is_non_retryable_error(exc) is True

    def test_TASK_NR_005_rate_limit_is_retryable(self):
        """429 rate limit should NOT be non-retryable (it's transient)."""
        exc = Exception("Error code: 429 Too Many Requests")
        exc.status_code = 429
        assert LLMAITaskRunner._is_non_retryable_error(exc) is False


# ============================================================
# TestCircuitBreaker (TASK_CB_001-004)
# ============================================================
class TestCircuitBreaker:
    """Test the circuit breaker that aborts after MAX_CONSECUTIVE_FAILURES (3).

    Layer 5 of anti-DDoS: prevents runaway loops when an LLM endpoint is
    consistently failing. When tripped, broadcasts model_aborted via Socket.IO
    so the frontend shows a failure badge on the Assessors tab.
    """

    def test_TASK_CB_001_below_threshold_returns_false(self):
        """2 consecutive failures (below 3) should not trip the breaker."""
        assert LLMAITaskRunner._check_circuit_breaker(2, "m", 1, "ranking") is False

    def test_TASK_CB_002_at_threshold_returns_true(self):
        """Exactly 3 consecutive failures should trip the breaker."""
        assert LLMAITaskRunner._check_circuit_breaker(3, "m", 1, "ranking") is True

    def test_TASK_CB_003_above_threshold_returns_true(self):
        """More than 3 consecutive failures should trip the breaker."""
        assert LLMAITaskRunner._check_circuit_breaker(5, "m", 1, "ranking") is True

    def test_TASK_CB_004_zero_returns_false(self):
        """Zero failures should not trip the breaker."""
        assert LLMAITaskRunner._check_circuit_breaker(0, "m", 1, "ranking") is False


# ============================================================
# TestParseJson (TASK_PARSE_001-005)
# ============================================================
class TestParseJson:
    """Test JSON parsing with markdown fence stripping.

    LLMs sometimes wrap JSON responses in markdown code fences
    (```json ... ```). _parse_json strips these before parsing.
    """

    def test_TASK_PARSE_001_valid_json(self):
        """Plain JSON string is parsed correctly."""
        result = LLMAITaskRunner._parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_TASK_PARSE_002_markdown_fence_stripped(self):
        """JSON wrapped in ```json ... ``` fences is parsed correctly."""
        result = LLMAITaskRunner._parse_json('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_TASK_PARSE_003_empty_raises(self):
        """Empty string raises json.JSONDecodeError."""
        with pytest.raises(Exception):
            LLMAITaskRunner._parse_json("")

    def test_TASK_PARSE_004_none_raises(self):
        """None input raises an exception (converted to empty string internally)."""
        with pytest.raises(Exception):
            LLMAITaskRunner._parse_json(None)

    def test_TASK_PARSE_005_plain_fence_stripped(self):
        """JSON wrapped in plain ``` fences (no language tag) is parsed correctly."""
        result = LLMAITaskRunner._parse_json('```\n{"a": 1}\n```')
        assert result == {"a": 1}


# ============================================================
# TestValidateBucketPayload (TASK_VB_001-005)
# ============================================================
class TestValidateBucketPayload:
    """Test bucket (ranking) payload validation.

    Bucket validation ensures every feature is assigned to exactly one bucket,
    with no duplicates and no missing features. Accepts string digit IDs
    from LLMs and converts them to int.
    """

    def test_TASK_VB_001_valid_payload_accepted(self):
        """Valid bucket assignment with all features assigned once."""
        features = [SimpleNamespace(feature_id=1), SimpleNamespace(feature_id=2)]
        payload = {"gut": [1], "schlecht": [2]}
        result = LLMAITaskRunner._validate_bucket_payload(payload, features, ["gut", "schlecht"])
        assert result == {"gut": [1], "schlecht": [2]}

    def test_TASK_VB_002_duplicate_ids_rejected(self):
        """Duplicate feature IDs across or within buckets are rejected."""
        features = [SimpleNamespace(feature_id=1), SimpleNamespace(feature_id=2)]
        payload = {"gut": [1, 1], "schlecht": [2]}
        result = LLMAITaskRunner._validate_bucket_payload(payload, features, ["gut", "schlecht"])
        assert result is None

    def test_TASK_VB_003_string_digit_conversion(self):
        """String digit feature IDs (common LLM output) are converted to int."""
        features = [SimpleNamespace(feature_id=1), SimpleNamespace(feature_id=2)]
        payload = {"gut": ["1"], "schlecht": ["2"]}
        result = LLMAITaskRunner._validate_bucket_payload(payload, features, ["gut", "schlecht"])
        assert result == {"gut": [1], "schlecht": [2]}

    def test_TASK_VB_004_missing_features_rejected(self):
        """Payload missing a feature ID is rejected (not all features assigned)."""
        features = [SimpleNamespace(feature_id=1), SimpleNamespace(feature_id=2)]
        payload = {"gut": [1], "schlecht": []}
        result = LLMAITaskRunner._validate_bucket_payload(payload, features, ["gut", "schlecht"])
        assert result is None

    def test_TASK_VB_005_non_dict_rejected(self):
        """Non-dict payload is rejected."""
        features = [SimpleNamespace(feature_id=1)]
        result = LLMAITaskRunner._validate_bucket_payload("not a dict", features, ["gut"])
        assert result is None


# ============================================================
# TestValidateComparisonPayload (TASK_VC_001-005)
# ============================================================
class TestValidateComparisonPayload:
    """Test comparison payload validation.

    Comparison validation accepts winner A/B/TIE (case-insensitive),
    validates confidence 1-5 (defaults to 3 if invalid), and
    passes through optional reasoning.
    """

    def test_TASK_VC_001_winner_A_valid(self):
        """Winner 'A' with valid confidence is accepted."""
        payload = {"winner": "A", "confidence": 4, "reasoning": "Better"}
        result = LLMAITaskRunner._validate_comparison_payload(payload)
        assert result is not None
        assert result["winner"] == "A"

    def test_TASK_VC_002_winner_B_valid(self):
        """Winner 'B' with valid confidence is accepted."""
        payload = {"winner": "B", "confidence": 2, "reasoning": "Clearer"}
        result = LLMAITaskRunner._validate_comparison_payload(payload)
        assert result is not None
        assert result["winner"] == "B"

    def test_TASK_VC_003_winner_C_rejected(self):
        """Invalid winner 'C' is rejected."""
        payload = {"winner": "C", "confidence": 3}
        result = LLMAITaskRunner._validate_comparison_payload(payload)
        assert result is None

    def test_TASK_VC_004_confidence_clamped_to_default(self):
        """Confidence outside 1-5 range defaults to 3."""
        payload = {"winner": "B", "confidence": 99}
        result = LLMAITaskRunner._validate_comparison_payload(payload)
        assert result["confidence"] == 3

    def test_TASK_VC_005_tie_accepted(self):
        """Winner 'TIE' is accepted."""
        payload = {"winner": "TIE", "confidence": 3}
        result = LLMAITaskRunner._validate_comparison_payload(payload)
        assert result is not None
        assert result["winner"] == "TIE"


# ============================================================
# TestValidateAuthenticityPayload (TASK_VA_001-004)
# ============================================================
class TestValidateAuthenticityPayload:
    """Test authenticity (real/fake) payload validation.

    Authenticity validation accepts vote 'real' or 'fake' (case-insensitive),
    validates confidence 1-5, and rejects any other vote value.
    Unlike comparison, invalid confidence causes rejection (not default).
    """

    def test_TASK_VA_001_vote_real_valid(self):
        """Vote 'real' with valid confidence is accepted."""
        payload = {"vote": "real", "confidence": 4}
        result = LLMAITaskRunner._validate_authenticity_payload(payload)
        assert result is not None
        assert result["vote"] == "real"

    def test_TASK_VA_002_vote_fake_valid(self):
        """Vote 'fake' with valid confidence is accepted."""
        payload = {"vote": "fake", "confidence": 2}
        result = LLMAITaskRunner._validate_authenticity_payload(payload)
        assert result is not None
        assert result["vote"] == "fake"

    def test_TASK_VA_003_invalid_vote_rejected(self):
        """Vote 'maybe' (not real/fake) is rejected."""
        payload = {"vote": "maybe", "confidence": 3}
        result = LLMAITaskRunner._validate_authenticity_payload(payload)
        assert result is None

    def test_TASK_VA_004_invalid_confidence_rejected(self):
        """Confidence outside 1-5 causes rejection (unlike comparison which defaults)."""
        payload = {"vote": "real", "confidence": 0}
        result = LLMAITaskRunner._validate_authenticity_payload(payload)
        assert result is None


# ============================================================
# TestValidateClassificationPayload (TASK_VCL_001-004)
# ============================================================
class TestValidateClassificationPayload:
    """Test labeling/classification payload validation.

    Classification validation checks that the label is in the allowed list
    (case-insensitive match), defaults confidence to 3 if invalid, and
    passes through optional reasoning.
    """

    def test_TASK_VCL_001_valid_label_accepted(self):
        """Label in allowed list with valid confidence is accepted."""
        payload = {"label": "positive", "confidence": 4, "reasoning": "good"}
        result = LLMAITaskRunner._validate_classification_payload(payload, ["positive", "negative"])
        assert result is not None
        assert result["label"] == "positive"

    def test_TASK_VCL_002_invalid_label_rejected(self):
        """Label not in allowed list is rejected."""
        payload = {"label": "unknown_label", "confidence": 3}
        result = LLMAITaskRunner._validate_classification_payload(payload, ["positive", "negative"])
        assert result is None

    def test_TASK_VCL_003_case_insensitive_match(self):
        """Label matching is case-insensitive."""
        payload = {"label": "POSITIVE", "confidence": 3}
        result = LLMAITaskRunner._validate_classification_payload(payload, ["positive", "negative"])
        assert result is not None

    def test_TASK_VCL_004_confidence_defaults_if_invalid(self):
        """Invalid confidence defaults to 3 instead of rejecting."""
        payload = {"label": "positive", "confidence": 99}
        result = LLMAITaskRunner._validate_classification_payload(payload, ["positive", "negative"])
        assert result is not None
        assert result["confidence"] == 3


# ============================================================
# TestResolveModelIds (TASK_RESOLVE_001-006)
# ============================================================
class TestResolveModelIds:
    """Test extraction and normalization of LLM model IDs from scenario config.

    _resolve_model_ids supports multiple config formats:
    - llm_evaluators: ["model-a"] (preferred)
    - selected_llms: ["model-b"] (legacy fallback)
    - llm_evaluators: [{"model_id": "model-c"}] (dict format from wizard)

    Also handles deduplication and override via model_ids parameter.
    """

    def _make_scenario(self, config_json):
        """Create a mock scenario with the given config."""
        return SimpleNamespace(config_json=config_json)

    def test_TASK_RESOLVE_001_from_llm_evaluators(self):
        """Models are extracted from llm_evaluators config key."""
        scenario = self._make_scenario({"llm_evaluators": ["model-a", "model-b"]})
        result = LLMAITaskRunner._resolve_model_ids(scenario)
        assert result == ["model-a", "model-b"]

    def test_TASK_RESOLVE_002_from_selected_llms_fallback(self):
        """Falls back to selected_llms when llm_evaluators is absent."""
        scenario = self._make_scenario({"selected_llms": ["fallback-model"]})
        result = LLMAITaskRunner._resolve_model_ids(scenario)
        assert result == ["fallback-model"]

    def test_TASK_RESOLVE_003_dict_format(self):
        """Extracts model_id from dict-format entries (wizard output)."""
        scenario = self._make_scenario({
            "llm_evaluators": [{"model_id": "dict-model"}]
        })
        result = LLMAITaskRunner._resolve_model_ids(scenario)
        assert result == ["dict-model"]

    def test_TASK_RESOLVE_004_deduplication(self):
        """Duplicate model IDs are removed (preserving order)."""
        scenario = self._make_scenario({
            "llm_evaluators": ["model-a", "model-a", "model-b"]
        })
        result = LLMAITaskRunner._resolve_model_ids(scenario)
        assert result == ["model-a", "model-b"]

    def test_TASK_RESOLVE_005_empty_config(self):
        """Empty config returns empty list."""
        scenario = self._make_scenario({})
        result = LLMAITaskRunner._resolve_model_ids(scenario)
        assert result == []

    def test_TASK_RESOLVE_006_override_model_ids(self):
        """Explicit model_ids parameter overrides config."""
        scenario = self._make_scenario({"llm_evaluators": ["ignored"]})
        result = LLMAITaskRunner._resolve_model_ids(scenario, model_ids=["override-model"])
        assert result == ["override-model"]

    def test_TASK_RESOLVE_007_string_config_parsed(self):
        """JSON string config is parsed before extraction."""
        scenario = self._make_scenario(json.dumps({"llm_evaluators": ["from-string"]}))
        result = LLMAITaskRunner._resolve_model_ids(scenario)
        assert result == ["from-string"]

    def test_TASK_RESOLVE_008_invalid_json_string_returns_empty(self):
        """Invalid JSON string config returns empty list."""
        scenario = self._make_scenario("not valid json")
        result = LLMAITaskRunner._resolve_model_ids(scenario)
        assert result == []


# ============================================================
# TestStoreError (TASK_STORE_001-003) -- needs app_context + db
# ============================================================
class TestStoreError:
    """Test error storage in LLMTaskResult table.

    _store_error creates new records or updates existing ones, and
    handles DB exceptions gracefully (catches, rolls back, no crash).
    This is critical because _store_error is called from within the
    item processing loop where an unhandled exception would abort
    the entire model run.
    """

    def test_TASK_STORE_001_creates_new_error_record(self, app, db, app_context):
        """New error record is created when no existing result exists."""
        from db.models.llm_task_result import LLMTaskResult
        from db.models.scenario import RatingScenarios, FeatureFunctionType
        from db.models import EvaluationItem

        # Create prerequisite data (FK constraints)
        ft = FeatureFunctionType(function_type_id=1, name="ranking")
        db.session.add(ft)
        db.session.commit()

        scenario = RatingScenarios(
            scenario_name="test-scenario",
            function_type_id=1,
            config_json={}
        )
        db.session.add(scenario)
        db.session.commit()

        item = EvaluationItem(subject="test item", content="test content")
        db.session.add(item)
        db.session.commit()

        LLMAITaskRunner._store_error(
            scenario_id=scenario.id,
            thread_id=item.item_id,
            model_id="test-model",
            task_type="ranking",
            error="test error message",
        )

        result = LLMTaskResult.query.filter_by(scenario_id=scenario.id).first()
        assert result is not None
        assert result.error == "test error message"
        assert result.payload_json is None

    def test_TASK_STORE_002_updates_existing_error(self, app, db, app_context):
        """Existing result record gets error field updated (not duplicated)."""
        from db.models.llm_task_result import LLMTaskResult
        from db.models.scenario import RatingScenarios, FeatureFunctionType
        from db.models import EvaluationItem

        ft = FeatureFunctionType(function_type_id=1, name="ranking")
        db.session.add(ft)
        db.session.commit()

        scenario = RatingScenarios(scenario_name="test", function_type_id=1, config_json={})
        db.session.add(scenario)
        db.session.commit()

        item = EvaluationItem(subject="test", content="test")
        db.session.add(item)
        db.session.commit()

        # Create existing record with old error
        existing = LLMTaskResult(
            scenario_id=scenario.id,
            thread_id=item.item_id,
            model_id="test-model",
            task_type="ranking",
            error="old error",
        )
        db.session.add(existing)
        db.session.commit()

        # Update with new error
        LLMAITaskRunner._store_error(
            scenario_id=scenario.id,
            thread_id=item.item_id,
            model_id="test-model",
            task_type="ranking",
            error="new error",
        )

        result = LLMTaskResult.query.filter_by(scenario_id=scenario.id).first()
        assert result.error == "new error"

    def test_TASK_STORE_003_db_exception_handled_gracefully(self, app, db, app_context):
        """DB exceptions are caught and rolled back -- no crash propagation.

        This is critical because _store_error is called from within the item
        processing loop. An unhandled DB exception here would abort all
        remaining items for this model.
        """
        with patch('services.llm.llm_ai_task_runner.LLMTaskResult') as mock_model:
            mock_model.query.filter_by.return_value.first.side_effect = Exception("DB Error")
            # Should not raise -- exception is caught internally
            LLMAITaskRunner._store_error(
                scenario_id=999,
                thread_id=999,
                model_id="test",
                task_type="ranking",
                error="test",
            )


# ============================================================
# TestRunForScenario (TASK_RUN_001-005) -- needs app_context + db
# ============================================================
class TestRunForScenario:
    """Test the main orchestration method that dispatches evaluation tasks.

    run_for_scenario is the single entry point for all LLM evaluations.
    It resolves model IDs from scenario config, acquires locks per model,
    dispatches to the correct runner method based on function_type, and
    always releases locks in a finally block (even on exceptions).
    """

    def _create_scenario(self, db, function_type_id=1, config_json=None):
        """Helper to create a scenario with required FK data for testing."""
        from db.models.scenario import RatingScenarios, FeatureFunctionType, ScenarioThreads
        from db.models import EvaluationItem

        if not FeatureFunctionType.query.filter_by(function_type_id=function_type_id).first():
            db.session.add(FeatureFunctionType(function_type_id=function_type_id, name="ranking"))
            db.session.commit()

        scenario = RatingScenarios(
            scenario_name="test",
            function_type_id=function_type_id,
            config_json=config_json or {"llm_evaluators": ["test-model"]},
        )
        db.session.add(scenario)
        db.session.commit()

        item = EvaluationItem(subject="test", content="test")
        db.session.add(item)
        db.session.commit()

        st = ScenarioThreads(scenario_id=scenario.id, thread_id=item.item_id)
        db.session.add(st)
        db.session.commit()

        return scenario

    def test_TASK_RUN_001_nonexistent_scenario_skipped(self, app, db, app_context):
        """Non-existent scenario is silently skipped (no exception)."""
        LLMAITaskRunner.run_for_scenario(99999)
        # No exception raised, no lock held
        assert not LLMAITaskRunner.is_running(99999, "any")

    @patch.object(LLMAITaskRunner, '_run_model_for_scenario')
    def test_TASK_RUN_002_lock_acquired_and_dispatched(self, mock_run, app, db, app_context):
        """Lock is acquired, runner dispatched, and lock released after completion."""
        scenario = self._create_scenario(db)

        LLMAITaskRunner.run_for_scenario(scenario.id)

        assert mock_run.called
        # Lock should be released after run completes
        assert not LLMAITaskRunner.is_running(scenario.id, "test-model")

    @patch.object(LLMAITaskRunner, '_run_model_for_scenario', side_effect=RuntimeError("boom"))
    def test_TASK_RUN_003_lock_released_on_exception(self, mock_run, app, db, app_context):
        """Lock is released even when the runner raises an unhandled exception.

        This is critical for resilience: if a runner crashes, the lock must
        be released so that subsequent retries (manual or auto-start) can
        acquire it. The finally block in run_for_scenario ensures release,
        but the exception itself propagates upward (caught by run_for_scenario_async).
        """
        scenario = self._create_scenario(db)

        with pytest.raises(RuntimeError, match="boom"):
            LLMAITaskRunner.run_for_scenario(scenario.id)

        # Lock must be released despite the exception (via finally block)
        assert not LLMAITaskRunner.is_running(scenario.id, "test-model")

    @patch.object(LLMAITaskRunner, '_run_model_for_scenario')
    def test_TASK_RUN_004_skip_if_lock_held(self, mock_run, app, db, app_context):
        """Model is skipped if another thread already holds the lock.

        This prevents the duplicate execution that previously caused 100% CPU.
        """
        scenario = self._create_scenario(db)

        # Pre-acquire the lock (simulating another thread running)
        LLMAITaskRunner._try_acquire(scenario.id, "test-model")

        LLMAITaskRunner.run_for_scenario(scenario.id)

        # Runner should NOT have been called (lock was already held)
        assert not mock_run.called

        # Clean up the pre-acquired lock
        LLMAITaskRunner._release(scenario.id, "test-model")

    @patch.object(LLMAITaskRunner, '_run_model_for_scenario')
    def test_TASK_RUN_005_dispatch_correct_function_type(self, mock_run, app, db, app_context):
        """Dispatch sends correct function_name (from FeatureFunctionType) to runner."""
        scenario = self._create_scenario(db, function_type_id=1)

        LLMAITaskRunner.run_for_scenario(scenario.id)

        # Check that _run_model_for_scenario was called with correct args
        call_args = mock_run.call_args
        assert call_args is not None
        # Positional args: (model_id, function_name, thread_ids, scenario)
        assert call_args[0][0] == "test-model"   # model_id
        assert call_args[0][1] == "ranking"       # function_name from FeatureFunctionType


# ============================================================
# TestRequestJson (TASK_REQ_001-003) -- mock LLMExecutionService
# ============================================================
class TestRequestJson:
    """Test the JSON request/retry loop that communicates with LLM APIs.

    _request_json retries invalid JSON responses up to MAX_RETRIES times
    (appending correction prompts to the conversation). On auth failures
    (401/403), it raises LLMNonRetryableError immediately without retrying.

    These tests mock LLMExecutionService.execute_chat_completion to avoid
    actual API calls.
    """

    def _make_response(self, content):
        """Create a mock LLM API response with the given content text."""
        msg = SimpleNamespace(
            content=content,
            role="assistant",
            function_call=None,
            tool_calls=None,
            refusal=None,
            reasoning_content=None,
        )
        choice = SimpleNamespace(message=msg)
        return SimpleNamespace(choices=[choice], usage=None)

    @patch('services.llm.llm_ai_task_runner.LLMExecutionService')
    @patch('services.llm.llm_ai_task_runner.get_setting', return_value="")
    def test_TASK_REQ_001_valid_json_first_attempt(self, mock_setting, mock_svc):
        """Valid JSON response is parsed and returned on first attempt."""
        mock_svc.execute_chat_completion.return_value = self._make_response('{"result": "ok"}')

        result, raw = LLMAITaskRunner._request_json(
            MagicMock(), "model-id", "system", "user"
        )
        assert result == {"result": "ok"}
        assert mock_svc.execute_chat_completion.call_count == 1

    @patch('services.llm.llm_ai_task_runner.LLMExecutionService')
    @patch('services.llm.llm_ai_task_runner.get_setting', return_value="")
    def test_TASK_REQ_002_retry_on_invalid_json(self, mock_setting, mock_svc):
        """Invalid JSON triggers retries, eventually raises LLMResponseError."""
        mock_svc.execute_chat_completion.return_value = self._make_response("not json at all")

        with pytest.raises(LLMResponseError):
            LLMAITaskRunner._request_json(
                MagicMock(), "model-id", "system", "user"
            )

        # Should have tried MAX_RETRIES + 1 times (initial + retries)
        assert mock_svc.execute_chat_completion.call_count == LLMAITaskRunner.MAX_RETRIES + 1

    @patch('services.llm.llm_ai_task_runner.LLMExecutionService')
    @patch('services.llm.llm_ai_task_runner.get_setting', return_value="")
    def test_TASK_REQ_003_non_retryable_error_on_401(self, mock_setting, mock_svc):
        """401 API error raises LLMNonRetryableError immediately (no retry).

        This is critical for layer 2: auth failures should not be retried
        because they will never succeed without user intervention.
        """
        exc = Exception("Error code: 401 Unauthorized")
        exc.status_code = 401
        mock_svc.execute_chat_completion.side_effect = exc

        with pytest.raises(LLMNonRetryableError):
            LLMAITaskRunner._request_json(
                MagicMock(), "model-id", "system", "user"
            )

        # Should NOT retry -- only 1 API call
        assert mock_svc.execute_chat_completion.call_count == 1
