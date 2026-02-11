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
PRESEED_PROMPT_NAME = "News Summary Prompt"
PRESEED_JOB_NAME = "News Summary Demo Job"
LIVE_PROMPT_NAME = "News Summary Eval"
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
        RatingScenarios.scenario_name.contains("News Summary")
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
    from db.seeders.demo_video_data import NEWS_ARTICLES, SAMPLE_SUMMARIES

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
        total_outputs = len(NEWS_ARTICLES) * 2 * 2

        job = GenerationJob(
            name=PRESEED_JOB_NAME,
            description="Demo batch: two prompts x two models x 10 news articles.",
            status=GenerationJobStatus.COMPLETED,
            config_json={
                "mode": "matrix",
                "sources": {"type": "manual", "items": NEWS_ARTICLES},
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
        for article_idx, article in enumerate(NEWS_ARTICLES):
            for summary_key, prompt_obj, prompt_name in [
                ("concise", preseed, PRESEED_PROMPT_NAME),
                ("analyst", temp_eval, LIVE_PROMPT_NAME),
            ]:
                for model in [mistral, magistral]:
                    summary = SAMPLE_SUMMARIES[summary_key][article_idx]
                    sys_prompt = _render_system(prompt_obj)
                    usr_prompt = _render_user(prompt_obj, article)

                    _db.session.add(GeneratedOutput(
                        job_id=job.id,
                        llm_model_id=model.id,
                        llm_model_name=model.model_id,
                        prompt_variant_name=prompt_name,
                        prompt_variables_json={
                            'source_index': article_idx,
                            'source_title': article['title']
                        },
                        generated_content=summary,
                        rendered_system_prompt=sys_prompt,
                        rendered_user_prompt=usr_prompt,
                        status=GeneratedOutputStatus.COMPLETED,
                        input_tokens=len(article['content'].split()) + 50,
                        output_tokens=len(summary.split()),
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

    # --- 1. Delete live prompt "News Summary Eval" (any owner) ---
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
        RatingScenarios.scenario_name.contains("News Summary")
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
    """Pre-seed prompt: detailed, verbose prompt with few-shot examples.
    Deliberately much longer and more prescriptive than the live prompt
    to show that different prompt styles produce visibly different outputs."""
    return {
        "blocks": {
            "Role Definition": {
                "content": (
                    "Role definition: You are a senior news analyst working for an international press agency. "
                    "Your summaries are used by editors who need to decide whether a story deserves front-page coverage. "
                    "You have deep expertise in technology, science, and policy reporting. "
                    "Your writing style is precise, uses active voice, and avoids hedging language."
                ),
                "position": 0
            },
            "Task Explanation": {
                "content": (
                    "Task explanation: Analyze the article and produce a structured 3-sentence summary.\n\n"
                    "Sentence 1 — Lead: State the core news event with the most important fact or figure.\n"
                    "Sentence 2 — Context: Provide essential background that helps the reader understand why this matters.\n"
                    "Sentence 3 — Outlook: Mention next steps, open questions, or broader implications.\n\n"
                    "Guidelines:\n"
                    "- Use specific numbers and names from the article when available.\n"
                    "- Do not speculate beyond what the article states.\n"
                    "- Keep each sentence under 30 words.\n"
                    "- Write in present tense for the lead, past tense for background, and future tense for outlook.\n\n"
                    "Few-shot examples:\n\n"
                    "Example input: 'SpaceX Successfully Lands Starship After Orbital Flight'\n"
                    "Example output: SpaceX lands its Starship rocket after a full orbital flight, achieving a key milestone "
                    "for the program. The company spent three years and an estimated $2 billion developing the reusable "
                    "heavy-lift vehicle. NASA now considers Starship the leading candidate for its Artemis lunar cargo missions.\n\n"
                    "Example input: 'Japan Approves First Gene-Edited Food for Consumer Sale'\n"
                    "Example output: Japan becomes the first country to approve a gene-edited tomato for direct sale to "
                    "consumers. Regulators determined that CRISPR-based edits carry no additional risk compared to conventional "
                    "breeding. The decision is expected to accelerate gene-editing approvals across Asia and influence ongoing "
                    "EU regulatory debates."
                ),
                "position": 1
            },
            "Data Format Explanation": {
                "content": (
                    "Data format explanation:\n"
                    "Input:\n"
                    "Title: {{title}}\n\n"
                    "Article:\n"
                    "{{content}}\n\n"
                    "Output:\n"
                    "Exactly 3 sentences in plain text following the Lead-Context-Outlook structure above. "
                    "No bullet points. No headings. No extra commentary."
                ),
                "position": 2
            }
        }
    }


def _build_eval_prompt_content():
    """Eval prompt: 3-sentence detailed summary with more context. Matches
    the block structure of the live-typed prompt but provides richer output."""
    return {
        "blocks": {
            "Role Definition": {
                "content": "Role definition: You are an analytical journalist who provides thorough context alongside factual reporting.",
                "position": 0
            },
            "Task Explanation": {
                "content": "Task explanation: Write a 3-sentence summary of the article. Include relevant background, mention key stakeholders, and explain broader implications beyond the headline.",
                "position": 1
            },
            "Data Format Explanation": {
                "content": (
                    "Data format explanation:\n"
                    "Input:\n"
                    "Title: {{title}}\n\n"
                    "Article:\n"
                    "{{content}}\n\n"
                    "Output:\n"
                    "Exactly 3 sentences in plain text. No bullet points. No extra commentary."
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


def _render_user(prompt, article):
    tpl = _get_block(prompt, "Data Format Explanation")
    if not tpl:
        return f"Title: {article['title']}\n\n{article['content']}"
    return tpl.replace("{{title}}", article["title"]).replace("{{content}}", article["content"])
