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
            model_id='mistralai/Mistral-Small-3.2-24B-Instruct-2506'
        ).first()
        magistral = LLMModel.query.filter_by(
            model_id='mistralai/Magistral-Small-2509'
        ).first()

        if not mistral or not magistral:
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
                "llm_models": [mistral.model_id, magistral.model_id],
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
                for model in [mistral, magistral]:
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

    return {'success': True, 'actions': actions}


def cleanup(include_preseed=False):
    """Delete live-recorded data. If include_preseed=True, also delete pre-seed data."""
    from db import db as _db
    from db.tables import UserPrompt
    from db.models.generation import GenerationJob, GeneratedOutput
    from db.models.scenario import RatingScenarios, UserPromptShare

    deleted = []

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

    # --- 4. Delete demo-created scenarios ---
    preseed_job = GenerationJob.query.filter_by(name=PRESEED_JOB_NAME).first()
    preseed_target_id = preseed_job.target_scenario_id if preseed_job else None

    demo_scenarios = RatingScenarios.query.filter(
        RatingScenarios.scenario_name.contains("Situation")
    ).all()

    for scenario in demo_scenarios:
        if not include_preseed and preseed_target_id and scenario.id == preseed_target_id:
            continue
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
    """Pre-seed prompt: structured situation analysis with JSON output and references.
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
                    "Analyze the email thread and produce a structured situation description of the client's current life circumstances in up to 3 bullet points.\n\n"
                    "Each bullet point must contain:\n"
                    "- **Text**: A concise description of one aspect of the life situation (max 2 sentences, max 160 characters)\n"
                    "- **Reference**: Direct quotes from the email thread as evidence\n\n"
                    "Focus on: housing situation, family relationships, children (age, development, health), professional/educational situation, health status, social conflicts.\n\n"
                    'Return the result as JSON:\n'
                    '```json\n'
                    '{"situation_descriptions": [{"text": "...", "reference": ["quote 1", "quote 2"]}]}\n'
                    '```\n\n'
                    "Rules:\n"
                    "- Use only facts from the thread, no speculation\n"
                    "- Avoid introductory phrases, present information directly\n"
                    "- When counselling parents, also include information about their children\n\n"
                    "Few-shot example:\n\n"
                    "Input: A single mother reports that her 8-year-old son has been refusing to attend school for two weeks, "
                    "complaining of stomach aches. The pediatrician found no physical cause. She works part-time and cannot stay home every day.\n\n"
                    "Output:\n"
                    '{"situation_descriptions": [{"text": "Single mother working part-time, unable to provide daily supervision due to work obligations.", '
                    '"reference": ["I work part-time and cannot stay home every day"]}, '
                    '{"text": "8-year-old son refusing school attendance for two weeks with psychosomatic symptoms.", '
                    '"reference": ["my son has been refusing to go to school for two weeks", "he complains of stomach aches but the pediatrician found nothing"]}]}'
                ),
                "position": 1
            },
            "Data Format Explanation": {
                "content": (
                    "Subject: {{subject}}\n\n"
                    "Email thread:\n"
                    "{{content}}\n\n"
                    'Return only the JSON object with the "situation_descriptions" array. No additional explanations.'
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
                    "Write a plain text paragraph. No JSON, no bullet points."
                ),
                "position": 2
            }
        }
    }


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
