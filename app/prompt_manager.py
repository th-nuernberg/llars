import json
import os
import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Message:
    role: str
    content: str

    def to_text(self) -> str:
        return f"[{self.role}]: {self.content}"

    def token_estimate(self) -> int:
        # Grobe Abschätzung: 4 Zeichen ≈ 1 Token
        return len(self.content) // 4 + 5  # +5 für Role und Formatierung


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
        """Lädt den System Prompt aus einer Datei."""
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
        """Liefert den Standard-System-Prompt zurück (identisch mit system_prompt.txt)."""
        return """# LLM-Rollendefinition
[... System Prompt Inhalt wie in der Datei ...]"""

    def _format_chat_history(self, messages: List[Message], rag_context: str = "") -> Tuple[str, bool]:
        """
        Formatiert die Chat-Historie und stellt sicher, dass sie in das Kontextfenster passt.
        Die aktuelle Nachricht wird bereits in der Historie enthalten sein.

        Args:
            messages: Liste der Chat-Nachrichten
            rag_context: Zusätzlicher Kontext aus der RAG-Pipeline

        Returns:
            Tuple aus formatiertem Text und Boolean ob Nachrichten gekürzt wurden
        """
        # Schätze Tokens für System Prompt und RAG Kontext
        system_tokens = len(self.system_prompt) // 4
        rag_tokens = len(rag_context) // 4
        format_tokens = 100  # Schätzung für Formatierungstokens
        base_tokens = system_tokens + rag_tokens + format_tokens

        # Verfügbare Tokens für Chat-Historie
        available_history_tokens = self.available_context_tokens - base_tokens

        # Formatiere Nachrichten, beginnend mit den neuesten
        formatted_messages = []
        current_tokens = 0
        messages_truncated = False

        for msg in messages[:-1]:  # Alle Nachrichten außer der letzten (aktuellen) Nachricht
            msg_tokens = msg.token_estimate()
            if current_tokens + msg_tokens > available_history_tokens:
                messages_truncated = True
                break
            formatted_messages.append(msg.to_text())
            current_tokens += msg_tokens

        chat_history = "\n".join(formatted_messages)

        return chat_history, messages_truncated

    def create_prompt(self,
                     current_message: str,
                     chat_history: List[Dict[str, str]] = None,
                     rag_context: str = "") -> str:
        """
        Erstellt das vollständige Prompt für das Modell.
        Die aktuelle Nachricht wird nur einmal am Ende eingefügt.
        """
        # Konvertiere Chat-Historie in Message-Objekte
        messages = []
        if chat_history:
            for msg in chat_history:
                messages.append(Message(
                    role=msg.get('role', 'unknown'),
                    content=msg.get('content', '')
                ))

        # Füge aktuelle Nachricht zur Historie hinzu
        messages.append(Message(role="user", content=current_message))

        # Formatiere Chat-Historie
        formatted_history, truncated = self._format_chat_history(messages, rag_context)

        if truncated:
            logging.info("Chat history was truncated to fit context window")

        # Baue finales Prompt mit nur einmaliger Erwähnung der aktuellen Nachricht
        prompt_parts = [
            f"<s>[INST]",
            self.system_prompt,
            f"\nBasierend auf der Anfrage wurden folgende relevante Informationen aus der Wissensdatenbank gefunden. Bitte berücksichtige diese Informationen in deiner Antwort, aber antworte natürlich und fließend, ohne den Kontext direkt zu zitieren: Relevante Informationen:\n{rag_context}" if rag_context else "",
            f"\nVorheriger Chatverlauf:\n{formatted_history}" if formatted_history else "",
            f"\n[/INST]",
            f"{current_message}",
            f"[/INST]"
        ]

        return "".join(prompt_parts)