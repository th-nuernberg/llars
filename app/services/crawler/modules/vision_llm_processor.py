"""
Vision-LLM Processing Module

Handles intelligent data extraction from screenshots using Vision-capable LLMs.
Extracts structured business information from visual page content.
"""

import os
import re
import json
import logging
from typing import Dict, Optional

from llm.openai_utils import extract_message_text

logger = logging.getLogger(__name__)


class VisionLLMProcessor:
    """
    Uses Vision-LLM to extract structured data from screenshots.

    Responsibilities:
    - Configure Vision-LLM API client
    - Build extraction prompts
    - Process screenshots with Vision-LLM
    - Parse and validate JSON responses
    - Provide structured business data extraction
    """

    DEFAULT_MODEL = None
    DEFAULT_MAX_TOKENS = 1000
    DEFAULT_TEMPERATURE = 0.1

    EXTRACTION_PROMPT = """Analysiere diesen Screenshot einer Website und extrahiere folgende Informationen.
Antworte NUR im JSON-Format ohne zusätzlichen Text.

Extrahiere diese Felder (setze null wenn nicht gefunden):
{
    "company_name": "Vollständiger Firmenname",
    "owner": "Name des Inhabers oder Geschäftsführers",
    "email": "Kontakt E-Mail Adresse",
    "phone": "Telefonnummer",
    "address": "Vollständige Adresse",
    "vat_id": "USt-IdNr falls vorhanden",
    "website_purpose": "Kurze Beschreibung wofür die Website/Firma steht (max 2 Sätze)",
    "services": ["Liste der angebotenen Dienstleistungen/Produkte"],
    "team_members": ["Liste der Teammitglieder mit Namen und Rolle falls sichtbar"]
}

Wichtig:
- Extrahiere nur Informationen die KLAR SICHTBAR sind
- Für owner: Suche nach "Inhaber", "Geschäftsführer", "CEO" oder ähnlichen Bezeichnungen
- Ignoriere generische Platzhalter oder Lorem ipsum
- Antworte AUSSCHLIESSLICH mit validem JSON"""

    def __init__(
        self,
        model: str = None,
        litellm_base_url: Optional[str] = None,
        litellm_api_key: Optional[str] = None,
        max_tokens: int = None,
        temperature: float = None
    ):
        """
        Initialize the Vision-LLM processor.

        Args:
            model: Vision-capable LLM model name
            litellm_base_url: LiteLLM API base URL
            litellm_api_key: LiteLLM API key
            max_tokens: Maximum tokens in response
            temperature: LLM temperature (0.0-1.0)
        """
        if model:
            self.model = model
        else:
            from db.models.llm_model import LLMModel
            default_model = LLMModel.get_default_model(
                model_type=LLMModel.MODEL_TYPE_LLM,
                supports_vision=True
            )
            if not default_model:
                raise RuntimeError("No vision-capable LLM model configured in llm_models")
            self.model = default_model.model_id
        self.litellm_base_url = litellm_base_url or os.getenv(
            'LITELLM_BASE_URL',
            'https://kiz1.in.ohmportal.de/llmproxy/v1'
        )
        self.litellm_api_key = litellm_api_key or os.getenv('LITELLM_API_KEY', '')
        self.max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        self.temperature = temperature or self.DEFAULT_TEMPERATURE

    async def extract_structured_data(
        self,
        screenshot_base64: str,
        url: str,
        html_text: Optional[str] = None
    ) -> Dict:
        """
        Extract structured business data from screenshot using Vision-LLM.

        Args:
            screenshot_base64: Base64-encoded screenshot
            url: URL of the page (for logging)
            html_text: Optional HTML text (currently unused, for future enhancement)

        Returns:
            Dict with extracted fields (company_name, owner, email, etc.)
            Empty dict if extraction fails
        """
        try:
            import openai

            client = openai.OpenAI(
                base_url=self.litellm_base_url,
                api_key=self.litellm_api_key
            )

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.EXTRACTION_PROMPT
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{screenshot_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            response_text = extract_message_text(response.choices[0].message).strip()
            if not response_text:
                logger.warning(f"Vision-LLM returned empty response for {url}")
                return {}

            # Parse JSON response
            extracted = self._parse_json_response(response_text)

            if extracted:
                logger.info(
                    f"Vision-LLM extracted data for {url}: "
                    f"{list(k for k, v in extracted.items() if v)}"
                )
            else:
                logger.warning(f"Vision-LLM returned no valid data for {url}")

            return extracted

        except Exception as e:
            logger.warning(f"Vision-LLM extraction failed for {url}: {e}")
            return {}

    def _parse_json_response(self, response_text: str) -> Dict:
        """
        Parse JSON response from Vision-LLM, handling markdown code blocks.

        Args:
            response_text: Raw response text from LLM

        Returns:
            Parsed dict or empty dict if parsing fails
        """
        try:
            # Clean up response (remove markdown code blocks if present)
            if response_text.startswith('```'):
                response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
                response_text = re.sub(r'\n?```$', '', response_text)

            extracted = json.loads(response_text)

            # Validate it's a dict
            if not isinstance(extracted, dict):
                logger.warning(f"Vision-LLM returned non-dict: {type(extracted)}")
                return {}

            return extracted

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Vision-LLM JSON response: {e}")
            logger.debug(f"Response text: {response_text[:200]}")
            return {}

    def is_available(self) -> bool:
        """
        Check if Vision-LLM is properly configured.

        Returns:
            True if API credentials are configured
        """
        return bool(self.litellm_base_url and self.litellm_api_key)
