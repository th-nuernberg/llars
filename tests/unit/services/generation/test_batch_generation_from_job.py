"""
Tests for BatchGenerationService from_job chain resolution.

Covers the _build_generation_matrix() logic when source_type='from_job',
including chain walking, terminal source resolution, and error handling.

Test IDs: [BATCH_FROM_JOB_001] through [BATCH_FROM_JOB_014]
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from uuid import uuid4


# =============================================================================
# Helpers
# =============================================================================

def _make_generation_job(db, *, name='Test Job', status='completed',
                         config_json=None, created_by='admin'):
    """Create a GenerationJob row."""
    from db.models.generation import GenerationJob, GenerationJobStatus
    job = GenerationJob(
        name=name,
        status=GenerationJobStatus.COMPLETED if status == 'completed' else GenerationJobStatus.CREATED,
        config_json=config_json or {},
        total_items=0,
        completed_items=0,
        failed_items=0,
        total_tokens=0,
        total_cost_usd=0.0,
        created_by=created_by,
    )
    db.session.add(job)
    db.session.flush()
    return job


def _make_scenario_with_items(db, *, num_items=3, created_by='admin'):
    """Create a scenario with linked EvaluationItems, return (scenario, item_ids)."""
    from db.models.scenario import RatingScenarios, EvaluationItem, ScenarioItems
    scenario = RatingScenarios(
        scenario_name='Source Scenario',
        function_type_id=1,
        begin=datetime.utcnow(),
        end=datetime.utcnow(),
        created_by=created_by,
    )
    db.session.add(scenario)
    db.session.flush()

    item_ids = []
    for i in range(num_items):
        item = EvaluationItem(
            subject=f'Item {i}',
            chat_id=9000 + i,
            institut_id=9000 + i,
            function_type_id=1,
        )
        db.session.add(item)
        db.session.flush()
        si = ScenarioItems(scenario_id=scenario.id, item_id=item.item_id)
        db.session.add(si)
        item_ids.append(item.item_id)

    db.session.flush()
    return scenario, item_ids


def _make_prompt(db):
    """Create a UserPrompt and return its prompt_id (used in config.prompts)."""
    from db.models.scenario import UserPrompt
    from db.models.user import User

    # Ensure a user exists for the FK constraint
    user = User.query.filter_by(username='admin').first()
    if not user:
        user = User(username='admin', password_hash='x', api_key=str(uuid4()), is_active=True)
        db.session.add(user)
        db.session.flush()

    prompt = UserPrompt(
        name='Test Prompt',
        user_id=user.id,
        content={'blocks': [{'type': 'text', 'content': 'Summarize: {{input}}'}]},
    )
    db.session.add(prompt)
    db.session.flush()
    return prompt.prompt_id


def _base_config(source_type, source_data, prompt_template_id):
    """Build a minimal valid generation config."""
    return {
        'sources': {'type': source_type, **source_data},
        'prompts': [{'template_id': prompt_template_id, 'variant_name': 'Test'}],
        'llm_models': ['Global/OpenAI/gpt-5-nano'],
    }


# =============================================================================
# Tests: from_job → scenario (single hop)
# =============================================================================

class TestFromJobScenarioSource:
    """Tests for from_job resolving to a scenario source."""

    def test_BATCH_FROM_JOB_001_single_hop_scenario(self, app, db, app_context):
        """
        [BATCH_FROM_JOB_001] from_job with scenario source resolves items correctly.

        Chain: new_job --from_job--> job_A (scenario source)
        Expected: Matrix uses items from the original scenario.
        """
        from services.generation.batch_generation_service import BatchGenerationService

        scenario, item_ids = _make_scenario_with_items(db, num_items=3)
        prompt_id = _make_prompt(db)

        # Job A: original job sourced from scenario
        job_a = _make_generation_job(db, config_json=_base_config(
            'scenario', {'scenario_id': scenario.id}, prompt_id
        ))
        db.session.commit()

        # Build matrix for a new job that uses from_job → job_a
        config = _base_config('from_job', {'job_id': job_a.id}, prompt_id)
        matrix = BatchGenerationService._build_generation_matrix(999, config)

        # 3 items × 1 prompt × 1 model = 3 outputs
        assert len(matrix) == 3
        resolved_item_ids = sorted(e['source_item_id'] for e in matrix)
        assert resolved_item_ids == sorted(item_ids)

    def test_BATCH_FROM_JOB_002_scenario_multiple_models(self, app, db, app_context):
        """
        [BATCH_FROM_JOB_002] from_job matrix expands correctly with multiple models.

        Chain: new_job --from_job--> job_A (scenario, 2 items)
        Config: 2 models → 2×1×2 = 4 matrix entries
        """
        from services.generation.batch_generation_service import BatchGenerationService

        scenario, item_ids = _make_scenario_with_items(db, num_items=2)
        prompt_id = _make_prompt(db)

        job_a = _make_generation_job(db, config_json=_base_config(
            'scenario', {'scenario_id': scenario.id}, prompt_id
        ))
        db.session.commit()

        config = {
            'sources': {'type': 'from_job', 'job_id': job_a.id},
            'prompts': [{'template_id': prompt_id, 'variant_name': 'Test'}],
            'llm_models': ['Global/OpenAI/gpt-5-nano', 'Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506'],
        }
        matrix = BatchGenerationService._build_generation_matrix(999, config)

        assert len(matrix) == 4  # 2 items × 1 prompt × 2 models


# =============================================================================
# Tests: from_job → from_job chain (multi-hop)
# =============================================================================

class TestFromJobChainWalking:
    """Tests for multi-hop from_job chain resolution."""

    def test_BATCH_FROM_JOB_003_two_hop_chain(self, app, db, app_context):
        """
        [BATCH_FROM_JOB_003] Two-hop chain resolves to original scenario.

        Chain: new_job --from_job--> job_B --from_job--> job_A (scenario)
        """
        from services.generation.batch_generation_service import BatchGenerationService

        scenario, item_ids = _make_scenario_with_items(db, num_items=4)
        prompt_id = _make_prompt(db)

        job_a = _make_generation_job(db, name='Job A', config_json=_base_config(
            'scenario', {'scenario_id': scenario.id}, prompt_id
        ))
        job_b = _make_generation_job(db, name='Job B', config_json=_base_config(
            'from_job', {'job_id': job_a.id}, prompt_id
        ))
        db.session.commit()

        config = _base_config('from_job', {'job_id': job_b.id}, prompt_id)
        matrix = BatchGenerationService._build_generation_matrix(999, config)

        assert len(matrix) == 4
        resolved_ids = sorted(e['source_item_id'] for e in matrix)
        assert resolved_ids == sorted(item_ids)

    def test_BATCH_FROM_JOB_004_three_hop_chain(self, app, db, app_context):
        """
        [BATCH_FROM_JOB_004] Three-hop chain resolves correctly.

        Chain: new → C → B → A (scenario)
        """
        from services.generation.batch_generation_service import BatchGenerationService

        scenario, item_ids = _make_scenario_with_items(db, num_items=2)
        prompt_id = _make_prompt(db)

        job_a = _make_generation_job(db, name='A', config_json=_base_config(
            'scenario', {'scenario_id': scenario.id}, prompt_id
        ))
        job_b = _make_generation_job(db, name='B', config_json=_base_config(
            'from_job', {'job_id': job_a.id}, prompt_id
        ))
        job_c = _make_generation_job(db, name='C', config_json=_base_config(
            'from_job', {'job_id': job_b.id}, prompt_id
        ))
        db.session.commit()

        config = _base_config('from_job', {'job_id': job_c.id}, prompt_id)
        matrix = BatchGenerationService._build_generation_matrix(999, config)

        assert len(matrix) == 2
        assert sorted(e['source_item_id'] for e in matrix) == sorted(item_ids)

    def test_BATCH_FROM_JOB_005_chain_depth_limit(self, app, db, app_context):
        """
        [BATCH_FROM_JOB_005] Chain deeper than 10 hops raises ValidationError.

        Builds a chain of 12 from_job hops (no terminal source reachable).
        """
        from services.generation.batch_generation_service import BatchGenerationService
        from decorators.error_handler import ValidationError

        prompt_id = _make_prompt(db)

        # Build a chain of 12 jobs, each pointing to the previous
        jobs = []
        for i in range(12):
            if i == 0:
                # First job also points to from_job (a loop-like structure)
                cfg = _base_config('from_job', {'job_id': 0}, prompt_id)  # placeholder
            else:
                cfg = _base_config('from_job', {'job_id': jobs[-1].id}, prompt_id)
            j = _make_generation_job(db, name=f'Chain-{i}', config_json=cfg)
            jobs.append(j)

        # Fix the first job to point to itself (creates circular-ish chain)
        jobs[0].config_json = _base_config('from_job', {'job_id': jobs[0].id}, prompt_id)
        db.session.commit()

        config = _base_config('from_job', {'job_id': jobs[-1].id}, prompt_id)

        with pytest.raises(ValidationError, match="chain too deep"):
            BatchGenerationService._build_generation_matrix(999, config)


# =============================================================================
# Tests: from_job → other terminal source types
# =============================================================================

class TestFromJobTerminalSources:
    """Tests for from_job resolving to non-scenario terminal sources."""

    def test_BATCH_FROM_JOB_006_manual_source(self, app, db, app_context):
        """
        [BATCH_FROM_JOB_006] from_job resolving to manual source preserves items.

        Chain: new_job → job_A (manual source with 2 items)
        """
        from services.generation.batch_generation_service import BatchGenerationService

        prompt_id = _make_prompt(db)
        manual_items = [
            {'input': 'First text to process'},
            {'input': 'Second text to process'},
        ]
        job_a = _make_generation_job(db, config_json={
            'sources': {'type': 'manual', 'items': manual_items},
            'prompts': [{'template_id': prompt_id, 'variant_name': 'Test'}],
            'llm_models': ['Global/OpenAI/gpt-5-nano'],
        })
        db.session.commit()

        config = _base_config('from_job', {'job_id': job_a.id}, prompt_id)
        matrix = BatchGenerationService._build_generation_matrix(999, config)

        assert len(matrix) == 2
        texts = sorted(e['custom_text'] for e in matrix)
        assert texts == ['First text to process', 'Second text to process']

    def test_BATCH_FROM_JOB_007_manual_structured_messages(self, app, db, app_context):
        """
        [BATCH_FROM_JOB_007] from_job with manual structured messages preserves subject/messages.

        Chain: new_job → job_A (manual with email-style messages)
        """
        from services.generation.batch_generation_service import BatchGenerationService

        prompt_id = _make_prompt(db)
        manual_items = [
            {
                'subject': 'Help Request',
                'messages': [
                    {'role': 'Client', 'content': 'I need help'},
                    {'role': 'Advisor', 'content': 'How can I assist?'},
                ],
            },
        ]
        job_a = _make_generation_job(db, config_json={
            'sources': {'type': 'manual', 'items': manual_items},
            'prompts': [{'template_id': prompt_id, 'variant_name': 'Test'}],
            'llm_models': ['Global/OpenAI/gpt-5-nano'],
        })
        db.session.commit()

        config = _base_config('from_job', {'job_id': job_a.id}, prompt_id)
        matrix = BatchGenerationService._build_generation_matrix(999, config)

        assert len(matrix) == 1
        entry = matrix[0]
        assert 'Help Request' in entry['custom_text']
        assert 'I need help' in entry['custom_text']
        assert entry['structured_data']['subject'] == 'Help Request'
        assert len(entry['structured_data']['messages']) == 2

    def test_BATCH_FROM_JOB_008_custom_texts_source(self, app, db, app_context):
        """
        [BATCH_FROM_JOB_008] from_job resolving to custom texts source.

        Chain: new_job → job_A (custom texts)
        """
        from services.generation.batch_generation_service import BatchGenerationService

        prompt_id = _make_prompt(db)
        job_a = _make_generation_job(db, config_json={
            'sources': {'type': 'custom', 'custom_texts': ['Alpha', 'Beta', 'Gamma']},
            'prompts': [{'template_id': prompt_id, 'variant_name': 'Test'}],
            'llm_models': ['Global/OpenAI/gpt-5-nano'],
        })
        db.session.commit()

        config = _base_config('from_job', {'job_id': job_a.id}, prompt_id)
        matrix = BatchGenerationService._build_generation_matrix(999, config)

        assert len(matrix) == 3
        texts = sorted(e['custom_text'] for e in matrix)
        assert texts == ['Alpha', 'Beta', 'Gamma']

    def test_BATCH_FROM_JOB_009_prompt_only_source(self, app, db, app_context):
        """
        [BATCH_FROM_JOB_009] from_job resolving to prompt_only source.

        Chain: new_job → job_A (prompt_only)
        """
        from services.generation.batch_generation_service import BatchGenerationService

        prompt_id = _make_prompt(db)
        job_a = _make_generation_job(db, config_json={
            'sources': {'type': 'prompt_only'},
            'prompts': [{'template_id': prompt_id, 'variant_name': 'Test'}],
            'llm_models': ['Global/OpenAI/gpt-5-nano'],
        })
        db.session.commit()

        config = _base_config('from_job', {'job_id': job_a.id}, prompt_id)
        matrix = BatchGenerationService._build_generation_matrix(999, config)

        # prompt_only: 1 empty input × 1 prompt × 1 model = 1
        assert len(matrix) == 1
        assert matrix[0]['source_item_id'] is None
        assert matrix[0]['custom_text'] == ''

    def test_BATCH_FROM_JOB_010_items_source(self, app, db, app_context):
        """
        [BATCH_FROM_JOB_010] from_job resolving to items source (direct item IDs).

        Chain: new_job → job_A (items source)
        """
        from services.generation.batch_generation_service import BatchGenerationService
        from db.models.scenario import EvaluationItem

        prompt_id = _make_prompt(db)

        # Create standalone items (not in a scenario)
        items = []
        for i in range(2):
            item = EvaluationItem(
                subject=f'Standalone {i}', chat_id=8000 + i,
                institut_id=8000 + i, function_type_id=1,
            )
            db.session.add(item)
            db.session.flush()
            items.append(item)

        item_ids = [it.item_id for it in items]
        job_a = _make_generation_job(db, config_json={
            'sources': {'type': 'items', 'item_ids': item_ids},
            'prompts': [{'template_id': prompt_id, 'variant_name': 'Test'}],
            'llm_models': ['Global/OpenAI/gpt-5-nano'],
        })
        db.session.commit()

        config = _base_config('from_job', {'job_id': job_a.id}, prompt_id)
        matrix = BatchGenerationService._build_generation_matrix(999, config)

        assert len(matrix) == 2
        resolved_ids = sorted(e['source_item_id'] for e in matrix)
        assert resolved_ids == sorted(item_ids)


# =============================================================================
# Tests: Error handling
# =============================================================================

class TestFromJobErrors:
    """Tests for from_job error conditions."""

    def test_BATCH_FROM_JOB_011_nonexistent_source_job(self, app, db, app_context):
        """
        [BATCH_FROM_JOB_011] from_job with nonexistent job_id raises ValidationError.
        """
        from services.generation.batch_generation_service import BatchGenerationService
        from decorators.error_handler import ValidationError

        prompt_id = _make_prompt(db)
        db.session.commit()

        config = _base_config('from_job', {'job_id': 99999}, prompt_id)

        with pytest.raises(ValidationError, match="not found"):
            BatchGenerationService._build_generation_matrix(999, config)

    def test_BATCH_FROM_JOB_012_broken_chain_missing_intermediate(self, app, db, app_context):
        """
        [BATCH_FROM_JOB_012] Chain with missing intermediate job raises ValidationError.

        Chain: new → job_B (from_job → job_id=99999 which doesn't exist)
        """
        from services.generation.batch_generation_service import BatchGenerationService
        from decorators.error_handler import ValidationError

        prompt_id = _make_prompt(db)
        job_b = _make_generation_job(db, config_json=_base_config(
            'from_job', {'job_id': 99999}, prompt_id
        ))
        db.session.commit()

        config = _base_config('from_job', {'job_id': job_b.id}, prompt_id)

        with pytest.raises(ValidationError, match="not found"):
            BatchGenerationService._build_generation_matrix(999, config)

    def test_BATCH_FROM_JOB_013_missing_job_id_in_config(self, app, db, app_context):
        """
        [BATCH_FROM_JOB_013] from_job source without job_id fails validation.
        """
        from services.generation.batch_generation_service import BatchGenerationService
        from decorators.error_handler import ValidationError

        prompt_id = _make_prompt(db)
        db.session.commit()

        config = {
            'sources': {'type': 'from_job'},  # Missing job_id
            'prompts': [{'template_id': prompt_id, 'variant_name': 'Test'}],
            'llm_models': ['Global/OpenAI/gpt-5-nano'],
        }

        with pytest.raises(ValidationError, match="requires 'job_id'"):
            BatchGenerationService._validate_config(config)


# =============================================================================
# Tests: from_job chain with different new prompts/models
# =============================================================================

class TestFromJobNewConfig:
    """Tests that from_job uses the NEW job's prompts/models, not the source job's."""

    def test_BATCH_FROM_JOB_014_new_prompts_override_source(self, app, db, app_context):
        """
        [BATCH_FROM_JOB_014] New job uses its own prompts/models, not the source job's.

        Source job: 1 prompt, 1 model → new job: 2 prompts, 1 model
        Expected: matrix uses new job's 2 prompts, not source's 1.
        """
        from services.generation.batch_generation_service import BatchGenerationService
        from db.models.scenario import UserPrompt

        prompt_id_1 = _make_prompt(db)

        from db.models.user import User
        admin = User.query.filter_by(username='admin').first()
        prompt_2 = UserPrompt(
            name='Second Prompt',
            user_id=admin.id,
            content={'blocks': [{'type': 'text', 'content': 'Analyze: {{input}}'}]},
        )
        db.session.add(prompt_2)
        db.session.flush()
        prompt_id_2 = prompt_2.prompt_id

        scenario, item_ids = _make_scenario_with_items(db, num_items=2)

        # Source job with 1 prompt
        job_a = _make_generation_job(db, config_json=_base_config(
            'scenario', {'scenario_id': scenario.id}, prompt_id_1
        ))
        db.session.commit()

        # New job uses from_job but with 2 prompts
        config = {
            'sources': {'type': 'from_job', 'job_id': job_a.id},
            'prompts': [
                {'template_id': prompt_id_1, 'variant_name': 'Summarize'},
                {'template_id': prompt_id_2, 'variant_name': 'Analyze'},
            ],
            'llm_models': ['Global/OpenAI/gpt-5-nano'],
        }
        matrix = BatchGenerationService._build_generation_matrix(999, config)

        # 2 items × 2 prompts × 1 model = 4
        assert len(matrix) == 4

        # Verify both prompts are used
        prompt_ids_used = {e['prompt_config']['template_id'] for e in matrix}
        assert prompt_ids_used == {prompt_id_1, prompt_id_2}
