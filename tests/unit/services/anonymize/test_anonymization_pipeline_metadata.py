"""
Unit Tests: Anonymization Pipeline Metadata Extraction
======================================================

Ensures model/provider/course metadata is extracted from imported chat JSON schemas.

Test IDs:
- ANONMETA-001: learn_counselling schema (snake_case)
- ANONMETA-002: camelCase + JSON-string nested metadata
"""

import json


def test_ANONMETA_001_extracts_model_and_course_from_learn_counselling_schema(app, app_context):
    from services.anonymize.anonymization_pipeline_service import AnonymizationPipelineService

    raw_conversation = {
        "id": 1,
        "title": "Test Conversation",
        "course_member": {"course": {"name": "Testkurs"}},
        "learn_counselling_messages": [
            {
                "message_number": 1,
                "content": "Hallo",
                "author": "vikl",
                "additions": {"llm_info": {"provider": "ionos", "model": "openai/gpt-oss-120b"}},
            },
            {
                "message_number": 2,
                "content": "Guten Tag",
                "author": "counselor",
            },
        ],
    }

    message_source_key, raw_messages = AnonymizationPipelineService._extract_message_collection(raw_conversation)
    normalized_messages = AnonymizationPipelineService._normalize_messages(raw_messages)
    metadata = AnonymizationPipelineService._build_metadata(
        raw_conversation=raw_conversation,
        message_source_key=message_source_key,
        raw_messages=raw_messages,
        normalized_messages=normalized_messages,
    )

    assert metadata["derived"]["models"] == ["openai/gpt-oss-120b"]
    assert metadata["derived"]["providers"] == ["ionos"]
    assert metadata["derived"]["courses"] == ["Testkurs"]


def test_ANONMETA_002_extracts_from_json_strings_and_camelcase_keys(app, app_context):
    from services.anonymize.anonymization_pipeline_service import AnonymizationPipelineService

    raw_conversation = {
        "id": "abc-123",
        "courseMember": json.dumps({"course": {"name": "CamelCourse"}}),
        "messages": [
            {
                "message_number": "1",
                "text": "Hello",
                "from": "user",
                "additions": json.dumps({"llmInfo": {"provider": "openai", "model": "gpt-4o-mini"}}),
            }
        ],
    }

    message_source_key, raw_messages = AnonymizationPipelineService._extract_message_collection(raw_conversation)
    normalized_messages = AnonymizationPipelineService._normalize_messages(raw_messages)
    metadata = AnonymizationPipelineService._build_metadata(
        raw_conversation=raw_conversation,
        message_source_key=message_source_key,
        raw_messages=raw_messages,
        normalized_messages=normalized_messages,
    )

    assert metadata["derived"]["models"] == ["gpt-4o-mini"]
    assert metadata["derived"]["providers"] == ["openai"]
    assert metadata["derived"]["courses"] == ["CamelCourse"]

