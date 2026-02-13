#!/usr/bin/env python3
"""
Seed demo data (prompts, batch job, demo scenarios) for a specific user.
Usage: python3 /app/scripts/seed_user_demo_data.py <username>
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Must import before app context
from main import app  # noqa: E402

TARGET_USER = sys.argv[1] if len(sys.argv) > 1 else None
if not TARGET_USER:
    print("Usage: python3 seed_user_demo_data.py <username>")
    sys.exit(1)

with app.app_context():
    from db import db as _db
    from db.tables import User, UserPrompt
    from db.models.generation import (
        GenerationJob, GeneratedOutput,
        GenerationJobStatus, GeneratedOutputStatus,
    )
    from db.models.llm_model import LLMModel
    from db.models.scenario import (
        UserPromptShare, RatingScenarios, ScenarioUsers,
        ScenarioItems, ScenarioItemDistribution, ScenarioRoles,
    )
    from db.seeders.scenarios import seed_demo_scenarios
    from db.seeders.demo_video_data import COUNSELLING_CASES, SAMPLE_OUTPUTS
    from services.demo_video_service import (
        _build_preseed_prompt_content, _build_eval_prompt_content,
        _render_system, _render_user,
        PRESEED_PROMPT_NAME, LIVE_PROMPT_NAME, PRESEED_JOB_NAME,
    )
    from datetime import datetime, timedelta

    user = User.query.filter_by(username=TARGET_USER).first()
    if not user:
        print(f"ERROR: User '{TARGET_USER}' not found")
        sys.exit(1)

    print(f"Seeding demo data for user '{TARGET_USER}' (id={user.id})...")

    # --- 1. Create prompts ---
    for prompt_name, build_fn in [
        (PRESEED_PROMPT_NAME, _build_preseed_prompt_content),
        (LIVE_PROMPT_NAME, _build_eval_prompt_content),
    ]:
        existing = UserPrompt.query.filter_by(user_id=user.id, name=prompt_name).first()
        if existing:
            print(f"  Prompt '{prompt_name}' already exists (id={existing.prompt_id})")
        else:
            p = UserPrompt(user_id=user.id, name=prompt_name, content=build_fn())
            _db.session.add(p)
            _db.session.flush()
            print(f"  Created prompt '{prompt_name}' (id={p.prompt_id})")

    _db.session.commit()

    # --- 2. Create batch generation job ---
    existing_job = GenerationJob.query.filter_by(
        name=PRESEED_JOB_NAME, created_by=TARGET_USER
    ).first()

    if existing_job:
        print(f"  Job '{PRESEED_JOB_NAME}' already exists (id={existing_job.id})")
    else:
        mistral = LLMModel.query.filter_by(
            model_id='mistralai/Mistral-Small-3.2-24B-Instruct-2506'
        ).first()
        magistral = LLMModel.query.filter_by(
            model_id='mistralai/Magistral-Small-2509'
        ).first()

        if not mistral or not magistral:
            print("  WARNING: Required LLM models not found, skipping job")
        else:
            preseed_prompt = UserPrompt.query.filter_by(
                user_id=user.id, name=PRESEED_PROMPT_NAME
            ).first()
            eval_prompt = UserPrompt.query.filter_by(
                user_id=user.id, name=LIVE_PROMPT_NAME
            ).first()

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
                        {"template_name": LIVE_PROMPT_NAME},
                    ],
                    "llm_models": [mistral.model_id, magistral.model_id],
                    "generation_params": {"temperature": 0.7, "max_tokens": 500},
                },
                total_items=total_outputs,
                completed_items=total_outputs,
                failed_items=0,
                total_tokens=total_outputs * 800,
                total_cost_usd=0.05,
                created_by=TARGET_USER,
                created_at=now - timedelta(hours=2),
                started_at=now - timedelta(hours=2),
                completed_at=now - timedelta(hours=1, minutes=45),
            )
            _db.session.add(job)
            _db.session.flush()

            output_idx = 0
            for case_idx, case in enumerate(COUNSELLING_CASES):
                for summary_key, prompt_obj, prompt_name in [
                    ("structured", preseed_prompt, PRESEED_PROMPT_NAME),
                    ("narrative", eval_prompt, LIVE_PROMPT_NAME),
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
                                'source_subject': case['subject'],
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
                            completed_at=now - timedelta(hours=1, minutes=50 - output_idx),
                        ))
                        output_idx += 1

            _db.session.commit()
            print(f"  Created job '{PRESEED_JOB_NAME}' (id={job.id}) with {total_outputs} outputs")

    # --- 3. Seed demo scenarios and add user ---
    DEMO_SCENARIO_NAMES = [
        'Demo Ranking Szenario',
        'Demo Verlauf Bewerter Szenario',
        'Demo Fake/Echt Szenario',
        'Demo Labeling Szenario',
        'LLM-as-Judge Demo',
        'SummEval Demo - Summarization',
    ]

    # Ensure demo scenarios exist
    try:
        seed_demo_scenarios(_db)
        print("  Demo scenarios seeded (or already existed)")
    except Exception as e:
        print(f"  WARNING: Demo scenario seeding failed: {e}")

    # Add user to all demo scenarios
    for scenario_name in DEMO_SCENARIO_NAMES:
        scenario = RatingScenarios.query.filter_by(scenario_name=scenario_name).first()
        if not scenario:
            print(f"  Scenario '{scenario_name}' not found, skipping")
            continue

        existing = ScenarioUsers.query.filter_by(
            scenario_id=scenario.id, user_id=user.id
        ).first()
        if existing:
            print(f"  Already member of '{scenario_name}'")
            continue

        su = ScenarioUsers(
            scenario_id=scenario.id,
            user_id=user.id,
            role=ScenarioRoles.EVALUATOR,
        )
        _db.session.add(su)
        _db.session.flush()

        scenario_items = ScenarioItems.query.filter_by(scenario_id=scenario.id).all()
        for si in scenario_items:
            _db.session.add(ScenarioItemDistribution(
                scenario_id=scenario.id,
                scenario_user_id=su.id,
                scenario_item_id=si.id,
            ))

        print(f"  Added to '{scenario_name}' ({len(scenario_items)} items)")

    _db.session.commit()
    print(f"\nDone! User '{TARGET_USER}' now has prompts, batch job, and access to 6 demo scenarios.")
