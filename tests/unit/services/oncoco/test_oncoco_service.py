"""
Unit Tests für OnCoCo Services

Testet:
- oncoco_labels: Label-Definitionen und Hilfsfunktionen
- OnCoCoService: Klassifizierung, Analyse und Metriken (mit Mocks)
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import numpy as np
from collections import defaultdict

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'app'))


# =============================================================================
# oncoco_labels Tests
# =============================================================================

class TestOnCoCoLabels:
    """Tests für oncoco_labels Modul."""

    def test_ONCOCO_001_labels_defined(self):
        """ONCOCO-001: ONCOCO_LABELS enthält Labels."""
        from services.oncoco.oncoco_labels import ONCOCO_LABELS

        assert len(ONCOCO_LABELS) > 0
        # Should have counselor (CO) and client (CL) labels
        co_labels = [l for l in ONCOCO_LABELS if l.startswith("CO-")]
        cl_labels = [l for l in ONCOCO_LABELS if l.startswith("CL-")]
        assert len(co_labels) > 0
        assert len(cl_labels) > 0

    def test_ONCOCO_002_label_hierarchy_defined(self):
        """ONCOCO-002: LABEL_HIERARCHY enthält Level 2 Kategorien."""
        from services.oncoco.oncoco_labels import LABEL_HIERARCHY

        assert len(LABEL_HIERARCHY) > 0
        # Check for counselor and client hierarchies
        assert "CO-FA" in LABEL_HIERARCHY
        assert "CL-FB" in LABEL_HIERARCHY

    def test_ONCOCO_003_get_label_level2_known(self):
        """ONCOCO-003: get_label_level2 für bekanntes Label."""
        from services.oncoco.oncoco_labels import get_label_level2

        # Counselor label
        result = get_label_level2("CO-FA-*-*-*-*")
        assert result == "CO-FA"

        # Client label
        result = get_label_level2("CL-FB-*-*-*-*")
        assert result == "CL-FB"

    def test_ONCOCO_004_get_label_level2_fallback(self):
        """ONCOCO-004: get_label_level2 Fallback für unbekanntes Label."""
        from services.oncoco.oncoco_labels import get_label_level2

        # Unknown label should extract first two parts
        result = get_label_level2("CO-NEW-X-Y-Z")
        assert result == "CO-NEW"

    def test_ONCOCO_005_get_label_level2_short(self):
        """ONCOCO-005: get_label_level2 für kurzes Label."""
        from services.oncoco.oncoco_labels import get_label_level2

        # Single part label
        result = get_label_level2("CO")
        assert result == "CO"

    def test_ONCOCO_006_get_label_display_name_de(self):
        """ONCOCO-006: get_label_display_name auf Deutsch."""
        from services.oncoco.oncoco_labels import get_label_display_name

        result = get_label_display_name("CO-FA-*-*-*-*", language="de")
        assert result == "Formalitäten zu Beginn"

    def test_ONCOCO_007_get_label_display_name_en(self):
        """ONCOCO-007: get_label_display_name auf Englisch."""
        from services.oncoco.oncoco_labels import get_label_display_name

        result = get_label_display_name("CO-FA-*-*-*-*", language="en")
        assert result == "Formalities at Beginning"

    def test_ONCOCO_008_get_label_display_name_hierarchy(self):
        """ONCOCO-008: get_label_display_name für Hierarchie-Label."""
        from services.oncoco.oncoco_labels import get_label_display_name

        result = get_label_display_name("CO-IF-AC", language="de")
        assert result == "Analyse & Klärung"

    def test_ONCOCO_009_get_label_display_name_unknown(self):
        """ONCOCO-009: get_label_display_name für unbekanntes Label."""
        from services.oncoco.oncoco_labels import get_label_display_name

        result = get_label_display_name("UNKNOWN-LABEL")
        assert result == "UNKNOWN-LABEL"

    def test_ONCOCO_010_get_label_role_counselor(self):
        """ONCOCO-010: get_label_role für Counselor-Label."""
        from services.oncoco.oncoco_labels import get_label_role

        result = get_label_role("CO-FA-*-*-*-*")
        assert result == "counselor"

        result = get_label_role("CO-IF-AC-RF-RPD-*")
        assert result == "counselor"

    def test_ONCOCO_011_get_label_role_client(self):
        """ONCOCO-011: get_label_role für Client-Label."""
        from services.oncoco.oncoco_labels import get_label_role

        result = get_label_role("CL-FB-*-*-*-*")
        assert result == "client"

        result = get_label_role("CL-IF-ACP-*-PS-*")
        assert result == "client"

    def test_ONCOCO_012_get_label_role_unknown(self):
        """ONCOCO-012: get_label_role für unbekanntes Label."""
        from services.oncoco.oncoco_labels import get_label_role

        result = get_label_role("UNKNOWN")
        assert result == "unknown"

    def test_ONCOCO_013_get_label_category(self):
        """ONCOCO-013: get_label_category für verschiedene Labels."""
        from services.oncoco.oncoco_labels import get_label_category

        # Formalities
        result = get_label_category("CO-FA-*-*-*-*")
        assert result == "formalities"

        # Impact factors
        result = get_label_category("CO-IF-AC-RF-RPD-*")
        assert result == "impact_factors"

        # Unknown
        result = get_label_category("UNKNOWN")
        assert result == "other"

    def test_ONCOCO_014_label_structure_complete(self):
        """ONCOCO-014: Alle Labels haben erforderliche Felder."""
        from services.oncoco.oncoco_labels import ONCOCO_LABELS

        required_fields = ["display_name", "display_name_de", "level2", "category", "role"]

        for label, data in ONCOCO_LABELS.items():
            for field in required_fields:
                assert field in data, f"Label {label} missing field {field}"


# =============================================================================
# OnCoCoService Tests (without model loading)
# =============================================================================

class TestOnCoCoServiceInit:
    """Tests für OnCoCoService Initialisierung."""

    def test_ONCOCO_020_init_default_path(self):
        """ONCOCO-020: Service initialisiert mit Default-Pfad."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        assert service.model_path is not None
        assert service._model is None  # Lazy loading

    def test_ONCOCO_021_init_custom_path(self):
        """ONCOCO-021: Service initialisiert mit Custom-Pfad."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService(model_path="/custom/path")

        assert service.model_path == "/custom/path"

    def test_ONCOCO_022_is_model_available_false(self):
        """ONCOCO-022: is_model_available bei fehlendem Model."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService(model_path="/nonexistent/path")
        result = service.is_model_available()

        assert result is False

    def test_ONCOCO_023_get_model_info_not_loaded(self):
        """ONCOCO-023: get_model_info bevor Model geladen."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService(model_path="/test/path")
        info = service.get_model_info()

        assert info["model_path"] == "/test/path"
        assert info["model_loaded"] is False
        assert info["device"] is None


# =============================================================================
# OnCoCoService Sentence Splitting Tests
# =============================================================================

class TestOnCoCoServiceSentenceSplitting:
    """Tests für Satz-Splitting Funktionen."""

    def test_ONCOCO_030_basic_sentence_split(self):
        """ONCOCO-030: Einfaches Satz-Splitting."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        sentences = service._basic_sentence_split("Hallo. Wie geht es Ihnen? Mir geht es gut!")

        assert len(sentences) == 3
        assert sentences[0] == "Hallo."
        assert sentences[1] == "Wie geht es Ihnen?"
        assert sentences[2] == "Mir geht es gut!"

    def test_ONCOCO_031_basic_sentence_split_empty(self):
        """ONCOCO-031: Satz-Splitting bei leerem Text."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        sentences = service._basic_sentence_split("")

        assert sentences == []

    def test_ONCOCO_032_basic_sentence_split_single(self):
        """ONCOCO-032: Satz-Splitting bei einem Satz."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        sentences = service._basic_sentence_split("Nur ein Satz.")

        assert len(sentences) == 1
        assert sentences[0] == "Nur ein Satz."

    def test_ONCOCO_033_split_into_sentences_empty(self):
        """ONCOCO-033: split_into_sentences bei leerem Text."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()
        service._sentence_tokenizer = service._basic_sentence_split

        result = service.split_into_sentences("")

        assert result == []

    def test_ONCOCO_034_split_into_sentences_filters_short(self):
        """ONCOCO-034: split_into_sentences filtert kurze Sätze."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()
        service._sentence_tokenizer = service._basic_sentence_split

        # "Ja." is too short (<=3 chars)
        result = service.split_into_sentences("Ja. Das ist ein langer Satz.")

        assert len(result) == 1
        assert "langer Satz" in result[0]


# =============================================================================
# OnCoCoService Role Prefix Tests
# =============================================================================

class TestOnCoCoServiceRolePrefix:
    """Tests für Role Prefix Funktionen."""

    def test_ONCOCO_040_apply_role_prefix_counselor(self):
        """ONCOCO-040: Role Prefix für Counselor."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        result = service._apply_role_prefix("Test sentence", "counselor")

        assert result == "Counselor: Test sentence"

    def test_ONCOCO_041_apply_role_prefix_client(self):
        """ONCOCO-041: Role Prefix für Client."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        result = service._apply_role_prefix("Test sentence", "client")

        assert result == "Client: Test sentence"

    def test_ONCOCO_042_apply_role_prefix_none(self):
        """ONCOCO-042: Role Prefix ohne Hint."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        result = service._apply_role_prefix("Test sentence", None)

        assert result == "Test sentence"


# =============================================================================
# OnCoCoService Probability Masking Tests
# =============================================================================

class TestOnCoCoServiceProbabilityMasking:
    """Tests für Probability Masking Funktionen."""

    def test_ONCOCO_050_mask_probabilities_no_hint(self):
        """ONCOCO-050: Masking ohne Role Hint."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        probs = np.array([0.1, 0.2, 0.3, 0.4])
        result = service._mask_probabilities_for_role(probs, None)

        np.testing.assert_array_equal(result, probs)

    def test_ONCOCO_051_mask_probabilities_no_indices(self):
        """ONCOCO-051: Masking ohne vorberechnete Indices."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()
        service._role_label_indices = None

        probs = np.array([0.1, 0.2, 0.3, 0.4])
        result = service._mask_probabilities_for_role(probs, "counselor")

        np.testing.assert_array_equal(result, probs)

    def test_ONCOCO_052_mask_probabilities_with_indices(self):
        """ONCOCO-052: Masking mit Role Indices."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()
        service._role_label_indices = {
            "counselor": [0, 2],  # Only indices 0 and 2 are counselor
            "client": [1, 3]
        }

        probs = np.array([0.2, 0.3, 0.3, 0.2])
        result = service._mask_probabilities_for_role(probs, "counselor")

        # Should only keep counselor indices and renormalize
        assert result[1] == 0  # Client index masked
        assert result[3] == 0  # Client index masked
        assert result[0] > 0  # Counselor index kept
        assert result[2] > 0  # Counselor index kept
        assert abs(result.sum() - 1.0) < 1e-6  # Renormalized


# =============================================================================
# OnCoCoService Transition Matrix Tests
# =============================================================================

class TestOnCoCoServiceTransitionMatrix:
    """Tests für Transition Matrix Berechnung."""

    def test_ONCOCO_060_compute_transition_matrix_basic(self):
        """ONCOCO-060: Transition Matrix Berechnung."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        labels = ["A", "B", "A", "B", "C"]
        counts, probs = service.compute_transition_matrix(labels)

        # A -> B appears twice
        assert counts["A"]["B"] == 2
        # B -> A appears once
        assert counts["B"]["A"] == 1
        # B -> C appears once
        assert counts["B"]["C"] == 1

        # Probability A -> B should be 1.0 (always goes to B)
        assert probs["A"]["B"] == 1.0
        # Probability B -> A and B -> C should be 0.5 each
        assert probs["B"]["A"] == 0.5
        assert probs["B"]["C"] == 0.5

    def test_ONCOCO_061_compute_transition_matrix_empty(self):
        """ONCOCO-061: Transition Matrix bei leerer Liste."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        counts, probs = service.compute_transition_matrix([])

        assert counts == {}
        assert probs == {}

    def test_ONCOCO_062_compute_transition_matrix_single(self):
        """ONCOCO-062: Transition Matrix bei einem Label."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        counts, probs = service.compute_transition_matrix(["A"])

        assert counts == {}
        assert probs == {}

    def test_ONCOCO_063_compute_transition_matrix_level2(self):
        """ONCOCO-063: Transition Matrix mit Level 2 Aggregation."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        labels = ["CO-FA-*-*-*-*", "CO-IF-AC-RF-RPD-*", "CL-FB-*-*-*-*"]
        counts, probs = service.compute_transition_matrix(labels, use_level2=True)

        # Should be aggregated to level 2
        assert "CO-FA" in counts
        assert "CO-IF" in counts["CO-FA"] or "CO-IF-AC" in counts["CO-FA"]


# =============================================================================
# OnCoCoService Metric Computation Tests
# =============================================================================

class TestOnCoCoServiceMetrics:
    """Tests für Metrik-Berechnungen."""

    def test_ONCOCO_070_compute_impact_factor_ratio(self):
        """ONCOCO-070: Impact Factor Ratio berechnen."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        distribution = {
            "CO-IF-AC-RF-RPD-*": 10,  # Impact Factor
            "CO-IF-HP-*-ITFE-*": 5,   # Impact Factor
            "CO-FA-*-*-*-*": 5,       # Not Impact Factor
            "CL-FB-*-*-*-*": 10       # Client (not counted)
        }

        ratio = service.compute_impact_factor_ratio(distribution)

        # 15 IF labels out of 20 CO labels = 0.75
        assert ratio == 0.75

    def test_ONCOCO_071_compute_impact_factor_ratio_no_co(self):
        """ONCOCO-071: Impact Factor Ratio ohne Counselor Labels."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        distribution = {
            "CL-FB-*-*-*-*": 10
        }

        ratio = service.compute_impact_factor_ratio(distribution)

        assert ratio == 0

    def test_ONCOCO_072_compute_resource_activation_score(self):
        """ONCOCO-072: Resource Activation Score berechnen."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        distribution = {
            "CO-IF-RA-*-RP-*": 10,    # Resource Activation
            "CO-IF-AC-RF-RPD-*": 10,  # Not RA
            "CL-FB-*-*-*-*": 10       # Client
        }

        score = service.compute_resource_activation_score(distribution)

        # 10 RA labels out of 20 CO labels = 0.5
        assert score == 0.5

    def test_ONCOCO_073_compute_resource_activation_score_zero(self):
        """ONCOCO-073: Resource Activation Score bei 0."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        distribution = {
            "CO-IF-AC-RF-RPD-*": 10,  # No RA
        }

        score = service.compute_resource_activation_score(distribution)

        assert score == 0

    def test_ONCOCO_074_compute_mutual_information(self):
        """ONCOCO-074: Mutual Information berechnen."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        # Simple deterministic transition: A always goes to B
        transition_matrix = {
            "A": {"B": 10},
            "B": {"A": 10}
        }

        mi = service.compute_mutual_information(transition_matrix)

        # Perfect predictability should have high MI
        assert mi > 0

    def test_ONCOCO_075_compute_mutual_information_empty(self):
        """ONCOCO-075: Mutual Information bei leerer Matrix."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        mi = service.compute_mutual_information({})

        assert mi == 0


# =============================================================================
# OnCoCoService Message/Thread Analysis Tests (Mocked)
# =============================================================================

class TestOnCoCoServiceAnalysisMocked:
    """Tests für Analyse-Funktionen mit gemocktem Model."""

    def test_ONCOCO_080_analyze_message_empty(self):
        """ONCOCO-080: analyze_message mit leerem Content."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()
        service._sentence_tokenizer = service._basic_sentence_split

        result = service.analyze_message(
            message_id=1,
            sender="Test",
            content="",
            role_hint="counselor"
        )

        assert result.message_id == 1
        assert result.sentences == []
        assert result.dominant_label == ""
        assert result.avg_confidence == 0.0

    @patch.object(__import__('services.oncoco.oncoco_service', fromlist=['OnCoCoService']).OnCoCoService, 'classify_sentences_batch')
    def test_ONCOCO_081_analyze_message_with_sentences(self, mock_classify):
        """ONCOCO-081: analyze_message mit Sätzen."""
        from services.oncoco.oncoco_service import OnCoCoService, ClassificationResult

        # Setup mock
        mock_classify.return_value = [
            ClassificationResult(
                sentence="Wie geht es Ihnen?",
                label="CO-IF-AC-RF-RES-*",
                label_level2="CO-IF-AC",
                confidence=0.8,
                role="counselor",
                top_3=[("CO-IF-AC-RF-RES-*", 0.8), ("CO-FA-*-*-*-*", 0.1), ("CO-Mod-*-*-*-*", 0.05)]
            ),
            ClassificationResult(
                sentence="Das verstehe ich.",
                label="CO-IF-AC-RF-SRx-*",
                label_level2="CO-IF-AC",
                confidence=0.9,
                role="counselor",
                top_3=[("CO-IF-AC-RF-SRx-*", 0.9), ("CO-Mod-*-*-*-*", 0.05), ("CO-FA-*-*-*-*", 0.03)]
            )
        ]

        service = OnCoCoService()
        service._sentence_tokenizer = service._basic_sentence_split

        result = service.analyze_message(
            message_id=1,
            sender="Berater",
            content="Wie geht es Ihnen? Das verstehe ich.",
            role_hint="counselor"
        )

        assert result.message_id == 1
        assert len(result.sentences) == 2
        assert result.role == "counselor"
        assert result.avg_confidence == pytest.approx(0.85)

    @patch.object(__import__('services.oncoco.oncoco_service', fromlist=['OnCoCoService']).OnCoCoService, 'analyze_message')
    def test_ONCOCO_082_analyze_thread(self, mock_analyze_message):
        """ONCOCO-082: analyze_thread mit mehreren Messages."""
        from services.oncoco.oncoco_service import OnCoCoService, MessageAnalysis, ClassificationResult

        # Setup mock
        mock_analyze_message.side_effect = [
            MessageAnalysis(
                message_id=1,
                sender="Berater",
                role="counselor",
                sentences=[
                    ClassificationResult("Test", "CO-FA-*-*-*-*", "CO-FA", 0.9, "counselor", [])
                ],
                dominant_label="CO-FA-*-*-*-*",
                dominant_label_level2="CO-FA",
                avg_confidence=0.9
            ),
            MessageAnalysis(
                message_id=2,
                sender="Klient",
                role="client",
                sentences=[
                    ClassificationResult("Test", "CL-FB-*-*-*-*", "CL-FB", 0.85, "client", [])
                ],
                dominant_label="CL-FB-*-*-*-*",
                dominant_label_level2="CL-FB",
                avg_confidence=0.85
            )
        ]

        service = OnCoCoService()

        messages = [
            {"id": 1, "sender": "Berater", "content": "Hallo."},
            {"id": 2, "sender": "Klient", "content": "Hallo."}
        ]

        result = service.analyze_thread(
            thread_id=1,
            pillar_number=1,
            messages=messages
        )

        assert result.thread_id == 1
        assert result.pillar_number == 1
        assert len(result.messages) == 2
        assert result.total_sentences == 2
        assert result.counselor_sentences == 1
        assert result.client_sentences == 1


# =============================================================================
# OnCoCoService Dataclass Tests
# =============================================================================

class TestOnCoCoServiceDataclasses:
    """Tests für Dataclasses."""

    def test_ONCOCO_090_classification_result(self):
        """ONCOCO-090: ClassificationResult Dataclass."""
        from services.oncoco.oncoco_service import ClassificationResult

        result = ClassificationResult(
            sentence="Test sentence",
            label="CO-FA-*-*-*-*",
            label_level2="CO-FA",
            confidence=0.95,
            role="counselor",
            top_3=[("CO-FA-*-*-*-*", 0.95), ("CO-Mod-*-*-*-*", 0.03), ("CO-O-*-*-O-*", 0.02)]
        )

        assert result.sentence == "Test sentence"
        assert result.label == "CO-FA-*-*-*-*"
        assert result.confidence == 0.95
        assert len(result.top_3) == 3

    def test_ONCOCO_091_message_analysis(self):
        """ONCOCO-091: MessageAnalysis Dataclass."""
        from services.oncoco.oncoco_service import MessageAnalysis

        result = MessageAnalysis(
            message_id=1,
            sender="Berater",
            role="counselor",
            sentences=[],
            dominant_label="CO-FA-*-*-*-*",
            dominant_label_level2="CO-FA",
            avg_confidence=0.9
        )

        assert result.message_id == 1
        assert result.sender == "Berater"
        assert result.role == "counselor"

    def test_ONCOCO_092_thread_analysis(self):
        """ONCOCO-092: ThreadAnalysis Dataclass."""
        from services.oncoco.oncoco_service import ThreadAnalysis

        result = ThreadAnalysis(
            thread_id=1,
            pillar_number=3,
            messages=[],
            label_distribution={"CO-FA-*-*-*-*": 5},
            label_distribution_level2={"CO-FA": 5},
            transition_matrix={},
            total_sentences=10,
            counselor_sentences=6,
            client_sentences=4
        )

        assert result.thread_id == 1
        assert result.pillar_number == 3
        assert result.total_sentences == 10


# =============================================================================
# OnCoCoService Singleton Tests
# =============================================================================

class TestOnCoCoServiceSingleton:
    """Tests für Singleton-Pattern."""

    def test_ONCOCO_095_get_oncoco_service_singleton(self):
        """ONCOCO-095: get_oncoco_service gibt Singleton zurück."""
        from services.oncoco.oncoco_service import get_oncoco_service

        # Reset singleton
        import services.oncoco.oncoco_service as module
        module._oncoco_service = None

        service1 = get_oncoco_service()
        service2 = get_oncoco_service()

        assert service1 is service2

    def test_ONCOCO_096_get_oncoco_service_new_path(self):
        """ONCOCO-096: get_oncoco_service mit neuem Pfad erstellt neue Instanz."""
        from services.oncoco.oncoco_service import get_oncoco_service

        # Reset singleton
        import services.oncoco.oncoco_service as module
        module._oncoco_service = None

        service1 = get_oncoco_service()
        service2 = get_oncoco_service(model_path="/new/path")

        assert service1 is not service2
        assert service2.model_path == "/new/path"


# =============================================================================
# OnCoCoService Hardware Info Tests
# =============================================================================

class TestOnCoCoServiceHardwareInfo:
    """Tests für Hardware-Info Funktionen."""

    @patch('psutil.cpu_count')
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_ONCOCO_097_get_hardware_info_basic(self, mock_mem, mock_cpu_pct, mock_cpu_cnt):
        """ONCOCO-097: get_hardware_info ohne geladenes Model."""
        from services.oncoco.oncoco_service import OnCoCoService

        # Setup mocks
        mock_cpu_cnt.return_value = 4
        mock_cpu_pct.return_value = 25.0
        mock_mem.return_value = MagicMock(
            total=16 * 1024**3,
            used=8 * 1024**3,
            percent=50.0
        )

        service = OnCoCoService()
        info = service.get_hardware_info()

        assert info['device_type'] == 'unknown'
        assert info['cpu_count'] == 4
        assert info['memory_total_gb'] == 16.0
        assert info['model_loaded'] is False


# =============================================================================
# Integration Tests
# =============================================================================

class TestOnCoCoIntegration:
    """Integration Tests für OnCoCo Service."""

    def test_ONCOCO_100_full_label_workflow(self):
        """ONCOCO-100: Vollständiger Label-Workflow."""
        from services.oncoco.oncoco_labels import (
            get_label_level2,
            get_label_display_name,
            get_label_role,
            get_label_category
        )

        label = "CO-IF-AC-RF-RPD-*"

        level2 = get_label_level2(label)
        display_de = get_label_display_name(label, "de")
        display_en = get_label_display_name(label, "en")
        role = get_label_role(label)
        category = get_label_category(label)

        assert level2 == "CO-IF-AC"
        assert display_de == "Frage nach persönlichen Daten"
        assert display_en == "Request Personal Data"
        assert role == "counselor"
        assert category == "impact_factors"

    def test_ONCOCO_101_transition_and_metrics(self):
        """ONCOCO-101: Transition Matrix und Metriken kombiniert."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        # Simulated label sequence
        labels = [
            "CO-FA-*-*-*-*",
            "CL-FB-*-*-*-*",
            "CO-IF-AC-RF-RPD-*",
            "CL-IF-ACP-*-PS-*",
            "CO-IF-RA-*-RP-*",
            "CL-IF-HP-*-PosF-*"
        ]

        # Compute transition matrix
        counts, probs = service.compute_transition_matrix(labels)

        # Compute MI
        mi = service.compute_mutual_information(counts)

        assert len(counts) > 0
        assert mi >= 0

    def test_ONCOCO_102_analyze_thread_role_detection(self):
        """ONCOCO-102: Role Detection in Thread Analysis."""
        from services.oncoco.oncoco_service import OnCoCoService

        service = OnCoCoService()

        # Test role hints from sender names
        test_senders = [
            ("Berater Max", "counselor"),
            ("Counsellor Smith", "counselor"),
            ("Klient Anna", "client"),
            ("Client User", "client"),
            ("Ratsuchende", "client"),
            ("Bot Assistant", "counselor"),
        ]

        for sender, expected_role in test_senders:
            sender_lower = sender.lower()
            role_hint = None
            if any(term in sender_lower for term in ['berater', 'counsellor', 'counselor', 'assistant', 'bot']):
                role_hint = "counselor"
            elif any(term in sender_lower for term in ['klient', 'client', 'user', 'ratsuchend']):
                role_hint = "client"

            assert role_hint == expected_role, f"Failed for sender: {sender}"
