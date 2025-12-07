"""
LLM Response Generator

Handles streaming LLM response generation for comparisons.
"""

import json
import logging
import threading
from typing import Optional, Dict, Any, List

from openai import OpenAI

from .session_service import ComparisonSessionService
from .prompt_generator import ComparisonPromptGenerator
from .evaluation_service import ComparisonEvaluationService

logger = logging.getLogger(__name__)


class LLMResponseGenerator:
    """Generates and streams LLM responses for comparison sessions."""

    # Default LLM endpoint configuration
    DEFAULT_SSH_CONTAINER = "llars_docker_ssh_proxy_service_2"
    DEFAULT_SSH_CONTAINER_PORT = "8195"

    # Suggestion endpoint configuration
    SUGGESTION_SSH_CONTAINER = "llars_docker_ssh_proxy_service"
    SUGGESTION_SSH_CONTAINER_PORT = "8093"
    SUGGESTION_MODEL = 'mistralai/Mistral-Small-3.1-24B-Instruct-2503'

    def __init__(
        self,
        ssh_container: Optional[str] = None,
        ssh_container_port: Optional[str] = None
    ):
        """
        Initialize the response generator.

        Args:
            ssh_container: SSH container hostname
            ssh_container_port: SSH container port
        """
        self.ssh_container = ssh_container or self.DEFAULT_SSH_CONTAINER
        self.ssh_container_port = ssh_container_port or self.DEFAULT_SSH_CONTAINER_PORT

    def generate_comparison_responses(
        self,
        session,
        message_id: int,
        socketio,
        client_id: str
    ) -> None:
        """
        Generate comparison responses from both LLMs.

        Starts two threads to generate responses in parallel.

        Args:
            session: ComparisonSession object
            message_id: ID of the message to populate
            socketio: SocketIO instance for streaming
            client_id: Client room ID for socket events
        """
        try:
            session_id = session.id

            from main import app
            with app.app_context():
                fresh_session = ComparisonSessionService.get_session_by_id(session_id)
                if not fresh_session:
                    raise ValueError(f"Session with ID {session_id} not found")

                persona = fresh_session.persona_json
                chat_history = ComparisonSessionService.build_chat_history(fresh_session)
                chat_history_text = "\n".join([
                    f"{msg['role']}: '{msg['content']}'"
                    for msg in chat_history
                ])

                system_prompt = ComparisonPromptGenerator.create_persona_prompt(
                    persona, chat_history_text
                )

                socketio.emit('streaming_started', {
                    'messageId': message_id,
                    'llmTypes': ['llm1', 'llm2']
                }, room=client_id)

                is_first_message = not chat_history

                # Start parallel generation threads
                thread1 = threading.Thread(
                    target=self._generate_llm_response,
                    args=('llm1', system_prompt, is_first_message,
                          message_id, socketio, client_id, session_id)
                )
                thread2 = threading.Thread(
                    target=self._generate_llm_response,
                    args=('llm2', system_prompt, is_first_message,
                          message_id, socketio, client_id, session_id)
                )

                thread1.start()
                thread2.start()

        except Exception as e:
            logger.error(f"Error in generate_comparison_responses: {str(e)}")
            socketio.emit('streaming_error', {
                'messageId': message_id,
                'error': f'Fehler beim Generieren der Antwort: {str(e)}'
            }, room=client_id)

    def _generate_llm_response(
        self,
        llm_type: str,
        message: str,
        is_first_message: bool,
        message_id: int,
        socketio,
        client_id: str,
        session_id: int
    ) -> None:
        """Generate response from a single LLM with streaming."""
        try:
            client = OpenAI(
                api_key="EMPTY",
                base_url=f"http://{self.ssh_container}:{self.ssh_container_port}/v1"
            )

            from main import app
            with app.app_context():
                session = ComparisonSessionService.get_session_by_id(session_id)
                if not session:
                    raise ValueError(f"Session with ID {session_id} not found")

                model_mapping = ComparisonSessionService.get_model_mapping_for_session(
                    session
                )
                model_name = model_mapping.get(llm_type)

            stream = client.chat.completions.create(
                model=model_name,
                messages=[{
                    'role': 'system',
                    'content': message
                }],
                temperature=0.7,
                max_tokens=50 if is_first_message else 100,
                stream=True
            )

            full_response = ""
            for chunk in stream:
                choice = chunk.choices[0]
                delta = choice.delta
                content = getattr(delta, "content", "")

                if content:
                    full_response += content
                    socketio.emit('streaming_update', {
                        'messageId': message_id,
                        'llmType': llm_type,
                        'content': content,
                        'fullContent': full_response
                    }, room=client_id)

                if getattr(choice, "finish_reason", None) is not None:
                    socketio.emit('streaming_complete', {
                        'messageId': message_id,
                        'llmType': llm_type,
                        'finalContent': full_response
                    }, room=client_id)
                    break

            self._save_response(message_id, llm_type, full_response)

        except Exception as e:
            logger.error(f"Error generating {llm_type} response: {str(e)}")
            socketio.emit('streaming_error', {
                'messageId': message_id,
                'llmType': llm_type,
                'error': f'Fehler beim Generieren der Antwort: {str(e)}'
            }, room=client_id)

    def _save_response(
        self,
        message_id: int,
        llm_type: str,
        response: str
    ) -> None:
        """Save LLM response and trigger async evaluation if complete."""
        try:
            from main import app
            with app.app_context():
                from db.tables import ComparisonMessage
                from db.db import db

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

                    # Trigger evaluation if both responses are complete
                    if ('llm1' in content and 'llm2' in content
                            and content['llm1'] and content['llm2']):
                        ComparisonEvaluationService.perform_async_evaluation(
                            message_id, message.session_id
                        )

        except Exception as e:
            logger.error(f"Error saving {llm_type} response: {str(e)}")
            from db.db import db
            db.session.rollback()

    @classmethod
    def generate_counselor_suggestion(cls, session) -> str:
        """
        Generate a counselor suggestion based on the conversation.

        Args:
            session: ComparisonSession object

        Returns:
            Suggested counselor response
        """
        try:
            session_id = session.id

            from main import app
            with app.app_context():
                fresh_session = ComparisonSessionService.get_session_by_id(session_id)
                if not fresh_session:
                    raise ValueError(f"Session with ID {session_id} not found")

                persona = fresh_session.persona_json
                chat_history = ComparisonSessionService.build_chat_history(fresh_session)

                suggestion_prompt = ComparisonPromptGenerator.create_counselor_suggestion_prompt(
                    persona, chat_history
                )

                client = OpenAI(
                    api_key="EMPTY",
                    base_url=f"http://{cls.SUGGESTION_SSH_CONTAINER}:{cls.SUGGESTION_SSH_CONTAINER_PORT}/v1"
                )

                response = client.chat.completions.create(
                    model=cls.SUGGESTION_MODEL,
                    messages=[{
                        'role': 'system',
                        'content': suggestion_prompt
                    }],
                    temperature=0.2,
                    max_tokens=150
                )

                suggestion = response.choices[0].message.content.strip()
                return suggestion

        except Exception as e:
            logger.error(f"Error generating counselor suggestion: {str(e)}")
            return "Wie fühlen Sie sich in dieser Situation?"
