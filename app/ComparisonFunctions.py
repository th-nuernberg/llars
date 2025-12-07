"""
Comparison Functions - Compatibility Layer

This module provides backward-compatible function exports for the refactored
comparison services. All functionality has been moved to:
- services.comparison.session_service
- services.comparison.evaluation_service
- services.comparison.persona_formatter
- services.comparison.prompt_generator
- services.comparison.response_generator

For new code, import directly from the services:
    from services.comparison import (
        ComparisonSessionService,
        ComparisonEvaluationService,
        PersonaFormatter,
        ComparisonPromptGenerator,
        LLMResponseGenerator
    )
"""

# Re-export all functions for backward compatibility
from services.comparison.session_service import ComparisonSessionService
from services.comparison.evaluation_service import ComparisonEvaluationService
from services.comparison.persona_formatter import PersonaFormatter
from services.comparison.prompt_generator import ComparisonPromptGenerator
from services.comparison.response_generator import LLMResponseGenerator


# Backward-compatible function exports
# Session Management
def get_session_by_id(session_id):
    """Get a session by ID. @deprecated: Use ComparisonSessionService.get_session_by_id()"""
    return ComparisonSessionService.get_session_by_id(session_id)


def get_model_mapping_for_session(session):
    """Get model mapping. @deprecated: Use ComparisonSessionService.get_model_mapping_for_session()"""
    return ComparisonSessionService.get_model_mapping_for_session(session)


def get_all_messages_by_session_id(session_id):
    """Get all messages. @deprecated: Use ComparisonSessionService.get_all_messages()"""
    return ComparisonSessionService.get_all_messages(session_id)


def get_message_by_id_and_session(message_id, session_id):
    """Get message. @deprecated: Use ComparisonSessionService.get_message()"""
    return ComparisonSessionService.get_message(message_id, session_id)


def set_message_selected(message_id, session_id, selected):
    """Set message selected. @deprecated: Use ComparisonSessionService.set_message_selected()"""
    return ComparisonSessionService.set_message_selected(message_id, session_id, selected)


def add_message(session_id, idx, message_type, content):
    """Add message. @deprecated: Use ComparisonSessionService.add_message()"""
    return ComparisonSessionService.add_message(session_id, idx, message_type, content)


def serialize_message(message):
    """Serialize message. @deprecated: Use ComparisonSessionService.serialize_message()"""
    return ComparisonSessionService.serialize_message(message)


def build_chat_history(session):
    """Build chat history. @deprecated: Use ComparisonSessionService.build_chat_history()"""
    return ComparisonSessionService.build_chat_history(session)


def build_chat_history_for_evaluation(session, up_to_idx):
    """Build chat history for eval. @deprecated: Use ComparisonSessionService.build_chat_history_text()"""
    return ComparisonSessionService.build_chat_history_text(session, up_to_idx)


# Evaluation
def perform_ai_evaluation(message_id, session_id, user_selection):
    """Perform AI evaluation. @deprecated: Use ComparisonEvaluationService.perform_evaluation()"""
    return ComparisonEvaluationService.perform_evaluation(message_id, session_id, user_selection)


def perform_ai_evaluation_fallback(message_id, session_id, user_selection):
    """Fallback evaluation. @deprecated: Use ComparisonEvaluationService._perform_fallback_evaluation()"""
    return ComparisonEvaluationService._perform_fallback_evaluation(message_id, session_id, user_selection)


def perform_ai_evaluation_async(message_id, session_id):
    """Async evaluation. @deprecated: Use ComparisonEvaluationService.perform_async_evaluation()"""
    return ComparisonEvaluationService.perform_async_evaluation(message_id, session_id)


def map_ai_rating_to_selection(ai_rating):
    """Map rating. @deprecated: Use ComparisonEvaluationService.map_rating_to_selection()"""
    return ComparisonEvaluationService.map_rating_to_selection(ai_rating)


def check_rating_match(user_selection, ai_selection):
    """Check match. @deprecated: Use ComparisonEvaluationService.check_rating_match()"""
    return ComparisonEvaluationService.check_rating_match(user_selection, ai_selection)


def save_user_justification(message_id, justification):
    """Save justification. @deprecated: Use ComparisonEvaluationService.save_user_justification()"""
    return ComparisonEvaluationService.save_user_justification(message_id, justification)


# Persona Formatting
def format_persona_info(persona):
    """Format persona. @deprecated: Use PersonaFormatter.format()"""
    return PersonaFormatter.format(persona)


# Prompt Generation
def create_system_prompt(persona, chat_history):
    """Create system prompt. @deprecated: Use ComparisonPromptGenerator.create_persona_prompt()"""
    is_first_message = not chat_history
    return ComparisonPromptGenerator.create_persona_prompt(persona, chat_history, is_first_message)


def create_counselor_suggestion_prompt(persona, chat_history):
    """Create counselor prompt. @deprecated: Use ComparisonPromptGenerator.create_counselor_suggestion_prompt()"""
    return ComparisonPromptGenerator.create_counselor_suggestion_prompt(persona, chat_history)


# Response Generation
def generate_comparison_responses(session, message_id, socketio, client_id):
    """Generate responses. @deprecated: Use LLMResponseGenerator().generate_comparison_responses()"""
    generator = LLMResponseGenerator()
    return generator.generate_comparison_responses(session, message_id, socketio, client_id)


def generate_llm_response(llm_type, message, is_first_message, message_id, socketio, client_id, session_id):
    """Generate LLM response. @deprecated: Use LLMResponseGenerator()._generate_llm_response()"""
    generator = LLMResponseGenerator()
    return generator._generate_llm_response(
        llm_type, message, is_first_message, message_id, socketio, client_id, session_id
    )


def save_llm_response(message_id, llm_type, response):
    """Save LLM response. @deprecated: Use LLMResponseGenerator()._save_response()"""
    generator = LLMResponseGenerator()
    return generator._save_response(message_id, llm_type, response)


def generate_counselor_suggestion(session):
    """Generate suggestion. @deprecated: Use LLMResponseGenerator.generate_counselor_suggestion()"""
    return LLMResponseGenerator.generate_counselor_suggestion(session)
