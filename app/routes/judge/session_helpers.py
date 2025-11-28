"""Helper functions for session management."""

import logging
from db.db import db
from db.tables import (
    JudgeSessionStatus,
    JudgeComparison, JudgeComparisonStatus,
    PillarThread
)


def configure_session_comparisons(
    session,
    pillars,
    comparison_mode,
    samples_per_pillar,
    position_swap,
    repetitions_per_pair=1,
    max_threads_per_pillar=None
):
    """
    Helper to configure session comparisons using the ComparisonGenerator.

    Supports three modes:
    - pillar_sample (default): Random samples per pillar pair
    - round_robin: All threads of pillar A vs all threads of pillar B
    - free_for_all: Every thread against every other thread

    Args:
        session: JudgeSession object
        pillars: List of pillar numbers
        comparison_mode: 'pillar_sample', 'round_robin', 'free_for_all', or 'all_pairs' (legacy)
        samples_per_pillar: Number of samples for pillar_sample mode
        position_swap: Whether to create A|B and B|A versions
        repetitions_per_pair: Number of repetitions (only for pillar_sample)
        max_threads_per_pillar: Optional limit on threads per pillar
    """
    from services.judge.comparison_generator import ComparisonGenerator

    logger = logging.getLogger(__name__)

    # Get threads for each pillar
    pillar_threads = {}
    for pillar in pillars:
        threads = PillarThread.query.filter_by(pillar_number=pillar).all()
        if threads:
            pillar_threads[pillar] = [t.thread_id for t in threads]

    if not pillar_threads:
        logger.warning("No threads available for any pillar")
        return

    # Use the new ComparisonGenerator
    generator = ComparisonGenerator()

    result = generator.generate(
        pillar_threads=pillar_threads,
        mode=comparison_mode,
        samples_per_pillar=samples_per_pillar,
        position_swap=position_swap,
        max_threads_per_pillar=max_threads_per_pillar,
        repetitions=repetitions_per_pair
    )

    # Create JudgeComparison objects from the generated pairs
    comparisons = []
    for idx, pair in enumerate(result.comparisons):
        comp = JudgeComparison(
            session_id=session.id,
            thread_a_id=pair.thread_a_id,
            thread_b_id=pair.thread_b_id,
            pillar_a=pair.pillar_a,
            pillar_b=pair.pillar_b,
            position_order=pair.position_order,
            queue_position=idx,
            status=JudgeComparisonStatus.PENDING
        )
        comparisons.append(comp)

    # Bulk insert for efficiency
    db.session.bulk_save_objects(comparisons)

    # Update session
    session.total_comparisons = len(comparisons)
    session.status = JudgeSessionStatus.QUEUED

    logger.info(
        f"Configured session {session.id} with {len(comparisons)} comparisons "
        f"using {result.mode.value} mode"
    )
