"""
API Routes for AI Writing Assistant

Provides endpoints for:
- Text completion (ghost text)
- Text rewriting/expansion
- AI chat
- Citation finding (RAG)
- Citation review
"""

import logging
from flask import Blueprint, request, jsonify, Response, stream_with_context
from decorators.permission_decorator import require_permission
from decorators.error_handler import handle_errors, ValidationError
from auth.auth_utils import AuthUtils

logger = logging.getLogger(__name__)

ai_writing_blueprint = Blueprint('ai_writing', __name__, url_prefix='/api/ai-writing')


# =============================================================================
# COMPLETION ENDPOINTS
# =============================================================================

@ai_writing_blueprint.route('/complete', methods=['POST'])
@require_permission('feature:latex_collab:ai')
@handle_errors(logger_name='ai_writing')
def complete():
    """
    Generate text completion at cursor position.

    Request:
        {
            "context": str,          # Text around cursor (max 2000 chars)
            "cursor_position": int,  # Position in context
            "document_type": str,    # "latex" or "markdown"
            "max_tokens": int,       # Default: 100
            "temperature": float     # Default: 0.3
        }

    Response:
        {
            "success": true,
            "completion": str,
            "confidence": float,
            "alternatives": []
        }
    """
    data = request.get_json() or {}

    context = data.get('context', '')
    if not context:
        raise ValidationError('context is required')

    cursor_position = data.get('cursor_position', len(context))
    document_type = data.get('document_type', 'latex')
    max_tokens = min(data.get('max_tokens', 100), 200)
    temperature = min(max(data.get('temperature', 0.3), 0.0), 1.0)

    from services.ai_writing import CompletionService
    service = CompletionService()

    result = service.complete(
        context=context,
        cursor_position=cursor_position,
        document_type=document_type,
        max_tokens=max_tokens,
        temperature=temperature
    )

    return jsonify({
        'success': True,
        **result
    })


# =============================================================================
# REWRITE ENDPOINTS
# =============================================================================

@ai_writing_blueprint.route('/rewrite', methods=['POST'])
@require_permission('feature:latex_collab:ai')
@handle_errors(logger_name='ai_writing')
def rewrite():
    """
    Rewrite text in a specified style.

    Request:
        {
            "text": str,             # Text to rewrite
            "style": str,            # "academic", "concise", "expanded", "simplified"
            "context": str,          # Surrounding context
            "preserve_meaning": bool # Default: true
        }

    Response:
        {
            "success": true,
            "result": str,
            "changes": []
        }
    """
    data = request.get_json() or {}

    text = data.get('text', '')
    if not text:
        raise ValidationError('text is required')

    style = data.get('style', 'academic')
    context = data.get('context', '')
    preserve_meaning = data.get('preserve_meaning', True)

    from services.ai_writing import RewriteService
    service = RewriteService()

    result = service.rewrite(
        text=text,
        style=style,
        context=context,
        preserve_meaning=preserve_meaning
    )

    return jsonify({
        'success': True,
        **result
    })


@ai_writing_blueprint.route('/expand', methods=['POST'])
@require_permission('feature:latex_collab:ai')
@handle_errors(logger_name='ai_writing')
def expand():
    """Expand text with more details."""
    data = request.get_json() or {}

    text = data.get('text', '')
    if not text:
        raise ValidationError('text is required')

    context = data.get('context', '')

    from services.ai_writing import RewriteService
    service = RewriteService()

    result = service.expand(text=text, context=context)

    return jsonify({
        'success': True,
        **result
    })


@ai_writing_blueprint.route('/summarize', methods=['POST'])
@require_permission('feature:latex_collab:ai')
@handle_errors(logger_name='ai_writing')
def summarize():
    """Summarize text."""
    data = request.get_json() or {}

    text = data.get('text', '')
    if not text:
        raise ValidationError('text is required')

    from services.ai_writing import RewriteService
    service = RewriteService()

    result = service.summarize(text=text)

    return jsonify({
        'success': True,
        **result
    })


@ai_writing_blueprint.route('/abstract', methods=['POST'])
@require_permission('feature:latex_collab:ai')
@handle_errors(logger_name='ai_writing')
def generate_abstract():
    """Generate abstract for document."""
    data = request.get_json() or {}

    content = data.get('content', '')
    if not content:
        raise ValidationError('content is required')

    from services.ai_writing import RewriteService
    service = RewriteService()

    result = service.generate_abstract(document_content=content)

    return jsonify({
        'success': True,
        **result
    })


@ai_writing_blueprint.route('/titles', methods=['POST'])
@require_permission('feature:latex_collab:ai')
@handle_errors(logger_name='ai_writing')
def suggest_titles():
    """Suggest titles for document."""
    data = request.get_json() or {}

    content = data.get('content', '')
    if not content:
        raise ValidationError('content is required')

    num_suggestions = data.get('num_suggestions', 5)

    from services.ai_writing import RewriteService
    service = RewriteService()

    result = service.suggest_titles(
        document_content=content,
        num_suggestions=num_suggestions
    )

    return jsonify({
        'success': True,
        **result
    })


@ai_writing_blueprint.route('/fix-latex', methods=['POST'])
@require_permission('feature:latex_collab:ai')
@handle_errors(logger_name='ai_writing')
def fix_latex():
    """Analyze and fix LaTeX errors."""
    data = request.get_json() or {}

    content = data.get('content', '')
    if not content:
        raise ValidationError('content is required')

    from services.ai_writing import RewriteService
    service = RewriteService()

    result = service.fix_latex(content=content)

    return jsonify({
        'success': True,
        **result
    })


# =============================================================================
# CHAT ENDPOINTS
# =============================================================================

@ai_writing_blueprint.route('/chat', methods=['POST'])
@require_permission('feature:latex_collab:ai')
@handle_errors(logger_name='ai_writing')
def chat():
    """
    Process chat message.

    Request:
        {
            "message": str,
            "document_content": str,  # Max 4000 chars
            "history": [],            # Previous messages
            "stream": bool            # Default: false
        }

    Response (non-streaming):
        {
            "success": true,
            "response": str,
            "artifacts": []
        }
    """
    data = request.get_json() or {}

    message = data.get('message', '')
    if not message:
        raise ValidationError('message is required')

    document_content = data.get('document_content', '')
    history = data.get('history', [])
    stream = data.get('stream', False)

    from services.ai_writing import AIChatService
    service = AIChatService()

    if stream:
        # Streaming response
        def generate():
            for chunk in service.stream_chat(
                message=message,
                document_content=document_content,
                history=history
            ):
                import json
                yield f"data: {json.dumps(chunk)}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    # Non-streaming response
    result = service.chat(
        message=message,
        document_content=document_content,
        history=history
    )

    return jsonify({
        'success': True,
        **result
    })


@ai_writing_blueprint.route('/command', methods=['POST'])
@require_permission('feature:latex_collab:ai')
@handle_errors(logger_name='ai_writing')
def execute_command():
    """
    Execute an @-command.

    Request:
        {
            "command": str,        # e.g., "rewrite", "expand", "cite"
            "args": str,           # Command arguments
            "selected_text": str,  # Currently selected text
            "document_content": str
        }
    """
    data = request.get_json() or {}

    command = data.get('command', '')
    if not command:
        raise ValidationError('command is required')

    args = data.get('args', '')
    selected_text = data.get('selected_text', '')
    document_content = data.get('document_content', '')

    from services.ai_writing import AIChatService
    service = AIChatService()

    result = service.execute_command(
        command=command,
        args=args,
        selected_text=selected_text,
        document_content=document_content
    )

    return jsonify({
        'success': True,
        **result
    })


# =============================================================================
# CITATION ENDPOINTS
# =============================================================================

@ai_writing_blueprint.route('/find-citations', methods=['POST'])
@require_permission('feature:latex_collab:ai')
@handle_errors(logger_name='ai_writing')
def find_citations():
    """
    Find citations using RAG.

    Request:
        {
            "claim": str,           # Statement needing citation
            "context": str,         # Surrounding text
            "collection_ids": [],   # RAG collection IDs
            "limit": int,           # Default: 10
            "format": str           # "bibtex", "apa", "mla"
        }
    """
    data = request.get_json() or {}

    claim = data.get('claim', '')
    if not claim:
        raise ValidationError('claim is required')

    context = data.get('context', '')
    collection_ids = data.get('collection_ids', [])
    limit = min(data.get('limit', 10), 20)
    format = data.get('format', 'bibtex')

    from services.ai_writing import CitationService
    service = CitationService()

    result = service.find_citations(
        claim=claim,
        context=context,
        collection_ids=collection_ids,
        limit=limit,
        format=format
    )

    return jsonify({
        'success': True,
        **result
    })


@ai_writing_blueprint.route('/review-citations', methods=['POST'])
@require_permission('feature:latex_collab:ai')
@handle_errors(logger_name='ai_writing')
def review_citations():
    """
    Review document for claims needing citations.

    Request:
        {
            "content": str  # Full document content
        }
    """
    data = request.get_json() or {}

    content = data.get('content', '')
    if not content:
        raise ValidationError('content is required')

    from services.ai_writing import CitationService
    service = CitationService()

    result = service.review_citations(content=content)

    return jsonify({
        'success': True,
        **result
    })


@ai_writing_blueprint.route('/ignore-warning', methods=['POST'])
@require_permission('feature:latex_collab:ai')
@handle_errors(logger_name='ai_writing')
def ignore_warning():
    """Mark a citation warning as ignored."""
    data = request.get_json() or {}

    document_id = data.get('document_id')
    text = data.get('text', '')

    if not document_id or not text:
        raise ValidationError('document_id and text are required')

    user = AuthUtils.get_current_user()

    from services.ai_writing import CitationService
    service = CitationService()

    success = service.ignore_warning(
        document_id=document_id,
        text=text,
        user_id=user.id
    )

    return jsonify({
        'success': success
    })


# =============================================================================
# HEALTH CHECK
# =============================================================================

@ai_writing_blueprint.route('/health', methods=['GET'])
@require_permission('feature:latex_collab:ai')
@handle_errors(logger_name='ai_writing')
def health_check():
    """Check if AI writing service is available."""
    try:
        from llm.litellm_client import LiteLLMClient
        client = LiteLLMClient()

        return jsonify({
            'success': True,
            'status': 'healthy',
            'model': client.model,
            'base_url': client.base_url
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 503
