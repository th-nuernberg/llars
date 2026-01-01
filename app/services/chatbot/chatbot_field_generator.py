"""
Chatbot Field Generator Service.

Handles automatic generation of chatbot fields using LLM.
Responsible for:
- Generating chatbot names
- Generating display names
- Creating system prompts
- Creating welcome messages
- Generating descriptions
- Selecting appropriate icons (constrained decoding)
"""

import logging
import os
import re
import json
from typing import Dict, Any, Optional, Iterable, List

from openai import OpenAI
from llm.openai_utils import extract_delta_text, extract_message_text

from db.tables import Chatbot, RAGCollection, CollectionDocumentLink
from db.models.llm_model import LLMModel

logger = logging.getLogger(__name__)


# Curated list of MDI icons suitable for chatbots, organized by category
CHATBOT_ICONS = {
    # General/Default
    'general': [
        'mdi-robot', 'mdi-robot-outline', 'mdi-chat', 'mdi-chat-outline',
        'mdi-message', 'mdi-message-outline', 'mdi-forum', 'mdi-forum-outline',
        'mdi-comment', 'mdi-comment-outline', 'mdi-assistant',
    ],
    # Business/Corporate
    'business': [
        'mdi-briefcase', 'mdi-briefcase-outline', 'mdi-domain', 'mdi-office-building',
        'mdi-store', 'mdi-storefront', 'mdi-handshake', 'mdi-account-tie',
        'mdi-cash', 'mdi-currency-eur', 'mdi-chart-line', 'mdi-chart-bar',
    ],
    # Education/Learning
    'education': [
        'mdi-school', 'mdi-book-open', 'mdi-book', 'mdi-bookshelf',
        'mdi-graduation-cap', 'mdi-pencil', 'mdi-lead-pencil', 'mdi-notebook',
        'mdi-library', 'mdi-brain', 'mdi-lightbulb', 'mdi-lightbulb-outline',
    ],
    # Health/Medical
    'health': [
        'mdi-hospital', 'mdi-medical-bag', 'mdi-pill', 'mdi-heart-pulse',
        'mdi-stethoscope', 'mdi-doctor', 'mdi-tooth', 'mdi-eye',
        'mdi-run', 'mdi-yoga', 'mdi-meditation', 'mdi-spa',
    ],
    # Technology
    'technology': [
        'mdi-laptop', 'mdi-desktop-classic', 'mdi-cellphone', 'mdi-tablet',
        'mdi-code-tags', 'mdi-cog', 'mdi-cogs', 'mdi-wrench',
        'mdi-database', 'mdi-server', 'mdi-cloud', 'mdi-chip',
    ],
    # Food/Restaurant
    'food': [
        'mdi-food', 'mdi-food-fork-drink', 'mdi-silverware-fork-knife',
        'mdi-pizza', 'mdi-hamburger', 'mdi-coffee', 'mdi-beer',
        'mdi-glass-wine', 'mdi-cupcake', 'mdi-ice-cream', 'mdi-noodles',
    ],
    # Travel/Transport
    'travel': [
        'mdi-airplane', 'mdi-car', 'mdi-bus', 'mdi-train',
        'mdi-taxi', 'mdi-bike', 'mdi-ship-wheel', 'mdi-map-marker',
        'mdi-earth', 'mdi-compass', 'mdi-hiking', 'mdi-beach',
    ],
    # Sports/Fitness
    'sports': [
        'mdi-dumbbell', 'mdi-weight-lifter', 'mdi-basketball', 'mdi-soccer',
        'mdi-tennis', 'mdi-golf', 'mdi-swim', 'mdi-bike',
        'mdi-run-fast', 'mdi-dance-ballroom', 'mdi-karate', 'mdi-yoga',
    ],
    # Entertainment/Media
    'entertainment': [
        'mdi-music', 'mdi-movie', 'mdi-gamepad', 'mdi-television',
        'mdi-camera', 'mdi-palette', 'mdi-brush', 'mdi-theater',
        'mdi-party-popper', 'mdi-guitar-acoustic', 'mdi-piano', 'mdi-microphone',
    ],
    # Legal/Government
    'legal': [
        'mdi-gavel', 'mdi-scale-balance', 'mdi-shield', 'mdi-account-group',
        'mdi-file-document', 'mdi-file-certificate', 'mdi-stamp',
        'mdi-bank', 'mdi-town-hall', 'mdi-badge-account',
    ],
    # Real Estate/Home
    'realestate': [
        'mdi-home', 'mdi-home-outline', 'mdi-home-city', 'mdi-office-building',
        'mdi-floor-plan', 'mdi-key', 'mdi-door', 'mdi-window-open',
        'mdi-sofa', 'mdi-bed', 'mdi-lamp', 'mdi-garage',
    ],
    # Nature/Environment
    'nature': [
        'mdi-tree', 'mdi-flower', 'mdi-leaf', 'mdi-pine-tree',
        'mdi-paw', 'mdi-dog', 'mdi-cat', 'mdi-bird',
        'mdi-fish', 'mdi-horse', 'mdi-duck', 'mdi-bee',
    ],
    # Finance/Banking
    'finance': [
        'mdi-bank', 'mdi-credit-card', 'mdi-wallet', 'mdi-cash-multiple',
        'mdi-piggy-bank', 'mdi-safe', 'mdi-calculator', 'mdi-receipt',
        'mdi-bitcoin', 'mdi-chart-areaspline', 'mdi-trending-up',
    ],
    # Support/Help
    'support': [
        'mdi-help-circle', 'mdi-help-circle-outline', 'mdi-information',
        'mdi-headset', 'mdi-phone', 'mdi-email', 'mdi-lifebuoy',
        'mdi-wrench', 'mdi-tools', 'mdi-comment-question',
    ],
}

# Flattened list of all icons for validation
ALL_CHATBOT_ICONS = [icon for icons in CHATBOT_ICONS.values() for icon in icons]


class ChatbotFieldGenerator:
    """Handles LLM-based field generation for chatbots."""

    # LLM settings for field generation
    DEFAULT_MODEL = None

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
            'system': """Du bist ein Experte für das Erstellen von System-Prompts für RAG-basierte Chatbots.

WICHTIGE REGELN:
1. Verwende NUR Informationen aus dem bereitgestellten Kontext (URL und Dokumentbeschreibungen)
2. Erfinde KEINE Details über die Organisation, die nicht im Kontext stehen
3. Halte den Prompt generisch genug, wenn spezifische Informationen fehlen
4. Der Chatbot hat Zugriff auf eine Wissensbasis und kann daraus zitieren

Erstelle einen professionellen, aber nicht übertriebenen System-Prompt.""",
            'user_template': """Erstelle einen System-Prompt für einen RAG-Chatbot basierend auf folgendem Kontext:

**Website:** {url}

**Verfügbare Wissensbasis:**
{collection_info}

**Anforderungen an den System-Prompt:**
1. Definiere die Rolle des Chatbots basierend auf den Dokumentthemen
2. Der Bot soll hilfreich und präzise antworten
3. Bei Unsicherheit ehrlich sagen, dass er die Antwort nicht weiß
4. Nutzer ermutigen, spezifische Fragen zu stellen
5. KEINE erfundenen Details über die Organisation

Der Prompt sollte 2-3 Absätze lang sein. Beginne mit "**System-Prompt:**" """
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
        },
        'icon': {
            'system': """Du bist ein präzises Icon-Auswahl-System. Deine Aufgabe ist es, basierend auf der Beschreibung das EINE passendste Icon auszuwählen.

REGELN:
1. Analysiere die URL und Dokumentbeschreibungen sorgfältig
2. Wähle ein Icon, das zur Branche/zum Thema passt
3. Antworte NUR mit dem Icon-Namen (z.B. mdi-school)
4. Keine Erklärung, keine Anführungszeichen, keine Satzzeichen""",
            'user_template': """Analysiere den folgenden Kontext und wähle das passendste Icon:

KONTEXT:
- Website: {url}
- Inhalt: {collection_info}

ICON-KATEGORIEN:
{icon_list}

BEISPIELE:
- Baufirma/Architektur → mdi-office-building oder mdi-domain
- Universität/Schule → mdi-school oder mdi-graduation-cap
- Arztpraxis/Gesundheit → mdi-hospital oder mdi-medical-bag
- Anwaltskanzlei → mdi-gavel oder mdi-scale-balance
- IT/Software → mdi-laptop oder mdi-code-tags
- Restaurant → mdi-food oder mdi-silverware-fork-knife

Welches Icon passt am besten? Antworte NUR mit dem Icon-Namen:"""
        },
        'color': {
            'system': """Du bist ein Experte für Branding und Farbauswahl.
Wähle eine passende Primärfarbe für einen Chatbot basierend auf der Branche/dem Thema.
Antworte NUR mit einem HEX-Farbcode (z.B. #3498db), ohne Erklärung.""",
            'user_template': """Wähle eine passende Primärfarbe für einen Chatbot basierend auf:
- URL: {url}
- {collection_info}

Berücksichtige die Branche und das Thema. Wähle eine professionelle, ansprechende Farbe.
Antworte NUR mit dem HEX-Farbcode (z.B. #3498db)."""
        }
    }

    # Common brand colors by industry for fallback
    INDUSTRY_COLORS = {
        'health': '#4CAF50',      # Green - health, wellness
        'finance': '#1976D2',     # Blue - trust, stability
        'technology': '#2196F3',  # Light blue - innovation
        'education': '#FF9800',   # Orange - energy, learning
        'legal': '#455A64',       # Dark blue-gray - professional
        'food': '#E91E63',        # Pink/Red - appetite
        'travel': '#00BCD4',      # Cyan - adventure
        'entertainment': '#9C27B0', # Purple - creativity
        'business': '#607D8B',    # Blue-gray - corporate
        'support': '#00ACC1',     # Teal - helpful
        'default': '#5C6BC0',     # Indigo - neutral
    }

    @staticmethod
    def generate_icon(chatbot_id: int, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate an appropriate icon for a chatbot using LLM with constrained output.

        Uses a curated list of MDI icons and asks the LLM to select the most appropriate one.

        Args:
            chatbot_id: The chatbot ID
            context: Optional additional context

        Returns:
            Dict with generated icon name
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            raise ValueError('Chatbot not found')

        collection_info = ChatbotFieldGenerator._get_collection_context(chatbot)

        # Add chatbot name to context if available for better understanding
        chatbot_name_context = ""
        if chatbot.display_name and chatbot.display_name != chatbot.name:
            chatbot_name_context = f"\n- Chatbot-Name: {chatbot.display_name}"
        elif chatbot.name:
            chatbot_name_context = f"\n- Chatbot-Name: {chatbot.name}"

        # Format icon list for the prompt - group by category for better context
        icon_list_parts = []
        for category, icons in CHATBOT_ICONS.items():
            icon_list_parts.append(f"[{category}]: {', '.join(icons)}")
        icon_list = '\n'.join(icon_list_parts)

        prompt_config = ChatbotFieldGenerator.PROMPTS['icon']
        user_prompt = prompt_config['user_template'].format(
            url=chatbot.source_url or 'N/A',
            collection_info=collection_info + chatbot_name_context,
            icon_list=icon_list
        )

        try:
            # Use lower temperature for more deterministic icon selection
            generated_icon = ChatbotFieldGenerator._generate_with_llm(
                system_prompt=prompt_config['system'],
                user_prompt=user_prompt,
                temperature=0.3
            )

            # Log raw response for debugging
            logger.info(f"[ChatbotFieldGenerator] Raw LLM icon response for chatbot {chatbot_id}: {repr(generated_icon)}")

            # Clean and validate the generated icon
            generated_icon = ChatbotFieldGenerator._clean_icon(generated_icon)

            logger.info(f"[ChatbotFieldGenerator] Generated icon for chatbot {chatbot_id}: {generated_icon}")

            return {
                'success': True,
                'field': 'icon',
                'value': generated_icon
            }

        except Exception as e:
            logger.error(f"[ChatbotFieldGenerator] Icon generation error: {e}")
            # Return default icon on error
            return {
                'success': True,
                'field': 'icon',
                'value': 'mdi-robot'
            }

    @staticmethod
    def _clean_icon(icon: str) -> str:
        """
        Clean and validate a generated icon name.

        Args:
            icon: Raw generated icon name

        Returns:
            Valid MDI icon name (defaults to mdi-robot if invalid)
        """
        if not icon:
            logger.warning("[ChatbotFieldGenerator] _clean_icon: empty input, returning mdi-robot")
            return 'mdi-robot'

        original = icon
        # Clean up: remove quotes, whitespace, punctuation, newlines
        icon = icon.strip().strip('"\'').strip()
        icon = icon.split('\n')[0].strip()  # Take first line only
        icon = icon.split()[0] if icon.split() else icon  # Take first word only
        icon = icon.rstrip('.,;:!?')  # Remove trailing punctuation
        icon = icon.lower()

        logger.debug(f"[ChatbotFieldGenerator] _clean_icon: after basic cleanup: {repr(icon)}")

        # Ensure it starts with mdi-
        if not icon.startswith('mdi-'):
            icon = 'mdi-' + icon

        logger.debug(f"[ChatbotFieldGenerator] _clean_icon: after mdi- prefix: {repr(icon)}")

        # Exact match
        if icon in ALL_CHATBOT_ICONS:
            logger.info(f"[ChatbotFieldGenerator] _clean_icon: exact match found: {icon}")
            return icon

        # Try without 'mdi-' prefix variations
        icon_base = icon.replace('mdi-', '')
        for valid_icon in ALL_CHATBOT_ICONS:
            valid_base = valid_icon.replace('mdi-', '')
            # Exact base match
            if icon_base == valid_base:
                logger.info(f"[ChatbotFieldGenerator] _clean_icon: base match found: {valid_icon}")
                return valid_icon
            # Contains match
            if icon_base in valid_base or valid_base in icon_base:
                logger.info(f"[ChatbotFieldGenerator] _clean_icon: partial match found: {valid_icon} (base: {icon_base})")
                return valid_icon

        # Fuzzy matching: find closest icon by common words
        icon_words = set(icon_base.replace('-', ' ').split())
        best_match = None
        best_score = 0
        for valid_icon in ALL_CHATBOT_ICONS:
            valid_words = set(valid_icon.replace('mdi-', '').replace('-', ' ').split())
            score = len(icon_words & valid_words)
            if score > best_score:
                best_score = score
                best_match = valid_icon

        if best_match and best_score > 0:
            logger.info(f"[ChatbotFieldGenerator] _clean_icon: fuzzy match found: {best_match} (score: {best_score})")
            return best_match

        logger.warning(f"[ChatbotFieldGenerator] _clean_icon: no match found for {repr(original)}, returning mdi-robot")
        return 'mdi-robot'

    @staticmethod
    def generate_color(chatbot_id: int, context: Optional[str] = None, force_llm: bool = False) -> Dict[str, Any]:
        """
        Generate an appropriate color for a chatbot.

        First checks if the collection has a brand_color from crawling (unless force_llm=True).
        Falls back to LLM generation if no brand color exists or force_llm is set.

        Args:
            chatbot_id: The chatbot ID
            context: Optional additional context
            force_llm: If True, skip crawled color and always use LLM generation

        Returns:
            Dict with generated color hex code
        """
        chatbot = Chatbot.query.get(chatbot_id)
        if not chatbot:
            raise ValueError('Chatbot not found')

        # Check for crawled brand color (unless force_llm is set)
        if not force_llm and chatbot.primary_collection_id:
            collection = RAGCollection.query.get(chatbot.primary_collection_id)
            if collection and collection.color:
                logger.info(f"[ChatbotFieldGenerator] Using brand color from collection: {collection.color}")
                return {
                    'success': True,
                    'field': 'color',
                    'value': collection.color,
                    'source': 'crawled'
                }

        # LLM generation (either as fallback or forced)
        collection_info = ChatbotFieldGenerator._get_collection_context(chatbot)

        prompt_config = ChatbotFieldGenerator.PROMPTS['color']
        user_prompt = prompt_config['user_template'].format(
            url=chatbot.source_url or 'N/A',
            collection_info=collection_info
        )

        try:
            generated_color = ChatbotFieldGenerator._generate_with_llm(
                system_prompt=prompt_config['system'],
                user_prompt=user_prompt
            )

            # Clean and validate the generated color
            generated_color = ChatbotFieldGenerator._clean_color(generated_color)

            logger.info(f"[ChatbotFieldGenerator] Generated color for chatbot {chatbot_id}: {generated_color}")

            return {
                'success': True,
                'field': 'color',
                'value': generated_color,
                'source': 'llm'
            }

        except Exception as e:
            logger.error(f"[ChatbotFieldGenerator] Color generation error: {e}")
            # Return default color on error
            return {
                'success': True,
                'field': 'color',
                'value': ChatbotFieldGenerator.INDUSTRY_COLORS['default'],
                'source': 'fallback'
            }

    @staticmethod
    def _clean_color(color: str) -> str:
        """
        Clean and validate a generated color hex code.

        Args:
            color: Raw generated color

        Returns:
            Valid hex color code (defaults to indigo if invalid)
        """
        if not color:
            return ChatbotFieldGenerator.INDUSTRY_COLORS['default']

        # Clean up: remove quotes, whitespace, etc.
        color = color.strip().strip('"\'').strip()

        # Extract hex code using regex
        hex_match = re.search(r'#?([0-9a-fA-F]{6})', color)
        if hex_match:
            return f'#{hex_match.group(1)}'

        # Try 3-digit hex
        hex_match = re.search(r'#?([0-9a-fA-F]{3})(?![0-9a-fA-F])', color)
        if hex_match:
            # Expand 3-digit to 6-digit
            short = hex_match.group(1)
            return f'#{short[0]*2}{short[1]*2}{short[2]*2}'

        return ChatbotFieldGenerator.INDUSTRY_COLORS['default']

    @staticmethod
    def _get_default_llm_model_id() -> str:
        model_id = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_LLM)
        if not model_id:
            raise ValueError("No default LLM model configured in llm_models")
        return model_id

    @staticmethod
    def generate_field(chatbot_id: int, field: str, context: Optional[str] = None, force_llm: bool = False) -> Dict[str, Any]:
        """
        Generate a field value using LLM based on the chatbot's context.

        Args:
            chatbot_id: The chatbot ID
            field: The field to generate (name, display_name, system_prompt, welcome_message, description)
            context: Optional additional context
            force_llm: If True, skip cached/crawled values and force LLM generation (applies to color)

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

        # Use specialized methods for icon and color
        if field == 'icon':
            return ChatbotFieldGenerator.generate_icon(chatbot_id, context)
        if field == 'color':
            return ChatbotFieldGenerator.generate_color(chatbot_id, context, force_llm=force_llm)

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
    def _get_collection_context(chatbot: Chatbot, max_docs: int = 10, include_descriptions: bool = True) -> str:
        """
        Get rich context information from the chatbot's collection.

        Includes document titles AND descriptions/content summaries to provide
        meaningful context for LLM-based field generation (especially system prompts).

        Args:
            chatbot: The chatbot instance
            max_docs: Maximum number of documents to include (default: 10)
            include_descriptions: Whether to include document descriptions (default: True)

        Returns:
            String with detailed collection context
        """
        if not chatbot.primary_collection_id:
            return "Noch keine Dokumente vorhanden"

        collection = RAGCollection.query.get(chatbot.primary_collection_id)
        if not collection:
            return "Noch keine Dokumente vorhanden"

        # Get sample documents with more context
        links = CollectionDocumentLink.query.filter_by(
            collection_id=collection.id
        ).limit(max_docs).all()

        if not links:
            return "Noch keine Dokumente vorhanden"

        # Build rich context with titles and descriptions
        context_parts = []
        seen_titles = set()  # Deduplicate similar titles

        for link in links:
            if not link.document:
                continue

            title = link.document.title or link.document.filename
            # Skip duplicate/very similar titles
            title_key = title[:50].lower()
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)

            if include_descriptions and link.document.description:
                # Truncate description to 200 chars for context
                desc = link.document.description[:200]
                if len(link.document.description) > 200:
                    desc += "..."
                context_parts.append(f"- \"{title}\": {desc}")
            else:
                context_parts.append(f"- \"{title}\"")

        if not context_parts:
            return "Noch keine Dokumente vorhanden"

        # Build summary
        doc_count = collection.document_count or len(links)
        summary = f"Die Wissensbasis enthält {doc_count} Dokumente. Beispiele:\n"
        summary += "\n".join(context_parts[:8])  # Limit to 8 for prompt length

        return summary

    @staticmethod
    def _generate_with_llm(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """
        Generate text using LLM.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            temperature: LLM temperature (0.0-1.0)

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
            model=ChatbotFieldGenerator._get_default_llm_model_id(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=500
        )

        text = extract_message_text(response.choices[0].message)
        return (text or "").strip()

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

        # For icon and color, use specialized non-streaming methods
        if field == 'icon':
            result = ChatbotFieldGenerator.generate_icon(chatbot_id, context)
            yield {"done": True, "value": result.get('value', 'mdi-robot')}
            return
        if field == 'color':
            result = ChatbotFieldGenerator.generate_color(chatbot_id, context)
            yield {"done": True, "value": result.get('value', '#5d7a4a')}
            return

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
            model=ChatbotFieldGenerator._get_default_llm_model_id(),
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
            delta = extract_delta_text(chunk.choices[0].delta)

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
