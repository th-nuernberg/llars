"""
Persona Formatter

Handles formatting of persona data for prompts and display.
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class PersonaFormatter:
    """Formats persona data for various use cases."""

    @staticmethod
    def format(persona: Optional[Dict[str, Any]]) -> str:
        """
        Format a persona dict into a readable markdown string.

        Args:
            persona: Persona dictionary with name and properties

        Returns:
            Formatted markdown string
        """
        if not persona or not isinstance(persona, dict):
            return ""

        formatter = PersonaFormatter()
        return formatter._build_persona_output(persona)

    def _build_persona_output(self, persona: Dict[str, Any]) -> str:
        """Build the complete persona output string."""
        output = f"## Persona: {persona.get('name', 'Unknown')}\n\n"
        properties = persona.get('properties', {})

        # Add each section if present
        output += self._format_steckbrief(properties)
        output += self._format_hauptanliegen(properties)
        output += self._format_optional_sections(properties)
        output += self._format_emotionale_merkmale(properties, persona.get('name', 'der Persona'))
        output += self._format_ressourcen(properties)
        output += self._format_soziales_umfeld(properties)
        output += self._format_prinzipien(properties)

        return output

    def _format_steckbrief(self, properties: Dict[str, Any]) -> str:
        """Format the Steckbrief section."""
        if 'Steckbrief' not in properties or not properties['Steckbrief']:
            return ""

        steckbrief = properties['Steckbrief']
        if not isinstance(steckbrief, dict):
            logger.warning(f"Steckbrief is not a dict but {type(steckbrief)}")
            return ""

        output = "**Steckbrief:**\n"
        for key, value in steckbrief.items():
            output += f"- **{key}**: {value}\n"
        return output + "\n"

    def _format_hauptanliegen(self, properties: Dict[str, Any]) -> str:
        """Format the Hauptanliegen section."""
        if 'Hauptanliegen' not in properties or not properties['Hauptanliegen']:
            return ""

        hauptanliegen = properties['Hauptanliegen']
        bullets = hauptanliegen.replace('. ', '.\n- ')
        return f"**Hauptanliegen**\n- {bullets}\n\n"

    def _format_optional_sections(self, properties: Dict[str, Any]) -> str:
        """Format optional sections like Nebenanliegen and Sprachliche Merkmale."""
        output = ""
        sections = {
            'Nebenanliegen': 'Nebenanliegen',
            'Sprachliche Merkmale': 'Sprachliche Merkmale'
        }

        for key, title in sections.items():
            if key in properties and properties[key]:
                output += f"**{title}**\n"
                items = properties[key] if isinstance(properties[key], list) else [properties[key]]
                for item in items:
                    output += f"- {item}\n"
                output += "\n"

        return output

    def _format_emotionale_merkmale(
        self,
        properties: Dict[str, Any],
        persona_name: str
    ) -> str:
        """Format the Emotionale Merkmale section."""
        if 'Emotionale Merkmale' not in properties or not properties['Emotionale Merkmale']:
            return ""

        emotionale = properties['Emotionale Merkmale']
        output = "**Emotionale Merkmale:**\n"

        # Grundhaltung
        if 'Grundhaltung' in emotionale:
            output += f"- **Emotionale Grundhaltung zu Beginn des Gesprächs**: {emotionale['Grundhaltung']}.\n"

        # Ausgeprägte Emotionen
        if 'ausgepraegte Emotionen' in emotionale:
            output += f"- **Ausgeprägte Emotionen** bei {persona_name}:\n"
            for emotion in emotionale['ausgepraegte Emotionen']:
                output += f"- {emotion}\n"

        # Emotion Details
        output += self._format_emotion_details(emotionale.get('details'), persona_name)

        return output + "\n"

    def _format_emotion_details(
        self,
        details: Optional[Dict[str, Any]],
        persona_name: str
    ) -> str:
        """Format emotion details with triggers and reactions."""
        if not details:
            return ""

        if not isinstance(details, dict):
            logger.warning(f"Emotion details is not a dict but {type(details)}")
            return ""

        output = ""
        for emotion, emotion_details in details.items():
            if not isinstance(emotion_details, dict):
                continue
            if 'ausloeser' not in emotion_details or 'reaktion' not in emotion_details:
                continue

            output += f"  - **{emotion}**:\n"
            ausloeser = emotion_details.get('ausloeser', 'n/a')
            reaktion = emotion_details.get('reaktion', '')
            output += (
                f"    - Die Emotion {emotion} wird bei {persona_name} "
                f"durch {ausloeser} ausgelöst und löst folgende Reaktion aus: {reaktion}. "
            )

            if 'beispielsausloeser' in emotion_details:
                output += (
                    f"-Beispielnachrichten des Beraters (mögliche Auslöser für diese Emotion) "
                    f"{emotion}:>\"{emotion_details['beispielsausloeser']}\".\n"
                )

            if 'beispielsreaktion' in emotion_details:
                output += f"-Beispielsreaktion der Persona für {emotion}:>\"{emotion_details['beispielsreaktion']}\".\n"
            else:
                output += "\n"

        return output

    def _format_ressourcen(self, properties: Dict[str, Any]) -> str:
        """Format the Ressourcen section."""
        if 'Ressourcen' not in properties or not properties['Ressourcen']:
            return ""

        ressourcen = properties['Ressourcen']
        output = "**Folgende Ressourcen stehen der Persona zur Verfügung:**\n"
        output += f"- Emotional (Fähigkeit, mit Gefühlen und Stress umzugehen): {'Ja' if ressourcen.get('emotional') else 'Nein'}\n"
        output += f"- Sozial (Unterstützung durch Familie, Freunde, Netzwerke): {'Ja' if ressourcen.get('sozial') else 'Nein'}\n"
        output += f"- Finanziell (Verfügbarkeit von Geld oder materiellen Mitteln): {'Ja' if ressourcen.get('finanziell') else 'Nein'}\n"

        andere_text = "Ja" if ressourcen.get('andere') else "Nein"
        if ressourcen.get('andere') and ressourcen.get('andereDetails'):
            andere_text += f" ({ressourcen['andereDetails']})"
        output += f"- Andere: {andere_text}\n\n"

        return output

    def _format_soziales_umfeld(self, properties: Dict[str, Any]) -> str:
        """Format the Soziales Umfeld section."""
        if 'Soziales Umfeld' not in properties or not properties['Soziales Umfeld']:
            return ""

        output = "**Soziales Umfeld**\n"
        soziales_umfeld = properties['Soziales Umfeld']

        if isinstance(soziales_umfeld, str):
            for item in soziales_umfeld.split(', '):
                output += f"- {item.strip()}\n"
        elif isinstance(soziales_umfeld, list):
            for item in soziales_umfeld:
                output += f"- {item}\n"

        return output

    def _format_prinzipien(self, properties: Dict[str, Any]) -> str:
        """Format the Konversationsprinzipien section."""
        if 'Prinzipien' not in properties or not properties['Prinzipien']:
            return ""

        output = "**Konversationsprinzipien**\n"
        prinzipien = (
            properties['Prinzipien']
            if isinstance(properties['Prinzipien'], list)
            else [properties['Prinzipien']]
        )

        for prinzip in prinzipien:
            formatted_prinzip = prinzip.strip().replace('.', '.\n  - ')
            output += f"- {formatted_prinzip}\n"

        return output

    @staticmethod
    def get_persona_summary(persona: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get a summary of persona for counselor suggestion prompts.

        Args:
            persona: Persona dictionary

        Returns:
            Dict with key persona information
        """
        if not persona or not isinstance(persona, dict):
            return {}

        summary = {}
        properties = persona.get('properties', {})

        if 'Hauptanliegen' in properties:
            summary['hauptanliegen'] = properties['Hauptanliegen']

        if 'Nebenanliegen' in properties and properties['Nebenanliegen']:
            summary['nebenanliegen'] = properties['Nebenanliegen']

        if 'Steckbrief' in properties:
            summary['steckbrief'] = properties['Steckbrief']

        return summary
