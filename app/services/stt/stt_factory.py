"""
STT Factory
Pluggable Speech-to-Text provider factory, modeled after LLMClientFactory.
Resolves providers from DB config or falls back to environment defaults.
"""

import logging
import os
from typing import Dict, Optional, Type

from .stt_base import STTBase

logger = logging.getLogger(__name__)

# Provider type → implementation class mapping
PROVIDER_MAP: Dict[str, str] = {
    "openai_whisper": "services.stt.providers.openai_whisper.OpenAIWhisperProvider",
    "groq": "services.stt.providers.groq_whisper.GroqWhisperProvider",
    "deepgram": "services.stt.providers.deepgram.DeepgramProvider",
    "local": "services.stt.providers.local_whisper.LocalWhisperProvider",
    "azure": "services.stt.providers.azure_speech.AzureSpeechProvider",
}


class STTFactory:
    """Central factory for creating STT provider instances."""

    @staticmethod
    def _load_class(dotted_path: str) -> Type[STTBase]:
        """Dynamically import a provider class from dotted path."""
        module_path, class_name = dotted_path.rsplit(".", 1)
        import importlib

        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    @staticmethod
    def _get_db_provider(provider_id: Optional[int] = None) -> Optional[dict]:
        """Load provider config from database."""
        try:
            from db.models.messaging import MessagingConversation  # Trigger model import

            # Look up STT provider config from a hypothetical stt_providers table
            # For now, we'll use environment-based fallback
            return None
        except Exception:
            return None

    @staticmethod
    def create(
        provider_type: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> STTBase:
        """
        Create an STT provider instance.

        Args:
            provider_type: Provider type (openai_whisper, groq, deepgram, local, azure)
            config: Provider configuration dict (api_key, base_url, model_name, etc.)

        Returns:
            STTBase instance ready for transcription
        """
        # Resolve provider type
        if not provider_type:
            provider_type = os.getenv("STT_DEFAULT_PROVIDER", "openai_whisper")

        if provider_type not in PROVIDER_MAP:
            raise ValueError(
                f"Unknown STT provider: {provider_type}. "
                f"Available: {', '.join(PROVIDER_MAP.keys())}"
            )

        # Build config from environment if not provided
        if not config:
            config = STTFactory._build_env_config(provider_type)

        # Import and instantiate provider
        class_path = PROVIDER_MAP[provider_type]
        provider_class = STTFactory._load_class(class_path)

        logger.info("Creating STT provider: %s", provider_type)
        return provider_class(config)

    @staticmethod
    def _build_env_config(provider_type: str) -> dict:
        """Build provider config from environment variables."""
        config = {}

        if provider_type == "openai_whisper":
            config["api_key"] = os.getenv("OPENAI_API_KEY", "")
            config["model_name"] = "whisper-1"
            config["base_url"] = "https://api.openai.com/v1"

        elif provider_type == "groq":
            config["api_key"] = os.getenv("GROQ_API_KEY", "")
            config["model_name"] = "whisper-large-v3"
            config["base_url"] = "https://api.groq.com/openai/v1"

        elif provider_type == "deepgram":
            config["api_key"] = os.getenv("DEEPGRAM_API_KEY", "")
            config["model_name"] = "nova-2"

        elif provider_type == "local":
            config["model_name"] = os.getenv("WHISPER_MODEL", "base")

        elif provider_type == "azure":
            config["api_key"] = os.getenv("AZURE_SPEECH_KEY", "")
            config["base_url"] = os.getenv("AZURE_SPEECH_REGION", "westeurope")

        return config

    @staticmethod
    def list_providers() -> Dict[str, str]:
        """List all available provider types."""
        return {k: v.rsplit(".", 1)[-1] for k, v in PROVIDER_MAP.items()}

    @staticmethod
    def test_provider(
        provider_type: str, config: Optional[dict] = None
    ) -> bool:
        """Test if a provider is working."""
        try:
            provider = STTFactory.create(provider_type, config)
            return provider.test_connection()
        except Exception as e:
            logger.error("STT provider test failed (%s): %s", provider_type, e)
            return False
