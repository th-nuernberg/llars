"""
Tests for ComparisonGenerator service.

Covers comparison generation in all modes (pillar_sample, round_robin, free_for_all),
estimation, mode normalization, thread limiting, and position swap behavior.
"""

import pytest
from unittest.mock import patch


class TestModeNormalization:
    """Tests for ComparisonGenerator._normalize_mode."""

    def test_CGEN_001_normalize_pillar_sample(self, app, app_context):
        """[CGEN-001] Normalizes pillar_sample mode."""
        from services.judge.comparison_generator import ComparisonGenerator, ComparisonMode
        gen = ComparisonGenerator()
        assert gen._normalize_mode('pillar_sample') == ComparisonMode.PILLAR_SAMPLE

    def test_CGEN_002_normalize_round_robin(self, app, app_context):
        """[CGEN-002] Normalizes round_robin mode."""
        from services.judge.comparison_generator import ComparisonGenerator, ComparisonMode
        gen = ComparisonGenerator()
        assert gen._normalize_mode('round_robin') == ComparisonMode.ROUND_ROBIN

    def test_CGEN_003_normalize_free_for_all(self, app, app_context):
        """[CGEN-003] Normalizes free_for_all mode."""
        from services.judge.comparison_generator import ComparisonGenerator, ComparisonMode
        gen = ComparisonGenerator()
        assert gen._normalize_mode('free_for_all') == ComparisonMode.FREE_FOR_ALL

    def test_CGEN_004_normalize_legacy_all_pairs(self, app, app_context):
        """[CGEN-004] Legacy all_pairs maps to pillar_sample."""
        from services.judge.comparison_generator import ComparisonGenerator, ComparisonMode
        gen = ComparisonGenerator()
        assert gen._normalize_mode('all_pairs') == ComparisonMode.PILLAR_SAMPLE

    def test_CGEN_005_normalize_unknown_fallback(self, app, app_context):
        """[CGEN-005] Unknown mode falls back to pillar_sample."""
        from services.judge.comparison_generator import ComparisonGenerator, ComparisonMode
        gen = ComparisonGenerator()
        assert gen._normalize_mode('nonexistent') == ComparisonMode.PILLAR_SAMPLE

    def test_CGEN_006_normalize_case_insensitive(self, app, app_context):
        """[CGEN-006] Mode normalization is case-insensitive."""
        from services.judge.comparison_generator import ComparisonGenerator, ComparisonMode
        gen = ComparisonGenerator()
        assert gen._normalize_mode('ROUND_ROBIN') == ComparisonMode.ROUND_ROBIN
        assert gen._normalize_mode('Free_For_All') == ComparisonMode.FREE_FOR_ALL


class TestLimitThreads:
    """Tests for ComparisonGenerator._limit_threads."""

    def test_CGEN_010_no_limit_needed(self, app, app_context):
        """[CGEN-010] No limiting when threads within max."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [10, 20, 30], 2: [40, 50]}
        result = gen._limit_threads(threads, 5)
        assert len(result[1]) == 3
        assert len(result[2]) == 2

    def test_CGEN_011_limits_to_max(self, app, app_context):
        """[CGEN-011] Limits threads to max_threads."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: list(range(20)), 2: list(range(15))}
        result = gen._limit_threads(threads, 5)
        assert len(result[1]) == 5
        assert len(result[2]) == 5

    def test_CGEN_012_original_not_mutated(self, app, app_context):
        """[CGEN-012] Original dict is not mutated."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [10, 20, 30]}
        gen._limit_threads(threads, 2)
        assert len(threads[1]) == 3  # Still original size


class TestPillarSampleGeneration:
    """Tests for pillar_sample mode generation."""

    def test_CGEN_020_basic_generation(self, app, app_context):
        """[CGEN-020] Generates correct number of comparisons."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [1, 2, 3], 2: [4, 5, 6]}

        result = gen.generate(threads, mode='pillar_sample', samples_per_pillar=3, position_swap=False)
        assert result.total_count == 3  # 1 pillar pair * 3 samples
        assert result.mode.value == 'pillar_sample'

    def test_CGEN_021_with_position_swap(self, app, app_context):
        """[CGEN-021] Position swap doubles comparisons."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [1, 2, 3], 2: [4, 5, 6]}

        result = gen.generate(threads, mode='pillar_sample', samples_per_pillar=3, position_swap=True)
        assert result.total_count == 6  # 3 * 2 (swap)

    def test_CGEN_022_multiple_pillar_pairs(self, app, app_context):
        """[CGEN-022] Multiple pillars create multiple pairs."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [1, 2, 3], 2: [4, 5, 6], 3: [7, 8, 9]}

        # 3 pillar pairs: (1,2), (1,3), (2,3)
        result = gen.generate(threads, mode='pillar_sample', samples_per_pillar=2, position_swap=False)
        assert result.total_count == 6  # 3 pairs * 2 samples

    def test_CGEN_023_limited_by_available_threads(self, app, app_context):
        """[CGEN-023] Sample count limited by available threads."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [1], 2: [2, 3, 4]}

        result = gen.generate(threads, mode='pillar_sample', samples_per_pillar=10, position_swap=False)
        assert result.total_count == 1  # Limited by pillar 1 having only 1 thread

    def test_CGEN_024_repetitions(self, app, app_context):
        """[CGEN-024] Repetitions multiply comparisons."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [1, 2, 3], 2: [4, 5, 6]}

        result = gen.generate(threads, mode='pillar_sample', samples_per_pillar=2, position_swap=False, repetitions=3)
        assert result.total_count == 6  # 1 pair * 2 samples * 3 reps


class TestRoundRobinGeneration:
    """Tests for round_robin mode generation."""

    def test_CGEN_030_basic_round_robin(self, app, app_context):
        """[CGEN-030] Generates all cross-pillar combinations."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [1, 2], 2: [3, 4]}

        result = gen.generate(threads, mode='round_robin', position_swap=False)
        # 2 * 2 = 4 comparisons
        assert result.total_count == 4

    def test_CGEN_031_round_robin_with_swap(self, app, app_context):
        """[CGEN-031] Position swap doubles round robin comparisons."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [1, 2], 2: [3, 4]}

        result = gen.generate(threads, mode='round_robin', position_swap=True)
        assert result.total_count == 8  # 4 * 2

    def test_CGEN_032_round_robin_three_pillars(self, app, app_context):
        """[CGEN-032] Three pillars create all cross-pillar pairs."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [1], 2: [2], 3: [3]}

        result = gen.generate(threads, mode='round_robin', position_swap=False)
        # 3 pillar pairs: (1,2)=1, (1,3)=1, (2,3)=1 = 3
        assert result.total_count == 3


class TestFreeForAllGeneration:
    """Tests for free_for_all mode generation."""

    def test_CGEN_040_basic_free_for_all(self, app, app_context):
        """[CGEN-040] Generates all unique thread pairs."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [1, 2], 2: [3]}

        result = gen.generate(threads, mode='free_for_all', position_swap=False)
        # 3 threads total: (1,2), (1,3), (2,3) = 3
        assert result.total_count == 3

    def test_CGEN_041_free_for_all_with_swap(self, app, app_context):
        """[CGEN-041] Position swap doubles free-for-all."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [1, 2], 2: [3]}

        result = gen.generate(threads, mode='free_for_all', position_swap=True)
        assert result.total_count == 6  # 3 * 2

    def test_CGEN_042_includes_intra_pillar(self, app, app_context):
        """[CGEN-042] Free-for-all includes within-pillar comparisons."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [1, 2, 3]}

        result = gen.generate(threads, mode='free_for_all', position_swap=False)
        # 3 choose 2 = 3
        assert result.total_count == 3


class TestEstimate:
    """Tests for ComparisonGenerator.estimate."""

    def test_CGEN_050_estimate_pillar_sample(self, app, app_context):
        """[CGEN-050] Estimates pillar_sample correctly."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [1, 2, 3], 2: [4, 5, 6]}

        est = gen.estimate(threads, mode='pillar_sample', samples_per_pillar=3)
        assert est['total_comparisons'] == 6  # 3 * 2 (swap)
        assert est['position_swap'] is True
        assert est['mode'] == 'pillar_sample'
        assert est['total_threads'] == 6

    def test_CGEN_051_estimate_round_robin(self, app, app_context):
        """[CGEN-051] Estimates round_robin correctly."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [1, 2], 2: [3, 4]}

        est = gen.estimate(threads, mode='round_robin', position_swap=False)
        assert est['total_comparisons'] == 4

    def test_CGEN_052_estimate_free_for_all(self, app, app_context):
        """[CGEN-052] Estimates free_for_all correctly."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [1, 2], 2: [3, 4]}

        est = gen.estimate(threads, mode='free_for_all', position_swap=False)
        # 4 choose 2 = 6
        assert est['total_comparisons'] == 6

    def test_CGEN_053_estimate_duration_by_workers(self, app, app_context):
        """[CGEN-053] Duration estimates include worker-based estimates."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [1, 2], 2: [3, 4]}

        est = gen.estimate(threads, mode='pillar_sample', samples_per_pillar=2)
        assert 'estimated_duration_by_workers' in est
        assert 1 in est['estimated_duration_by_workers']
        assert 4 in est['estimated_duration_by_workers']

    def test_CGEN_054_estimate_with_thread_limit(self, app, app_context):
        """[CGEN-054] Estimation respects thread limit."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: list(range(20)), 2: list(range(20))}

        est = gen.estimate(threads, mode='pillar_sample', samples_per_pillar=5, max_threads_per_pillar=5)
        assert est['threads_per_pillar'][1] == 5


class TestGenerationResult:
    """Tests for GenerationResult metadata."""

    def test_CGEN_060_result_has_metadata(self, app, app_context):
        """[CGEN-060] GenerationResult includes expected metadata."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [1, 2], 3: [5, 6]}

        result = gen.generate(threads, mode='pillar_sample', samples_per_pillar=2, position_swap=False)
        assert result.pillars_used == [1, 3]
        assert result.threads_per_pillar == {1: 2, 3: 2}
        assert result.estimated_duration_minutes >= 0

    def test_CGEN_061_comparison_pair_fields(self, app, app_context):
        """[CGEN-061] ComparisonPair has all expected fields."""
        from services.judge.comparison_generator import ComparisonGenerator
        gen = ComparisonGenerator()
        threads = {1: [10], 2: [20]}

        result = gen.generate(threads, mode='pillar_sample', samples_per_pillar=1, position_swap=False)
        pair = result.comparisons[0]
        assert hasattr(pair, 'thread_a_id')
        assert hasattr(pair, 'thread_b_id')
        assert hasattr(pair, 'pillar_a')
        assert hasattr(pair, 'pillar_b')
        assert hasattr(pair, 'position_order')
        assert pair.position_order == 1


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_CGEN_070_generate_comparisons(self, app, app_context):
        """[CGEN-070] generate_comparisons convenience function works."""
        from services.judge.comparison_generator import generate_comparisons
        threads = {1: [1, 2], 2: [3, 4]}
        result = generate_comparisons(threads, mode='pillar_sample', samples_per_pillar=2, position_swap=False)
        assert result.total_count == 2

    def test_CGEN_071_estimate_comparisons(self, app, app_context):
        """[CGEN-071] estimate_comparisons convenience function works."""
        from services.judge.comparison_generator import estimate_comparisons
        threads = {1: [1, 2], 2: [3, 4]}
        est = estimate_comparisons(threads, mode='pillar_sample', samples_per_pillar=2)
        assert 'total_comparisons' in est
