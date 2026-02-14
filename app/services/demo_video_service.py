"""
Demo Video Data Service for IJCAI 2026

Core logic for seeding/cleanup of demo video data.
Used by both CLI script (scripts/demo_video_manage.py) and API routes.
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger('demo_video_service')

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PRESEED_PROMPT_NAME = "Structured Situation Analysis"
PRESEED_JOB_NAME = "Counselling Situation Extraction"
LIVE_PROMPT_NAME = "Situation Summary"
LIVE_JOB_NAME = "Live Collab Batch Job"
EVAL_SCENARIO_NAME = "IJCAI Counselling Evaluation"

DEMO_USER = "ijcai_reviewer_1"
COLLAB_USER = "ijcai_reviewer_2"


def get_status():
    """Return structured status of demo data."""
    from db.tables import User, UserPrompt
    from db.models.generation import GenerationJob, GeneratedOutput
    from db.models.scenario import RatingScenarios, UserPromptShare

    demo_user = User.query.filter_by(username=DEMO_USER).first()
    if not demo_user:
        return {'error': f"User '{DEMO_USER}' not found"}

    result = {'user': DEMO_USER, 'prompts': {}, 'jobs': {}, 'scenarios': []}

    for name in [PRESEED_PROMPT_NAME, LIVE_PROMPT_NAME]:
        p = UserPrompt.query.filter_by(user_id=demo_user.id, name=name).first()
        if p:
            shares = UserPromptShare.query.filter_by(prompt_id=p.prompt_id).all()
            result['prompts'][name] = {
                'exists': True, 'id': p.prompt_id,
                'shared_with': [s.shared_with_user.username for s in shares if s.shared_with_user]
            }
        else:
            result['prompts'][name] = {'exists': False}

    for name in [PRESEED_JOB_NAME, LIVE_JOB_NAME]:
        j = GenerationJob.query.filter_by(name=name, created_by=DEMO_USER).first()
        if j:
            output_count = GeneratedOutput.query.filter_by(job_id=j.id).count()
            result['jobs'][name] = {
                'exists': True, 'id': j.id,
                'status': j.status.value, 'outputs': output_count
            }
        else:
            result['jobs'][name] = {'exists': False}

    scenarios = RatingScenarios.query.filter(
        RatingScenarios.scenario_name.contains("Situation")
    ).all()
    result['scenarios'] = [
        {'name': s.scenario_name, 'id': s.id, 'created_by': s.created_by}
        for s in scenarios
    ]

    return result


def seed():
    """Seed pre-recording data. Returns dict with results."""
    from db import db as _db
    from db.tables import User, UserPrompt
    from db.models.generation import (
        GenerationJob, GeneratedOutput,
        GenerationJobStatus, GeneratedOutputStatus,
    )
    from db.models.llm_model import LLMModel
    from db.models.scenario import UserPromptShare
    from db.seeders.demo_video_data import COUNSELLING_CASES, SAMPLE_OUTPUTS

    actions = []

    demo_user = User.query.filter_by(username=DEMO_USER).first()
    if not demo_user:
        return {'success': False, 'error': f"User '{DEMO_USER}' not found"}

    collab_user = User.query.filter_by(username=COLLAB_USER).first()

    # --- 1. Create pre-seed prompt ---
    preseed = UserPrompt.query.filter_by(
        user_id=demo_user.id, name=PRESEED_PROMPT_NAME
    ).first()

    if not preseed:
        preseed = UserPrompt(
            user_id=demo_user.id,
            name=PRESEED_PROMPT_NAME,
            content=_build_preseed_prompt_content()
        )
        _db.session.add(preseed)
        _db.session.flush()
        actions.append(f"Created prompt '{PRESEED_PROMPT_NAME}' (id={preseed.prompt_id})")
    else:
        actions.append(f"Prompt '{PRESEED_PROMPT_NAME}' already exists (id={preseed.prompt_id})")

    # Share with collab user
    if collab_user:
        existing_share = UserPromptShare.query.filter_by(
            prompt_id=preseed.prompt_id,
            shared_with_user_id=collab_user.id
        ).first()
        if not existing_share:
            _db.session.add(UserPromptShare(
                prompt_id=preseed.prompt_id,
                shared_with_user_id=collab_user.id
            ))
            actions.append(f"Shared '{PRESEED_PROMPT_NAME}' with {COLLAB_USER}")

    _db.session.commit()

    # --- 2. Create completed generation job ---
    existing_job = GenerationJob.query.filter_by(
        name=PRESEED_JOB_NAME, created_by=DEMO_USER
    ).first()
    if existing_job:
        actions.append(f"Job '{PRESEED_JOB_NAME}' already exists (id={existing_job.id})")
    else:
        mistral = LLMModel.query.filter_by(
            model_id='LiteLLM/mistralai/Mistral-Small-3.2-24B-Instruct-2506'
        ).first()
        gpt5_nano = LLMModel.query.filter_by(
            model_id='OpenAI/gpt-5-nano'
        ).first()

        if not mistral or not gpt5_nano:
            actions.append("Required LLM models not found, skipping job seeding")
            return {'success': True, 'actions': actions, 'warning': 'no_models'}

        # Temporarily create eval prompt for rendering
        temp_eval = UserPrompt(
            user_id=demo_user.id,
            name="_temp_eval_prompt",
            content=_build_eval_prompt_content()
        )
        _db.session.add(temp_eval)
        _db.session.flush()

        now = datetime.utcnow()
        total_outputs = len(COUNSELLING_CASES) * 2 * 2

        job = GenerationJob(
            name=PRESEED_JOB_NAME,
            description="Demo batch: two prompts x two models x 10 counselling cases.",
            status=GenerationJobStatus.COMPLETED,
            config_json={
                "mode": "matrix",
                "sources": {"type": "manual", "items": COUNSELLING_CASES},
                "prompts": [
                    {"template_name": PRESEED_PROMPT_NAME},
                    {"template_name": LIVE_PROMPT_NAME}
                ],
                "llm_models": [mistral.model_id, gpt5_nano.model_id],
                "generation_params": {"temperature": 0.7, "max_tokens": 500}
            },
            total_items=total_outputs,
            completed_items=total_outputs,
            failed_items=0,
            total_tokens=total_outputs * 800,
            total_cost_usd=0.05,
            created_by=DEMO_USER,
            created_at=now - timedelta(hours=2),
            started_at=now - timedelta(hours=2),
            completed_at=now - timedelta(hours=1, minutes=45)
        )
        _db.session.add(job)
        _db.session.flush()

        output_idx = 0
        for case_idx, case in enumerate(COUNSELLING_CASES):
            for summary_key, prompt_obj, prompt_name in [
                ("structured", preseed, PRESEED_PROMPT_NAME),
                ("narrative", temp_eval, LIVE_PROMPT_NAME),
            ]:
                for model in [mistral, gpt5_nano]:
                    output_text = SAMPLE_OUTPUTS[summary_key][case_idx]
                    sys_prompt = _render_system(prompt_obj)
                    usr_prompt = _render_user(prompt_obj, case)

                    _db.session.add(GeneratedOutput(
                        job_id=job.id,
                        llm_model_id=model.id,
                        llm_model_name=model.model_id,
                        prompt_variant_name=prompt_name,
                        prompt_variables_json={
                            'source_index': case_idx,
                            'source_subject': case['subject']
                        },
                        generated_content=output_text,
                        rendered_system_prompt=sys_prompt,
                        rendered_user_prompt=usr_prompt,
                        status=GeneratedOutputStatus.COMPLETED,
                        input_tokens=len(case['content'].split()) + 50,
                        output_tokens=len(output_text.split()),
                        total_cost_usd=0.001,
                        processing_time_ms=1500 + (output_idx * 50),
                        attempt_count=1,
                        created_at=now - timedelta(hours=2),
                        completed_at=now - timedelta(hours=1, minutes=50 - output_idx)
                    ))
                    output_idx += 1

        _db.session.delete(temp_eval)
        _db.session.commit()
        actions.append(f"Created job '{PRESEED_JOB_NAME}' (id={job.id}) with {total_outputs} outputs")

    # --- 3. Seed demo scenarios (same as development) and add IJCAI reviewers ---
    scenario_actions = _seed_demo_scenarios_for_ijcai(_db, demo_user, collab_user)
    actions.extend(scenario_actions)

    # --- 4. Seed evaluation scenario from batch generation ---
    eval_actions = _seed_evaluation_scenario(_db, demo_user, collab_user)
    actions.extend(eval_actions)

    return {'success': True, 'actions': actions}


def cleanup(include_preseed=False):
    """Delete live-recorded data. If include_preseed=True, also delete pre-seed data."""
    from db import db as _db
    from db.tables import User, UserPrompt
    from db.models.generation import GenerationJob, GeneratedOutput
    from db.models.scenario import (
        RatingScenarios, UserPromptShare, UserFeatureRanking,
        Feature, EvaluationItem, ScenarioItems, Message,
        UserConsultingCategorySelection, UserMailHistoryRating,
        ItemDimensionRating, ItemLabelingEvaluation, UserMessageRating,
        ScenarioItemDistribution,
    )
    from db.models.llm_task_result import LLMTaskResult
    from db.models.user_llm_provider import UserLLMProvider

    deleted = []

    # --- 0. Delete demo user's LLM providers (so they can be recreated during recording) ---
    demo_user = User.query.filter_by(username=DEMO_USER).first()
    if demo_user:
        user_providers = UserLLMProvider.query.filter_by(user_id=demo_user.id).all()
        for up in user_providers:
            _db.session.delete(up)
            deleted.append(f"User provider '{up.name}' (type={up.provider_type})")

    # --- 1. Delete live prompt "Situation Summary" (any owner) ---
    live_prompts = UserPrompt.query.filter_by(name=LIVE_PROMPT_NAME).all()
    for lp in live_prompts:
        shares_deleted = UserPromptShare.query.filter_by(
            prompt_id=lp.prompt_id
        ).delete()
        _db.session.delete(lp)
        deleted.append(f"Prompt '{LIVE_PROMPT_NAME}' owner_id={lp.user_id} (+{shares_deleted} shares)")

    # --- 2. Delete live job ---
    live_job = GenerationJob.query.filter_by(name=LIVE_JOB_NAME).first()
    if live_job:
        outputs_deleted = GeneratedOutput.query.filter_by(job_id=live_job.id).delete()
        _db.session.delete(live_job)
        deleted.append(f"Job '{LIVE_JOB_NAME}' (+{outputs_deleted} outputs)")

    # --- 3. Delete pre-seed data (prompt + job + outputs) ---
    if include_preseed:
        preseed_job = GenerationJob.query.filter_by(name=PRESEED_JOB_NAME).first()
        if preseed_job:
            outputs_deleted = GeneratedOutput.query.filter_by(job_id=preseed_job.id).delete()
            _db.session.delete(preseed_job)
            deleted.append(f"Job '{PRESEED_JOB_NAME}' (+{outputs_deleted} outputs)")

        preseed_prompts = UserPrompt.query.filter_by(name=PRESEED_PROMPT_NAME).all()
        for pp in preseed_prompts:
            shares_deleted = UserPromptShare.query.filter_by(
                prompt_id=pp.prompt_id
            ).delete()
            _db.session.delete(pp)
            deleted.append(f"Prompt '{PRESEED_PROMPT_NAME}' owner_id={pp.user_id} (+{shares_deleted} shares)")

    # --- 4. Delete evaluation scenario and its items/features/rankings ---
    eval_scenario = RatingScenarios.query.filter_by(
        scenario_name=EVAL_SCENARIO_NAME
    ).first()
    if eval_scenario:
        # Delete LLM task results for this scenario
        llm_results_deleted = LLMTaskResult.query.filter_by(
            scenario_id=eval_scenario.id
        ).delete(synchronize_session=False)
        if llm_results_deleted:
            deleted.append(f"Deleted {llm_results_deleted} LLM task results")

        # Delete rankings for items in this scenario
        scenario_item_ids = [
            si.thread_id for si in
            ScenarioItems.query.filter_by(scenario_id=eval_scenario.id).all()
        ]
        if scenario_item_ids:
            feature_ids = [
                f.feature_id for f in
                Feature.query.filter(Feature.item_id.in_(scenario_item_ids)).all()
            ]
            if feature_ids:
                rankings_deleted = UserFeatureRanking.query.filter(
                    UserFeatureRanking.feature_id.in_(feature_ids)
                ).delete(synchronize_session=False)
                deleted.append(f"Deleted {rankings_deleted} rankings")

                features_deleted = Feature.query.filter(
                    Feature.feature_id.in_(feature_ids)
                ).delete(synchronize_session=False)
                deleted.append(f"Deleted {features_deleted} features")

        # Delete scenario first (cascades ScenarioUsers, ScenarioItems, ScenarioItemDistribution)
        _db.session.delete(eval_scenario)
        _db.session.flush()
        deleted.append(f"Scenario '{EVAL_SCENARIO_NAME}' (id={eval_scenario.id})")

        # Now delete orphaned evaluation items and their FK-dependents
        if scenario_item_ids:
            for model_cls in [
                Message, UserMessageRating, UserConsultingCategorySelection,
                UserMailHistoryRating, ItemDimensionRating, ItemLabelingEvaluation,
            ]:
                count = model_cls.query.filter(
                    model_cls.item_id.in_(scenario_item_ids)
                ).delete(synchronize_session=False)
                if count:
                    deleted.append(f"Deleted {count} {model_cls.__tablename__}")

            items_deleted = EvaluationItem.query.filter(
                EvaluationItem.item_id.in_(scenario_item_ids)
            ).delete(synchronize_session=False)
            deleted.append(f"Deleted {items_deleted} evaluation items")

    # --- 5. Delete other demo-created scenarios ---
    preseed_job = GenerationJob.query.filter_by(name=PRESEED_JOB_NAME).first()
    preseed_target_id = preseed_job.target_scenario_id if preseed_job else None

    demo_scenarios = RatingScenarios.query.filter(
        RatingScenarios.scenario_name.contains("Situation")
    ).all()

    for scenario in demo_scenarios:
        if not include_preseed and preseed_target_id and scenario.id == preseed_target_id:
            continue
        if eval_scenario and scenario.id == eval_scenario.id:
            continue  # Already deleted above
        _db.session.delete(scenario)
        deleted.append(f"Scenario '{scenario.scenario_name}' (id={scenario.id})")

    _db.session.commit()

    return {'success': True, 'deleted': deleted}


def reset():
    """Full reset: cleanup (including pre-seed) + seed."""
    cleanup_result = cleanup(include_preseed=True)
    seed_result = seed()
    return {
        'success': seed_result.get('success', False),
        'cleanup': cleanup_result,
        'seed': seed_result,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_preseed_prompt_content():
    """Pre-seed prompt: structured situation analysis with numbered list and references.
    Deliberately more prescriptive than the live prompt to produce visibly different outputs."""
    return {
        "blocks": {
            "Role Definition": {
                "content": (
                    "You are an assistant for professionals in psychosocial online counselling. "
                    "You support counsellors in systematically capturing the current life situation of help-seeking clients. "
                    "You analyze email threads between clients and counsellors and extract factual information about the client's circumstances."
                ),
                "position": 0
            },
            "Task Explanation": {
                "content": (
                    "Analyze the email thread and produce a structured situation description of the client's current life circumstances as a numbered list of up to 3 points.\n\n"
                    "Each point must contain:\n"
                    "- A concise description of one aspect of the life situation (max 2 sentences)\n"
                    "- Direct quotes from the email thread as evidence, placed after a dash\n\n"
                    "Focus on: housing situation, family relationships, children (age, development, health), professional/educational situation, health status, social conflicts.\n\n"
                    "Rules:\n"
                    "- Use only facts from the thread, no speculation\n"
                    "- Avoid introductory phrases, present information directly\n"
                    "- When counselling parents, also include information about their children\n\n"
                    "Few-shot example:\n\n"
                    "Input: A single mother reports that her 8-year-old son has been refusing to attend school for two weeks, "
                    "complaining of stomach aches. The pediatrician found no physical cause. She works part-time and cannot stay home every day.\n\n"
                    "Output:\n"
                    '1. Single mother working part-time, unable to provide daily supervision due to work obligations. '
                    '— "I work part-time and cannot stay home every day"\n'
                    '2. 8-year-old son refusing school attendance for two weeks with psychosomatic symptoms. '
                    '— "my son has been refusing to go to school for two weeks", "he complains of stomach aches but the pediatrician found nothing"'
                ),
                "position": 1
            },
            "Data Format Explanation": {
                "content": (
                    "Subject: {{subject}}\n\n"
                    "Email thread:\n"
                    "{{content}}\n\n"
                    "Return only the numbered list. No additional explanations."
                ),
                "position": 2
            }
        }
    }


def _build_eval_prompt_content():
    """Live prompt: brief narrative situation summary. Matches
    the block structure of the live-typed prompt but produces shorter, narrative output."""
    return {
        "blocks": {
            "Role Definition": {
                "content": "You are a counselling assistant who helps professionals extract key facts from client communications in online psychosocial counselling.",
                "position": 0
            },
            "Task Explanation": {
                "content": "Read the email thread and write a brief situation overview in 2-3 sentences. Focus on the client's living situation, family, health, and main concerns. Write in third person, present tense.",
                "position": 1
            },
            "Data Format Explanation": {
                "content": (
                    "Subject: {{subject}}\n\n"
                    "Email thread:\n"
                    "{{content}}\n\n"
                    "Write a plain text paragraph, no bullet points."
                ),
                "position": 2
            }
        }
    }


DEMO_SCENARIO_NAMES = [
    'Demo Ranking Szenario',
    'Demo Verlauf Bewerter Szenario',
    'Demo Fake/Echt Szenario',
    'Demo Labeling Szenario',
    'LLM-as-Judge Demo',
    'SummEval Demo - Summarization',
]


def _seed_demo_scenarios_for_ijcai(db_session, demo_user, collab_user):
    """Seed the standard demo scenarios and add IJCAI reviewers as evaluators."""
    from db.seeders.scenarios import seed_demo_scenarios
    from db.models.scenario import (
        RatingScenarios, ScenarioUsers, ScenarioItems,
        ScenarioItemDistribution, ScenarioRoles,
    )

    actions = []

    # Call the standard demo scenario seeder (idempotent)
    try:
        seed_demo_scenarios(db_session)
        actions.append("Demo scenarios seeded (or already existed)")
    except Exception as e:
        logger.warning(f"Failed to seed demo scenarios: {e}")
        actions.append(f"Demo scenario seeding failed: {e}")
        return actions

    # Add IJCAI reviewers to all demo scenarios
    for scenario_name in DEMO_SCENARIO_NAMES:
        scenario = RatingScenarios.query.filter_by(scenario_name=scenario_name).first()
        if not scenario:
            continue

        for user in [demo_user, collab_user]:
            if not user:
                continue

            # Add as EVALUATOR if not already a member
            existing = ScenarioUsers.query.filter_by(
                scenario_id=scenario.id, user_id=user.id
            ).first()
            if existing:
                continue

            su = ScenarioUsers(
                scenario_id=scenario.id,
                user_id=user.id,
                role=ScenarioRoles.EVALUATOR,
            )
            db_session.session.add(su)
            db_session.session.flush()

            # Create item distributions for this user
            scenario_items = ScenarioItems.query.filter_by(scenario_id=scenario.id).all()
            for si in scenario_items:
                db_session.session.add(ScenarioItemDistribution(
                    scenario_id=scenario.id,
                    scenario_user_id=su.id,
                    scenario_item_id=si.id,
                ))

            actions.append(f"Added {user.username} to '{scenario_name}' ({len(scenario_items)} items)")

    db_session.session.commit()
    return actions


def _seed_evaluation_scenario(db_session, demo_user, collab_user):
    """
    Seed a ranking evaluation scenario from the pre-seeded batch generation.

    Creates:
    - A ranking scenario with 10 items (one per counselling case)
    - 4 features per item (2 prompts × 2 models)
    - Both IJCAI reviewers as human evaluators
    - LLM evaluator rankings (Magistral + GPT-5 Mini)
    - Pre-filled rankings: reviewer_1 has 8/10 done, reviewer_2 has 10/10 done
    - Last items left for live demo (shows pending/in_progress/done states)
    """
    from db.models.scenario import (
        RatingScenarios, ScenarioUsers, ScenarioItems,
        ScenarioItemDistribution, ScenarioRoles,
        EvaluationItem, Feature, FeatureType, FeatureFunctionType,
        LLM, UserFeatureRanking,
    )
    from db.models.llm_task_result import LLMTaskResult
    from db.models.generation import GenerationJob, GeneratedOutput
    from db.seeders.demo_video_data import COUNSELLING_CASES

    actions = []

    # Check if scenario already exists
    existing = RatingScenarios.query.filter_by(
        scenario_name=EVAL_SCENARIO_NAME
    ).first()
    if existing:
        actions.append(f"Eval scenario '{EVAL_SCENARIO_NAME}' already exists (id={existing.id})")
        return actions

    # Get the pre-seeded batch job
    preseed_job = GenerationJob.query.filter_by(
        name=PRESEED_JOB_NAME, created_by=DEMO_USER
    ).first()
    if not preseed_job:
        actions.append("Pre-seed job not found, skipping eval scenario")
        return actions

    # Get or create ranking function type
    ranking_type = FeatureFunctionType.query.filter_by(name='ranking').first()
    if not ranking_type:
        ranking_type = FeatureFunctionType(name='ranking')
        db_session.session.add(ranking_type)
        db_session.session.flush()

    # Get or create feature type for situation descriptions
    ft = FeatureType.query.filter_by(name='Situation Summary').first()
    if not ft:
        ft = FeatureType(name='Situation Summary')
        db_session.session.add(ft)
        db_session.session.flush()

    # Get or create LLM entries (legacy llms table, not llm_models)
    def _get_or_create_llm(name):
        llm = LLM.query.filter_by(name=name).first()
        if not llm:
            llm = LLM(name=name)
            db_session.session.add(llm)
            db_session.session.flush()
        return llm

    llm_mistral = _get_or_create_llm('Mistral Small')
    llm_gpt5_nano = _get_or_create_llm('GPT-5 Nano')

    # --- Create the ranking scenario ---
    scenario = RatingScenarios(
        scenario_name=EVAL_SCENARIO_NAME,
        function_type_id=ranking_type.function_type_id,
        begin=datetime.utcnow() - timedelta(days=1),
        end=datetime.utcnow() + timedelta(days=30),
        timestamp=datetime.utcnow(),
        created_by=DEMO_USER,
        config_json={
            "evaluation": "ranking",
            "enable_llm_evaluation": True,
            "llm_evaluators": [
                "LiteLLM/mistralai/Magistral-Small-2509",
                "OpenAI/gpt-5-mini",
            ],
        }
    )
    db_session.session.add(scenario)
    db_session.session.flush()
    actions.append(f"Created eval scenario '{EVAL_SCENARIO_NAME}' (id={scenario.id})")

    # --- Add users ---
    reviewer_1_su = ScenarioUsers(
        scenario_id=scenario.id,
        user_id=demo_user.id,
        role=ScenarioRoles.OWNER,
    )
    db_session.session.add(reviewer_1_su)
    db_session.session.flush()

    reviewer_2_su = None
    if collab_user:
        reviewer_2_su = ScenarioUsers(
            scenario_id=scenario.id,
            user_id=collab_user.id,
            role=ScenarioRoles.EVALUATOR,
        )
        db_session.session.add(reviewer_2_su)
        db_session.session.flush()

    # --- Create evaluation items + features from batch outputs ---
    # Group outputs by case (source_index)
    outputs = GeneratedOutput.query.filter_by(job_id=preseed_job.id).all()

    # Group by source_index
    outputs_by_case = {}
    for out in outputs:
        case_idx = (out.prompt_variables_json or {}).get('source_index', 0)
        outputs_by_case.setdefault(case_idx, []).append(out)

    items = []
    item_features = {}  # item_id -> list of features

    for case_idx in sorted(outputs_by_case.keys()):
        case = COUNSELLING_CASES[case_idx] if case_idx < len(COUNSELLING_CASES) else None
        case_outputs = outputs_by_case[case_idx]

        # Create evaluation item
        item = EvaluationItem(
            chat_id=20000 + case_idx,
            institut_id=99,
            subject=case['subject'] if case else f"Case {case_idx}",
            sender='demo',
            function_type_id=ranking_type.function_type_id,
        )
        db_session.session.add(item)
        db_session.session.flush()
        items.append(item)

        # Link item to scenario
        si = ScenarioItems(
            scenario_id=scenario.id,
            thread_id=item.item_id,
        )
        db_session.session.add(si)
        db_session.session.flush()

        # Create distributions for evaluators
        for su in [reviewer_1_su, reviewer_2_su]:
            if su:
                db_session.session.add(ScenarioItemDistribution(
                    scenario_id=scenario.id,
                    scenario_user_id=su.id,
                    scenario_item_id=si.id,
                ))

        # Create features from outputs (4 per item: 2 prompts × 2 models)
        features = []
        for out in case_outputs:
            model_name = out.llm_model_name or ''
            if 'Mistral' in model_name or 'mistral' in model_name:
                llm_ref = llm_mistral
            elif 'gpt-5' in model_name or 'GPT-5' in model_name:
                llm_ref = llm_gpt5_nano
            else:
                llm_ref = llm_mistral

            feature = Feature(
                item_id=item.item_id,
                type_id=ft.type_id,
                llm_id=llm_ref.llm_id,
                content=out.generated_content,
            )
            db_session.session.add(feature)
            db_session.session.flush()
            features.append(feature)

        item_features[item.item_id] = features

    actions.append(f"Created {len(items)} evaluation items with features")

    # --- Pre-fill rankings ---
    # Buckets: Gut (best), Mittel (acceptable), Schlecht (poor), Neutral
    # Ranking patterns for different evaluators (to create realistic disagreement)
    # Each pattern assigns 4 features to buckets: [feature_0_bucket, feature_1_bucket, ...]
    ranking_patterns = [
        ['Gut', 'Mittel', 'Gut', 'Schlecht'],       # Case 0
        ['Gut', 'Schlecht', 'Mittel', 'Mittel'],     # Case 1
        ['Mittel', 'Gut', 'Gut', 'Schlecht'],        # Case 2
        ['Gut', 'Mittel', 'Schlecht', 'Gut'],        # Case 3
        ['Mittel', 'Gut', 'Mittel', 'Schlecht'],     # Case 4
        ['Gut', 'Gut', 'Schlecht', 'Mittel'],        # Case 5
        ['Schlecht', 'Mittel', 'Gut', 'Gut'],        # Case 6
        ['Gut', 'Mittel', 'Gut', 'Mittel'],          # Case 7
        ['Mittel', 'Gut', 'Schlecht', 'Gut'],        # Case 8
        ['Gut', 'Schlecht', 'Gut', 'Mittel'],        # Case 9
    ]

    # Slightly different patterns for reviewer_2 (to create IRR variation)
    ranking_patterns_r2 = [
        ['Gut', 'Mittel', 'Mittel', 'Schlecht'],     # Case 0 (one disagreement)
        ['Gut', 'Schlecht', 'Mittel', 'Mittel'],     # Case 1 (same)
        ['Gut', 'Gut', 'Mittel', 'Schlecht'],        # Case 2 (one disagreement)
        ['Gut', 'Mittel', 'Schlecht', 'Mittel'],     # Case 3 (one disagreement)
        ['Mittel', 'Gut', 'Mittel', 'Schlecht'],     # Case 4 (same)
        ['Gut', 'Gut', 'Schlecht', 'Mittel'],        # Case 5 (same)
        ['Schlecht', 'Gut', 'Gut', 'Mittel'],        # Case 6 (one disagreement)
        ['Mittel', 'Mittel', 'Gut', 'Mittel'],       # Case 7 (two disagreements)
        ['Mittel', 'Gut', 'Schlecht', 'Gut'],        # Case 8 (same)
        ['Gut', 'Mittel', 'Gut', 'Schlecht'],        # Case 9 (two disagreements)
    ]

    # LLM evaluator patterns (more consistent between each other)
    ranking_patterns_magistral = [
        ['Gut', 'Mittel', 'Gut', 'Schlecht'],
        ['Gut', 'Mittel', 'Mittel', 'Schlecht'],
        ['Mittel', 'Gut', 'Gut', 'Schlecht'],
        ['Gut', 'Mittel', 'Schlecht', 'Mittel'],
        ['Mittel', 'Gut', 'Mittel', 'Schlecht'],
        ['Gut', 'Gut', 'Schlecht', 'Mittel'],
        ['Schlecht', 'Mittel', 'Gut', 'Gut'],
        ['Gut', 'Mittel', 'Gut', 'Schlecht'],
        ['Mittel', 'Gut', 'Schlecht', 'Gut'],
        ['Gut', 'Schlecht', 'Gut', 'Mittel'],
    ]

    ranking_patterns_gpt5mini = [
        ['Gut', 'Mittel', 'Mittel', 'Schlecht'],
        ['Gut', 'Schlecht', 'Gut', 'Mittel'],
        ['Gut', 'Gut', 'Mittel', 'Schlecht'],
        ['Gut', 'Mittel', 'Schlecht', 'Gut'],
        ['Mittel', 'Gut', 'Schlecht', 'Mittel'],
        ['Gut', 'Mittel', 'Schlecht', 'Mittel'],
        ['Schlecht', 'Gut', 'Gut', 'Mittel'],
        ['Gut', 'Gut', 'Mittel', 'Schlecht'],
        ['Mittel', 'Gut', 'Schlecht', 'Gut'],
        ['Gut', 'Mittel', 'Gut', 'Schlecht'],
    ]

    def _add_rankings(user_id, patterns, num_items, llm_id=None):
        """Add ranking entries for a user/LLM for the first num_items items."""
        count = 0
        for case_idx in range(min(num_items, len(items))):
            item = items[case_idx]
            features = item_features.get(item.item_id, [])
            pattern = patterns[case_idx] if case_idx < len(patterns) else ['Neutral'] * 4

            for feat_idx, feature in enumerate(features):
                bucket = pattern[feat_idx] if feat_idx < len(pattern) else 'Neutral'
                ranking = UserFeatureRanking(
                    user_id=user_id,
                    feature_id=feature.feature_id,
                    ranking_content=float(feat_idx + 1),
                    type_id=ft.type_id,
                    llm_id=llm_id or feature.llm_id,
                    bucket=bucket,
                )
                db_session.session.add(ranking)
                count += 1
        return count

    # Reviewer 1 (demo_user): 8 fully ranked + item 9 partially (2/4 features)
    r1_count = _add_rankings(demo_user.id, ranking_patterns, 8)
    # Add 2 partial rankings for item 9 (case_idx=8) → in_progress
    item_9 = items[8] if len(items) > 8 else None
    if item_9:
        item_9_features = item_features.get(item_9.item_id, [])
        pattern_9 = ranking_patterns[8]
        for feat_idx in range(min(2, len(item_9_features))):
            ranking = UserFeatureRanking(
                user_id=demo_user.id,
                feature_id=item_9_features[feat_idx].feature_id,
                ranking_content=float(feat_idx + 1),
                type_id=ft.type_id,
                llm_id=item_9_features[feat_idx].llm_id,
                bucket=pattern_9[feat_idx],
            )
            db_session.session.add(ranking)
            r1_count += 1
    actions.append(f"Added {r1_count} rankings for {DEMO_USER} (8 done + item 9 in_progress)")

    # Reviewer 2 (collab_user): all 10 items ranked (fully done)
    if collab_user:
        r2_count = _add_rankings(collab_user.id, ranking_patterns_r2, 10)
        actions.append(f"Added {r2_count} rankings for {COLLAB_USER} (10/10 items)")

    # LLM evaluators: stored in LLMTaskResult (not UserFeatureRanking)
    def _add_llm_rankings(model_id, patterns, num_items):
        """Add LLMTaskResult entries for an LLM evaluator."""
        count = 0
        for case_idx in range(min(num_items, len(items))):
            item = items[case_idx]
            features = item_features.get(item.item_id, [])
            pattern = patterns[case_idx] if case_idx < len(patterns) else ['neutral'] * 4

            # Build payload_json: { "gut": [fid1, ...], "mittel": [...], ... }
            bucket_map = {}
            for feat_idx, feature in enumerate(features):
                bucket = pattern[feat_idx].lower() if feat_idx < len(pattern) else 'neutral'
                bucket_map.setdefault(bucket, []).append(feature.feature_id)

            db_session.session.add(LLMTaskResult(
                scenario_id=scenario.id,
                item_id=item.item_id,
                model_id=model_id,
                task_type="ranking",
                payload_json=bucket_map,
                raw_response=None,
                error=None,
            ))
            count += 1
        return count

    magistral_count = _add_llm_rankings(
        "LiteLLM/mistralai/Magistral-Small-2509", ranking_patterns_magistral, 10
    )
    actions.append(f"Added {magistral_count} Magistral LLM rankings (10/10 items)")

    gpt5mini_count = _add_llm_rankings(
        "OpenAI/gpt-5-mini", ranking_patterns_gpt5mini, 10
    )
    actions.append(f"Added {gpt5mini_count} GPT-5 Mini LLM rankings (10/10 items)")

    db_session.session.commit()
    return actions


def _get_block(prompt, name):
    blocks = (prompt.content or {}).get('blocks', {})
    block = blocks.get(name, {})
    return block.get('content', '') if isinstance(block, dict) else ''


def _render_system(prompt):
    parts = [_get_block(prompt, "Role Definition"), _get_block(prompt, "Task Explanation")]
    return "\n\n".join(p for p in parts if p)


def _render_user(prompt, case):
    tpl = _get_block(prompt, "Data Format Explanation")
    if not tpl:
        return f"Subject: {case['subject']}\n\n{case['content']}"
    return tpl.replace("{{subject}}", case["subject"]).replace("{{content}}", case["content"])
