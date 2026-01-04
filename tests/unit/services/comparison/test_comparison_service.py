"""
Unit Tests für Comparison Services

Testet:
- ComparisonSessionService: CRUD für Sessions und Messages
- ComparisonEvaluationService: AI-Evaluation und Vergleiche
- ComparisonPromptGenerator: Prompt-Generierung
- PersonaFormatter: Persona-Formatierung
- LLMResponseGenerator: Response-Generierung (mocked)
"""

import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, Mock


# =============================================================================
# Fixtures - Using global fixtures from conftest.py
# =============================================================================

# Note: app, db, client fixtures are inherited from conftest.py


@pytest.fixture
def sample_user(app, db):
    """Erstellt einen Test-Benutzer."""
    with app.app_context():
        from db.models.user import User, UserGroup

        # Create default group first
        group = UserGroup(name='test_group')
        db.session.add(group)
        db.session.commit()

        user = User(
            username='testuser',
            password_hash='test_hash',
            api_key='test-api-key-12345',
            group_id=group.id
        )
        db.session.add(user)
        db.session.commit()
        return {'id': user.id, 'username': user.username}


@pytest.fixture
def sample_scenario(app, db, sample_user):
    """Erstellt ein Test-Szenario."""
    with app.app_context():
        from db.models.scenario import RatingScenarios, FeatureFunctionType

        # Create function type first
        func_type = FeatureFunctionType(name='comparison')
        db.session.add(func_type)
        db.session.commit()

        scenario = RatingScenarios(
            scenario_name='Test Scenario',
            function_type_id=func_type.function_type_id,
            begin=datetime(2024, 1, 1),
            end=datetime(2025, 12, 31),
            llm1_model='gpt-4',
            llm2_model='claude-3'
        )
        db.session.add(scenario)
        db.session.commit()
        return {'id': scenario.id, 'name': scenario.scenario_name}


@pytest.fixture
def sample_persona():
    """Erstellt eine Test-Persona."""
    return {
        'name': 'Maria Müller',
        'properties': {
            'Steckbrief': {
                'Alter': '45 Jahre',
                'Beruf': 'Krankenschwester',
                'Familienstand': 'geschieden'
            },
            'Hauptanliegen': 'Stress am Arbeitsplatz und Burnout-Symptome.',
            'Nebenanliegen': ['Schlafprobleme', 'Beziehungskonflikte'],
            'Sprachliche Merkmale': ['emotionale Ausdrucksweise', 'kurze Sätze'],
            'Emotionale Merkmale': {
                'Grundhaltung': 'angespannt und erschöpft',
                'ausgepraegte Emotionen': ['Frustration', 'Angst'],
                'details': {
                    'Frustration': {
                        'ausloeser': 'mangelnde Anerkennung',
                        'reaktion': 'Rückzug',
                        'beispielsausloeser': 'Ihre Arbeit wird nie gewürdigt',
                        'beispielsreaktion': 'Das sagt mir keiner!'
                    }
                }
            },
            'Ressourcen': {
                'emotional': True,
                'sozial': False,
                'finanziell': True,
                'andere': True,
                'andereDetails': 'Yoga-Kurs'
            },
            'Soziales Umfeld': 'alleinstehend, wenige Freunde',
            'Prinzipien': ['Reagiert nicht auf Provokationen', 'Bleibt höflich']
        }
    }


@pytest.fixture
def sample_session(app, db, sample_user, sample_scenario, sample_persona):
    """Erstellt eine Test-Comparison-Session."""
    with app.app_context():
        from db.models.scenario import ComparisonSession
        from db.models.user import User

        # Get fresh user reference
        user = User.query.get(sample_user['id'])

        session = ComparisonSession(
            scenario_id=sample_scenario['id'],
            user_id=user.id,
            persona_json=sample_persona,
            persona_name=sample_persona['name']
        )
        db.session.add(session)
        db.session.commit()
        return {'id': session.id, 'scenario_id': sample_scenario['id']}


@pytest.fixture
def sample_messages(app, db, sample_session):
    """Erstellt Test-Messages für eine Session."""
    with app.app_context():
        from db.models.scenario import ComparisonMessage

        messages = []

        # User message
        msg1 = ComparisonMessage(
            session_id=sample_session['id'],
            idx=0,
            type='user',
            content='Wie geht es Ihnen heute?'
        )
        db.session.add(msg1)

        # Bot pair message
        bot_content = json.dumps({
            'llm1': 'Es geht mir nicht so gut.',
            'llm2': 'Ich fühle mich erschöpft.'
        })
        msg2 = ComparisonMessage(
            session_id=sample_session['id'],
            idx=1,
            type='bot_pair',
            content=bot_content,
            selected='llm1'
        )
        db.session.add(msg2)

        # Another user message
        msg3 = ComparisonMessage(
            session_id=sample_session['id'],
            idx=2,
            type='user',
            content='Was belastet Sie am meisten?'
        )
        db.session.add(msg3)

        db.session.commit()

        messages = [
            {'id': msg1.id, 'idx': 0, 'type': 'user'},
            {'id': msg2.id, 'idx': 1, 'type': 'bot_pair'},
            {'id': msg3.id, 'idx': 2, 'type': 'user'}
        ]
        return messages


# =============================================================================
# ComparisonSessionService Tests
# =============================================================================

class TestComparisonSessionService:
    """Tests für ComparisonSessionService."""

    def test_COMP_001_get_session_by_id_success(self, app, sample_session):
        """COMP-001: Session erfolgreich per ID abrufen."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService

            session = ComparisonSessionService.get_session_by_id(sample_session['id'])

            assert session is not None
            assert session.id == sample_session['id']
            assert session.scenario_id == sample_session['scenario_id']

    def test_COMP_002_get_session_by_id_not_found(self, app):
        """COMP-002: Nicht existierende Session gibt None zurück."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService

            session = ComparisonSessionService.get_session_by_id(99999)

            assert session is None

    def test_COMP_003_get_model_mapping_for_session(self, app, sample_session):
        """COMP-003: Model-Mapping für Session abrufen."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService
            from db.models.scenario import ComparisonSession

            session = ComparisonSession.query.get(sample_session['id'])
            mapping = ComparisonSessionService.get_model_mapping_for_session(session)

            assert 'llm1' in mapping
            assert 'llm2' in mapping
            assert mapping['llm1'] == 'gpt-4'
            assert mapping['llm2'] == 'claude-3'

    def test_COMP_004_get_model_mapping_no_scenario(self, app, db, sample_user, sample_persona):
        """COMP-004: Model-Mapping ohne gültiges Szenario wirft Error."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService
            from db.models.scenario import ComparisonSession

            # Create session with non-existent scenario
            session = ComparisonSession(
                scenario_id=99999,
                user_id=sample_user['id'],
                persona_json=sample_persona,
                persona_name='Test'
            )
            db.session.add(session)
            db.session.commit()

            with pytest.raises(ValueError):
                ComparisonSessionService.get_model_mapping_for_session(session)

    def test_COMP_005_get_all_messages(self, app, sample_session, sample_messages):
        """COMP-005: Alle Messages einer Session abrufen."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService

            messages = ComparisonSessionService.get_all_messages(sample_session['id'])

            assert len(messages) == 3
            # Should be ordered by idx
            assert messages[0].idx == 0
            assert messages[1].idx == 1
            assert messages[2].idx == 2

    def test_COMP_006_get_all_messages_empty(self, app, sample_session):
        """COMP-006: Leere Message-Liste bei Session ohne Messages."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService

            messages = ComparisonSessionService.get_all_messages(sample_session['id'])

            assert messages == []

    def test_COMP_007_get_message_success(self, app, sample_session, sample_messages):
        """COMP-007: Einzelne Message erfolgreich abrufen."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService

            message = ComparisonSessionService.get_message(
                sample_messages[0]['id'],
                sample_session['id']
            )

            assert message is not None
            assert message.type == 'user'
            assert message.idx == 0

    def test_COMP_008_get_message_wrong_session(self, app, sample_session, sample_messages):
        """COMP-008: Message mit falscher Session-ID gibt None."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService

            message = ComparisonSessionService.get_message(
                sample_messages[0]['id'],
                99999  # Wrong session
            )

            assert message is None

    def test_COMP_009_set_message_selected_success(self, app, sample_session, sample_messages):
        """COMP-009: Message Selection erfolgreich setzen."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService
            from db.models.scenario import ComparisonMessage

            # Bot pair message
            result = ComparisonSessionService.set_message_selected(
                sample_messages[1]['id'],
                sample_session['id'],
                'llm2'
            )

            assert result is True

            # Verify in DB
            message = ComparisonMessage.query.get(sample_messages[1]['id'])
            assert message.selected == 'llm2'

    def test_COMP_010_set_message_selected_not_found(self, app, sample_session):
        """COMP-010: Selection für nicht existierende Message gibt False."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService

            result = ComparisonSessionService.set_message_selected(99999, sample_session['id'], 'llm1')

            assert result is False

    def test_COMP_011_add_message(self, app, sample_session):
        """COMP-011: Neue Message hinzufügen."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService
            from db.models.scenario import ComparisonMessage

            message_id = ComparisonSessionService.add_message(
                session_id=sample_session['id'],
                idx=0,
                message_type='user',
                content='Test message content'
            )

            assert message_id is not None
            assert message_id > 0

            # Verify in DB
            message = ComparisonMessage.query.get(message_id)
            assert message.content == 'Test message content'
            assert message.type == 'user'
            assert message.selected is None

    def test_COMP_012_serialize_message_user(self, app, sample_session, sample_messages):
        """COMP-012: User-Message serialisieren."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService
            from db.models.scenario import ComparisonMessage

            message = ComparisonMessage.query.get(sample_messages[0]['id'])
            serialized = ComparisonSessionService.serialize_message(message)

            assert serialized['messageId'] == message.id
            assert serialized['idx'] == 0
            assert serialized['type'] == 'user'
            assert serialized['content'] == 'Wie geht es Ihnen heute?'
            assert 'timestamp' in serialized

    def test_COMP_013_serialize_message_bot_pair(self, app, sample_session, sample_messages):
        """COMP-013: Bot-Pair-Message serialisieren (JSON Content)."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService
            from db.models.scenario import ComparisonMessage

            message = ComparisonMessage.query.get(sample_messages[1]['id'])
            serialized = ComparisonSessionService.serialize_message(message)

            assert serialized['type'] == 'bot_pair'
            assert isinstance(serialized['content'], dict)
            assert 'llm1' in serialized['content']
            assert 'llm2' in serialized['content']
            assert serialized['selected'] == 'llm1'

    def test_COMP_014_build_chat_history(self, app, sample_session, sample_messages, sample_persona):
        """COMP-014: Chat-History in OpenAI-Format aufbauen."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService
            from db.models.scenario import ComparisonSession

            session = ComparisonSession.query.get(sample_session['id'])
            history = ComparisonSessionService.build_chat_history(session)

            # Should have user and assistant messages
            assert len(history) >= 1
            # First should be user message mapped to 'user' role
            user_msgs = [m for m in history if m['role'] == 'user']
            asst_msgs = [m for m in history if m['role'] == 'assistant']

            assert len(user_msgs) >= 1
            # Bot pair with selection becomes assistant
            assert len(asst_msgs) >= 1

    def test_COMP_015_build_chat_history_text(self, app, sample_session, sample_messages):
        """COMP-015: Chat-History als Text für Evaluation aufbauen."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService
            from db.models.scenario import ComparisonSession

            session = ComparisonSession.query.get(sample_session['id'])
            history_text = ComparisonSessionService.build_chat_history_text(session, up_to_idx=2)

            assert 'Berater:' in history_text
            assert 'Klient:' in history_text

    def test_COMP_016_update_message_content(self, app, sample_session, sample_messages):
        """COMP-016: Message Content (LLM Response) aktualisieren."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService
            from db.models.scenario import ComparisonMessage

            result = ComparisonSessionService.update_message_content(
                sample_messages[1]['id'],
                'llm1',
                'Updated response from LLM1'
            )

            assert result is True

            # Verify
            message = ComparisonMessage.query.get(sample_messages[1]['id'])
            content = json.loads(message.content)
            assert content['llm1'] == 'Updated response from LLM1'

    def test_COMP_017_is_response_complete_true(self, app, sample_session, sample_messages):
        """COMP-017: Response ist komplett (beide LLMs haben geantwortet)."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService

            # Bot pair message has both responses
            result = ComparisonSessionService.is_response_complete(sample_messages[1]['id'])

            # is_response_complete returns last truthy value from and-chain
            assert result  # Truthy check

    def test_COMP_018_is_response_complete_false(self, app, db, sample_session):
        """COMP-018: Response ist nicht komplett (nur ein LLM)."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService
            from db.models.scenario import ComparisonMessage

            # Create incomplete message
            incomplete_content = json.dumps({'llm1': 'Only one response', 'llm2': ''})
            msg = ComparisonMessage(
                session_id=sample_session['id'],
                idx=0,
                type='bot_pair',
                content=incomplete_content
            )
            db.session.add(msg)
            db.session.commit()

            result = ComparisonSessionService.is_response_complete(msg.id)

            # Empty string is falsy, so result should be falsy
            assert not result

    def test_COMP_019_is_response_complete_not_found(self, app):
        """COMP-019: Response-Check für nicht existierende Message."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService

            result = ComparisonSessionService.is_response_complete(99999)

            assert result is False


# =============================================================================
# ComparisonEvaluationService Tests
# =============================================================================

class TestComparisonEvaluationService:
    """Tests für ComparisonEvaluationService."""

    def test_COMP_020_rating_map(self, app):
        """COMP-020: Rating-Map Konstanten prüfen."""
        with app.app_context():
            from services.comparison.evaluation_service import ComparisonEvaluationService

            assert ComparisonEvaluationService.RATING_MAP['model_1'] == 'llm1'
            assert ComparisonEvaluationService.RATING_MAP['model_2'] == 'llm2'
            assert ComparisonEvaluationService.RATING_MAP['same'] == 'tie'

    def test_COMP_021_map_rating_to_selection(self, app):
        """COMP-021: AI-Rating zu Selection mappen."""
        with app.app_context():
            from services.comparison.evaluation_service import ComparisonEvaluationService

            assert ComparisonEvaluationService.map_rating_to_selection('model_1') == 'llm1'
            assert ComparisonEvaluationService.map_rating_to_selection('model_2') == 'llm2'
            assert ComparisonEvaluationService.map_rating_to_selection('same') == 'tie'
            assert ComparisonEvaluationService.map_rating_to_selection('unknown') == 'error'

    def test_COMP_022_check_rating_match_same(self, app):
        """COMP-022: Rating-Match wenn User und AI gleich wählen."""
        with app.app_context():
            from services.comparison.evaluation_service import ComparisonEvaluationService

            assert ComparisonEvaluationService.check_rating_match('llm1', 'llm1') is True
            assert ComparisonEvaluationService.check_rating_match('llm2', 'llm2') is True
            assert ComparisonEvaluationService.check_rating_match('tie', 'tie') is True

    def test_COMP_023_check_rating_match_different(self, app):
        """COMP-023: Rating-Mismatch wenn User und AI unterschiedlich wählen."""
        with app.app_context():
            from services.comparison.evaluation_service import ComparisonEvaluationService

            assert ComparisonEvaluationService.check_rating_match('llm1', 'llm2') is False
            assert ComparisonEvaluationService.check_rating_match('llm2', 'tie') is False

    def test_COMP_024_check_rating_match_error(self, app):
        """COMP-024: Rating-Match bei AI-Error ist immer True."""
        with app.app_context():
            from services.comparison.evaluation_service import ComparisonEvaluationService

            assert ComparisonEvaluationService.check_rating_match('llm1', 'error') is True
            assert ComparisonEvaluationService.check_rating_match('llm2', 'error') is True

    def test_COMP_025_parse_message_content_json_string(self, app):
        """COMP-025: Message Content als JSON-String parsen."""
        with app.app_context():
            from services.comparison.evaluation_service import ComparisonEvaluationService

            content = json.dumps({'llm1': 'Response 1', 'llm2': 'Response 2'})
            result = ComparisonEvaluationService._parse_message_content(content)

            assert result is not None
            assert result['llm1'] == 'Response 1'
            assert result['llm2'] == 'Response 2'

    def test_COMP_026_parse_message_content_dict(self, app):
        """COMP-026: Message Content als Dict parsen."""
        with app.app_context():
            from services.comparison.evaluation_service import ComparisonEvaluationService

            content = {'llm1': 'Response 1', 'llm2': 'Response 2'}
            result = ComparisonEvaluationService._parse_message_content(content)

            assert result is not None
            assert result['llm1'] == 'Response 1'

    def test_COMP_027_parse_message_content_invalid_json(self, app):
        """COMP-027: Ungültiger JSON-String gibt None."""
        with app.app_context():
            from services.comparison.evaluation_service import ComparisonEvaluationService

            result = ComparisonEvaluationService._parse_message_content('invalid json')

            assert result is None

    def test_COMP_028_parse_message_content_missing_keys(self, app):
        """COMP-028: Dict ohne llm1/llm2 Keys gibt None."""
        with app.app_context():
            from services.comparison.evaluation_service import ComparisonEvaluationService

            content = {'only_one': 'value'}
            result = ComparisonEvaluationService._parse_message_content(content)

            assert result is None

    def test_COMP_029_save_user_justification(self, app, db, sample_session, sample_messages):
        """COMP-029: User-Begründung speichern."""
        with app.app_context():
            from services.comparison.evaluation_service import ComparisonEvaluationService
            from db.models.scenario import ComparisonEvaluation

            # Create evaluation first
            evaluation = ComparisonEvaluation(
                message_id=sample_messages[1]['id'],
                user_selection='llm1',
                ai_selection='llm1',
                ai_reason='Both responses are similar',
                match_result=True
            )
            db.session.add(evaluation)
            db.session.commit()

            result = ComparisonEvaluationService.save_user_justification(
                sample_messages[1]['id'],
                'Ich finde LLM1 empathischer'
            )

            assert result is True

            # Verify
            saved = ComparisonEvaluation.query.filter_by(
                message_id=sample_messages[1]['id']
            ).first()
            assert saved.user_justification == 'Ich finde LLM1 empathischer'

    def test_COMP_030_save_user_justification_no_evaluation(self, app):
        """COMP-030: Begründung speichern ohne existierende Evaluation gibt False."""
        with app.app_context():
            from services.comparison.evaluation_service import ComparisonEvaluationService

            result = ComparisonEvaluationService.save_user_justification(
                99999,
                'Some justification'
            )

            assert result is False

    def test_COMP_031_perform_evaluation_with_existing(self, app, db, sample_session, sample_messages):
        """COMP-031: Evaluation mit existierender AI-Bewertung durchführen."""
        with app.app_context():
            from services.comparison.evaluation_service import ComparisonEvaluationService
            from db.models.scenario import ComparisonEvaluation

            # Create pre-existing evaluation
            evaluation = ComparisonEvaluation(
                message_id=sample_messages[1]['id'],
                user_selection='',
                ai_selection='llm1',
                ai_reason='LLM1 shows more empathy',
                match_result=True
            )
            db.session.add(evaluation)
            db.session.commit()

            matches, details = ComparisonEvaluationService.perform_evaluation(
                sample_messages[1]['id'],
                sample_session['id'],
                'llm1'  # User selects same as AI
            )

            assert matches is True
            assert details['ai_selection'] == 'llm1'
            assert details['user_selection'] == 'llm1'

    def test_COMP_032_perform_evaluation_mismatch(self, app, db, sample_session, sample_messages):
        """COMP-032: Evaluation mit unterschiedlicher User/AI-Wahl."""
        with app.app_context():
            from services.comparison.evaluation_service import ComparisonEvaluationService
            from db.models.scenario import ComparisonEvaluation

            # Create pre-existing evaluation
            evaluation = ComparisonEvaluation(
                message_id=sample_messages[1]['id'],
                user_selection='',
                ai_selection='llm2',
                ai_reason='LLM2 is better',
                match_result=True
            )
            db.session.add(evaluation)
            db.session.commit()

            matches, details = ComparisonEvaluationService.perform_evaluation(
                sample_messages[1]['id'],
                sample_session['id'],
                'llm1'  # User selects different from AI
            )

            assert matches is False
            assert details['ai_selection'] == 'llm2'
            assert details['user_selection'] == 'llm1'


# =============================================================================
# PersonaFormatter Tests
# =============================================================================

class TestPersonaFormatter:
    """Tests für PersonaFormatter."""

    def test_COMP_040_format_complete_persona(self, app, sample_persona):
        """COMP-040: Vollständige Persona formatieren."""
        with app.app_context():
            from services.comparison.persona_formatter import PersonaFormatter

            result = PersonaFormatter.format(sample_persona)

            assert '## Persona: Maria Müller' in result
            assert '**Steckbrief:**' in result
            assert 'Alter' in result
            assert '45 Jahre' in result
            assert '**Hauptanliegen**' in result
            assert 'Stress am Arbeitsplatz' in result

    def test_COMP_041_format_none_persona(self, app):
        """COMP-041: None-Persona gibt leeren String."""
        with app.app_context():
            from services.comparison.persona_formatter import PersonaFormatter

            result = PersonaFormatter.format(None)

            assert result == ""

    def test_COMP_042_format_empty_persona(self, app):
        """COMP-042: Leeres Dict gibt leeren String (falsy check)."""
        with app.app_context():
            from services.comparison.persona_formatter import PersonaFormatter

            # Empty dict is falsy, so returns empty string
            result = PersonaFormatter.format({})

            assert result == ""

    def test_COMP_043_format_steckbrief(self, app, sample_persona):
        """COMP-043: Steckbrief-Sektion formatieren."""
        with app.app_context():
            from services.comparison.persona_formatter import PersonaFormatter

            result = PersonaFormatter.format(sample_persona)

            assert '**Steckbrief:**' in result
            assert '**Alter**: 45 Jahre' in result
            assert '**Beruf**: Krankenschwester' in result

    def test_COMP_044_format_hauptanliegen(self, app, sample_persona):
        """COMP-044: Hauptanliegen-Sektion formatieren."""
        with app.app_context():
            from services.comparison.persona_formatter import PersonaFormatter

            result = PersonaFormatter.format(sample_persona)

            assert '**Hauptanliegen**' in result
            assert 'Burnout' in result

    def test_COMP_045_format_nebenanliegen_list(self, app, sample_persona):
        """COMP-045: Nebenanliegen als Liste formatieren."""
        with app.app_context():
            from services.comparison.persona_formatter import PersonaFormatter

            result = PersonaFormatter.format(sample_persona)

            assert '**Nebenanliegen**' in result
            assert 'Schlafprobleme' in result
            assert 'Beziehungskonflikte' in result

    def test_COMP_046_format_emotionale_merkmale(self, app, sample_persona):
        """COMP-046: Emotionale Merkmale formatieren."""
        with app.app_context():
            from services.comparison.persona_formatter import PersonaFormatter

            result = PersonaFormatter.format(sample_persona)

            assert '**Emotionale Merkmale:**' in result
            assert 'angespannt und erschöpft' in result
            assert 'Frustration' in result

    def test_COMP_047_format_ressourcen(self, app, sample_persona):
        """COMP-047: Ressourcen-Sektion formatieren."""
        with app.app_context():
            from services.comparison.persona_formatter import PersonaFormatter

            result = PersonaFormatter.format(sample_persona)

            assert 'Ressourcen' in result
            assert 'Emotional' in result
            assert 'Ja' in result

    def test_COMP_048_format_soziales_umfeld_string(self, app, sample_persona):
        """COMP-048: Soziales Umfeld als String formatieren."""
        with app.app_context():
            from services.comparison.persona_formatter import PersonaFormatter

            result = PersonaFormatter.format(sample_persona)

            assert '**Soziales Umfeld**' in result
            assert 'alleinstehend' in result

    def test_COMP_049_format_prinzipien(self, app, sample_persona):
        """COMP-049: Konversationsprinzipien formatieren."""
        with app.app_context():
            from services.comparison.persona_formatter import PersonaFormatter

            result = PersonaFormatter.format(sample_persona)

            assert '**Konversationsprinzipien**' in result
            assert 'Provokationen' in result

    def test_COMP_050_get_persona_summary(self, app, sample_persona):
        """COMP-050: Persona-Summary für Counselor-Prompt abrufen."""
        with app.app_context():
            from services.comparison.persona_formatter import PersonaFormatter

            summary = PersonaFormatter.get_persona_summary(sample_persona)

            assert 'hauptanliegen' in summary
            assert 'Stress' in summary['hauptanliegen']
            assert 'nebenanliegen' in summary
            assert 'steckbrief' in summary

    def test_COMP_051_get_persona_summary_none(self, app):
        """COMP-051: Summary für None-Persona gibt leeres Dict."""
        with app.app_context():
            from services.comparison.persona_formatter import PersonaFormatter

            summary = PersonaFormatter.get_persona_summary(None)

            assert summary == {}


# =============================================================================
# ComparisonPromptGenerator Tests
# =============================================================================

class TestComparisonPromptGenerator:
    """Tests für ComparisonPromptGenerator."""

    def test_COMP_060_create_persona_prompt(self, app, sample_persona):
        """COMP-060: Persona-Prompt erstellen."""
        with app.app_context():
            from services.comparison.prompt_generator import ComparisonPromptGenerator

            prompt = ComparisonPromptGenerator.create_persona_prompt(
                sample_persona,
                'User: Hallo\nAssistant: Hallo'
            )

            assert 'Maria Müller' in prompt
            assert 'Rollenanweisung' in prompt
            assert 'Hallo' in prompt

    def test_COMP_061_create_persona_prompt_first_message(self, app, sample_persona):
        """COMP-061: Persona-Prompt für erste Nachricht enthält Hinweis."""
        with app.app_context():
            from services.comparison.prompt_generator import ComparisonPromptGenerator

            prompt = ComparisonPromptGenerator.create_persona_prompt(
                sample_persona,
                '',
                is_first_message=True
            )

            assert 'erste Nachricht' in prompt

    def test_COMP_062_create_counselor_suggestion_prompt(self, app, sample_persona):
        """COMP-062: Counselor-Suggestion-Prompt erstellen."""
        with app.app_context():
            from services.comparison.prompt_generator import ComparisonPromptGenerator

            chat_history = [
                {'role': 'assistant', 'content': 'Ich bin gestresst'},
                {'role': 'user', 'content': 'Das verstehe ich'}
            ]

            prompt = ComparisonPromptGenerator.create_counselor_suggestion_prompt(
                sample_persona,
                chat_history
            )

            assert 'Berater' in prompt
            assert 'Klient' in prompt
            assert 'empathische' in prompt.lower()

    def test_COMP_063_build_persona_info(self, app, sample_persona):
        """COMP-063: Persona-Info für Counselor-Prompt aufbauen."""
        with app.app_context():
            from services.comparison.prompt_generator import ComparisonPromptGenerator

            info = ComparisonPromptGenerator._build_persona_info(sample_persona)

            assert 'Hauptanliegen' in info
            assert 'Stress' in info

    def test_COMP_064_build_persona_info_none(self, app):
        """COMP-064: Persona-Info für None gibt leeren String."""
        with app.app_context():
            from services.comparison.prompt_generator import ComparisonPromptGenerator

            info = ComparisonPromptGenerator._build_persona_info(None)

            assert info == ""

    def test_COMP_065_build_chat_history_text(self, app):
        """COMP-065: Chat-History-Text aus Message-Liste aufbauen."""
        with app.app_context():
            from services.comparison.prompt_generator import ComparisonPromptGenerator

            chat_history = [
                {'role': 'assistant', 'content': 'Ich bin müde'},
                {'role': 'user', 'content': 'Was belastet Sie?'},
                {'role': 'assistant', 'content': 'Die Arbeit'}
            ]

            text = ComparisonPromptGenerator._build_chat_history_text(chat_history)

            assert 'Klient: Ich bin müde' in text
            assert 'Berater: Was belastet Sie?' in text

    def test_COMP_066_build_chat_history_text_empty(self, app):
        """COMP-066: Leere Chat-History gibt leeren String."""
        with app.app_context():
            from services.comparison.prompt_generator import ComparisonPromptGenerator

            text = ComparisonPromptGenerator._build_chat_history_text([])

            assert text == ""

    def test_COMP_067_build_chat_history_text_max_messages(self, app):
        """COMP-067: Chat-History auf max_messages begrenzt."""
        with app.app_context():
            from services.comparison.prompt_generator import ComparisonPromptGenerator

            # Create 10 messages
            chat_history = [
                {'role': 'user' if i % 2 == 0 else 'assistant', 'content': f'Message {i}'}
                for i in range(10)
            ]

            text = ComparisonPromptGenerator._build_chat_history_text(chat_history, max_messages=3)

            # Should only contain last 3 messages
            assert 'Message 7' in text
            assert 'Message 8' in text
            assert 'Message 9' in text
            assert 'Message 0' not in text


# =============================================================================
# LLMResponseGenerator Tests (Mocked)
# =============================================================================

class TestLLMResponseGenerator:
    """Tests für LLMResponseGenerator (mit Mocks)."""

    def test_COMP_070_init_default_config(self, app):
        """COMP-070: Default-Konfiguration bei Initialisierung."""
        with app.app_context():
            from services.comparison.response_generator import LLMResponseGenerator

            generator = LLMResponseGenerator()

            assert generator.ssh_container == LLMResponseGenerator.DEFAULT_SSH_CONTAINER
            assert generator.ssh_container_port == LLMResponseGenerator.DEFAULT_SSH_CONTAINER_PORT

    def test_COMP_071_init_custom_config(self, app):
        """COMP-071: Custom-Konfiguration bei Initialisierung."""
        with app.app_context():
            from services.comparison.response_generator import LLMResponseGenerator

            generator = LLMResponseGenerator(
                ssh_container='custom_container',
                ssh_container_port='9999'
            )

            assert generator.ssh_container == 'custom_container'
            assert generator.ssh_container_port == '9999'

    @patch('services.comparison.response_generator.LLMModel')
    def test_COMP_072_get_default_llm_model_id_success(self, mock_llm_model, app):
        """COMP-072: Default LLM Model ID erfolgreich abrufen."""
        with app.app_context():
            from services.comparison.response_generator import LLMResponseGenerator

            mock_llm_model.get_default_model_id.return_value = 'gpt-4-turbo'
            mock_llm_model.MODEL_TYPE_LLM = 'llm'

            model_id = LLMResponseGenerator._get_default_llm_model_id()

            assert model_id == 'gpt-4-turbo'

    @patch('services.comparison.response_generator.LLMModel')
    def test_COMP_073_get_default_llm_model_id_not_configured(self, mock_llm_model, app):
        """COMP-073: Fehler wenn kein Default LLM konfiguriert."""
        with app.app_context():
            from services.comparison.response_generator import LLMResponseGenerator

            mock_llm_model.get_default_model_id.return_value = None
            mock_llm_model.MODEL_TYPE_LLM = 'llm'

            with pytest.raises(RuntimeError, match="No default LLM model"):
                LLMResponseGenerator._get_default_llm_model_id()

    def test_COMP_074_generate_comparison_responses_emits_started(
        self, app, sample_session, sample_persona
    ):
        """COMP-074: generate_comparison_responses sendet streaming_started Event."""
        with app.app_context():
            from services.comparison.response_generator import LLMResponseGenerator
            from services.comparison.session_service import ComparisonSessionService
            from db.models.scenario import ComparisonSession

            # Setup mocks
            mock_socket = MagicMock()
            session = ComparisonSession.query.get(sample_session['id'])

            generator = LLMResponseGenerator()

            # Mock internal methods and app import
            with patch.object(generator, '_generate_llm_response'):
                with patch('services.comparison.response_generator.ComparisonSessionService') as mock_svc:
                    mock_svc.get_session_by_id.return_value = session
                    mock_svc.build_chat_history.return_value = []

                    # Mock the app import inside the method
                    with patch.dict('sys.modules', {'main': MagicMock(app=app)}):
                        generator.generate_comparison_responses(
                            session,
                            message_id=1,
                            socketio=mock_socket,
                            client_id='test-client'
                        )

            # Check streaming_started was emitted
            mock_socket.emit.assert_called()
            calls = [c for c in mock_socket.emit.call_args_list if c[0][0] == 'streaming_started']
            assert len(calls) >= 1

    @patch('services.comparison.response_generator.OpenAI')
    @patch('services.comparison.response_generator.ComparisonSessionService')
    @patch('services.comparison.response_generator.LLMResponseGenerator._get_default_llm_model_id')
    def test_COMP_075_generate_counselor_suggestion_returns_string(
        self, mock_get_model, mock_session_service, mock_openai, app, sample_session, sample_persona
    ):
        """COMP-075: generate_counselor_suggestion gibt String zurück."""
        with app.app_context():
            from services.comparison.response_generator import LLMResponseGenerator
            from db.models.scenario import ComparisonSession

            # Setup mocks
            session = ComparisonSession.query.get(sample_session['id'])
            mock_session_service.get_session_by_id.return_value = session
            mock_session_service.build_chat_history.return_value = []
            mock_get_model.return_value = 'test-model'

            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message = MagicMock()
            mock_response.choices[0].message.content = 'Wie kann ich Ihnen helfen?'

            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            with patch('services.comparison.response_generator.extract_message_text',
                      return_value='Wie kann ich Ihnen helfen?'):
                result = LLMResponseGenerator.generate_counselor_suggestion(session)

            assert isinstance(result, str)
            assert len(result) > 0

    @patch('services.comparison.response_generator.OpenAI')
    @patch('services.comparison.response_generator.ComparisonSessionService')
    def test_COMP_076_generate_counselor_suggestion_error_fallback(
        self, mock_session_service, mock_openai, app, sample_session
    ):
        """COMP-076: generate_counselor_suggestion gibt Fallback bei Fehler."""
        with app.app_context():
            from services.comparison.response_generator import LLMResponseGenerator
            from db.models.scenario import ComparisonSession

            session = ComparisonSession.query.get(sample_session['id'])
            mock_session_service.get_session_by_id.side_effect = Exception("API Error")

            result = LLMResponseGenerator.generate_counselor_suggestion(session)

            assert result == "Wie fühlen Sie sich in dieser Situation?"


# =============================================================================
# Integration Tests
# =============================================================================

class TestComparisonIntegration:
    """Integration Tests für Comparison Services."""

    def test_COMP_080_full_message_flow(self, app, sample_session):
        """COMP-080: Kompletter Message-Flow (add, serialize, select)."""
        with app.app_context():
            from services.comparison.session_service import ComparisonSessionService

            # Add user message
            user_msg_id = ComparisonSessionService.add_message(
                session_id=sample_session['id'],
                idx=0,
                message_type='user',
                content='Hallo, wie geht es Ihnen?'
            )

            # Add bot pair message
            bot_content = json.dumps({'llm1': '', 'llm2': ''})
            bot_msg_id = ComparisonSessionService.add_message(
                session_id=sample_session['id'],
                idx=1,
                message_type='bot_pair',
                content=bot_content
            )

            # Update bot responses
            ComparisonSessionService.update_message_content(bot_msg_id, 'llm1', 'Mir geht es gut.')
            ComparisonSessionService.update_message_content(bot_msg_id, 'llm2', 'Ich bin erschöpft.')

            # Check completion
            assert ComparisonSessionService.is_response_complete(bot_msg_id)

            # Set selection
            ComparisonSessionService.set_message_selected(bot_msg_id, sample_session['id'], 'llm2')

            # Get all messages
            messages = ComparisonSessionService.get_all_messages(sample_session['id'])
            assert len(messages) == 2

            # Verify serialization
            from db.models.scenario import ComparisonMessage
            bot_msg = ComparisonMessage.query.get(bot_msg_id)
            serialized = ComparisonSessionService.serialize_message(bot_msg)

            assert serialized['selected'] == 'llm2'
            assert serialized['content']['llm1'] == 'Mir geht es gut.'
            assert serialized['content']['llm2'] == 'Ich bin erschöpft.'

    def test_COMP_081_evaluation_flow(self, app, db, sample_session, sample_messages):
        """COMP-081: Kompletter Evaluation-Flow."""
        with app.app_context():
            from services.comparison.evaluation_service import ComparisonEvaluationService
            from db.models.scenario import ComparisonEvaluation

            # Pre-create AI evaluation
            evaluation = ComparisonEvaluation(
                message_id=sample_messages[1]['id'],
                user_selection='',
                ai_selection='llm1',
                ai_reason='LLM1 zeigt mehr Empathie',
                match_result=True
            )
            db.session.add(evaluation)
            db.session.commit()

            # User makes selection
            matches, details = ComparisonEvaluationService.perform_evaluation(
                sample_messages[1]['id'],
                sample_session['id'],
                'llm1'
            )

            # Save justification
            ComparisonEvaluationService.save_user_justification(
                sample_messages[1]['id'],
                'Die Antwort war authentischer'
            )

            # Verify
            saved = ComparisonEvaluation.query.filter_by(
                message_id=sample_messages[1]['id']
            ).first()

            assert saved.user_selection == 'llm1'
            assert saved.user_justification == 'Die Antwort war authentischer'
            assert saved.match_result is True

    def test_COMP_082_persona_in_prompt_flow(self, app, sample_persona):
        """COMP-082: Persona-Formatierung in Prompt-Generierung."""
        with app.app_context():
            from services.comparison.persona_formatter import PersonaFormatter
            from services.comparison.prompt_generator import ComparisonPromptGenerator

            # Format persona
            formatted = PersonaFormatter.format(sample_persona)

            # Create prompt with formatted persona
            prompt = ComparisonPromptGenerator.create_persona_prompt(
                sample_persona,
                'User: Hallo'
            )

            # Verify persona details are in prompt
            assert 'Maria Müller' in prompt
            assert 'Stress' in prompt or 'Burnout' in prompt
