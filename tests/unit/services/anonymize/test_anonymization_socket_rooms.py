"""
Unit Tests: Anonymization Socket Rooms
=======================================

Tests for Socket.IO room name helpers.

Test IDs:
- ANON_ROOM_001: Overview room constant is correct
- ANON_ROOM_002: Conversation room generates correct name
- ANON_ROOM_003: Conversation room handles different ID types
"""


class TestAnonymizationSocketRooms:

    def test_ANON_ROOM_001_overview_room_constant(self):
        """[ANON_ROOM-001] Overview room has expected constant value."""
        from services.anonymize.socket_rooms import ANONYMIZATION_OVERVIEW_ROOM
        assert ANONYMIZATION_OVERVIEW_ROOM == "anonymization_overview"

    def test_ANON_ROOM_002_conversation_room_name(self):
        """[ANON_ROOM-002] Conversation room generates correct name for given ID."""
        from services.anonymize.socket_rooms import anonymization_conversation_room
        assert anonymization_conversation_room(42) == "anonymization_conversation_42"
        assert anonymization_conversation_room(1) == "anonymization_conversation_1"

    def test_ANON_ROOM_003_conversation_room_type_coercion(self):
        """[ANON_ROOM-003] Conversation room handles string IDs by converting to int."""
        from services.anonymize.socket_rooms import anonymization_conversation_room
        assert anonymization_conversation_room("123") == "anonymization_conversation_123"
