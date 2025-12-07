"""
Comparison Evaluation Service

Handles AI evaluation of LLM responses and user selections.
"""

import json
import logging
import threading
from typing import Optional, Tuple, Dict, Any

from db.tables import ComparisonSession, ComparisonMessage, ComparisonEvaluation
from db.db import db
from single_message_evaluation import SingleEvaluator

from .persona_formatter import PersonaFormatter
from .session_service import ComparisonSessionService

logger = logging.getLogger(__name__)


class ComparisonEvaluationService:
    """Service for evaluating and comparing LLM responses."""

    # Mapping from AI rating to selection format
    RATING_MAP = {
        'model_1': 'llm1',
        'model_2': 'llm2',
        'same': 'tie'
    }

    @classmethod
    def perform_evaluation(
        cls,
        message_id: int,
        session_id: int,
        user_selection: str
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Perform AI evaluation and compare with user selection.

        Args:
            message_id: ID of the message to evaluate
            session_id: ID of the session
            user_selection: User's selection (llm1, llm2, or tie)

        Returns:
            Tuple of (matches, evaluation_details)
        """
        try:
            evaluation = ComparisonEvaluation.query.filter_by(
                message_id=message_id
            ).order_by(ComparisonEvaluation.timestamp.desc()).first()

            if not evaluation:
                logger.warning(
                    f"No AI evaluation found for message {message_id}, performing now..."
                )
                return cls._perform_fallback_evaluation(
                    message_id, session_id, user_selection
                )

            # Update with user selection
            evaluation.user_selection = user_selection
            ai_selection = evaluation.ai_selection

            matches = cls.check_rating_match(user_selection, ai_selection)
            evaluation.match_result = matches

            db.session.commit()

            return matches, {
                'ai_selection': ai_selection,
                'ai_reason': evaluation.ai_reason,
                'user_selection': user_selection
            }

        except Exception as e:
            logger.error(f"Error in AI evaluation check: {str(e)}")
            return True, None

    @classmethod
    def _perform_fallback_evaluation(
        cls,
        message_id: int,
        session_id: int,
        user_selection: str
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Perform evaluation when no pre-computed evaluation exists."""
        try:
            message = ComparisonMessage.query.filter_by(
                id=message_id, session_id=session_id
            ).first()
            if not message or message.type != 'bot_pair':
                return True, None

            session = ComparisonSession.query.filter_by(id=session_id).first()
            if not session:
                return True, None

            content = cls._parse_message_content(message.content)
            if not content:
                return True, None

            # Build context and evaluate
            chat_history = ComparisonSessionService.build_chat_history_text(
                session, message.idx
            )

            persona_description = (
                PersonaFormatter.format(session.persona_json)
                if session.persona_json
                else "Keine Persona-Information verfügbar"
            )

            evaluator = SingleEvaluator()
            result = evaluator.evaluate_responses(
                persona_description=persona_description,
                history=chat_history,
                response1=content['llm1'],
                response2=content['llm2']
            )

            ai_selection = cls.map_rating_to_selection(result.get('rating', 'error'))
            ai_reason = result.get('reason', 'Keine Begründung verfügbar')

            matches = cls.check_rating_match(user_selection, ai_selection)

            # Save evaluation
            evaluation = ComparisonEvaluation(
                message_id=message_id,
                user_selection=user_selection,
                ai_selection=ai_selection,
                ai_reason=ai_reason,
                match_result=matches
            )

            db.session.add(evaluation)
            db.session.commit()

            return matches, {
                'ai_selection': ai_selection,
                'ai_reason': ai_reason,
                'user_selection': user_selection
            }

        except Exception as e:
            logger.error(f"Error in AI evaluation fallback: {str(e)}")
            return True, None

    @classmethod
    def perform_async_evaluation(cls, message_id: int, session_id: int) -> None:
        """
        Perform AI evaluation asynchronously in a background thread.

        Args:
            message_id: ID of the message to evaluate
            session_id: ID of the session
        """
        def run_evaluation():
            try:
                from main import app
                with app.app_context():
                    cls._run_evaluation_in_context(message_id, session_id)
            except Exception as e:
                logger.error(f"Error in async AI evaluation: {str(e)}")

        thread = threading.Thread(target=run_evaluation)
        thread.daemon = True
        thread.start()

    @classmethod
    def _run_evaluation_in_context(cls, message_id: int, session_id: int) -> None:
        """Run evaluation within Flask app context."""
        message = ComparisonMessage.query.filter_by(
            id=message_id, session_id=session_id
        ).first()
        if not message or message.type != 'bot_pair':
            return

        session = ComparisonSession.query.filter_by(id=session_id).first()
        if not session:
            return

        # Skip if already evaluated
        existing = ComparisonEvaluation.query.filter_by(message_id=message_id).first()
        if existing:
            return

        content = cls._parse_message_content(message.content)
        if not content:
            return

        chat_history = ComparisonSessionService.build_chat_history_text(
            session, message.idx
        )

        persona_description = (
            PersonaFormatter.format(session.persona_json)
            if session.persona_json
            else "Keine Persona-Information verfügbar"
        )

        evaluator = SingleEvaluator()
        result = evaluator.evaluate_responses(
            persona_description=persona_description,
            history=chat_history,
            response1=content['llm1'],
            response2=content['llm2']
        )

        ai_selection = cls.map_rating_to_selection(result.get('rating', 'error'))
        ai_reason = result.get('reason', 'Keine Begründung verfügbar')

        evaluation = ComparisonEvaluation(
            message_id=message_id,
            user_selection='',
            ai_selection=ai_selection,
            ai_reason=ai_reason,
            match_result=True
        )

        db.session.add(evaluation)
        db.session.commit()

        logger.info(f"AI evaluation completed for message {message_id}: {ai_selection}")

    @classmethod
    def save_user_justification(cls, message_id: int, justification: str) -> bool:
        """Save user's justification for their selection."""
        try:
            evaluation = ComparisonEvaluation.query.filter_by(
                message_id=message_id
            ).order_by(ComparisonEvaluation.timestamp.desc()).first()

            if evaluation:
                evaluation.user_justification = justification
                db.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving user justification: {str(e)}")
            return False

    @classmethod
    def map_rating_to_selection(cls, ai_rating: str) -> str:
        """Map AI rating format to selection format."""
        return cls.RATING_MAP.get(ai_rating, 'error')

    @staticmethod
    def check_rating_match(user_selection: str, ai_selection: str) -> bool:
        """Check if user and AI selections match."""
        if ai_selection == 'error':
            return True
        return user_selection == ai_selection

    @staticmethod
    def _parse_message_content(content: Any) -> Optional[Dict[str, str]]:
        """Parse message content to dict format."""
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                logger.error("Could not parse message content")
                return None

        if not isinstance(content, dict):
            return None

        if 'llm1' not in content or 'llm2' not in content:
            return None

        return content
