# prompt_manager.py
import os
import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str

    def to_text(self) -> str:
        return f"{self.role}: {self.content}"

    def token_estimate(self) -> int:
        # Rough estimate: 4 characters ≈ 1 token
        return len(self.content) // 4 + 5  # +5 for role and formatting


class PromptManager:
    def __init__(self,
                 system_prompt_path: str = "/app/prompts/system_prompt.txt",
                 max_context_tokens: int = 16384,
                 max_new_tokens: int = 1000):
        self.system_prompt_path = system_prompt_path
        self.max_context_tokens = max_context_tokens
        self.max_new_tokens = max_new_tokens
        self.available_context_tokens = max_context_tokens - max_new_tokens
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Loads the system prompt from a file."""
        try:
            if not os.path.exists(self.system_prompt_path):
                logging.warning(f"System prompt file not found at {self.system_prompt_path}, using default prompt")
                return self._get_default_system_prompt()

            with open(self.system_prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logging.error(f"Error loading system prompt: {e}")
            return self._get_default_system_prompt()

    def _get_default_system_prompt(self) -> str:
        """Returns the default system prompt."""
        return """# LLM-Rollendefinition
[... Default System Prompt Content ...]"""

    def _format_chat_history(self, messages: List[Message]) -> Tuple[str, bool]:
        """
        Formats the chat history and ensures it fits within the context window.

        Args:
            messages: List of chat messages

        Returns:
            Tuple of formatted text and Boolean indicating if messages were truncated
        """
        # Estimate tokens for System Prompt
        system_tokens = len(self.system_prompt) // 4
        format_tokens = 100  # Estimate for formatting tokens
        base_tokens = system_tokens + format_tokens

        # Available tokens for chat history
        available_history_tokens = self.available_context_tokens - base_tokens

        # Format messages, starting from the latest
        formatted_messages = []
        current_tokens = 0
        messages_truncated = False

        for msg in reversed(messages):  # Start from the latest messages
            msg_tokens = msg.token_estimate()
            if current_tokens + msg_tokens > available_history_tokens:
                messages_truncated = True
                break
            formatted_messages.insert(0, msg.to_text())
            current_tokens += msg_tokens

        chat_history = "\n".join(formatted_messages)

        return chat_history, messages_truncated

    def create_prompt(self,
                      chat_history: List[Dict[str, str]] = None,
                      rag_context: str = "") -> str:
        """
        Creates the full prompt for the model.
        The chat history is included in the prompt.
        """
        # Convert chat history to Message objects
        messages = []
        if chat_history:
            for msg in chat_history:
                messages.append(Message(
                    role=msg.get('role', 'unknown'),
                    content=msg.get('content', '')
                ))

        # Format chat history
        formatted_history, truncated = self._format_chat_history(messages)

        if truncated:
            logging.info("Chat history was truncated to fit context window")

        # Replace placeholders in system prompt
        enriched_system_prompt = self.system_prompt.replace('###RAGPIPELINEKONTEXT###', rag_context)
        enriched_system_prompt = enriched_system_prompt.replace('###CHATVERLAUF###', formatted_history)

        # Build the instruction
        instruction = enriched_system_prompt

        # Build the prompt according to the model's expected format
        prompt = f"<s>[INST]\n{instruction}\n[/INST]"

        return prompt
