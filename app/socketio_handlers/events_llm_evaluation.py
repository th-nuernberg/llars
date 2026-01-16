"""
Socket.IO Event Handlers for LLM Evaluation.

Handles real-time communication for:
- LLM evaluator progress tracking
- Live evaluation results streaming
- Token usage updates
"""

import logging
from flask_socketio import emit, join_room, leave_room
from flask import request

logger = logging.getLogger(__name__)


def register_llm_evaluation_events(socketio):
    """
    Register Socket.IO events for LLM Evaluation functionality.

    Events:
        llm_eval:join_scenario - Join a scenario room for live updates
        llm_eval:leave_scenario - Leave a scenario room
        llm_eval:get_progress - Get current evaluation progress
    """

    @socketio.on('llm_eval:join_scenario')
    def handle_join_scenario(data):
        """
        Handle client joining an evaluation scenario room.

        Args:
            data: dict with 'scenario_id'

        Emits:
            llm_eval:joined - Confirmation of join
        """
        scenario_id = data.get('scenario_id')
        if not scenario_id:
            emit('llm_eval:error', {'message': 'scenario_id erforderlich'})
            return

        room = f"llm_eval_scenario_{scenario_id}"
        join_room(room)

        logger.info(f"[LLM Eval] Client {request.sid} joined room {room}")

        emit('llm_eval:joined', {
            'scenario_id': scenario_id,
            'room': room,
            'message': 'Erfolgreich verbunden'
        })

    @socketio.on('llm_eval:leave_scenario')
    def handle_leave_scenario(data):
        """
        Handle client leaving an evaluation scenario room.

        Args:
            data: dict with 'scenario_id'
        """
        scenario_id = data.get('scenario_id')
        if not scenario_id:
            return

        room = f"llm_eval_scenario_{scenario_id}"
        leave_room(room)

        logger.info(f"[LLM Eval] Client {request.sid} left room {room}")

        emit('llm_eval:left', {
            'scenario_id': scenario_id,
            'room': room
        })

    @socketio.on('llm_eval:join_overview')
    def handle_join_overview():
        """
        Handle client joining the evaluation overview room.
        This room receives updates for ALL active evaluations.
        """
        room = "llm_eval_overview"
        join_room(room)
        logger.info(f"[LLM Eval] Client {request.sid} joined overview room")
        emit('llm_eval:overview_joined', {'room': room})

    @socketio.on('llm_eval:leave_overview')
    def handle_leave_overview():
        """
        Handle client leaving the evaluation overview room.
        """
        room = "llm_eval_overview"
        leave_room(room)
        logger.info(f"[LLM Eval] Client {request.sid} left overview room")

    @socketio.on('llm_eval:get_progress')
    def handle_get_progress(data):
        """
        Get current evaluation progress for a scenario.

        Args:
            data: dict with 'scenario_id'

        Emits:
            llm_eval:progress - Current evaluation progress
        """
        from db.models import RatingScenarios, LLMTaskResult, ScenarioThreads

        scenario_id = data.get('scenario_id')
        if not scenario_id:
            emit('llm_eval:error', {'message': 'scenario_id erforderlich'})
            return

        scenario = RatingScenarios.query.get(scenario_id)
        if not scenario:
            emit('llm_eval:error', {'message': 'Szenario nicht gefunden'})
            return

        # Get total threads
        total_threads = ScenarioThreads.query.filter_by(
            scenario_id=scenario_id
        ).count()

        # Get LLM evaluators from config
        config = scenario.config_json if isinstance(scenario.config_json, dict) else {}
        llm_evaluators = config.get('llm_evaluators', [])

        # Get completed evaluations per model
        model_progress = {}
        for model_id in llm_evaluators:
            completed = LLMTaskResult.query.filter_by(
                scenario_id=scenario_id,
                model_id=model_id,
            ).filter(LLMTaskResult.payload_json.isnot(None)).count()

            errors = LLMTaskResult.query.filter_by(
                scenario_id=scenario_id,
                model_id=model_id,
            ).filter(LLMTaskResult.error.isnot(None)).count()

            model_progress[model_id] = {
                'completed': completed,
                'errors': errors,
                'total': total_threads,
                'progress_percent': (completed / total_threads * 100) if total_threads > 0 else 0
            }

        # Calculate overall progress
        total_tasks = total_threads * len(llm_evaluators) if llm_evaluators else total_threads
        total_completed = sum(m['completed'] for m in model_progress.values())
        total_errors = sum(m['errors'] for m in model_progress.values())

        emit('llm_eval:progress', {
            'scenario_id': scenario_id,
            'total_threads': total_threads,
            'llm_evaluators': llm_evaluators,
            'model_progress': model_progress,
            'overall': {
                'completed': total_completed,
                'errors': total_errors,
                'total': total_tasks,
                'progress_percent': (total_completed / total_tasks * 100) if total_tasks > 0 else 0
            }
        })

    @socketio.on('llm_eval:get_result')
    def handle_get_result(data):
        """
        Get detailed evaluation result for a specific thread/model combination.

        Args:
            data: dict with 'scenario_id', 'thread_id', 'model_id'

        Emits:
            llm_eval:result - Evaluation result with reasoning
        """
        from db.models import LLMTaskResult

        scenario_id = data.get('scenario_id')
        thread_id = data.get('thread_id')
        model_id = data.get('model_id')

        if not all([scenario_id, thread_id, model_id]):
            emit('llm_eval:error', {'message': 'scenario_id, thread_id und model_id erforderlich'})
            return

        result = LLMTaskResult.query.filter_by(
            scenario_id=scenario_id,
            thread_id=thread_id,
            model_id=model_id
        ).first()

        if not result:
            emit('llm_eval:result', {
                'scenario_id': scenario_id,
                'thread_id': thread_id,
                'model_id': model_id,
                'status': 'not_found',
                'result': None
            })
            return

        emit('llm_eval:result', {
            'scenario_id': scenario_id,
            'thread_id': thread_id,
            'model_id': model_id,
            'status': 'error' if result.error else 'completed',
            'result': result.to_dict(include_raw=False)
        })

    logger.info("[LLM Eval Socket] Events registered")


# Broadcast functions (called from LLMAITaskRunner)
def broadcast_evaluation_started(socketio, scenario_id: int, model_id: str, thread_id: int):
    """
    Broadcast that an evaluation has started.

    Args:
        socketio: SocketIO instance
        scenario_id: Scenario ID
        model_id: Model ID
        thread_id: Thread ID being evaluated
    """
    room = f"llm_eval_scenario_{scenario_id}"
    socketio.emit('llm_eval:task_started', {
        'scenario_id': scenario_id,
        'model_id': model_id,
        'thread_id': thread_id,
        'status': 'running'
    }, room=room)

    # Also emit to overview room
    socketio.emit('llm_eval:task_started', {
        'scenario_id': scenario_id,
        'model_id': model_id,
        'thread_id': thread_id,
        'status': 'running'
    }, room="llm_eval_overview")


def broadcast_evaluation_completed(
    socketio,
    scenario_id: int,
    model_id: str,
    thread_id: int,
    task_type: str,
    result: dict,
    *,
    tokens_used: int = 0,
    cost_usd: float = 0.0,
    processing_time_ms: int = 0,
):
    """
    Broadcast that an evaluation has completed.

    Args:
        socketio: SocketIO instance
        scenario_id: Scenario ID
        model_id: Model ID
        thread_id: Thread ID
        task_type: Task type (ranking, rating, etc.)
        result: Evaluation result
        tokens_used: Total tokens used
        cost_usd: Estimated cost in USD
        processing_time_ms: Processing time in milliseconds
    """
    room = f"llm_eval_scenario_{scenario_id}"
    data = {
        'scenario_id': scenario_id,
        'model_id': model_id,
        'thread_id': thread_id,
        'task_type': task_type,
        'status': 'completed',
        'result': result,
        'meta': {
            'tokens_used': tokens_used,
            'cost_usd': cost_usd,
            'processing_time_ms': processing_time_ms,
        }
    }
    socketio.emit('llm_eval:task_completed', data, room=room)
    socketio.emit('llm_eval:task_completed', data, room="llm_eval_overview")


def broadcast_evaluation_failed(
    socketio,
    scenario_id: int,
    model_id: str,
    thread_id: int,
    task_type: str,
    error: str,
):
    """
    Broadcast that an evaluation has failed.

    Args:
        socketio: SocketIO instance
        scenario_id: Scenario ID
        model_id: Model ID
        thread_id: Thread ID
        task_type: Task type
        error: Error message
    """
    room = f"llm_eval_scenario_{scenario_id}"
    data = {
        'scenario_id': scenario_id,
        'model_id': model_id,
        'thread_id': thread_id,
        'task_type': task_type,
        'status': 'failed',
        'error': error,
    }
    socketio.emit('llm_eval:task_failed', data, room=room)
    socketio.emit('llm_eval:task_failed', data, room="llm_eval_overview")


def broadcast_scenario_completed(
    socketio,
    scenario_id: int,
    summary: dict,
):
    """
    Broadcast that all evaluations for a scenario are complete.

    Args:
        socketio: SocketIO instance
        scenario_id: Scenario ID
        summary: Summary statistics
    """
    room = f"llm_eval_scenario_{scenario_id}"
    data = {
        'scenario_id': scenario_id,
        'status': 'all_completed',
        'summary': summary,
    }
    socketio.emit('llm_eval:scenario_completed', data, room=room)
    socketio.emit('llm_eval:scenario_completed', data, room="llm_eval_overview")
