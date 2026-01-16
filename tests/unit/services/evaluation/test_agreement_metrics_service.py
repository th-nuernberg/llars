"""
Tests for AgreementMetricsService.

Tests inter-rater reliability metric calculations.
"""

import pytest


class TestAgreementMetricsService:
    """Tests for AgreementMetricsService."""

    def test_AGREE_001_percent_agreement_perfect(self, app, db):
        """Perfect agreement should return 100%."""
        from services.evaluation.agreement_metrics_service import AgreementMetricsService

        data = {
            1: {"rater1": 5, "rater2": 5},
            2: {"rater1": 4, "rater2": 4},
            3: {"rater1": 3, "rater2": 3},
        }
        raters = ["rater1", "rater2"]
        items = [1, 2, 3]

        result = AgreementMetricsService._percent_agreement(data, raters, items)

        assert result == 100.0

    def test_AGREE_002_percent_agreement_no_agreement(self, app, db):
        """No agreement should return 0%."""
        from services.evaluation.agreement_metrics_service import AgreementMetricsService

        data = {
            1: {"rater1": 1, "rater2": 5},
            2: {"rater1": 2, "rater2": 4},
            3: {"rater1": 3, "rater2": 1},
        }
        raters = ["rater1", "rater2"]
        items = [1, 2, 3]

        result = AgreementMetricsService._percent_agreement(data, raters, items)

        assert result == 0.0

    def test_AGREE_003_cohens_kappa_perfect(self, app, db):
        """Perfect agreement should give kappa close to 1."""
        from services.evaluation.agreement_metrics_service import AgreementMetricsService

        data = {
            1: {"r1": "A", "r2": "A"},
            2: {"r1": "B", "r2": "B"},
            3: {"r1": "A", "r2": "A"},
            4: {"r1": "B", "r2": "B"},
        }
        items = [1, 2, 3, 4]

        kappa = AgreementMetricsService._cohens_kappa(data, "r1", "r2", items)

        assert kappa == 1.0

    def test_AGREE_004_cohens_kappa_chance(self, app, db):
        """Random agreement should give kappa close to 0."""
        from services.evaluation.agreement_metrics_service import AgreementMetricsService

        # Construct data where agreement matches chance expectation
        data = {
            1: {"r1": "A", "r2": "B"},
            2: {"r1": "B", "r2": "A"},
            3: {"r1": "A", "r2": "A"},
            4: {"r1": "B", "r2": "B"},
        }
        items = [1, 2, 3, 4]

        kappa = AgreementMetricsService._cohens_kappa(data, "r1", "r2", items)

        # Kappa should be low (around 0 or slightly negative)
        assert -0.5 <= kappa <= 0.5

    def test_AGREE_005_spearman_rho_perfect_positive(self, app, db):
        """Perfect positive correlation should give rho = 1."""
        from services.evaluation.agreement_metrics_service import AgreementMetricsService

        data = {
            1: {"r1": 1, "r2": 1},
            2: {"r1": 2, "r2": 2},
            3: {"r1": 3, "r2": 3},
            4: {"r1": 4, "r2": 4},
        }
        items = [1, 2, 3, 4]

        rho = AgreementMetricsService._spearman_rho(data, "r1", "r2", items)

        assert rho == 1.0

    def test_AGREE_006_spearman_rho_perfect_negative(self, app, db):
        """Perfect negative correlation should give rho = -1."""
        from services.evaluation.agreement_metrics_service import AgreementMetricsService

        data = {
            1: {"r1": 1, "r2": 4},
            2: {"r1": 2, "r2": 3},
            3: {"r1": 3, "r2": 2},
            4: {"r1": 4, "r2": 1},
        }
        items = [1, 2, 3, 4]

        rho = AgreementMetricsService._spearman_rho(data, "r1", "r2", items)

        assert rho == -1.0

    def test_AGREE_007_krippendorff_alpha_ordinal(self, app, db):
        """Krippendorff alpha for ordinal data with high agreement."""
        from services.evaluation.agreement_metrics_service import AgreementMetricsService

        # High agreement data
        data = {
            1: {"r1": 4, "r2": 4, "r3": 5},
            2: {"r1": 3, "r2": 3, "r3": 3},
            3: {"r1": 5, "r2": 5, "r3": 5},
            4: {"r1": 2, "r2": 2, "r3": 2},
        }
        raters = ["r1", "r2", "r3"]
        items = [1, 2, 3, 4]

        alpha = AgreementMetricsService._krippendorff_alpha(data, raters, items, "ordinal")

        # Should be relatively high
        assert alpha is not None
        assert alpha > 0.5

    def test_AGREE_008_krippendorff_alpha_nominal(self, app, db):
        """Krippendorff alpha for nominal data."""
        from services.evaluation.agreement_metrics_service import AgreementMetricsService

        data = {
            1: {"r1": "real", "r2": "real", "r3": "real"},
            2: {"r1": "fake", "r2": "fake", "r3": "fake"},
            3: {"r1": "real", "r2": "real", "r3": "fake"},
            4: {"r1": "fake", "r2": "fake", "r3": "fake"},
        }
        raters = ["r1", "r2", "r3"]
        items = [1, 2, 3, 4]

        alpha = AgreementMetricsService._krippendorff_alpha(data, raters, items, "nominal")

        assert alpha is not None

    def test_AGREE_009_interpret_kappa(self, app, db):
        """Kappa interpretation should return correct labels."""
        from services.evaluation.agreement_metrics_service import AgreementMetricsService

        assert "perfekte" in AgreementMetricsService._interpret_kappa(0.9).lower()
        assert "substanzielle" in AgreementMetricsService._interpret_kappa(0.7).lower()
        assert "moderate" in AgreementMetricsService._interpret_kappa(0.5).lower()
        assert "keine" in AgreementMetricsService._interpret_kappa(-0.1).lower()

    def test_AGREE_010_interpret_alpha(self, app, db):
        """Alpha interpretation should return correct labels."""
        from services.evaluation.agreement_metrics_service import AgreementMetricsService

        assert "zuverlässig" in AgreementMetricsService._interpret_alpha(0.85).lower()
        assert "ausreichend" in AgreementMetricsService._interpret_alpha(0.7).lower()
        assert "gering" in AgreementMetricsService._interpret_alpha(0.2).lower()

    def test_AGREE_011_interpret_correlation(self, app, db):
        """Correlation interpretation should include direction and strength."""
        from services.evaluation.agreement_metrics_service import AgreementMetricsService

        result = AgreementMetricsService._interpret_correlation(0.9)
        assert "stark" in result.lower()
        assert "positive" in result.lower()

        result = AgreementMetricsService._interpret_correlation(-0.7)
        assert "stark" in result.lower()
        assert "negative" in result.lower()

    def test_AGREE_012_metric_descriptions_available(self, app, db):
        """All metrics should have descriptions."""
        from services.evaluation.agreement_metrics_service import AgreementMetricsService

        descriptions = AgreementMetricsService.METRIC_DESCRIPTIONS

        expected_metrics = [
            "krippendorff_alpha",
            "cohens_kappa",
            "fleiss_kappa",
            "kendall_tau",
            "spearman_rho",
            "percent_agreement",
        ]

        for metric in expected_metrics:
            assert metric in descriptions
            assert "name" in descriptions[metric]
            assert "description" in descriptions[metric]
            assert "range" in descriptions[metric]

    def test_AGREE_013_rank_values_with_ties(self, app, db):
        """Ranking should handle ties correctly."""
        from services.evaluation.agreement_metrics_service import AgreementMetricsService

        values = [3, 1, 3, 5, 3]
        ranks = AgreementMetricsService._rank_values(values)

        # Value 1 gets rank 1
        # Three 3s share ranks 2, 3, 4 -> average 3
        # Value 5 gets rank 5
        assert ranks[1] == 1.0  # Index 1 has value 1
        assert ranks[0] == 3.0  # Index 0 has value 3, tied
        assert ranks[2] == 3.0  # Index 2 has value 3, tied
        assert ranks[4] == 3.0  # Index 4 has value 3, tied
        assert ranks[3] == 5.0  # Index 3 has value 5
