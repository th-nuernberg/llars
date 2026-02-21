"""
Generation API Routes.

Routes for batch generation jobs that connect Prompt Engineering
with Evaluation through LLM-generated outputs.

Endpoints:
    POST   /api/generation/jobs                    - Create a new job
    GET    /api/generation/jobs                    - List jobs for user
    GET    /api/generation/jobs/<id>               - Get job details
    POST   /api/generation/jobs/<id>/start         - Start a job
    POST   /api/generation/jobs/<id>/pause         - Pause a job
    POST   /api/generation/jobs/<id>/cancel        - Cancel a job
    DELETE /api/generation/jobs/<id>               - Delete a job

    GET    /api/generation/jobs/<id>/outputs       - Get job outputs (paginated)
    GET    /api/generation/outputs/<id>            - Get single output

    POST   /api/generation/jobs/<id>/export/csv    - Export to CSV
    POST   /api/generation/jobs/<id>/export/json   - Export to JSON
    POST   /api/generation/jobs/<id>/to-scenario   - Create evaluation scenario

    GET    /api/generation/jobs/<id>/statistics    - Get job statistics
    POST   /api/generation/estimate                - Estimate cost for config
"""

from routes.generation.generation_routes import generation_bp
from routes.generation.generation_debug_routes import generation_debug_bp

__all__ = ['generation_bp', 'generation_debug_bp']
