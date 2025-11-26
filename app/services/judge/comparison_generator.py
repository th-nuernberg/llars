"""
Comparison Generator Service for LLM-as-Judge.

Generates comparison pairs based on different modes:
- pillar_sample: Random samples per pillar pair (default, fast)
- round_robin: All threads of one pillar vs all threads of another
- free_for_all: Every thread against every other thread

Author: LLARS Team
Date: November 2025
"""

import logging
import random
from dataclasses import dataclass
from enum import Enum
from itertools import combinations
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ComparisonMode(Enum):
    """Available comparison modes."""
    PILLAR_SAMPLE = "pillar_sample"
    ROUND_ROBIN = "round_robin"
    FREE_FOR_ALL = "free_for_all"

    # Legacy alias
    ALL_PAIRS = "all_pairs"  # Maps to PILLAR_SAMPLE


@dataclass
class ComparisonPair:
    """Represents a single comparison to be made."""
    thread_a_id: int
    thread_b_id: int
    pillar_a: int
    pillar_b: int
    position_order: int  # 1 = A|B, 2 = B|A (for position swap)


@dataclass
class GenerationResult:
    """Result of comparison generation."""
    comparisons: List[ComparisonPair]
    total_count: int
    mode: ComparisonMode
    pillars_used: List[int]
    threads_per_pillar: Dict[int, int]
    estimated_duration_minutes: float


class ComparisonGenerator:
    """
    Generates comparison pairs for Judge sessions.

    Supports multiple comparison modes for different use cases:
    - pillar_sample: Quick overview of pillar quality differences
    - round_robin: Comprehensive pillar comparison with thread-level stats
    - free_for_all: Complete thread ranking across all pillars
    """

    # Estimated seconds per comparison (including LLM latency)
    SECONDS_PER_COMPARISON = 10

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ComparisonGenerator")

    def generate(
        self,
        pillar_threads: Dict[int, List[int]],
        mode: str = "pillar_sample",
        samples_per_pillar: int = 10,
        position_swap: bool = True,
        max_threads_per_pillar: Optional[int] = None,
        repetitions: int = 1
    ) -> GenerationResult:
        """
        Generate comparison pairs based on the specified mode.

        Args:
            pillar_threads: Dict mapping pillar_number -> list of thread_ids
            mode: Comparison mode ('pillar_sample', 'round_robin', 'free_for_all')
            samples_per_pillar: Number of samples for pillar_sample mode
            position_swap: Whether to create A|B and B|A versions
            max_threads_per_pillar: Optional limit on threads per pillar
            repetitions: Number of times to repeat each comparison (for statistical stability)

        Returns:
            GenerationResult with list of ComparisonPair objects
        """
        # Normalize mode
        comparison_mode = self._normalize_mode(mode)

        # Apply thread limit if specified
        if max_threads_per_pillar:
            pillar_threads = self._limit_threads(pillar_threads, max_threads_per_pillar)

        # Generate based on mode
        if comparison_mode == ComparisonMode.PILLAR_SAMPLE:
            comparisons = self._generate_pillar_sample(
                pillar_threads, samples_per_pillar, position_swap, repetitions
            )
        elif comparison_mode == ComparisonMode.ROUND_ROBIN:
            comparisons = self._generate_round_robin(
                pillar_threads, position_swap
            )
        elif comparison_mode == ComparisonMode.FREE_FOR_ALL:
            comparisons = self._generate_free_for_all(
                pillar_threads, position_swap
            )
        else:
            raise ValueError(f"Unknown comparison mode: {mode}")

        # Calculate statistics
        threads_per_pillar = {p: len(t) for p, t in pillar_threads.items()}
        estimated_minutes = (len(comparisons) * self.SECONDS_PER_COMPARISON) / 60

        self.logger.info(
            f"Generated {len(comparisons)} comparisons using {comparison_mode.value} mode"
        )

        return GenerationResult(
            comparisons=comparisons,
            total_count=len(comparisons),
            mode=comparison_mode,
            pillars_used=list(pillar_threads.keys()),
            threads_per_pillar=threads_per_pillar,
            estimated_duration_minutes=estimated_minutes
        )

    def estimate(
        self,
        pillar_threads: Dict[int, List[int]],
        mode: str = "pillar_sample",
        samples_per_pillar: int = 10,
        position_swap: bool = True,
        max_threads_per_pillar: Optional[int] = None
    ) -> Dict:
        """
        Estimate comparison counts without generating actual pairs.

        Useful for UI to show expected workload before starting.

        Returns:
            Dict with estimation details
        """
        comparison_mode = self._normalize_mode(mode)

        # Apply thread limit if specified
        if max_threads_per_pillar:
            pillar_threads = self._limit_threads(pillar_threads, max_threads_per_pillar)

        pillars = sorted(pillar_threads.keys())
        pillar_pairs = list(combinations(pillars, 2))

        if comparison_mode == ComparisonMode.PILLAR_SAMPLE:
            # samples_per_pillar comparisons per pillar pair
            base_comparisons = len(pillar_pairs) * samples_per_pillar

        elif comparison_mode == ComparisonMode.ROUND_ROBIN:
            # All threads of pillar i vs all threads of pillar j
            base_comparisons = sum(
                len(pillar_threads[p1]) * len(pillar_threads[p2])
                for p1, p2 in pillar_pairs
            )

        elif comparison_mode == ComparisonMode.FREE_FOR_ALL:
            # All threads vs all other threads
            all_threads = []
            for threads in pillar_threads.values():
                all_threads.extend(threads)
            n = len(all_threads)
            base_comparisons = n * (n - 1) // 2
        else:
            base_comparisons = 0

        swap_multiplier = 2 if position_swap else 1
        total_comparisons = base_comparisons * swap_multiplier

        estimated_minutes = (total_comparisons * self.SECONDS_PER_COMPARISON) / 60

        return {
            "mode": comparison_mode.value,
            "pillars": pillars,
            "threads_per_pillar": {p: len(t) for p, t in pillar_threads.items()},
            "total_threads": sum(len(t) for t in pillar_threads.values()),
            "pillar_pairs": len(pillar_pairs),
            "base_comparisons": base_comparisons,
            "position_swap": position_swap,
            "swap_multiplier": swap_multiplier,
            "total_comparisons": total_comparisons,
            "estimated_duration_minutes": round(estimated_minutes, 1),
            "estimated_duration_by_workers": {
                1: round(estimated_minutes, 1),
                2: round(estimated_minutes / 2, 1),
                3: round(estimated_minutes / 3, 1),
                4: round(estimated_minutes / 4, 1),
                5: round(estimated_minutes / 5, 1),
            }
        }

    def _normalize_mode(self, mode: str) -> ComparisonMode:
        """Normalize mode string to ComparisonMode enum."""
        mode_lower = mode.lower().strip()

        # Handle legacy 'all_pairs' mode
        if mode_lower == "all_pairs":
            return ComparisonMode.PILLAR_SAMPLE

        try:
            return ComparisonMode(mode_lower)
        except ValueError:
            self.logger.warning(f"Unknown mode '{mode}', falling back to pillar_sample")
            return ComparisonMode.PILLAR_SAMPLE

    def _limit_threads(
        self,
        pillar_threads: Dict[int, List[int]],
        max_threads: int
    ) -> Dict[int, List[int]]:
        """Limit threads per pillar to max_threads (random sample)."""
        limited = {}
        for pillar, threads in pillar_threads.items():
            if len(threads) > max_threads:
                limited[pillar] = random.sample(threads, max_threads)
            else:
                limited[pillar] = threads.copy()
        return limited

    def _generate_pillar_sample(
        self,
        pillar_threads: Dict[int, List[int]],
        samples_per_pillar: int,
        position_swap: bool,
        repetitions: int = 1
    ) -> List[ComparisonPair]:
        """
        Generate pillar_sample comparisons.

        For each pillar pair, randomly sample threads and pair them 1:1.
        With repetitions > 1, different thread samples are used each time.
        """
        comparisons = []
        pillars = sorted(pillar_threads.keys())
        pillar_pairs = list(combinations(pillars, 2))

        for rep in range(repetitions):
            for pillar_a, pillar_b in pillar_pairs:
                threads_a = pillar_threads[pillar_a].copy()
                threads_b = pillar_threads[pillar_b].copy()

                # Shuffle for random sampling
                random.shuffle(threads_a)
                random.shuffle(threads_b)

                # Take samples
                sample_count = min(
                    samples_per_pillar,
                    len(threads_a),
                    len(threads_b)
                )

                sample_a = threads_a[:sample_count]
                sample_b = threads_b[:sample_count]

                # Create pairs
                for ta, tb in zip(sample_a, sample_b):
                    # Position 1: A | B
                    comparisons.append(ComparisonPair(
                        thread_a_id=ta,
                        thread_b_id=tb,
                        pillar_a=pillar_a,
                        pillar_b=pillar_b,
                        position_order=1
                    ))

                    # Position 2: B | A (if position_swap enabled)
                    if position_swap:
                        comparisons.append(ComparisonPair(
                            thread_a_id=tb,
                            thread_b_id=ta,
                            pillar_a=pillar_b,
                            pillar_b=pillar_a,
                            position_order=2
                        ))

        return comparisons

    def _generate_round_robin(
        self,
        pillar_threads: Dict[int, List[int]],
        position_swap: bool
    ) -> List[ComparisonPair]:
        """
        Generate round_robin comparisons.

        Every thread from pillar A plays against every thread from pillar B.
        This is done for all pillar pairs.
        """
        comparisons = []
        pillars = sorted(pillar_threads.keys())
        pillar_pairs = list(combinations(pillars, 2))

        for pillar_a, pillar_b in pillar_pairs:
            threads_a = pillar_threads[pillar_a]
            threads_b = pillar_threads[pillar_b]

            # Every thread from A vs every thread from B
            for ta in threads_a:
                for tb in threads_b:
                    # Position 1: A | B
                    comparisons.append(ComparisonPair(
                        thread_a_id=ta,
                        thread_b_id=tb,
                        pillar_a=pillar_a,
                        pillar_b=pillar_b,
                        position_order=1
                    ))

                    # Position 2: B | A (if position_swap enabled)
                    if position_swap:
                        comparisons.append(ComparisonPair(
                            thread_a_id=tb,
                            thread_b_id=ta,
                            pillar_a=pillar_b,
                            pillar_b=pillar_a,
                            position_order=2
                        ))

        # Shuffle to avoid systematic ordering effects
        random.shuffle(comparisons)

        return comparisons

    def _generate_free_for_all(
        self,
        pillar_threads: Dict[int, List[int]],
        position_swap: bool
    ) -> List[ComparisonPair]:
        """
        Generate free_for_all comparisons.

        Every thread plays against every other thread, regardless of pillar.
        This includes intra-pillar comparisons.
        """
        comparisons = []

        # Build list of (thread_id, pillar) tuples
        all_threads: List[Tuple[int, int]] = []
        for pillar, threads in pillar_threads.items():
            for thread_id in threads:
                all_threads.append((thread_id, pillar))

        # Generate all unique pairs
        for i, (thread_a, pillar_a) in enumerate(all_threads):
            for thread_b, pillar_b in all_threads[i + 1:]:
                # Position 1: A | B
                comparisons.append(ComparisonPair(
                    thread_a_id=thread_a,
                    thread_b_id=thread_b,
                    pillar_a=pillar_a,
                    pillar_b=pillar_b,
                    position_order=1
                ))

                # Position 2: B | A (if position_swap enabled)
                if position_swap:
                    comparisons.append(ComparisonPair(
                        thread_a_id=thread_b,
                        thread_b_id=thread_a,
                        pillar_a=pillar_b,
                        pillar_b=pillar_a,
                        position_order=2
                    ))

        # Shuffle to avoid systematic ordering effects
        random.shuffle(comparisons)

        return comparisons


# Convenience function for direct use
def generate_comparisons(
    pillar_threads: Dict[int, List[int]],
    mode: str = "pillar_sample",
    **kwargs
) -> GenerationResult:
    """
    Convenience function to generate comparisons.

    Args:
        pillar_threads: Dict mapping pillar_number -> list of thread_ids
        mode: 'pillar_sample', 'round_robin', or 'free_for_all'
        **kwargs: Additional arguments passed to generator

    Returns:
        GenerationResult with comparison pairs
    """
    generator = ComparisonGenerator()
    return generator.generate(pillar_threads, mode, **kwargs)


def estimate_comparisons(
    pillar_threads: Dict[int, List[int]],
    mode: str = "pillar_sample",
    **kwargs
) -> Dict:
    """
    Convenience function to estimate comparison counts.

    Args:
        pillar_threads: Dict mapping pillar_number -> list of thread_ids
        mode: 'pillar_sample', 'round_robin', or 'free_for_all'
        **kwargs: Additional arguments passed to generator

    Returns:
        Dict with estimation details
    """
    generator = ComparisonGenerator()
    return generator.estimate(pillar_threads, mode, **kwargs)
