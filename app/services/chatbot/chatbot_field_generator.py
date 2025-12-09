"""
Chatbot Field Generator Service.

Handles automatic generation of chatbot fields using LLM.
Responsible for:
- Generating chatbot names
- Generating display names
- Creating system prompts
- Creating welcome messages
- Generating descriptions
"""

import logging
import os
import re
from typing import Dict, Any, Optional, Iterable

from openai import OpenAI

from db.tables import Chatbot, RAGCollection, CollectionDocumentLink

logger = logging.getLogger(__name__)


class ChatbotFieldGenerator:
    """Handles LLM-based field generation for chatbots."""

    # LLM settings for field generation
    DEFAULT_MODEL = "mistralai/Mistral-Small-3.2-24B-Instruct-2506"

    # Field generation prompts
    PROMPTS = {
        'name': {
            'system': "Du bist ein Experte für das Benennen von Chatbots. Generiere einen kurzen, prägnanten internen Namen (nur Kleinbuchstaben, Unterstriche erlaubt, keine Leerzeichen).",
            'user_template': "Generiere einen internen Namen für einen Chatbot basierend auf:\n- URL: {url}\n- {collection_info}\n\nAntworte NUR mit dem Namen, ohne Erklärung."
        },
        'display_name': {
            'system': "Du bist ein Experte für Chatbot-Branding. Generiere einen ansprechenden Anzeigenamen für einen Chatbot.",
            'user_template': "Generiere einen freundlichen Anzeigenamen für einen Chatbot basierend auf:\n- URL: {url}\n- {collection_info}\n\nAntworte NUR mit dem Namen, ohne Erklärung."
        },
        'system_prompt': {
            'system': "Du bist ein Experte für das Erstellen von System-Prompts für Chatbots. Erstelle einen professionellen System-Prompt.",
            'user_template': """Erstelle einen System-Prompt für einen Chatbot mit folgenden Eigenschaften:
- Basiert auf Inhalten von: {url}
- {collection_info}
- Soll hilfreich und präzise antworten
- Soll bei Unsicherheit ehrlich sagen, wenn er keine Antwort weiß

Der Prompt sollte 2-3 Absätze lang sein und die Persönlichkeit des Bots definieren."""
        },
        'welcome_message': {
            'system': "Du bist ein Experte für Chatbot-Kommunikation. Erstelle eine einladende Willkommensnachricht.",
            'user_template': """Erstelle eine Willkommensnachricht für einen Chatbot mit:
- Basiert auf: {url}
- {collection_info}

Die Nachricht sollte freundlich sein und den Nutzer einladen, Fragen zu stellen. Max 2-3 Sätze."""
        },
        'description': {
            'system': "Du bist ein Experte für Produktbeschreibungen. Erstelle eine kurze Beschreibung für einen Chatbot.",
            'user_template': "Erstelle eine kurze Beschreibung (1-2 Sätze) für einen Chatbot basierend auf:\n- URL: {url}\n- {collection_info}"
        }
    }

    @staticmethod
    def generate_field(chatbot_id: int, field: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a field value using LLM based on the chatbot's context.

        Args:
            chatbot_id: The chatbot ID
            field: The field to generate (name, display_name, system_prompt, welcome_message, description)
            context: Optional additional context

        Returns:
            Dict with generated value

        Raises:
            ValueError: If chatbot not found or unknown field
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            raise ValueError('Chatbot not found')

        if field not in ChatbotFieldGenerator.PROMPTS:
            raise ValueError(f'Unknown field: {field}')

        # Get collection info for context
        collection_info = ChatbotFieldGenerator._get_collection_context(chatbot)

        # Build prompt
        prompt_config = ChatbotFieldGenerator.PROMPTS[field]
        user_prompt = prompt_config['user_template'].format(
            url=chatbot.source_url or 'N/A',
            collection_info=collection_info
        )

        try:
            # Generate using LLM
            generated_value = ChatbotFieldGenerator._generate_with_llm(
                system_prompt=prompt_config['system'],
                user_prompt=user_prompt
            )

            # Clean up the value based on field type
            if field == 'name':
                generated_value = ChatbotFieldGenerator._clean_name(generated_value)

            logger.info(f"[ChatbotFieldGenerator] Generated {field} for chatbot {chatbot_id}")

            return {
                'success': True,
                'field': field,
                'value': generated_value
            }

        except Exception as e:
            logger.error(f"[ChatbotFieldGenerator] Field generation error: {e}")
            raise

    @staticmethod
    def _get_collection_context(chatbot: Chatbot) -> str:
        """
        Get context information from the chatbot's collection.

        Args:
            chatbot: The chatbot instance

        Returns:
            String with collection context
        """
        if not chatbot.primary_collection_id:
            return "Noch keine Dokumente vorhanden"

        collection = RAGCollection.query.get(chatbot.primary_collection_id)
        if not collection:
            return "Noch keine Dokumente vorhanden"

        # Get sample documents
        links = CollectionDocumentLink.query.filter_by(
            collection_id=collection.id
        ).limit(5).all()

        if not links:
            return "Noch keine Dokumente vorhanden"

        doc_titles = [
            link.document.title or link.document.filename
            for link in links if link.document
        ]

        return f"Die Wissensbasis enthält Dokumente wie: {', '.join(doc_titles)}"

    @staticmethod
    def _generate_with_llm(system_prompt: str, user_prompt: str) -> str:
        """
        Generate text using LLM.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt

        Returns:
            Generated text

        Raises:
            Exception: If LLM request fails
        """
        # Use LiteLLM endpoint
        client = OpenAI(
            base_url=os.environ.get('LITELLM_BASE_URL', 'https://kiz1.in.ohmportal.de/llmproxy/v1'),
            api_key=os.environ.get('LITELLM_API_KEY', 'dummy')
        )

        response = client.chat.completions.create(
            model=ChatbotFieldGenerator.DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content.strip()

    @staticmethod
    def stream_field_generation(chatbot_id: int, field: str, context: Optional[str] = None) -> Iterable[Dict[str, Any]]:
        """
        Stream generation for a field as SSE-friendly dicts.

        Yields:
            {"delta": "..."} for incremental tokens and a final {"done": True, "value": "..."}.
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            raise ValueError('Chatbot not found')

        if field not in ChatbotFieldGenerator.PROMPTS:
            raise ValueError(f'Unknown field: {field}')

        collection_info = ChatbotFieldGenerator._get_collection_context(chatbot)
        prompt_config = ChatbotFieldGenerator.PROMPTS[field]
        user_prompt = prompt_config['user_template'].format(
            url=chatbot.source_url or 'N/A',
            collection_info=collection_info
        )

        # Use LiteLLM endpoint in streaming mode
        client = OpenAI(
            base_url=os.environ.get('LITELLM_BASE_URL', 'https://kiz1.in.ohmportal.de/llmproxy/v1'),
            api_key=os.environ.get('LITELLM_API_KEY', 'dummy')
        )

        stream = client.chat.completions.create(
            model=ChatbotFieldGenerator.DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": prompt_config['system']},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500,
            stream=True
        )

        accumulated = ""
        for chunk in stream:
            content = chunk.choices[0].delta.content
            delta = ""
            if isinstance(content, list):
                delta = "".join([
                    getattr(part, 'text', '') if hasattr(part, 'text') else str(part)
                    for part in content
                ])
            elif isinstance(content, str):
                delta = content

            if not delta:
                continue

            accumulated += delta
            yield {"delta": delta}

        # Final clean-up for name field
        final_value = accumulated
        if field == 'name':
            final_value = ChatbotFieldGenerator._clean_name(final_value)

        yield {"done": True, "value": final_value}

    @staticmethod
    def _clean_name(name: str) -> str:
        """
        Clean and validate a generated name.

        Args:
            name: Raw generated name

        Returns:
            Cleaned name (lowercase, underscores only, max 50 chars)
        """
        # Ensure valid name format
        cleaned = re.sub(r'[^a-z0-9_]', '_', name.lower())
        cleaned = cleaned[:50]  # Limit length
        return cleaned
