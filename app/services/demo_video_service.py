"""
Demo Video Data Service for IJCAI 2026

Core logic for seeding/cleanup of demo video data.
Used by both CLI script (scripts/demo_video_manage.py) and API routes.
"""

import logging
from datetime import datetime, timedelta
from types import SimpleNamespace

logger = logging.getLogger('demo_video_service')

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PRESEED_PROMPT_NAME = "Structured Situation Analysis"
PRESEED_JOB_NAME = "Counselling Situation Extraction"
LIVE_PROMPT_NAME = "Live Situation Summary"
LIVE_JOB_NAME = "Live Collab Batch Job"
EVAL_SCENARIO_NAME = "IJCAI Counselling Evaluation"
EVAL_SCENARIO_NAME_5_BUCKETS = "IJCAI Counselling Evaluation (5 Buckets)"
LEGACY_EVAL_SCENARIO_NAME = "Counselling Situation Extraction"

GENERATION_PROMPT_TEMPLATE_NAMES = [PRESEED_PROMPT_NAME, LIVE_PROMPT_NAME]
GENERATION_MODEL_IDS = [
    "Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506",
    "Global/OpenAI/gpt-5-nano",
]
EVALUATION_MODEL_IDS = [
    "Global/Mistral/Magistral-Small-2509",
    "Global/OpenAI/gpt-5-mini",
]

# Persist prompt provenance under the exact prompt template names from batch generation.
STRUCTURED_FEATURE_TYPE_NAME = PRESEED_PROMPT_NAME
NARRATIVE_FEATURE_TYPE_NAME = LIVE_PROMPT_NAME
MERGED_FEATURE_TYPE_NAME = "Situation Summary"
DEFAULT_SPLIT_BY_PROMPT = False
PRESEED_PROMPT_KEY = PRESEED_PROMPT_NAME.lower()
LIVE_PROMPT_KEY = LIVE_PROMPT_NAME.lower()

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
        (RatingScenarios.scenario_name.contains("Situation"))
        | (RatingScenarios.scenario_name.contains("IJCAI"))
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
    from db.seeders.demo_video_data import (
        COUNSELLING_CASES, SAMPLE_OUTPUTS, OUTPUT_METADATA,
        JOB_TOTAL_TOKENS, JOB_TOTAL_COST_USD,
    )

    actions = []

    # --- 0. Deactivate OpenAI models (they should only be via user provider) ---
    openai_models = LLMModel.query.filter(
        LLMModel.model_id.like('OpenAI/%')
    ).all()
    deactivated = 0
    for m in openai_models:
        if m.is_active:
            m.is_active = False
            deactivated += 1
    if deactivated:
        _db.session.commit()
        actions.append(f"Deactivated {deactivated} OpenAI model(s)")

    # Rebalance auto-generated LLM model colors so demo tags remain distinguishable.
    try:
        rebalanced_colors = LLMModel.rebalance_auto_generated_colors(
            model_types=[LLMModel.MODEL_TYPE_LLM]
        )
        if rebalanced_colors:
            _db.session.commit()
            actions.append(f"Rebalanced LLM model colors ({rebalanced_colors} model(s))")
    except Exception as e:
        _db.session.rollback()
        logger.warning(f"Failed to rebalance LLM model colors: {e}")

    # Hard guard for the two demo models used side-by-side in the video.
    # This ensures they remain visually distinct even if legacy/custom colors exist.
    try:
        forced_contrast_updates = _ensure_demo_model_color_contrast()
        if forced_contrast_updates:
            _db.session.commit()
            actions.append(
                "Adjusted demo model colors for contrast "
                f"({forced_contrast_updates} model(s))"
            )
    except Exception as e:
        _db.session.rollback()
        logger.warning(f"Failed to enforce demo model color contrast: {e}")

    demo_user = User.query.filter_by(username=DEMO_USER).first()
    if not demo_user:
        return {'success': False, 'error': f"User '{DEMO_USER}' not found"}

    collab_user = User.query.filter_by(username=COLLAB_USER).first()

    # --- 1. Ensure setup prompt exists (live prompt is intentionally created during recording) ---
    preseed_content = _build_preseed_prompt_content()
    preseed = UserPrompt.query.filter_by(
        user_id=demo_user.id,
        name=PRESEED_PROMPT_NAME
    ).first()
    if not preseed:
        preseed = UserPrompt(
            user_id=demo_user.id,
            name=PRESEED_PROMPT_NAME,
            content=preseed_content
        )
        _db.session.add(preseed)
        _db.session.flush()
        actions.append(f"Created prompt '{PRESEED_PROMPT_NAME}' (id={preseed.prompt_id})")
    elif (preseed.content or {}) != preseed_content:
        preseed.content = preseed_content
        actions.append(
            f"Updated prompt '{PRESEED_PROMPT_NAME}' (id={preseed.prompt_id}) to current demo template"
        )
    else:
        actions.append(f"Prompt '{PRESEED_PROMPT_NAME}' already exists (id={preseed.prompt_id})")

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

    # Keep the live prompt template in-memory for seeded outputs only.
    live_prompt = SimpleNamespace(content=_build_eval_prompt_content())
    actions.append(
        f"Skipped pre-seeding prompt '{LIVE_PROMPT_NAME}' (created live during recording)"
    )

    # --- 2. Create completed generation job ---
    existing_job = GenerationJob.query.filter_by(
        name=PRESEED_JOB_NAME, created_by=DEMO_USER
    ).first()
    if existing_job:
        actions.append(f"Job '{PRESEED_JOB_NAME}' already exists (id={existing_job.id})")
    else:
        mistral = LLMModel.query.filter_by(model_id=GENERATION_MODEL_IDS[0]).first()
        gpt5_nano = LLMModel.query.filter_by(model_id=GENERATION_MODEL_IDS[1]).first()

        if not mistral or not gpt5_nano:
            actions.append("Required LLM models not found, skipping job seeding")
            return {'success': True, 'actions': actions, 'warning': 'no_models'}

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
            total_tokens=JOB_TOTAL_TOKENS,
            total_cost_usd=JOB_TOTAL_COST_USD,
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
                ("narrative", live_prompt, LIVE_PROMPT_NAME),
            ]:
                for model, model_key in [(mistral, 'mistral'), (gpt5_nano, 'gpt5_nano')]:
                    output_text = SAMPLE_OUTPUTS[summary_key][model_key][case_idx]
                    meta = OUTPUT_METADATA[summary_key][model_key][case_idx]
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
                        input_tokens=meta['input_tokens'],
                        output_tokens=meta['output_tokens'],
                        total_cost_usd=meta['cost_usd'],
                        processing_time_ms=meta['processing_time_ms'],
                        attempt_count=1,
                        created_at=now - timedelta(hours=2),
                        completed_at=now - timedelta(hours=1, minutes=50 - output_idx)
                    ))
                    output_idx += 1

        _db.session.commit()
        actions.append(f"Created job '{PRESEED_JOB_NAME}' (id={job.id}) with {total_outputs} outputs")

    # --- 3. Seed demo scenarios (same as development) and add IJCAI reviewers ---
    scenario_actions = _seed_demo_scenarios_for_ijcai(_db, demo_user, collab_user)
    actions.extend(scenario_actions)

    # --- 4. Seed evaluation scenario from batch generation ---
    eval_actions = _seed_evaluation_scenario(_db, demo_user, collab_user)
    actions.extend(eval_actions)
    eval_5_bucket_actions = _seed_evaluation_scenario_5_buckets(_db, demo_user, collab_user)
    actions.extend(eval_5_bucket_actions)

    return {'success': True, 'actions': actions}


def cleanup(include_preseed=False):
    """Delete live-recorded data. If include_preseed=True, also delete pre-seed data."""
    from db import db as _db
    from db.tables import User
    from db.models.generation import GenerationJob, GeneratedOutput
    from db.models.scenario import (
        RatingScenarios, UserFeatureRanking,
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

    # --- 1. Delete live prompt (any owner, normalized/prefix) ---
    for info in _delete_prompts_by_name_prefix(_db, LIVE_PROMPT_NAME):
        deleted.append(
            f"Prompt '{info['name']}' owner_id={info['owner_id']} (+{info['shares_deleted']} shares)"
        )

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

        for info in _delete_prompts_by_name_prefix(_db, PRESEED_PROMPT_NAME):
            deleted.append(
                f"Prompt '{info['name']}' owner_id={info['owner_id']} (+{info['shares_deleted']} shares)"
            )

    # --- 4. Delete evaluation scenario and its items/features/rankings ---
    # Search by current name AND legacy name (in case of rename between deployments)
    eval_scenarios = RatingScenarios.query.filter(
        RatingScenarios.scenario_name.in_([
            EVAL_SCENARIO_NAME,
            EVAL_SCENARIO_NAME_5_BUCKETS,
            LEGACY_EVAL_SCENARIO_NAME,  # legacy name
        ])
    ).all()

    all_eval_item_ids = []

    for eval_scenario in eval_scenarios:
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
        all_eval_item_ids.extend(scenario_item_ids)

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

        # Delete scenario (cascades ScenarioUsers, ScenarioItems, ScenarioItemDistribution)
        _db.session.delete(eval_scenario)
        _db.session.flush()
        deleted.append(f"Scenario '{eval_scenario.scenario_name}' (id={eval_scenario.id})")

    # Delete orphaned evaluation items and their FK-dependents
    if all_eval_item_ids:
        for model_cls in [
            Message, UserMessageRating, UserConsultingCategorySelection,
            UserMailHistoryRating, ItemDimensionRating, ItemLabelingEvaluation,
        ]:
            count = model_cls.query.filter(
                model_cls.item_id.in_(all_eval_item_ids)
            ).delete(synchronize_session=False)
            if count:
                deleted.append(f"Deleted {count} {model_cls.__tablename__}")

        items_deleted = EvaluationItem.query.filter(
            EvaluationItem.item_id.in_(all_eval_item_ids)
        ).delete(synchronize_session=False)
        deleted.append(f"Deleted {items_deleted} evaluation items")

    # Also clean up any demo evaluation items by known chat_id range (safety net)
    demo_items = EvaluationItem.query.filter(
        EvaluationItem.institut_id == 99,
        (
            EvaluationItem.chat_id.between(20000, 20099)
            | EvaluationItem.chat_id.between(21000, 21099)
        ),
    ).all()
    if demo_items:
        demo_item_ids = [i.item_id for i in demo_items]
        # Clean FK references first
        for model_cls in [
            Message, UserMessageRating, UserConsultingCategorySelection,
            UserMailHistoryRating, ItemDimensionRating, ItemLabelingEvaluation,
        ]:
            model_cls.query.filter(
                model_cls.item_id.in_(demo_item_ids)
            ).delete(synchronize_session=False)
        demo_feature_ids = [
            f.feature_id for f in
            Feature.query.filter(Feature.item_id.in_(demo_item_ids)).all()
        ]
        if demo_feature_ids:
            UserFeatureRanking.query.filter(
                UserFeatureRanking.feature_id.in_(demo_feature_ids)
            ).delete(synchronize_session=False)
            Feature.query.filter(
                Feature.feature_id.in_(demo_feature_ids)
            ).delete(synchronize_session=False)
        # Delete ScenarioItems references
        ScenarioItems.query.filter(
            ScenarioItems.thread_id.in_(demo_item_ids)
        ).delete(synchronize_session=False)
        EvaluationItem.query.filter(
            EvaluationItem.item_id.in_(demo_item_ids)
        ).delete(synchronize_session=False)
        deleted.append(
            f"Safety-net: deleted {len(demo_items)} demo evaluation items "
            "(chat_id 20000-20099 and 21000-21099)"
        )

    # --- 5. Delete other demo-created scenarios ---
    preseed_job = GenerationJob.query.filter_by(name=PRESEED_JOB_NAME).first()
    preseed_target_id = preseed_job.target_scenario_id if preseed_job else None

    deleted_scenario_ids = {s.id for s in eval_scenarios}
    demo_scenarios = RatingScenarios.query.filter(
        RatingScenarios.scenario_name.contains("Situation")
    ).all()

    for scenario in demo_scenarios:
        if not include_preseed and preseed_target_id and scenario.id == preseed_target_id:
            continue
        if scenario.id in deleted_scenario_ids:
            continue  # Already deleted above
        _db.session.delete(scenario)
        deleted.append(f"Scenario '{scenario.scenario_name}' (id={scenario.id})")

    _db.session.commit()

    return {'success': True, 'deleted': deleted}


def reset():
    """Full reset: cleanup (including pre-seed) + seed."""
    cleanup_result = cleanup(include_preseed=True)
    seed_result = seed()
    # Final safeguard: ensure the live prompt is absent after reset so it can be
    # created during recording.
    live_prompt_cleanup = cleanup_live_prompt_only()
    if live_prompt_cleanup.get('deleted'):
        for entry in live_prompt_cleanup['deleted']:
            seed_result.setdefault('actions', []).append(f"Post-seed cleanup: {entry}")
    return {
        'success': seed_result.get('success', False),
        'cleanup': cleanup_result,
        'seed': seed_result,
    }


def cleanup_live_prompt_only():
    """Delete only live prompt variants, keeping all seeded baseline data."""
    from db import db as _db

    deleted = []
    for info in _delete_prompts_by_name_prefix(_db, LIVE_PROMPT_NAME):
        deleted.append(
            f"Prompt '{info['name']}' owner_id={info['owner_id']} (+{info['shares_deleted']} shares)"
        )

    _db.session.commit()
    return {'success': True, 'deleted': deleted}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _delete_prompts_by_name_prefix(db_handle, prompt_name_prefix):
    """
    Delete prompts by normalized name-prefix match, including shares.

    Uses LOWER(TRIM(name)) LIKE '<prefix>%' to catch case/whitespace variants.
    """
    from sqlalchemy import func
    from db.tables import UserPrompt
    from db.models.scenario import UserPromptShare

    normalized_prefix = str(prompt_name_prefix or "").strip().lower()
    if not normalized_prefix:
        return []

    prompts = UserPrompt.query.filter(
        func.lower(func.trim(UserPrompt.name)).like(f"{normalized_prefix}%")
    ).all()

    deleted = []
    for prompt in prompts:
        shares_deleted = UserPromptShare.query.filter_by(
            prompt_id=prompt.prompt_id
        ).delete()
        deleted.append({
            'name': prompt.name,
            'owner_id': prompt.user_id,
            'shares_deleted': shares_deleted,
        })
        db_handle.session.delete(prompt)

    return deleted


def _build_preseed_prompt_content():
    """Pre-seed prompt: structured situation analysis with numbered list and references.
    Deliberately more prescriptive than the live prompt to produce visibly different outputs."""
    return {
        "collaboration_attribution": {
            "owner": DEMO_USER,
            "shared_with": [COLLAB_USER],
            "note": "Prompt seeded with explicit block-level authorship for demo traceability."
        },
        "blocks": {
            "System Prompt": {
                "content": (
                    "You are an assistant for professionals in psychosocial online counselling. "
                    "You support counsellors in systematically capturing the current life situation of help-seeking clients. "
                    "You analyze email threads between clients and counsellors and extract factual information about the client's circumstances."
                ),
                "position": 0,
                "author": DEMO_USER
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
                "position": 1,
                "author": COLLAB_USER
            },
            "Data Format Explanation": {
                "content": (
                    "Subject: {{subject}}\n\n"
                    "Email thread:\n"
                    "{{content}}\n\n"
                    "Return only the numbered list. No additional explanations."
                ),
                "position": 2,
                "author": DEMO_USER
            }
        }
    }


def _build_eval_prompt_content():
    """Live prompt: brief narrative situation summary. Matches
    the block structure of the live-typed prompt but produces shorter, narrative output."""
    return {
        "collaboration_attribution": {
            "owner": DEMO_USER,
            "shared_with": [COLLAB_USER],
            "note": "Live prompt seeded for collab demo; block authorship is explicit."
        },
        "blocks": {
            "System Prompt": {
                "content": "You are a counselling assistant who helps professionals extract key facts from client communications in online psychosocial counselling.",
                "position": 0,
                "author": COLLAB_USER
            },
            "Task Explanation": {
                "content": "Read the email thread and write a brief situation overview in 2-3 sentences. Focus on the client's living situation, family, health, and main concerns. Write in third person, present tense.",
                "position": 1,
                "author": DEMO_USER
            },
            "Data Format Explanation": {
                "content": (
                    "Subject: {{subject}} Content: {{content}}\n"
                    "The data below is provided as a subject line followed by the email thread content from a counselling session."
                ),
                "position": 2,
                "author": COLLAB_USER,
                "contributors": [
                    {
                        "author": DEMO_USER,
                        "text": "The data below is provided as a subject line followed by the email thread content from a counselling session."
                    },
                    {
                        "author": COLLAB_USER,
                        "text": "Subject: {{subject}}  Content: {{content}}"
                    }
                ]
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


def _resolve_counselling_case_content(item, counselling_cases, fallback_index=None):
    """
    Resolve the original counselling case content for an evaluation item.

    Uses deterministic mapping by chat_id first (20000 + case_idx), then subject,
    then optional fallback by scenario item order.
    """
    if item and item.chat_id is not None:
        try:
            case_idx = int(item.chat_id) - 20000
            if 0 <= case_idx < len(counselling_cases):
                content = counselling_cases[case_idx].get("content")
                if content:
                    return content
        except Exception:
            pass

    subject = (item.subject or "").strip() if item else ""
    if subject:
        for case in counselling_cases:
            if (case.get("subject") or "").strip() == subject and case.get("content"):
                return case["content"]

    if fallback_index is not None and 0 <= fallback_index < len(counselling_cases):
        return counselling_cases[fallback_index].get("content")

    return None


def _normalize_hex_color(color: str | None) -> str | None:
    if not color or not isinstance(color, str):
        return None
    value = color.strip().upper()
    if value.startswith('#') and len(value) == 7:
        return value
    return None


def _hex_to_rgb_tuple(color: str | None):
    normalized = _normalize_hex_color(color)
    if not normalized:
        return None
    value = normalized[1:]
    return (
        int(value[0:2], 16),
        int(value[2:4], 16),
        int(value[4:6], 16),
    )


def _color_distance_sq(color_a: str | None, color_b: str | None) -> int:
    rgb_a = _hex_to_rgb_tuple(color_a)
    rgb_b = _hex_to_rgb_tuple(color_b)
    if not rgb_a or not rgb_b:
        return 0
    dr = rgb_a[0] - rgb_b[0]
    dg = rgb_a[1] - rgb_b[1]
    db = rgb_a[2] - rgb_b[2]
    return dr * dr + dg * dg + db * db


def _ensure_demo_model_color_contrast():
    """
    Ensure the two key demo models have clearly distinguishable colors.

    Returns number of changed model colors.
    """
    from db.models.llm_model import LLMModel, NEUTRAL_COLOR_CANDIDATES

    mistral_id = GENERATION_MODEL_IDS[0]
    gpt5_nano_id = GENERATION_MODEL_IDS[1]
    min_pair_distance_sq = 12000  # ~109 RGB euclidean distance

    target_ids = [mistral_id, gpt5_nano_id]
    target_models = LLMModel.query.filter(LLMModel.model_id.in_(target_ids)).all()
    if len(target_models) < 2:
        return 0

    models_by_id = {m.model_id: m for m in target_models}
    mistral = models_by_id.get(mistral_id)
    gpt5_nano = models_by_id.get(gpt5_nano_id)
    if not mistral or not gpt5_nano:
        return 0

    # Build base palette from all other model colors.
    base_palette = []
    for model_id, color in LLMModel.query.with_entities(LLMModel.model_id, LLMModel.color).all():
        if model_id in target_ids:
            continue
        normalized = _normalize_hex_color(color)
        if normalized:
            base_palette.append(normalized)

    changed = 0

    # Reassign mistral first using distance-aware generator.
    mistral_new = _normalize_hex_color(
        LLMModel.generate_color(mistral.model_id, existing_colors=base_palette)
    )
    if mistral_new and _normalize_hex_color(mistral.color) != mistral_new:
        mistral.color = mistral_new
        changed += 1

    palette_with_mistral = [*base_palette]
    if mistral_new:
        palette_with_mistral.append(mistral_new)

    # Initial OpenAI candidate from generator.
    gpt_new = _normalize_hex_color(
        LLMModel.generate_color(gpt5_nano.model_id, existing_colors=palette_with_mistral)
    )

    # Enforce minimum pair distance if needed.
    if _color_distance_sq(gpt_new, mistral_new) < min_pair_distance_sq:
        best_color = gpt_new
        best_score = (-1, -1)
        for candidate in NEUTRAL_COLOR_CANDIDATES:
            candidate_norm = _normalize_hex_color(candidate)
            if not candidate_norm:
                continue
            pair_dist = _color_distance_sq(candidate_norm, mistral_new)
            min_dist_to_others = pair_dist
            for existing_color in palette_with_mistral:
                dist = _color_distance_sq(candidate_norm, existing_color)
                if dist < min_dist_to_others:
                    min_dist_to_others = dist

            # Prefer satisfying threshold first, then maximize pair distance, then global min distance.
            score = (1 if pair_dist >= min_pair_distance_sq else 0, pair_dist + min_dist_to_others)
            if score > best_score:
                best_score = score
                best_color = candidate_norm
        gpt_new = best_color

    if gpt_new and _normalize_hex_color(gpt5_nano.color) != gpt_new:
        gpt5_nano.color = gpt_new
        changed += 1

    return changed


def _ensure_eval_scenario_reference_messages(db_session, scenario, counselling_cases):
    """Backfill missing reference messages for demo evaluation scenario items."""
    from db.models.scenario import ScenarioItems, EvaluationItem, Message

    added = 0
    scenario_items = ScenarioItems.query.filter_by(scenario_id=scenario.id).order_by(ScenarioItems.id.asc()).all()

    for idx, scenario_item in enumerate(scenario_items):
        item_id = scenario_item.thread_id or scenario_item.item_id
        if not item_id:
            continue

        eval_item = EvaluationItem.query.get(item_id)
        if not eval_item:
            continue

        has_messages = Message.query.filter_by(item_id=eval_item.item_id).first() is not None
        if has_messages:
            continue

        source_content = _resolve_counselling_case_content(eval_item, counselling_cases, fallback_index=idx)
        if not source_content:
            continue

        db_session.session.add(Message(
            item_id=eval_item.item_id,
            sender='source',
            content=source_content,
            timestamp=datetime.utcnow() - timedelta(hours=2),
            generated_by='Human',
        ))
        added += 1

    if added > 0:
        db_session.session.commit()

    return added


def _output_prompt_priority(prompt_name):
    normalized = str(prompt_name or "").strip().lower()
    if normalized == PRESEED_PROMPT_NAME.lower():
        return 0
    if normalized == LIVE_PROMPT_NAME.lower():
        return 1
    return 2


def _output_model_priority(model_name):
    normalized = str(model_name or "").strip().lower()
    if "mistral" in normalized:
        return 0
    if "gpt-5" in normalized or "gpt5" in normalized:
        return 1
    return 2


def _sort_outputs_for_case(outputs):
    return sorted(
        outputs,
        key=lambda out: (
            _output_prompt_priority(getattr(out, "prompt_variant_name", None)),
            _output_model_priority(getattr(out, "llm_model_name", None)),
            str(getattr(out, "prompt_variant_name", "") or "").lower(),
            str(getattr(out, "llm_model_name", "") or "").lower(),
            int(getattr(out, "id", 0) or 0),
        )
    )


def _resolve_eval_llm_for_output(output, llm_mistral, llm_gpt5_nano):
    model_name = str(getattr(output, "llm_model_name", "") or "").lower()
    if "gpt-5" in model_name or "gpt5" in model_name:
        return llm_gpt5_nano
    if "mistral" in model_name:
        return llm_mistral
    return llm_mistral


def _normalize_prompt_key(prompt_name):
    return str(prompt_name or "").strip().lower()


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _is_split_by_prompt_enabled(config):
    """Resolve prompt-splitting mode from scenario config (defaults to merged)."""
    if not isinstance(config, dict):
        return DEFAULT_SPLIT_BY_PROMPT

    direct_candidates = [
        config.get("split_by_prompt"),
        config.get("splitByPrompt"),
    ]
    for value in direct_candidates:
        if value is not None:
            return _to_bool(value)

    eval_config = config.get("eval_config")
    if isinstance(eval_config, dict):
        nested_candidates = [
            eval_config.get("split_by_prompt"),
            eval_config.get("splitByPrompt"),
        ]
        nested_cfg = eval_config.get("config")
        if isinstance(nested_cfg, dict):
            nested_candidates.extend([
                nested_cfg.get("split_by_prompt"),
                nested_cfg.get("splitByPrompt"),
            ])

        for value in nested_candidates:
            if value is not None:
                return _to_bool(value)

    return DEFAULT_SPLIT_BY_PROMPT


def _get_or_create_prompt_feature_types(
    db_session,
    split_by_prompt: bool = DEFAULT_SPLIT_BY_PROMPT,
):
    """
    Ensure feature types exist for demo generation outputs.

    Default behavior keeps all outputs in one shared feature type (no prompt split).
    """
    from db.models.scenario import FeatureType

    split_mode = _to_bool(split_by_prompt)
    if split_mode:
        feature_type_specs = {
            PRESEED_PROMPT_KEY: STRUCTURED_FEATURE_TYPE_NAME,
            LIVE_PROMPT_KEY: NARRATIVE_FEATURE_TYPE_NAME,
        }
    else:
        feature_type_specs = {
            PRESEED_PROMPT_KEY: MERGED_FEATURE_TYPE_NAME,
            LIVE_PROMPT_KEY: MERGED_FEATURE_TYPE_NAME,
        }

    feature_type_by_prompt = {}
    for prompt_key, feature_type_name in feature_type_specs.items():
        feature_type = FeatureType.query.filter_by(name=feature_type_name).first()
        if not feature_type:
            feature_type = FeatureType(name=feature_type_name)
            db_session.session.add(feature_type)
            db_session.session.flush()
        feature_type_by_prompt[prompt_key] = feature_type

    # Keep structured/shared type as deterministic fallback for unknown prompt labels.
    fallback_feature_type = feature_type_by_prompt[PRESEED_PROMPT_KEY]
    return feature_type_by_prompt, fallback_feature_type


def _resolve_prompt_feature_type(prompt_name, feature_type_by_prompt, fallback_feature_type):
    """
    Resolve the seeded feature type for an output prompt label.

    Handles exact prompt names and common aliases to keep provenance robust
    when prompt labels differ slightly across runs.
    """
    prompt_key = _normalize_prompt_key(prompt_name)
    if prompt_key in feature_type_by_prompt:
        return feature_type_by_prompt[prompt_key]

    if "structured" in prompt_key:
        return feature_type_by_prompt.get(PRESEED_PROMPT_KEY, fallback_feature_type)
    if "narrative" in prompt_key or "live situation summary" in prompt_key:
        return feature_type_by_prompt.get(LIVE_PROMPT_KEY, fallback_feature_type)

    return fallback_feature_type


def _select_balanced_partial_features(features):
    """
    Pick two partial-ranking features that keep prompt/model coverage balanced.

    Preferred pair:
    - different prompt (feature type)
    - different generation model (llm_id)
    """
    if len(features) <= 2:
        return list(features)

    # Best case: one per prompt and one per model.
    for i, first in enumerate(features):
        for second in features[i + 1:]:
            if first.type_id != second.type_id and first.llm_id != second.llm_id:
                return [first, second]

    # Next best: at least one per prompt.
    for i, first in enumerate(features):
        for second in features[i + 1:]:
            if first.type_id != second.type_id:
                return [first, second]

    # Last fallback: first and last to maximize spread.
    return [features[0], features[-1]]


def _ensure_eval_scenario_integrity(
    db_session,
    scenario,
    counselling_cases,
    ranking_type,
    feature_type_by_prompt,
    fallback_feature_type,
    llm_mistral,
    llm_gpt5_nano,
    split_by_prompt=False,
    preseed_job=None,
):
    """
    Ensure seeded evaluation scenario is complete and demo-ready.

    Repairs missing:
    - evaluation items / scenario links
    - scenario item distributions for current scenario users
    - source/reference messages
    - feature texts derived from pre-seeded outputs
    """
    from db.models.scenario import (
        ScenarioItems,
        EvaluationItem,
        Message,
        Feature,
        ScenarioUsers,
        ScenarioItemDistribution,
    )
    from db.models.generation import GeneratedOutput

    counters = {
        "items_created": 0,
        "scenario_links_created": 0,
        "distributions_created": 0,
        "messages_added": 0,
        "features_added": 0,
        "features_retyped": 0,
        "config_updated": 0,
    }

    config = scenario.config_json or {}
    if not isinstance(config, dict):
        config = {}
    config_changed = False

    if config.get("evaluation") != "ranking":
        config["evaluation"] = "ranking"
        config_changed = True
    if config.get("enable_llm_evaluation") is not True:
        config["enable_llm_evaluation"] = True
        config_changed = True
    if config.get("llm_evaluators") != EVALUATION_MODEL_IDS:
        config["llm_evaluators"] = list(EVALUATION_MODEL_IDS)
        config_changed = True
    if config.get("demo_generation_prompts") != GENERATION_PROMPT_TEMPLATE_NAMES:
        config["demo_generation_prompts"] = list(GENERATION_PROMPT_TEMPLATE_NAMES)
        config_changed = True
    if config.get("split_by_prompt") != bool(split_by_prompt):
        config["split_by_prompt"] = bool(split_by_prompt)
        config_changed = True

    feature_type_names = {
        "structured": feature_type_by_prompt[PRESEED_PROMPT_KEY].name,
        "narrative": feature_type_by_prompt[LIVE_PROMPT_KEY].name,
    }
    if config.get("demo_prompt_feature_types") != feature_type_names:
        config["demo_prompt_feature_types"] = feature_type_names
        config_changed = True

    if config.get("source_generation_job_name") != PRESEED_JOB_NAME:
        config["source_generation_job_name"] = PRESEED_JOB_NAME
        config_changed = True
    if config.get("source_generation_models") != GENERATION_MODEL_IDS:
        config["source_generation_models"] = list(GENERATION_MODEL_IDS)
        config_changed = True
    if config.get("source_generation_prompt_templates") != GENERATION_PROMPT_TEMPLATE_NAMES:
        config["source_generation_prompt_templates"] = list(GENERATION_PROMPT_TEMPLATE_NAMES)
        config_changed = True
    if preseed_job and config.get("source_generation_job_id") != preseed_job.id:
        config["source_generation_job_id"] = preseed_job.id
        config_changed = True

    if config_changed:
        scenario.config_json = config
        counters["config_updated"] += 1

    scenario_users = ScenarioUsers.query.filter_by(scenario_id=scenario.id).all()
    scenario_items = ScenarioItems.query.filter_by(scenario_id=scenario.id).order_by(ScenarioItems.id.asc()).all()
    existing_distributions = {
        (row.scenario_user_id, row.scenario_item_id)
        for row in ScenarioItemDistribution.query.filter_by(scenario_id=scenario.id).all()
    }

    outputs_by_case = {}
    if preseed_job:
        outputs = GeneratedOutput.query.filter_by(job_id=preseed_job.id).order_by(GeneratedOutput.id.asc()).all()
        for out in outputs:
            try:
                case_idx = int((out.prompt_variables_json or {}).get("source_index", -1))
            except (TypeError, ValueError):
                case_idx = -1
            if 0 <= case_idx < len(counselling_cases):
                outputs_by_case.setdefault(case_idx, []).append(out)
        for case_idx in list(outputs_by_case.keys()):
            outputs_by_case[case_idx] = _sort_outputs_for_case(outputs_by_case[case_idx])

    case_to_item = {}
    case_to_scenario_item = {}
    used_case_indices = set()

    for idx, scenario_item in enumerate(scenario_items):
        item_id = scenario_item.thread_id or scenario_item.item_id
        if not item_id:
            continue
        eval_item = EvaluationItem.query.get(item_id)
        if not eval_item:
            continue

        case_idx = None
        if eval_item.chat_id is not None:
            try:
                candidate = int(eval_item.chat_id) - 20000
                if 0 <= candidate < len(counselling_cases):
                    case_idx = candidate
            except (TypeError, ValueError):
                case_idx = None

        if case_idx is None:
            subject = (eval_item.subject or "").strip()
            if subject:
                for i, case in enumerate(counselling_cases):
                    if i in used_case_indices:
                        continue
                    if (case.get("subject") or "").strip() == subject:
                        case_idx = i
                        break

        if case_idx is None and idx < len(counselling_cases) and idx not in used_case_indices:
            case_idx = idx

        if case_idx is None or case_idx in case_to_item:
            continue

        case_to_item[case_idx] = eval_item
        case_to_scenario_item[case_idx] = scenario_item
        used_case_indices.add(case_idx)

    for case_idx, case in enumerate(counselling_cases):
        eval_item = case_to_item.get(case_idx)
        scenario_item = case_to_scenario_item.get(case_idx)

        if not eval_item:
            eval_item = EvaluationItem.query.filter_by(
                chat_id=20000 + case_idx,
                institut_id=99,
                function_type_id=ranking_type.function_type_id,
            ).first()
            if not eval_item:
                eval_item = EvaluationItem(
                    chat_id=20000 + case_idx,
                    institut_id=99,
                    subject=case.get("subject") or f"Case {case_idx}",
                    sender="demo",
                    function_type_id=ranking_type.function_type_id,
                )
                db_session.session.add(eval_item)
                db_session.session.flush()
                counters["items_created"] += 1
            case_to_item[case_idx] = eval_item

        if not scenario_item:
            scenario_item = ScenarioItems.query.filter_by(
                scenario_id=scenario.id,
                item_id=eval_item.item_id,
            ).first()
            if not scenario_item:
                scenario_item = ScenarioItems(
                    scenario_id=scenario.id,
                    thread_id=eval_item.item_id,
                )
                db_session.session.add(scenario_item)
                db_session.session.flush()
                counters["scenario_links_created"] += 1
            case_to_scenario_item[case_idx] = scenario_item

        for scenario_user in scenario_users:
            key = (scenario_user.id, scenario_item.id)
            if key in existing_distributions:
                continue
            db_session.session.add(ScenarioItemDistribution(
                scenario_id=scenario.id,
                scenario_user_id=scenario_user.id,
                scenario_item_id=scenario_item.id,
            ))
            existing_distributions.add(key)
            counters["distributions_created"] += 1

        if Message.query.filter_by(item_id=eval_item.item_id).first() is None and case.get("content"):
            db_session.session.add(Message(
                item_id=eval_item.item_id,
                sender="source",
                content=case["content"],
                timestamp=datetime.utcnow() - timedelta(hours=2),
                generated_by="Human",
            ))
            counters["messages_added"] += 1

        case_outputs = outputs_by_case.get(case_idx, [])
        if not case_outputs:
            continue

        existing_features = (
            Feature.query
            .filter_by(item_id=eval_item.item_id)
            .order_by(Feature.feature_id.asc())
            .all()
        )
        existing_by_signature = {}
        for feature in existing_features:
            feature_content = str(feature.content or "").strip()
            if not feature_content:
                continue
            signature = (feature.llm_id, feature_content)
            existing_by_signature.setdefault(signature, []).append(feature)

        expected_features = []
        for output in case_outputs:
            rendered_content = str(output.generated_content or "").strip()
            if not rendered_content:
                continue
            llm_ref = _resolve_eval_llm_for_output(output, llm_mistral, llm_gpt5_nano)
            feature_type = _resolve_prompt_feature_type(
                prompt_name=getattr(output, "prompt_variant_name", None),
                feature_type_by_prompt=feature_type_by_prompt,
                fallback_feature_type=fallback_feature_type,
            )
            expected_features.append((llm_ref.llm_id, rendered_content, feature_type.type_id))

        for llm_id, content, expected_type_id in expected_features:
            signature = (llm_id, content)
            candidates = existing_by_signature.get(signature, [])

            matched_feature = None
            for idx, candidate in enumerate(candidates):
                if candidate.type_id == expected_type_id:
                    matched_feature = candidates.pop(idx)
                    break

            if matched_feature is None and candidates:
                matched_feature = candidates.pop(0)
                if matched_feature.type_id != expected_type_id:
                    matched_feature.type_id = expected_type_id
                    counters["features_retyped"] += 1

            if matched_feature is None:
                db_session.session.add(Feature(
                    item_id=eval_item.item_id,
                    type_id=expected_type_id,
                    llm_id=llm_id,
                    content=content,
                ))
                counters["features_added"] += 1

    if any(counters.values()):
        db_session.session.commit()

    actions = []
    if counters["items_created"] or counters["scenario_links_created"]:
        actions.append(
            f"Repaired eval items: +{counters['items_created']} items, "
            f"+{counters['scenario_links_created']} scenario links"
        )
    if counters["distributions_created"]:
        actions.append(f"Repaired scenario distributions: +{counters['distributions_created']}")
    if counters["messages_added"]:
        actions.append(f"Backfilled reference messages: +{counters['messages_added']}")
    if counters["features_retyped"]:
        actions.append(f"Corrected prompt feature mapping: +{counters['features_retyped']}")
    if counters["features_added"]:
        actions.append(f"Backfilled ranking features: +{counters['features_added']}")
    if counters["config_updated"]:
        actions.append(
            "Updated demo scenario config "
            f"(split_by_prompt={bool(split_by_prompt)})"
        )

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
        EvaluationItem, Feature, FeatureFunctionType,
        LLM, Message, UserFeatureRanking,
    )
    from db.models.llm_task_result import LLMTaskResult
    from db.models.generation import GenerationJob, GeneratedOutput
    from db.seeders.demo_video_data import COUNSELLING_CASES

    actions = []

    # Get the pre-seeded batch job
    preseed_job = GenerationJob.query.filter_by(
        name=PRESEED_JOB_NAME, created_by=DEMO_USER
    ).first()

    # Get or create ranking function type
    ranking_type = FeatureFunctionType.query.filter_by(name='ranking').first()
    if not ranking_type:
        ranking_type = FeatureFunctionType(name='ranking')
        db_session.session.add(ranking_type)
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

    # Check if scenario already exists. If yes, repair missing demo integrity and keep it.
    existing = RatingScenarios.query.filter_by(
        scenario_name=EVAL_SCENARIO_NAME
    ).first()
    split_by_prompt = (
        _is_split_by_prompt_enabled(existing.config_json)
        if existing else DEFAULT_SPLIT_BY_PROMPT
    )
    feature_type_by_prompt, fallback_feature_type = _get_or_create_prompt_feature_types(
        db_session,
        split_by_prompt=split_by_prompt,
    )
    if existing:
        actions.extend(_ensure_eval_scenario_integrity(
            db_session=db_session,
            scenario=existing,
            counselling_cases=COUNSELLING_CASES,
            ranking_type=ranking_type,
            feature_type_by_prompt=feature_type_by_prompt,
            fallback_feature_type=fallback_feature_type,
            llm_mistral=llm_mistral,
            llm_gpt5_nano=llm_gpt5_nano,
            split_by_prompt=split_by_prompt,
            preseed_job=preseed_job,
        ))
        actions.append(f"Eval scenario '{EVAL_SCENARIO_NAME}' already exists (id={existing.id})")
        return actions

    if not preseed_job:
        actions.append("Pre-seed job not found, skipping eval scenario")
        return actions

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
            "split_by_prompt": bool(split_by_prompt),
            "llm_evaluators": list(EVALUATION_MODEL_IDS),
            "demo_generation_prompts": list(GENERATION_PROMPT_TEMPLATE_NAMES),
            "demo_prompt_feature_types": {
                "structured": feature_type_by_prompt[PRESEED_PROMPT_KEY].name,
                "narrative": feature_type_by_prompt[LIVE_PROMPT_KEY].name,
            },
            "source_generation_job_id": preseed_job.id,
            "source_generation_job_name": PRESEED_JOB_NAME,
            "source_generation_models": list(GENERATION_MODEL_IDS),
            "source_generation_prompt_templates": list(GENERATION_PROMPT_TEMPLATE_NAMES),
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
    outputs = GeneratedOutput.query.filter_by(job_id=preseed_job.id).order_by(GeneratedOutput.id.asc()).all()

    # Group by source_index
    outputs_by_case = {}
    for out in outputs:
        try:
            case_idx = int((out.prompt_variables_json or {}).get('source_index', -1))
        except (TypeError, ValueError):
            case_idx = -1
        if case_idx < 0:
            continue
        outputs_by_case.setdefault(case_idx, []).append(out)

    items = []
    item_features = {}  # item_id -> list of features

    for case_idx in range(len(COUNSELLING_CASES)):
        case = COUNSELLING_CASES[case_idx] if case_idx < len(COUNSELLING_CASES) else None
        case_outputs = _sort_outputs_for_case(outputs_by_case.get(case_idx, []))

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

        # Add source/reference text for right-side panel in ranking UI.
        if case and case.get('content'):
            db_session.session.add(Message(
                item_id=item.item_id,
                sender='source',
                content=case['content'],
                timestamp=datetime.utcnow() - timedelta(hours=2),
                generated_by='Human',
            ))

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
            llm_ref = _resolve_eval_llm_for_output(out, llm_mistral, llm_gpt5_nano)
            feature_type = _resolve_prompt_feature_type(
                prompt_name=out.prompt_variant_name,
                feature_type_by_prompt=feature_type_by_prompt,
                fallback_feature_type=fallback_feature_type,
            )

            feature = Feature(
                item_id=item.item_id,
                type_id=feature_type.type_id,
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
                    type_id=feature.type_id,
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
        feature_index_by_id = {
            feature.feature_id: idx
            for idx, feature in enumerate(item_9_features)
        }
        partial_features = _select_balanced_partial_features(item_9_features)
        for partial_rank_idx, feature in enumerate(partial_features[:2]):
            feat_idx = feature_index_by_id.get(feature.feature_id, partial_rank_idx)
            ranking = UserFeatureRanking(
                user_id=demo_user.id,
                feature_id=feature.feature_id,
                ranking_content=float(partial_rank_idx + 1),
                type_id=feature.type_id,
                llm_id=feature.llm_id,
                bucket=pattern_9[feat_idx] if feat_idx < len(pattern_9) else 'Neutral',
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
        EVALUATION_MODEL_IDS[0], ranking_patterns_magistral, 10
    )
    actions.append(f"Added {magistral_count} Magistral LLM rankings (10/10 items)")

    gpt5mini_count = _add_llm_rankings(
        EVALUATION_MODEL_IDS[1], ranking_patterns_gpt5mini, 10
    )
    actions.append(f"Added {gpt5mini_count} GPT-5 Mini LLM rankings (10/10 items)")

    db_session.session.commit()
    return actions


def _seed_evaluation_scenario_5_buckets(db_session, demo_user, collab_user):
    """
    Seed an additional ranking scenario from the same batch generation with 5 buckets.

    Purpose:
    - Provide a dedicated demo scenario for 5-bucket ranking workflows
    - Keep full cartesian coverage (2 prompts x 2 models per counselling case)
    - Pre-fill both human and LLM rankings for immediate evaluation tab demo
    """
    from db.models.scenario import (
        RatingScenarios, ScenarioUsers, ScenarioItems,
        ScenarioItemDistribution, ScenarioRoles,
        EvaluationItem, Feature, FeatureFunctionType,
        LLM, Message, UserFeatureRanking,
    )
    from db.models.llm_task_result import LLMTaskResult
    from db.models.generation import GenerationJob, GeneratedOutput
    from db.seeders.demo_video_data import COUNSELLING_CASES

    actions = []

    preseed_job = GenerationJob.query.filter_by(
        name=PRESEED_JOB_NAME, created_by=DEMO_USER
    ).first()

    ranking_type = FeatureFunctionType.query.filter_by(name='ranking').first()
    if not ranking_type:
        ranking_type = FeatureFunctionType(name='ranking')
        db_session.session.add(ranking_type)
        db_session.session.flush()

    def _get_or_create_llm(name):
        llm = LLM.query.filter_by(name=name).first()
        if not llm:
            llm = LLM(name=name)
            db_session.session.add(llm)
            db_session.session.flush()
        return llm

    llm_mistral = _get_or_create_llm('Mistral Small')
    llm_gpt5_nano = _get_or_create_llm('GPT-5 Nano')

    existing = RatingScenarios.query.filter_by(
        scenario_name=EVAL_SCENARIO_NAME_5_BUCKETS
    ).first()
    split_by_prompt = (
        _is_split_by_prompt_enabled(existing.config_json)
        if existing else DEFAULT_SPLIT_BY_PROMPT
    )
    feature_type_by_prompt, fallback_feature_type = _get_or_create_prompt_feature_types(
        db_session,
        split_by_prompt=split_by_prompt,
    )
    if existing:
        actions.extend(_ensure_eval_scenario_integrity(
            db_session=db_session,
            scenario=existing,
            counselling_cases=COUNSELLING_CASES,
            ranking_type=ranking_type,
            feature_type_by_prompt=feature_type_by_prompt,
            fallback_feature_type=fallback_feature_type,
            llm_mistral=llm_mistral,
            llm_gpt5_nano=llm_gpt5_nano,
            split_by_prompt=split_by_prompt,
            preseed_job=preseed_job,
        ))
        actions.append(
            f"Eval scenario '{EVAL_SCENARIO_NAME_5_BUCKETS}' already exists (id={existing.id})"
        )
        return actions

    if not preseed_job:
        actions.append("Pre-seed job not found, skipping 5-bucket eval scenario")
        return actions

    scenario = RatingScenarios(
        scenario_name=EVAL_SCENARIO_NAME_5_BUCKETS,
        function_type_id=ranking_type.function_type_id,
        begin=datetime.utcnow() - timedelta(days=1),
        end=datetime.utcnow() + timedelta(days=30),
        timestamp=datetime.utcnow(),
        created_by=DEMO_USER,
        config_json={
            "evaluation": "ranking",
            "enable_llm_evaluation": True,
            "split_by_prompt": bool(split_by_prompt),
            "llm_evaluators": list(EVALUATION_MODEL_IDS),
            "demo_generation_prompts": list(GENERATION_PROMPT_TEMPLATE_NAMES),
            "demo_prompt_feature_types": {
                "structured": feature_type_by_prompt[PRESEED_PROMPT_KEY].name,
                "narrative": feature_type_by_prompt[LIVE_PROMPT_KEY].name,
            },
            "source_generation_job_id": preseed_job.id,
            "source_generation_job_name": PRESEED_JOB_NAME,
            "source_generation_models": list(GENERATION_MODEL_IDS),
            "source_generation_prompt_templates": list(GENERATION_PROMPT_TEMPLATE_NAMES),
            "buckets": [
                {"id": "sehr_gut", "name": {"de": "Sehr gut", "en": "Very good"}, "color": "#7FB26B"},
                {"id": "gut", "name": {"de": "Gut", "en": "Good"}, "color": "#B0CA97"},
                {"id": "mittel", "name": {"de": "Mittel", "en": "Medium"}, "color": "#D1BC8A"},
                {"id": "schlecht", "name": {"de": "Schlecht", "en": "Poor"}, "color": "#E8A087"},
                {"id": "sehr_schlecht", "name": {"de": "Sehr schlecht", "en": "Very poor"}, "color": "#D77974"},
            ],
        },
    )
    db_session.session.add(scenario)
    db_session.session.flush()
    actions.append(
        f"Created eval scenario '{EVAL_SCENARIO_NAME_5_BUCKETS}' (id={scenario.id})"
    )

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

    outputs = GeneratedOutput.query.filter_by(job_id=preseed_job.id).order_by(GeneratedOutput.id.asc()).all()

    outputs_by_case = {}
    for out in outputs:
        try:
            case_idx = int((out.prompt_variables_json or {}).get('source_index', -1))
        except (TypeError, ValueError):
            case_idx = -1
        if case_idx < 0:
            continue
        outputs_by_case.setdefault(case_idx, []).append(out)

    items = []
    item_features = {}

    for case_idx in range(len(COUNSELLING_CASES)):
        case = COUNSELLING_CASES[case_idx] if case_idx < len(COUNSELLING_CASES) else None
        case_outputs = _sort_outputs_for_case(outputs_by_case.get(case_idx, []))

        item = EvaluationItem(
            chat_id=21000 + case_idx,
            institut_id=99,
            subject=case['subject'] if case else f"Case {case_idx}",
            sender='demo',
            function_type_id=ranking_type.function_type_id,
        )
        db_session.session.add(item)
        db_session.session.flush()
        items.append(item)

        if case and case.get('content'):
            db_session.session.add(Message(
                item_id=item.item_id,
                sender='source',
                content=case['content'],
                timestamp=datetime.utcnow() - timedelta(hours=2),
                generated_by='Human',
            ))

        si = ScenarioItems(
            scenario_id=scenario.id,
            thread_id=item.item_id,
        )
        db_session.session.add(si)
        db_session.session.flush()

        for su in [reviewer_1_su, reviewer_2_su]:
            if su:
                db_session.session.add(ScenarioItemDistribution(
                    scenario_id=scenario.id,
                    scenario_user_id=su.id,
                    scenario_item_id=si.id,
                ))

        features = []
        for out in case_outputs:
            llm_ref = _resolve_eval_llm_for_output(out, llm_mistral, llm_gpt5_nano)
            feature_type = _resolve_prompt_feature_type(
                prompt_name=out.prompt_variant_name,
                feature_type_by_prompt=feature_type_by_prompt,
                fallback_feature_type=fallback_feature_type,
            )

            feature = Feature(
                item_id=item.item_id,
                type_id=feature_type.type_id,
                llm_id=llm_ref.llm_id,
                content=out.generated_content,
            )
            db_session.session.add(feature)
            db_session.session.flush()
            features.append(feature)

        item_features[item.item_id] = features

    actions.append(
        f"Created {len(items)} evaluation items with features for '{EVAL_SCENARIO_NAME_5_BUCKETS}'"
    )

    ranking_patterns = [
        ['sehr_gut', 'gut', 'mittel', 'schlecht'],
        ['gut', 'mittel', 'schlecht', 'sehr_schlecht'],
        ['sehr_gut', 'mittel', 'gut', 'schlecht'],
        ['gut', 'schlecht', 'mittel', 'sehr_schlecht'],
        ['mittel', 'gut', 'schlecht', 'sehr_gut'],
        ['sehr_gut', 'gut', 'schlecht', 'mittel'],
        ['mittel', 'schlecht', 'gut', 'sehr_schlecht'],
        ['gut', 'mittel', 'sehr_gut', 'schlecht'],
        ['schlecht', 'gut', 'mittel', 'sehr_schlecht'],
        ['sehr_gut', 'mittel', 'gut', 'schlecht'],
    ]

    ranking_patterns_r2 = [
        ['gut', 'gut', 'mittel', 'schlecht'],
        ['gut', 'mittel', 'schlecht', 'sehr_schlecht'],
        ['sehr_gut', 'mittel', 'mittel', 'schlecht'],
        ['gut', 'schlecht', 'mittel', 'schlecht'],
        ['mittel', 'gut', 'schlecht', 'gut'],
        ['sehr_gut', 'mittel', 'schlecht', 'mittel'],
        ['mittel', 'schlecht', 'gut', 'sehr_schlecht'],
        ['gut', 'mittel', 'gut', 'schlecht'],
        ['schlecht', 'mittel', 'mittel', 'sehr_schlecht'],
        ['gut', 'mittel', 'gut', 'schlecht'],
    ]

    ranking_patterns_magistral = [
        ['sehr_gut', 'gut', 'mittel', 'schlecht'],
        ['gut', 'mittel', 'schlecht', 'sehr_schlecht'],
        ['sehr_gut', 'mittel', 'gut', 'schlecht'],
        ['gut', 'mittel', 'schlecht', 'sehr_schlecht'],
        ['mittel', 'gut', 'schlecht', 'gut'],
        ['sehr_gut', 'gut', 'schlecht', 'mittel'],
        ['mittel', 'schlecht', 'gut', 'sehr_schlecht'],
        ['gut', 'mittel', 'sehr_gut', 'schlecht'],
        ['schlecht', 'gut', 'mittel', 'sehr_schlecht'],
        ['sehr_gut', 'mittel', 'gut', 'schlecht'],
    ]

    ranking_patterns_gpt5mini = [
        ['gut', 'gut', 'mittel', 'schlecht'],
        ['gut', 'mittel', 'schlecht', 'sehr_schlecht'],
        ['sehr_gut', 'mittel', 'mittel', 'schlecht'],
        ['gut', 'schlecht', 'mittel', 'sehr_schlecht'],
        ['mittel', 'gut', 'schlecht', 'gut'],
        ['sehr_gut', 'mittel', 'schlecht', 'mittel'],
        ['mittel', 'schlecht', 'gut', 'sehr_schlecht'],
        ['gut', 'mittel', 'gut', 'schlecht'],
        ['schlecht', 'mittel', 'mittel', 'sehr_schlecht'],
        ['gut', 'mittel', 'gut', 'schlecht'],
    ]

    def _add_rankings(user_id, patterns, num_items):
        count = 0
        for case_idx in range(min(num_items, len(items))):
            item = items[case_idx]
            features = item_features.get(item.item_id, [])
            pattern = patterns[case_idx] if case_idx < len(patterns) else ['mittel'] * 4

            for feat_idx, feature in enumerate(features):
                bucket = pattern[feat_idx] if feat_idx < len(pattern) else 'mittel'
                db_session.session.add(UserFeatureRanking(
                    user_id=user_id,
                    feature_id=feature.feature_id,
                    ranking_content=float(feat_idx + 1),
                    type_id=feature.type_id,
                    llm_id=feature.llm_id,
                    bucket=bucket,
                ))
                count += 1
        return count

    r1_count = _add_rankings(demo_user.id, ranking_patterns, 10)
    actions.append(f"Added {r1_count} rankings for {DEMO_USER} (10/10 items)")

    if collab_user:
        r2_count = _add_rankings(collab_user.id, ranking_patterns_r2, 10)
        actions.append(f"Added {r2_count} rankings for {COLLAB_USER} (10/10 items)")

    def _add_llm_rankings(model_id, patterns, num_items):
        count = 0
        for case_idx in range(min(num_items, len(items))):
            item = items[case_idx]
            features = item_features.get(item.item_id, [])
            pattern = patterns[case_idx] if case_idx < len(patterns) else ['mittel'] * 4

            bucket_map = {}
            for feat_idx, feature in enumerate(features):
                bucket = str(pattern[feat_idx] if feat_idx < len(pattern) else 'mittel').strip().lower()
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
        EVALUATION_MODEL_IDS[0], ranking_patterns_magistral, 10
    )
    actions.append(f"Added {magistral_count} Magistral LLM rankings (10/10 items)")

    gpt5mini_count = _add_llm_rankings(
        EVALUATION_MODEL_IDS[1], ranking_patterns_gpt5mini, 10
    )
    actions.append(f"Added {gpt5mini_count} GPT-5 Mini LLM rankings (10/10 items)")

    db_session.session.commit()
    return actions


def _get_block(prompt, name):
    blocks = (prompt.content or {}).get('blocks', {})
    block = blocks.get(name, {})
    return block.get('content', '') if isinstance(block, dict) else ''


def _render_system(prompt):
    parts = [_get_block(prompt, "System Prompt"), _get_block(prompt, "Task Explanation")]
    return "\n\n".join(p for p in parts if p)


def _render_user(prompt, case):
    tpl = _get_block(prompt, "Data Format Explanation")
    if not tpl:
        return f"Subject: {case['subject']}\n\n{case['content']}"
    return tpl.replace("{{subject}}", case["subject"]).replace("{{content}}", case["content"])
