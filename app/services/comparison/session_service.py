"""
Comparison Session Service

Handles CRUD operations for comparison sessions and messages.
"""

import json
import logging
from typing import Optional, List, Dict, Any

from db.tables import ComparisonSession, ComparisonMessage, RatingScenarios
from db.database import db
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)


class ComparisonSessionService:
    """Service for managing comparison sessions and messages."""

    @staticmethod
    def get_session_by_id(session_id: int) -> Optional[ComparisonSession]:
        """Get a session by ID with scenario eagerly loaded."""
        return ComparisonSession.query.options(
            joinedload(ComparisonSession.scenario)
        ).filter_by(id=session_id).first()

    @staticmethod
    def get_model_mapping_for_session(session: ComparisonSession) -> Dict[str, str]:
        """Get the LLM model mapping for a session's scenario."""
        try:
            scenario = RatingScenarios.query.filter_by(id=session.scenario_id).first()

            if scenario and scenario.llm1_model and scenario.llm2_model:
                return {
                    'llm1': scenario.llm1_model,
                    'llm2': scenario.llm2_model
                }
            else:
                raise ValueError("No valid model mapping found for the session or scenario.")
        except Exception as e:
            logger.error(f"Error getting model mapping: {str(e)}")
            raise ValueError(f"Error accessing scenario data: {str(e)}")

    @staticmethod
    def get_all_messages(session_id: int) -> List[ComparisonMessage]:
        """Get all messages for a session ordered by index."""
        return ComparisonMessage.query.filter_by(
            session_id=session_id
        ).order_by(ComparisonMessage.idx).all()

    @staticmethod
    def get_message(message_id: int, session_id: int) -> Optional[ComparisonMessage]:
        """Get a specific message by ID and session."""
        return ComparisonMessage.query.filter_by(
            id=message_id,
            session_id=session_id
        ).first()

    @staticmethod
    def set_message_selected(message_id: int, session_id: int, selected: str) -> bool:
        """Mark a message as selected with the given choice."""
        message = ComparisonMessage.query.filter_by(
            id=message_id,
            session_id=session_id
        ).first()
        if message:
            message.selected = selected
            db.session.commit()
            return True
        return False

    @staticmethod
    def add_message(
        session_id: int,
        idx: int,
        message_type: str,
        content: Any
    ) -> int:
        """Add a new message to a session."""
        message = ComparisonMessage(
            session_id=session_id,
            idx=idx,
            type=message_type,
            content=content,
            selected=None
        )
        db.session.add(message)
        db.session.commit()
        return message.id

    @staticmethod
    def serialize_message(message: ComparisonMessage) -> Dict[str, Any]:
        """Serialize a message for API response."""
        content = message.content
        if isinstance(content, str) and message.type == 'bot_pair':
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                content = {"llm1": "", "llm2": ""}

        return {
            'messageId': message.id,
            'idx': message.idx,
            'type': message.type,
            'content': content,
            'selected': message.selected,
            'timestamp': message.timestamp.isoformat(),
        }

    @staticmethod
    def build_chat_history(session: ComparisonSession) -> List[Dict[str, str]]:
        """Build chat history in OpenAI message format."""
        messages = []

        try:
            for message in session.messages:
                if message.type == 'bot_pair':
                    content_data = (
                        json.loads(message.content)
                        if isinstance(message.content, str)
                        else message.content
                    )
                    selected_content = content_data.get(message.selected, '')
                    if selected_content:
                        messages.append({
                            'role': 'assistant',
                            'content': selected_content
                        })
                elif message.type == 'user':
                    messages.append({
                        'role': 'user',
                        'content': message.content
                    })
        except Exception as e:
            logger.error(f"Error building chat history: {str(e)}")

        return messages

    @staticmethod
    def build_chat_history_text(session: ComparisonSession, up_to_idx: int) -> str:
        """Build chat history as text for evaluation prompts."""
        messages = ComparisonMessage.query.filter_by(
            session_id=session.id
        ).filter(
            ComparisonMessage.idx < up_to_idx
        ).order_by(ComparisonMessage.idx).all()

        history_parts = []
        for msg in messages:
            if msg.type == 'user':
                history_parts.append(f"Berater: {msg.content}")
            elif msg.type == 'bot_pair' and msg.selected:
                content = msg.content
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except json.JSONDecodeError:
                        continue

                if isinstance(content, dict) and msg.selected in content:
                    history_parts.append(f"Klient: {content[msg.selected]}")

        return "\n".join(history_parts)

    @staticmethod
    def update_message_content(
        message_id: int,
        llm_type: str,
        response: str
    ) -> bool:
        """Update the LLM response in a message."""
        try:
            message = ComparisonMessage.query.filter_by(id=message_id).first()
            if message:
                content = (
                    json.loads(message.content)
                    if isinstance(message.content, str)
                    else message.content
                )
                content[llm_type] = response
                message.content = json.dumps(content)
                db.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating message content: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def is_response_complete(message_id: int) -> bool:
        """Check if both LLM responses are complete."""
        message = ComparisonMessage.query.filter_by(id=message_id).first()
        if not message:
            return False

        content = (
            json.loads(message.content)
            if isinstance(message.content, str)
            else message.content
        )
        return (
            isinstance(content, dict)
            and 'llm1' in content
            and 'llm2' in content
            and content['llm1']
            and content['llm2']
        )
