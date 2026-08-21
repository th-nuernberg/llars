"""
Unit tests for the referral-link badge color and the scenario-team origin object.

Covers:
- ``ReferralLink.resolved_color`` — admin override vs. deterministic auto-color.
- ``services.referral_service._normalize_hex_color`` — validation/normalization.
- ``routes.scenarios.scenario_manager_api._compose_member_origin`` — the two
  origin dimensions (account: referral/existing; scenario join: owner /
  referral_autoenroll / invited / self).

These exercise pure logic only — no live database or app context needed.

Test IDs: REF-ORIGIN-001..012.
"""

from __future__ import annotations

import pytest

from db.models.referral import ReferralLink, REFERRAL_LINK_COLOR_PALETTE
from services.referral_service import _normalize_hex_color
from routes.scenarios.scenario_manager_api import _compose_member_origin


# --------------------------------------------------------------------------- #
# ReferralLink.resolved_color
# --------------------------------------------------------------------------- #
class TestResolvedColor:
    def test_ref_origin_001_override_wins(self):
        link = ReferralLink(id=5, color='#abc123')
        assert link.resolved_color == '#abc123'

    def test_ref_origin_002_auto_color_is_from_palette(self):
        link = ReferralLink(id=5, color=None)
        assert link.resolved_color in REFERRAL_LINK_COLOR_PALETTE

    def test_ref_origin_003_auto_color_is_deterministic(self):
        # Same id -> same auto-color on every render (no backfill needed).
        assert ReferralLink(id=7).resolved_color == ReferralLink(id=7).resolved_color

    def test_ref_origin_004_auto_color_indexes_by_id(self):
        n = len(REFERRAL_LINK_COLOR_PALETTE)
        assert ReferralLink(id=3).resolved_color == REFERRAL_LINK_COLOR_PALETTE[3 % n]

    def test_ref_origin_005_missing_id_does_not_crash(self):
        # An unsaved link (id None) still yields a valid palette color.
        assert ReferralLink(color=None).resolved_color == REFERRAL_LINK_COLOR_PALETTE[0]


# --------------------------------------------------------------------------- #
# _normalize_hex_color
# --------------------------------------------------------------------------- #
class TestNormalizeHexColor:
    def test_ref_origin_006_none_and_blank_clear(self):
        assert _normalize_hex_color(None) is None
        assert _normalize_hex_color('') is None
        assert _normalize_hex_color('   ') is None

    def test_ref_origin_007_adds_hash_and_lowercases(self):
        assert _normalize_hex_color('B0CA97') == '#b0ca97'
        assert _normalize_hex_color('#FF6B6B') == '#ff6b6b'

    def test_ref_origin_008_rejects_malformed(self):
        from decorators.error_handler import ValidationError
        for bad in ('nope', '#12345', '#1234567', 'rgb(1,2,3)'):
            with pytest.raises(ValidationError):
                _normalize_hex_color(bad)


# --------------------------------------------------------------------------- #
# _compose_member_origin
# --------------------------------------------------------------------------- #
def _referral(**over):
    base = {
        'slug': 'ki-2026', 'label': 'KI 2026', 'campaign': 'KI 2026',
        'registered_at': '2026-06-03T10:00:00', 'color': '#FF6B6B',
        'autoenroll_here': False,
    }
    base.update(over)
    return base


class TestComposeMemberOrigin:
    def test_ref_origin_009_referral_account_carries_color(self):
        o = _compose_member_origin(
            _referral(), invited_by=None, invited_at=None,
            invitation_status='accepted', is_owner=False, username='anna')
        assert o['account'] == 'referral'
        assert o['referral']['color'] == '#FF6B6B'
        assert o['scenario']['status'] == 'accepted'

    def test_ref_origin_010_no_referral_is_existing(self):
        o = _compose_member_origin(
            None, invited_by='admin', invited_at=None,
            invitation_status='accepted', is_owner=False, username='bob')
        assert o['account'] == 'existing'
        assert o['referral'] is None

    def test_ref_origin_011_joined_via_priority(self):
        # owner beats everything
        assert _compose_member_origin(
            _referral(autoenroll_here=True), invited_by='x', invited_at=None,
            invitation_status='accepted', is_owner=True, username='u'
        )['scenario']['joined_via'] == 'owner'
        # auto-enroll beats invited
        assert _compose_member_origin(
            _referral(autoenroll_here=True), invited_by='admin', invited_at=None,
            invitation_status='accepted', is_owner=False, username='u'
        )['scenario']['joined_via'] == 'referral_autoenroll'
        # invited when someone else invited
        assert _compose_member_origin(
            None, invited_by='admin', invited_at=None,
            invitation_status='accepted', is_owner=False, username='u'
        )['scenario']['joined_via'] == 'invited'

    def test_ref_origin_012_self_join_default(self):
        # invited_by == self (or missing) -> self, not "invited"
        o = _compose_member_origin(
            None, invited_by='u', invited_at=None,
            invitation_status='accepted', is_owner=False, username='u')
        assert o['scenario']['joined_via'] == 'self'
