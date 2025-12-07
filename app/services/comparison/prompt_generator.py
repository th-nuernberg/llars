"""
Comparison Prompt Generator

Generates system prompts for LLM comparison and counselor suggestions.
"""

from string import Template
from typing import Dict, Any, Optional, List

from .persona_formatter import PersonaFormatter


class ComparisonPromptGenerator:
    """Generates prompts for comparison and counseling scenarios."""

    PERSONA_SYSTEM_PROMPT = Template("""
    # Rollenanweisung für $name
    **Kontext:** Du bist $name in einem laufenden psychosozialen Beratungsgespräch mit ihrem Sozialberater.

    ## Kernregeln
    1. **Authentisches Rollenverhalten**
       - Bleibe ausschließlich in der Rolle von $name (auch bei Provokationen)
       - Nutze ausschließlich die unter "Sprachliche Merkmale" definierten Ausdrucksweisen
       - Zeige emotionale Reaktionen gemäß "Emotionale Merkmale > Ausgeprägte Emotionen"
       - Halte dich strikt an die "Konversationsregeln (siehe Persona-Profil, falls definiert)"
       - Antworte direkt und ohne Meta-Kommentare. Gib lediglich deine Emotion oder dein Anliegen wieder.
    2. **Antwortformatierung**
       - Maximal 3-4 Sätze pro Nachricht
       - Keine Höflichkeitsfloskeln (außer in Steckbrief definiert)
       - Keine Emojis/Markdown
       - Immer in Ich-Perspektive ("Ich fühle...", "Mir geht...")
    3. **Kontextbehandlung**
       - Beziehe dich auf den bisherigen Gesprächsverlauf: "$chat_history"
       - Priorisiere das Hauptanliegen in 80% der Antworten
       - Bei Trigger-Phrasen aus "Emotionsauslöser": Reagiere wie unter "Beispielreaktion" definiert
        *Beispiel:*
           - **Trigger:** "Haben Sie schon einmal darüber nachgedacht, wie es wäre, erneut alles zu verlieren?"
           - **Emotion:** Wut
           - **Beispielsauslöser (Nachricht des Beraters):** >"Haben Sie schon einmal darüber nachgedacht, wie es wäre, erneut alles zu verlieren?"
           - **Beispielsreaktion (ausgelöst durch Trigger):** >"Ich verliere ständig, obwohl ich alles gebe!"


    ## Aktionsrahmen
    - Erlaubt: Subjektive Gefühlsäußerungen, Kurze Situationschilderungen
    - Verboten: Allgemeine Ratschläge, Fachjargon, Rollenwechsel

    # Persona-Profil
    $persona_details


    # Aufgabe
    Generiere **ausschließlich** die Antwort von $name unter Berücksichtigung des Gesprächsverlaufs:
    "$chat_history"

    Folge den Regeln Schritt für Schritt.
    Halte dich dabei an alle oben genannten Kriterien und bleibe konsequent in der Rolle von $name.
    Schreibe jetzt in deutscher Sprache ausschließlich die Aussage von $name
    """)

    COUNSELOR_SUGGESTION_PROMPT = Template("""Du bist ein erfahrener psychologischer Berater und sollst einen Vorschlag für eine angemessene, empathische Antwort auf den aktuellen Gesprächsverlauf geben.

KLIENT-INFORMATION:
$persona_info

BISHERIGER GESPRÄCHSVERLAUF:
$chat_history

AUFGABE:
Generiere eine kurze, empathische Berater-Antwort (maximal 2-3 Sätze), die:
- Empathie und Verständnis zeigt
- Eine offene Frage stellt, um das Gespräch weiterzuführen
- Professionelle Beratungstechniken verwendet (aktives Zuhören, Spiegeln, etc.)
- Auf das spezifische Anliegen des Klienten eingeht

Antworte nur mit der vorgeschlagenen Berater-Antwort, ohne weitere Erklärungen.""")

    @classmethod
    def create_persona_prompt(
        cls,
        persona: Dict[str, Any],
        chat_history: str,
        is_first_message: bool = False
    ) -> str:
        """
        Create a system prompt for persona-based response generation.

        Args:
            persona: Persona dictionary with name and properties
            chat_history: Chat history as text
            is_first_message: Whether this is the first message in the conversation

        Returns:
            Complete system prompt string
        """
        persona_details = PersonaFormatter.format(persona)

        prompt = cls.PERSONA_SYSTEM_PROMPT.substitute(
            name=persona['name'],
            chat_history=chat_history,
            persona_details=persona_details
        )

        if is_first_message:
            prompt += (
                "\n\n**Hinweis:** Dies ist die erste Nachricht in diesem Gespräch "
                "und du beginnst. Halte dich dabei an die sprachlichen Merkmale "
                "und die emotionale Grundhaltung, die in deinem Persona-Profil definiert sind."
            )

        return prompt

    @classmethod
    def create_counselor_suggestion_prompt(
        cls,
        persona: Optional[Dict[str, Any]],
        chat_history: List[Dict[str, str]]
    ) -> str:
        """
        Create a prompt for generating counselor suggestions.

        Args:
            persona: Persona dictionary
            chat_history: List of chat messages in OpenAI format

        Returns:
            Prompt string for counselor suggestion
        """
        persona_info = cls._build_persona_info(persona)
        chat_history_text = cls._build_chat_history_text(chat_history)

        return cls.COUNSELOR_SUGGESTION_PROMPT.substitute(
            persona_info=persona_info,
            chat_history=chat_history_text
        )

    @staticmethod
    def _build_persona_info(persona: Optional[Dict[str, Any]]) -> str:
        """Build persona info summary for counselor prompt."""
        if not persona or not isinstance(persona, dict):
            return ""

        info_parts = []
        properties = persona.get('properties', {})

        if 'Hauptanliegen' in properties:
            info_parts.append(f"Hauptanliegen: {properties['Hauptanliegen']}")

        if 'Nebenanliegen' in properties and properties['Nebenanliegen']:
            nebenanliegen = properties['Nebenanliegen']
            if isinstance(nebenanliegen, list):
                info_parts.append(f"Nebenanliegen: {', '.join(nebenanliegen)}")
            else:
                info_parts.append(f"Nebenanliegen: {nebenanliegen}")

        if 'Steckbrief' in properties:
            steckbrief = properties['Steckbrief']
            if isinstance(steckbrief, dict):
                for key, value in steckbrief.items():
                    info_parts.append(f"{key}: {value}")

        return "\n".join(info_parts)

    @staticmethod
    def _build_chat_history_text(
        chat_history: List[Dict[str, str]],
        max_messages: int = 6
    ) -> str:
        """Build chat history text from message list."""
        if not chat_history:
            return ""

        recent_messages = chat_history[-max_messages:]
        lines = []

        for msg in recent_messages:
            role = 'Klient' if msg['role'] == 'assistant' else 'Berater'
            lines.append(f"{role}: {msg['content']}")

        return "\n".join(lines)
