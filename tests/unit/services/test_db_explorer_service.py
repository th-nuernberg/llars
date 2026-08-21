"""
Unit tests for DbExplorerService.

Tests table listing, table snapshots, table name validation (regex whitelist),
and JSON-safe serialization of various types (datetime, Decimal, bytes, etc.).
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import patch, MagicMock, PropertyMock


# ---------------------------------------------------------------------------
# Tests: _json_safe (static, no DB required)
# ---------------------------------------------------------------------------

class TestJsonSafe:
    """Tests for DbExplorerService._json_safe()."""

    def test_DBEXP_001_none_returns_none(self):
        """[DBEXP-001] None value returns None."""
        from services.db_explorer_service import DbExplorerService
        assert DbExplorerService._json_safe(None) is None

    def test_DBEXP_002_bool_passthrough(self):
        """[DBEXP-002] Boolean values are returned as-is."""
        from services.db_explorer_service import DbExplorerService
        assert DbExplorerService._json_safe(True) is True
        assert DbExplorerService._json_safe(False) is False

    def test_DBEXP_003_int_passthrough(self):
        """[DBEXP-003] Integer values are returned as-is."""
        from services.db_explorer_service import DbExplorerService
        assert DbExplorerService._json_safe(42) == 42

    def test_DBEXP_004_float_passthrough(self):
        """[DBEXP-004] Float values are returned as-is."""
        from services.db_explorer_service import DbExplorerService
        assert DbExplorerService._json_safe(3.14) == 3.14

    def test_DBEXP_005_str_passthrough(self):
        """[DBEXP-005] String values are returned as-is."""
        from services.db_explorer_service import DbExplorerService
        assert DbExplorerService._json_safe('hello') == 'hello'

    def test_DBEXP_006_datetime_to_isoformat(self):
        """[DBEXP-006] datetime is serialized to ISO format string."""
        from services.db_explorer_service import DbExplorerService
        dt = datetime(2026, 1, 15, 10, 30, 0)
        assert DbExplorerService._json_safe(dt) == '2026-01-15T10:30:00'

    def test_DBEXP_007_date_to_isoformat(self):
        """[DBEXP-007] date is serialized to ISO format string."""
        from services.db_explorer_service import DbExplorerService
        d = date(2026, 1, 15)
        assert DbExplorerService._json_safe(d) == '2026-01-15'

    def test_DBEXP_008_decimal_to_float(self):
        """[DBEXP-008] Decimal is converted to float."""
        from services.db_explorer_service import DbExplorerService
        result = DbExplorerService._json_safe(Decimal('3.14'))
        assert isinstance(result, float)
        assert abs(result - 3.14) < 1e-9

    def test_DBEXP_009_bytes_to_hex(self):
        """[DBEXP-009] bytes are converted to hex string."""
        from services.db_explorer_service import DbExplorerService
        result = DbExplorerService._json_safe(b'\xde\xad\xbe\xef')
        assert result == 'deadbeef'

    def test_DBEXP_010_bytearray_to_hex(self):
        """[DBEXP-010] bytearray is converted to hex string."""
        from services.db_explorer_service import DbExplorerService
        result = DbExplorerService._json_safe(bytearray(b'\xca\xfe'))
        assert result == 'cafe'

    def test_DBEXP_011_memoryview_to_hex(self):
        """[DBEXP-011] memoryview is converted to hex string."""
        from services.db_explorer_service import DbExplorerService
        result = DbExplorerService._json_safe(memoryview(b'\xab\xcd'))
        assert result == 'abcd'

    def test_DBEXP_012_unknown_type_to_str(self):
        """[DBEXP-012] Unknown types are stringified via str()."""
        from services.db_explorer_service import DbExplorerService
        result = DbExplorerService._json_safe({'key': 'val'})
        assert result == "{'key': 'val'}"

    def test_DBEXP_013_decimal_nan_falls_back_to_str(self):
        """[DBEXP-013] Decimal('NaN') falls back to str when float() fails."""
        from services.db_explorer_service import DbExplorerService
        # Decimal('Infinity') converts to float inf which is valid, but let us
        # test the str fallback by using a Decimal subclass that raises.
        class BadDecimal(Decimal):
            def __float__(self):
                raise ValueError('cannot convert')
        result = DbExplorerService._json_safe(BadDecimal('999'))
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Tests: _validate_table
# ---------------------------------------------------------------------------

class TestValidateTable:
    """Tests for DbExplorerService._validate_table()."""

    @patch.object(
        __import__('services.db_explorer_service', fromlist=['DbExplorerService']).DbExplorerService,
        'list_tables',
        return_value=['users', 'features', 'evaluation_items'],
    )
    def test_DBEXP_020_valid_table_name_accepted(self, _mock_list):
        """[DBEXP-020] A valid, existing table name passes validation."""
        from services.db_explorer_service import DbExplorerService
        assert DbExplorerService._validate_table('users') == 'users'

    @patch.object(
        __import__('services.db_explorer_service', fromlist=['DbExplorerService']).DbExplorerService,
        'list_tables',
        return_value=['users'],
    )
    def test_DBEXP_021_rejects_sql_injection_characters(self, _mock_list):
        """[DBEXP-021] Table names with SQL-unsafe characters are rejected."""
        from services.db_explorer_service import DbExplorerService
        with pytest.raises(ValueError, match='Invalid table name'):
            DbExplorerService._validate_table('users; DROP TABLE --')

    @patch.object(
        __import__('services.db_explorer_service', fromlist=['DbExplorerService']).DbExplorerService,
        'list_tables',
        return_value=['users'],
    )
    def test_DBEXP_022_rejects_empty_table_name(self, _mock_list):
        """[DBEXP-022] Empty table name is rejected."""
        from services.db_explorer_service import DbExplorerService
        with pytest.raises(ValueError, match='Invalid table name'):
            DbExplorerService._validate_table('')

    @patch.object(
        __import__('services.db_explorer_service', fromlist=['DbExplorerService']).DbExplorerService,
        'list_tables',
        return_value=['users'],
    )
    def test_DBEXP_023_rejects_none_table_name(self, _mock_list):
        """[DBEXP-023] None table name is rejected."""
        from services.db_explorer_service import DbExplorerService
        with pytest.raises(ValueError, match='Invalid table name'):
            DbExplorerService._validate_table(None)

    @patch.object(
        __import__('services.db_explorer_service', fromlist=['DbExplorerService']).DbExplorerService,
        'list_tables',
        return_value=['users'],
    )
    def test_DBEXP_024_rejects_unknown_table(self, _mock_list):
        """[DBEXP-024] A regex-valid but nonexistent table is rejected."""
        from services.db_explorer_service import DbExplorerService
        with pytest.raises(ValueError, match='Unknown table'):
            DbExplorerService._validate_table('nonexistent_table')

    @patch.object(
        __import__('services.db_explorer_service', fromlist=['DbExplorerService']).DbExplorerService,
        'list_tables',
        return_value=['my_table_123'],
    )
    def test_DBEXP_025_alphanumeric_and_underscores_allowed(self, _mock_list):
        """[DBEXP-025] Table names with letters, digits, and underscores pass regex."""
        from services.db_explorer_service import DbExplorerService
        assert DbExplorerService._validate_table('my_table_123') == 'my_table_123'

    @patch.object(
        __import__('services.db_explorer_service', fromlist=['DbExplorerService']).DbExplorerService,
        'list_tables',
        return_value=['users'],
    )
    def test_DBEXP_026_rejects_dots_in_name(self, _mock_list):
        """[DBEXP-026] Table names containing dots are rejected by regex."""
        from services.db_explorer_service import DbExplorerService
        with pytest.raises(ValueError, match='Invalid table name'):
            DbExplorerService._validate_table('schema.users')

    @patch.object(
        __import__('services.db_explorer_service', fromlist=['DbExplorerService']).DbExplorerService,
        'list_tables',
        return_value=['users'],
    )
    def test_DBEXP_027_strips_whitespace(self, _mock_list):
        """[DBEXP-027] Leading/trailing whitespace is stripped before validation."""
        from services.db_explorer_service import DbExplorerService
        # 'users' is in the list, and after strip it should match.
        assert DbExplorerService._validate_table('  users  ') == 'users'


# ---------------------------------------------------------------------------
# Tests: list_tables (uses app context + SQLite in-memory DB)
# ---------------------------------------------------------------------------

class TestListTables:
    """Tests for DbExplorerService.list_tables()."""

    def test_DBEXP_030_returns_sorted_table_names(self, app, db, app_context):
        """[DBEXP-030] Returns a sorted list of table names from the database."""
        from services.db_explorer_service import DbExplorerService

        tables = DbExplorerService.list_tables()

        assert isinstance(tables, list)
        assert len(tables) > 0
        # The test DB has tables from conftest.py (users, features, etc.)
        assert 'users' in tables
        assert tables == sorted(tables)


# ---------------------------------------------------------------------------
# Tests: get_table_snapshot (uses app context + SQLite in-memory DB)
# ---------------------------------------------------------------------------

class TestGetTableSnapshot:
    """Tests for DbExplorerService.get_table_snapshot()."""

    def test_DBEXP_040_returns_snapshot_for_valid_table(self, app, db, app_context):
        """[DBEXP-040] Returns a valid snapshot dict for an existing table."""
        from services.db_explorer_service import DbExplorerService

        result = DbExplorerService.get_table_snapshot(table='users')

        assert result['ok'] is True
        assert result['table'] == 'users'
        assert isinstance(result['columns'], list)
        assert len(result['columns']) > 0
        assert isinstance(result['rows'], list)
        assert result['error'] is None

    def test_DBEXP_041_raises_for_invalid_table(self, app, db, app_context):
        """[DBEXP-041] Raises ValueError for an invalid table name."""
        from services.db_explorer_service import DbExplorerService

        with pytest.raises(ValueError):
            DbExplorerService.get_table_snapshot(table='no_such_table')

    def test_DBEXP_042_limit_clamped_to_range(self, app, db, app_context):
        """[DBEXP-042] Limit is clamped between 1 and 200.

        Note: limit=0 is falsy, so ``int(limit or 50)`` yields 50 (the default).
        We use limit=-5 to test the min-clamp path (``max(1, min(200, -5))`` = 1).
        """
        from services.db_explorer_service import DbExplorerService

        result_low = DbExplorerService.get_table_snapshot(table='users', limit=-5)
        assert result_low['limit'] == 1

        result_high = DbExplorerService.get_table_snapshot(table='users', limit=999)
        assert result_high['limit'] == 200

        # limit=0 is treated as falsy → defaults to 50
        result_zero = DbExplorerService.get_table_snapshot(table='users', limit=0)
        assert result_zero['limit'] == 50

    def test_DBEXP_043_snapshot_includes_inserted_rows(self, app, db, app_context):
        """[DBEXP-043] Snapshot contains rows that were inserted into the table."""
        from db.models.user import User
        from services.db_explorer_service import DbExplorerService

        user = User(
            username='snapshot_test_user',
            password_hash='hash123',
            api_key='snapshot-api-key-unique',
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()

        result = DbExplorerService.get_table_snapshot(table='users')
        usernames = [row.get('username') for row in result['rows']]
        assert 'snapshot_test_user' in usernames
