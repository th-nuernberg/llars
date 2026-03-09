"""
Unit tests for user_profile_service.

Tests user profile helpers including:
- Hex color validation
- Collab color picking
- Avatar URL building
- User brief serialization
"""

import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from services.user_profile_service import (
    is_valid_collab_color,
    pick_collab_color,
    build_avatar_url,
    serialize_user_brief,
)
from db.models.user import DEFAULT_COLLAB_COLORS


class TestIsValidCollabColor:
    """Tests for hex color validation."""

    def test_UPROF_001_accepts_valid_hex_colors(self):
        """[UPROF-001] Should accept valid 6-digit hex colors with # prefix."""
        assert is_valid_collab_color('#FF5733') is True
        assert is_valid_collab_color('#000000') is True
        assert is_valid_collab_color('#ffffff') is True
        assert is_valid_collab_color('#aAbBcC') is True

    def test_UPROF_002_rejects_invalid_hex_colors(self):
        """[UPROF-002] Should reject malformed hex strings."""
        assert is_valid_collab_color('') is False
        assert is_valid_collab_color('FF5733') is False   # missing #
        assert is_valid_collab_color('#FFF') is False     # 3-digit shorthand
        assert is_valid_collab_color('#GGGGGG') is False  # invalid hex chars
        assert is_valid_collab_color('#FF573') is False   # too short
        assert is_valid_collab_color('#FF57331') is False  # too long
        assert is_valid_collab_color('not-a-color') is False

    def test_UPROF_003_rejects_none_and_non_string(self):
        """[UPROF-003] Should reject non-string inputs gracefully."""
        # match() expects a string; None / int will raise, which is expected
        with pytest.raises((TypeError, AttributeError)):
            is_valid_collab_color(None)
        with pytest.raises((TypeError, AttributeError)):
            is_valid_collab_color(12345)


class TestPickCollabColor:
    """Tests for picking unused collab colors."""

    def test_UPROF_004_picks_from_available_colors(self):
        """[UPROF-004] Should return a color from the default palette that is not yet used."""
        used = set(DEFAULT_COLLAB_COLORS[:10])  # leave last 2 available
        color = pick_collab_color(used_colors=used)
        assert color in DEFAULT_COLLAB_COLORS
        assert color not in used

    def test_UPROF_005_returns_palette_color_when_all_used(self):
        """[UPROF-005] Should fall back to any palette color when all are taken."""
        used = set(DEFAULT_COLLAB_COLORS)
        color = pick_collab_color(used_colors=used)
        assert color in DEFAULT_COLLAB_COLORS

    def test_UPROF_006_picks_color_when_none_used(self):
        """[UPROF-006] Should pick freely when no colors are used."""
        color = pick_collab_color(used_colors=set())
        assert color in DEFAULT_COLLAB_COLORS

    def test_UPROF_007_queries_db_when_used_colors_none(self, app, db, app_context):
        """[UPROF-007] Should query database for used colors when used_colors is None."""
        from db.models.user import User

        u1 = User(username='u1', password_hash='x', api_key='k1', collab_color='#FF6B6B')
        u2 = User(username='u2', password_hash='x', api_key='k2', collab_color='#4ECDC4')
        db.session.add_all([u1, u2])
        db.session.commit()

        color = pick_collab_color(used_colors=None)
        assert color in DEFAULT_COLLAB_COLORS
        # Should have queried DB and avoided already-used colors (unless all taken)
        # Since only 2 of 12 are used, picked color should differ
        assert color not in {'#FF6B6B', '#4ECDC4'}


class TestBuildAvatarUrl:
    """Tests for avatar URL generation."""

    def test_UPROF_008_builds_url_when_both_fields_present(self):
        """[UPROF-008] Should build URL from public_id when both avatar fields are set."""
        user = SimpleNamespace(avatar_public_id='abc123', avatar_file='photo.png')
        assert build_avatar_url(user) == '/api/users/avatar/abc123'

    def test_UPROF_009_returns_none_when_no_public_id(self):
        """[UPROF-009] Should return None when avatar_public_id is missing."""
        user = SimpleNamespace(avatar_public_id=None, avatar_file='photo.png')
        assert build_avatar_url(user) is None

    def test_UPROF_010_returns_none_when_no_avatar_file(self):
        """[UPROF-010] Should return None when avatar_file is missing."""
        user = SimpleNamespace(avatar_public_id='abc123', avatar_file=None)
        assert build_avatar_url(user) is None

    def test_UPROF_011_returns_none_when_both_missing(self):
        """[UPROF-011] Should return None when both avatar fields are absent."""
        user = SimpleNamespace(avatar_public_id=None, avatar_file=None)
        assert build_avatar_url(user) is None

    def test_UPROF_012_returns_none_when_attrs_not_exist(self):
        """[UPROF-012] Should return None for objects without avatar attributes."""
        user = SimpleNamespace()  # no avatar_public_id or avatar_file
        assert build_avatar_url(user) is None


class TestSerializeUserBrief:
    """Tests for canonical user brief serialization."""

    def test_UPROF_013_serializes_full_user(self):
        """[UPROF-013] Should include username, avatar_seed, and avatar_url."""
        user = SimpleNamespace(
            username='alice',
            avatar_seed='seed42',
            avatar_public_id='pub1',
            avatar_file='avatar.jpg',
        )
        brief = serialize_user_brief(user)

        assert brief['username'] == 'alice'
        assert brief['avatar_seed'] == 'seed42'
        assert brief['avatar_url'] == '/api/users/avatar/pub1'

    def test_UPROF_014_returns_nulls_for_none_user(self):
        """[UPROF-014] Should return all-None dict for None user."""
        brief = serialize_user_brief(None)
        assert brief == {'username': None, 'avatar_seed': None, 'avatar_url': None}

    def test_UPROF_015_returns_none_avatar_url_when_no_file(self):
        """[UPROF-015] Should return avatar_url=None when user lacks avatar file."""
        user = SimpleNamespace(
            username='bob',
            avatar_seed='seed99',
            avatar_public_id=None,
            avatar_file=None,
        )
        brief = serialize_user_brief(user)

        assert brief['username'] == 'bob'
        assert brief['avatar_seed'] == 'seed99'
        assert brief['avatar_url'] is None

    def test_UPROF_016_handles_user_without_avatar_seed(self):
        """[UPROF-016] Should handle user object missing avatar_seed gracefully."""
        user = SimpleNamespace(username='charlie')
        brief = serialize_user_brief(user)

        assert brief['username'] == 'charlie'
        assert brief['avatar_seed'] is None  # getattr default
        assert brief['avatar_url'] is None
