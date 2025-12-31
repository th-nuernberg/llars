"""
Chat Service for AI Writing Assistant

Provides conversational AI chat functionality with document context.
"""

import logging
import json
from typing import Optional, Dict, Any, List, Generator

from llm.litellm_client import LiteLLMClient
from .prompts import CHAT_SYSTEM_PROMPT, CHAT_USER_PROMPT_WITH_CONTEXT

logger = logging.getLogger(__name__)


class AIChatService:
    """Service for AI chat conversations with document context."""

    MAX_HISTORY_MESSAGES = 10
    MAX_DOCUMENT_TOKENS = 4000  # Approx chars
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 1000

    def __init__(self, model: Optional[str] = None):
        """
        Initialize chat service.

        Args:
            model: Optional model override
        """
        self.llm_client = LiteLLMClient(model=model)

    def chat(
        self,
        message: str,
        document_content: str = "",
        history: Optional[List[Dict[str, str]]] = None,
        stream: bool = False,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE
    ) -> Dict[str, Any]:
        """
        Process a chat message (non-streaming).

        Args:
            message: User message
            document_content: Current document content for context
            history: Previous conversation history
            stream: Whether to stream (ignored, use stream_chat instead)
            max_tokens: Maximum response tokens
            temperature: Sampling temperature

        Returns:
            Dict with response and optional artifacts
        """
        try:
            messages = self._build_messages(message, document_content, history)

            response = self.llm_client.complete(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            if not response:
                return {
                    "response": "Es tut mir leid, ich konnte keine Antwort generieren.",
                    "artifacts": []
                }

            # Extract any code artifacts from response
            artifacts = self._extract_artifacts(response)

            return {
                "response": response,
                "artifacts": artifacts
            }

        except Exception as e:
            logger.error(f"[AIChatService] Error in chat: {e}")
            return {
                "response": f"Ein Fehler ist aufgetreten: {str(e)}",
                "artifacts": [],
                "error": str(e)
            }

    def stream_chat(
        self,
        message: str,
        document_content: str = "",
        history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Process a chat message with streaming response.

        Args:
            message: User message
            document_content: Current document content
            history: Conversation history
            max_tokens: Maximum response tokens
            temperature: Sampling temperature

        Yields:
            Dict with delta text and done status
        """
        try:
            messages = self._build_messages(message, document_content, history)

            full_response = ""
            for delta in self.llm_client.stream_complete(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                full_response += delta
                yield {
                    "delta": delta,
                    "done": False
                }

            # Final message with artifacts
            artifacts = self._extract_artifacts(full_response)
            yield {
                "delta": "",
                "done": True,
                "artifacts": artifacts,
                "full_response": full_response
            }

        except Exception as e:
            logger.error(f"[AIChatService] Error in stream_chat: {e}")
            yield {
                "delta": "",
                "done": True,
                "error": str(e)
            }

    def execute_command(
        self,
        command: str,
        args: str = "",
        selected_text: str = "",
        document_content: str = ""
    ) -> Dict[str, Any]:
        """
        Execute an @-command.

        Args:
            command: Command name (e.g., 'rewrite', 'expand', 'cite')
            args: Command arguments
            selected_text: Currently selected text
            document_content: Full document content

        Returns:
            Dict with command result
        """
        try:
            # Build appropriate prompt based on command
            if command == 'ai':
                # Free-form AI prompt
                prompt = args
            elif command == 'rewrite':
                prompt = f"Formuliere folgenden Text wissenschaftlich um: {selected_text}"
            elif command == 'expand':
                prompt = f"Erweitere folgenden Text mit mehr Details: {selected_text}"
            elif command == 'summarize':
                prompt = f"Fasse folgenden Text zusammen: {selected_text}"
            elif command == 'fix':
                prompt = f"Korrigiere LaTeX/Grammatik-Fehler in: {selected_text}"
            elif command == 'translate':
                lang = args or 'en'
                prompt = f"Übersetze ins {lang}: {selected_text}"
            else:
                prompt = f"@{command} {args}: {selected_text}"

            return self.chat(
                message=prompt,
                document_content=document_content[:2000]
            )

        except Exception as e:
            logger.error(f"[AIChatService] Error executing command: {e}")
            return {"response": "", "error": str(e)}

    def _build_messages(
        self,
        message: str,
        document_content: str,
        history: Optional[List[Dict[str, str]]]
    ) -> List[Dict[str, str]]:
        """
        Build message list for LLM.

        Args:
            message: Current user message
            document_content: Document content
            history: Conversation history

        Returns:
            List of message dicts
        """
        messages = [
            {"role": "system", "content": CHAT_SYSTEM_PROMPT}
        ]

        # Add conversation history (limited)
        if history:
            for msg in history[-self.MAX_HISTORY_MESSAGES:]:
                if msg.get('role') in ['user', 'assistant']:
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })

        # Add current message with document context
        if document_content:
            # Truncate document if too long
            truncated_content = document_content[:self.MAX_DOCUMENT_TOKENS]
            if len(document_content) > self.MAX_DOCUMENT_TOKENS:
                truncated_content += "\n[... Dokument gekürzt ...]"

            user_message = CHAT_USER_PROMPT_WITH_CONTEXT.format(
                document_content=truncated_content,
                message=message
            )
        else:
            user_message = message

        messages.append({
            "role": "user",
            "content": user_message
        })

        return messages

    def _extract_artifacts(self, response: str) -> List[Dict[str, Any]]:
        """
        Extract code artifacts from response.

        Args:
            response: Full LLM response

        Returns:
            List of artifact dicts
        """
        artifacts = []

        # Find code blocks
        import re
        code_pattern = r'```(\w*)\n(.*?)```'
        matches = re.findall(code_pattern, response, re.DOTALL)

        for i, (language, code) in enumerate(matches):
            artifacts.append({
                "id": f"artifact_{i}",
                "type": "code",
                "language": language or "text",
                "content": code.strip(),
                "insertable": True
            })

        return artifacts


# Singleton instance
_chat_service: Optional[AIChatService] = None


def get_chat_service() -> AIChatService:
    """Get or create singleton AIChatService instance."""
    global _chat_service
    if _chat_service is None:
        _chat_service = AIChatService()
    return _chat_service
