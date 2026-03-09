"""Tests for research group seeders."""

from db.seeders.research_groups import _normalize_legacy_keywords_value


class TestResearchGroupSeeders:
    """Seeder normalization tests."""

    def test_RES_GRP_SEED_001_plain_text_keywords_become_single_item_list(self):
        """[RES-GRP-SEED-001] Legacy plain text keywords are wrapped in a list."""
        result = _normalize_legacy_keywords_value("Rolling review for ACL venues")
        assert result == ["Rolling review for ACL venues"]

    def test_RES_GRP_SEED_002_json_array_keywords_stay_array(self):
        """[RES-GRP-SEED-002] Existing JSON arrays are preserved."""
        result = _normalize_legacy_keywords_value('["nlp", "dialogue systems"]')
        assert result == ["nlp", "dialogue systems"]

    def test_RES_GRP_SEED_003_json_string_keywords_become_single_item_list(self):
        """[RES-GRP-SEED-003] JSON strings are normalized to the UI list shape."""
        result = _normalize_legacy_keywords_value('"Computational Linguistics"')
        assert result == ["Computational Linguistics"]

    def test_RES_GRP_SEED_004_blank_keywords_become_empty_list(self):
        """[RES-GRP-SEED-004] Blank keyword payloads normalize to an empty list."""
        assert _normalize_legacy_keywords_value("   ") == []
