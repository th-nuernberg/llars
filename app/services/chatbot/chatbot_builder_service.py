"""
Chatbot Builder Service.

Main facade for the Chatbot Builder wizard workflow.
Delegates to specialized services for:
- ChatbotCreator: Creating and managing chatbots
- ChatbotFieldGenerator: Auto-generating fields using LLM
- ChatbotBuildMonitor: Monitoring build processes

This service maintains backward compatibility with existing code
by providing a unified interface to all builder functionality.
"""

import logging
from typing import Dict, Any, Optional

from .chatbot_creator import ChatbotCreator
from .chatbot_field_generator import ChatbotFieldGenerator
from .chatbot_build_monitor import ChatbotBuildMonitor

logger = logging.getLogger(__name__)


class ChatbotBuilderService:
    """
    Main service for building chatbots via the wizard workflow.

    This is a facade that delegates to specialized services while
    maintaining backward compatibility with existing code.
    """

    # LLM settings for field generation (for compatibility)
    DEFAULT_MODEL = ChatbotFieldGenerator.DEFAULT_MODEL

    # ========== Chatbot Creation & Lifecycle ==========

    @staticmethod
    def create_wizard_chatbot(url: str, username: str) -> Dict[str, Any]:
        """
        Start the chatbot creation wizard with a URL.

        Delegates to: ChatbotCreator

        Args:
            url: The source URL to crawl
            username: Username creating the chatbot

        Returns:
            Dict with chatbot info and status
        """
        try:
            return ChatbotCreator.create_wizard_chatbot(url, username)
        except ValueError as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def start_crawl(
        chatbot_id: int,
        max_pages: int = 50,
        max_depth: int = 3,
        use_playwright: bool = True,
        use_vision_llm: bool = False
    ) -> Dict[str, Any]:
        """
        Start crawling the source URL for a chatbot.

        Delegates to: ChatbotCreator

        Args:
            chatbot_id: The chatbot ID
            max_pages: Maximum pages to crawl
            max_depth: Maximum crawl depth
            use_playwright: Whether to use Playwright for JavaScript rendering
            use_vision_llm: Whether to use Vision LLM for screenshot extraction

        Returns:
            Dict with status and job_id for tracking
        """
        try:
            return ChatbotCreator.start_crawl(
                chatbot_id, max_pages, max_depth, use_playwright, use_vision_llm
            )
        except ValueError as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def finalize_chatbot(chatbot_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Finalize the chatbot configuration and mark as ready.

        Delegates to: ChatbotCreator

        Args:
            chatbot_id: The chatbot ID
            data: Configuration data (name, display_name, system_prompt, etc.)

        Returns:
            Dict with result
        """
        try:
            return ChatbotCreator.finalize_chatbot(chatbot_id, data)
        except ValueError as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def update_build_status(chatbot_id: int, status: str, error: Optional[str] = None) -> Dict[str, Any]:
        """
        Update the build status of a chatbot.

        Delegates to: ChatbotCreator

        Args:
            chatbot_id: The chatbot ID
            status: New status
            error: Optional error message

        Returns:
            Dict with result
        """
        try:
            return ChatbotCreator.update_build_status(chatbot_id, status, error)
        except ValueError as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def cancel_build(chatbot_id: int) -> Dict[str, Any]:
        """
        Cancel the chatbot build process.

        Delegates to: ChatbotCreator

        Args:
            chatbot_id: The chatbot ID

        Returns:
            Dict with cancellation result
        """
        try:
            return ChatbotCreator.cancel_build(chatbot_id)
        except ValueError as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def resume_build(chatbot_id: int) -> Dict[str, Any]:
        """
        Resume a paused chatbot build process.

        Delegates to: ChatbotCreator

        Args:
            chatbot_id: The chatbot ID

        Returns:
            Dict with resume result
        """
        try:
            return ChatbotCreator.resume_build(chatbot_id)
        except ValueError as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def tweak_chatbot(chatbot_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Quick-tweak chatbot parameters (partial update).

        Delegates to: ChatbotCreator

        Args:
            chatbot_id: The chatbot ID
            data: Parameters to update

        Returns:
            Dict with updated fields
        """
        try:
            return ChatbotCreator.tweak_chatbot(chatbot_id, data)
        except ValueError as e:
            return {'success': False, 'error': str(e)}

    # ========== Field Generation ==========

    @staticmethod
    def generate_field(chatbot_id: int, field: str, context: Optional[str] = None, force_llm: bool = False) -> Dict[str, Any]:
        """
        Generate a field value using LLM based on the chatbot's context.

        Delegates to: ChatbotFieldGenerator

        Args:
            chatbot_id: The chatbot ID
            field: The field to generate (name, system_prompt, welcome_message)
            context: Optional additional context
            force_llm: If True, skip cached/crawled values and force LLM generation

        Returns:
            Dict with generated value
        """
        try:
            return ChatbotFieldGenerator.generate_field(chatbot_id, field, context, force_llm=force_llm)
        except ValueError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"[ChatbotBuilder] Field generation error: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def stream_field(chatbot_id: int, field: str, context: Optional[str] = None):
        """
        Stream field generation tokens for live updates.

        Yields:
            Dicts with delta tokens and optional final value.
        """
        return ChatbotFieldGenerator.stream_field_generation(chatbot_id, field, context)

    # ========== Build Monitoring ==========

    @staticmethod
    def get_build_status(chatbot_id: int) -> Dict[str, Any]:
        """
        Get the current build status of a chatbot.

        Delegates to: ChatbotBuildMonitor

        Args:
            chatbot_id: The chatbot ID

        Returns:
            Dict with build status and progress info
        """
        try:
            return ChatbotBuildMonitor.get_build_status(chatbot_id)
        except ValueError as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_admin_test_data(chatbot_id: int) -> Dict[str, Any]:
        """
        Get data for the admin test page.

        Delegates to: ChatbotBuildMonitor

        Args:
            chatbot_id: The chatbot ID

        Returns:
            Dict with chatbot config, collection info, stats, and sample documents
        """
        try:
            return ChatbotBuildMonitor.get_admin_test_data(chatbot_id)
        except ValueError as e:
            return {'success': False, 'error': str(e)}

    # ========== Internal Methods (for backward compatibility) ==========
    # These are called by ChatbotCreator but kept here for any external references

    @staticmethod
    def _monitor_crawl(app, chatbot_id: int, collection_id: int, job_id: str):
        """
        Monitor the crawl job and transition to embedding when done.

        Delegates to: ChatbotBuildMonitor
        (Kept for backward compatibility)
        """
        ChatbotBuildMonitor.monitor_crawl(app, chatbot_id, collection_id, job_id)

    @staticmethod
    def _start_embedding(app, chatbot_id: int, collection_id: int):
        """
        Start embedding process after crawl.

        Delegates to: ChatbotBuildMonitor
        (Kept for backward compatibility)
        """
        ChatbotBuildMonitor.start_embedding(app, chatbot_id, collection_id)

    @staticmethod
    def _monitor_embedding(app, chatbot_id: int, collection_id: int):
        """
        Monitor the embedding process and transition to configuring when done.

        Delegates to: ChatbotBuildMonitor
        (Kept for backward compatibility)
        """
        ChatbotBuildMonitor.monitor_embedding(app, chatbot_id, collection_id)
