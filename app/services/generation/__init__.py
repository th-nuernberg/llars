"""
Batch Generation Services.

Services for orchestrating batch LLM generation jobs that connect
Prompt Engineering with Evaluation.

Public API:
    from services.generation import BatchGenerationService, GenerationWorker

Example:
    # Create and run a generation job
    job = BatchGenerationService.create_job(
        name="Summarization Comparison",
        config={
            "sources": {"type": "scenario", "scenario_id": 123},
            "prompts": [{"template_id": 1}],
            "llm_models": ["gpt-4", "claude-3-sonnet"],
        },
        created_by="admin"
    )
    BatchGenerationService.start_job(job.id)
"""

from services.generation.batch_generation_service import BatchGenerationService
from services.generation.generation_worker import GenerationWorker
from services.generation.output_export_service import OutputExportService

__all__ = [
    'BatchGenerationService',
    'GenerationWorker',
    'OutputExportService',
]
