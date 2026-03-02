"""
Conference Wizard Routes

SSE streaming endpoint for AI-powered conference lookup.
Searches DuckDuckGo, scrapes conference websites, and uses LLM to extract structured data.
"""

import json
import logging

from flask import Blueprint, request, Response

from decorators.error_handler import handle_api_errors
from decorators.permission_decorator import require_permission

logger = logging.getLogger('conference_wizard')

conference_wizard_bp = Blueprint("conference_wizard", __name__)


@conference_wizard_bp.route("/conferences/wizard/stream", methods=["POST"])
@require_permission('feature:conference_manager:edit')
@handle_api_errors(logger_name='conference_wizard')
def wizard_stream():
    """
    Stream AI conference lookup using Server-Sent Events (SSE).

    Emits events:
        searching: Starting DuckDuckGo search
        search_results: Search results found
        scraping: Scraping conference website
        thinking: LLM is processing
        chunk: Streaming token from LLM
        result: Parsed conference data
        done: Analysis complete
        error: Error occurred

    Body:
        query: Conference name, acronym, or URL (required)
    """
    from services.llm.llm_client_factory import LLMClientFactory
    from db.models.llm_model import LLMModel
    from services.conference_wizard_service import ConferenceWizardService

    data = request.get_json(silent=True) or {}
    query = (data.get('query') or '').strip()

    if not query:
        return Response(
            f"event: error\ndata: {json.dumps({'error': 'validation', 'message': 'Query is required'})}\n\n",
            mimetype='text/event-stream'
        )

    # Pre-fetch LLM client (requires Flask context)
    default_model_id = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_LLM)
    if not default_model_id:
        return Response(
            f"event: error\ndata: {json.dumps({'error': 'no_llm', 'message': 'No default LLM model configured'})}\n\n",
            mimetype='text/event-stream'
        )

    client, model_id = LLMClientFactory.resolve_client_and_model_id(default_model_id)
    if not client:
        return Response(
            f"event: error\ndata: {json.dumps({'error': 'no_llm', 'message': 'No LLM provider available'})}\n\n",
            mimetype='text/event-stream'
        )

    def generate():
        """Generator for SSE streaming. Runs OUTSIDE Flask request context."""
        try:
            for event in ConferenceWizardService.search_and_analyze(query, client, model_id):
                event_name = event.get('event', 'message')
                event_data = json.dumps(event.get('data', {}))
                yield f"event: {event_name}\ndata: {event_data}\n\n"
        except Exception as e:
            logger.error(f"Wizard stream error: {e}")
            yield f"event: error\ndata: {json.dumps({'error': 'failed', 'message': str(e)})}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )
