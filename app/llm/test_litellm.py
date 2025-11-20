"""
Test script for LiteLLM integration

Usage:
    python -m app.llm.test_litellm
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.llm import LiteLLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_litellm_connection():
    """Test LiteLLM proxy connection"""
    logger.info("=" * 60)
    logger.info("Testing LiteLLM Proxy Connection")
    logger.info("=" * 60)

    try:
        # Initialize client
        client = LiteLLMClient()
        logger.info(f"✓ Client initialized successfully")
        logger.info(f"  Model: {client.model}")
        logger.info(f"  Base URL: {client.base_url}")

        # Test simple completion
        logger.info("\nTesting simple completion...")
        messages = [
            {"role": "user", "content": "Was ist 2+2? Antworte kurz."}
        ]

        response = client.complete(messages=messages, max_tokens=50)

        if response:
            logger.info(f"✓ Completion successful")
            logger.info(f"  Response: {response[:100]}...")
        else:
            logger.error(f"✗ Completion failed - no response")
            return False

        # Test streaming
        logger.info("\nTesting streaming completion...")
        stream_messages = [
            {"role": "user", "content": "Zähle von 1 bis 5."}
        ]

        logger.info("  Stream output: ", end="")
        for chunk in client.stream_complete(messages=stream_messages, max_tokens=100):
            print(chunk, end="", flush=True)
        print()

        logger.info(f"✓ Streaming successful")

        logger.info("\n" + "=" * 60)
        logger.info("All tests passed!")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        logger.exception("Full traceback:")
        return False


if __name__ == "__main__":
    success = test_litellm_connection()
    sys.exit(0 if success else 1)
