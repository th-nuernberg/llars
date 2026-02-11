#!/usr/bin/env python3
"""
Demo Video Data Manager for IJCAI 2026

Manages pre-seed data and cleanup for demo video recording.
All demo data is owned by DEMO_USER (ijcai_reviewer_1).

Usage (inside Flask container):
    python3 /app/scripts/demo_video_manage.py seed
    python3 /app/scripts/demo_video_manage.py cleanup
    python3 /app/scripts/demo_video_manage.py reset
    python3 /app/scripts/demo_video_manage.py status
"""

import sys
import os

sys.path.insert(0, '/app')
os.chdir('/app')

import argparse
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('demo_video_manage')

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PRESEED_PROMPT_NAME = "News Summary Prompt"
PRESEED_JOB_NAME = "News Summary Demo Job"
LIVE_PROMPT_NAME = "News Summary Eval"
LIVE_JOB_NAME = "Live Collab Batch Job"

# Demo user: main actor in the video
DEMO_USER = "ijcai_reviewer_1"
# Collab partner: opens prompts as second browser
COLLAB_USER = "ijcai_reviewer_2"


# ===================================================================
# STATUS
# ===================================================================

def cmd_status():
    """Show current state of demo data."""
    from main import app
    from db.tables import User, UserPrompt
    from db.models.generation import GenerationJob, GeneratedOutput
    from db.models.scenario import RatingScenarios, UserPromptShare

    with app.app_context():
        demo_user = User.query.filter_by(username=DEMO_USER).first()
        if not demo_user:
            logger.error(f"User '{DEMO_USER}' not found!")
            return

        print("\n" + "=" * 60)
        print(f"DEMO VIDEO DATA STATUS (user: {DEMO_USER})")
        print("=" * 60)

        # Prompts
        print(f"\n--- Prompts ({DEMO_USER}) ---")
        for name in [PRESEED_PROMPT_NAME, LIVE_PROMPT_NAME]:
            p = UserPrompt.query.filter_by(user_id=demo_user.id, name=name).first()
            if p:
                shares = UserPromptShare.query.filter_by(prompt_id=p.prompt_id).all()
                share_names = [s.shared_with_user.username for s in shares if s.shared_with_user]
                print(f"  [EXISTS] {name} (id={p.prompt_id}, shared_with={share_names})")
            else:
                print(f"  [MISSING] {name}")

        # Also check admin-owned prompts (from dev seeder)
        admin = User.query.filter_by(username='admin').first()
        if admin:
            for name in [PRESEED_PROMPT_NAME, LIVE_PROMPT_NAME]:
                p = UserPrompt.query.filter_by(user_id=admin.id, name=name).first()
                if p:
                    print(f"  [INFO] {name} also exists for admin (id={p.prompt_id})")

        # Generation Jobs
        print(f"\n--- Generation Jobs ({DEMO_USER}) ---")
        for name in [PRESEED_JOB_NAME, LIVE_JOB_NAME]:
            j = GenerationJob.query.filter_by(name=name, created_by=DEMO_USER).first()
            if j:
                output_count = GeneratedOutput.query.filter_by(job_id=j.id).count()
                print(f"  [EXISTS] {name} (id={j.id}, status={j.status.value}, "
                      f"created_by={j.created_by}, outputs={output_count})")
            else:
                print(f"  [MISSING] {name}")
            # Also show admin-owned jobs for info
            admin_j = GenerationJob.query.filter_by(name=name, created_by='admin').first()
            if admin_j:
                print(f"  [INFO] {name} also exists for admin (id={admin_j.id})")

        # Scenarios
        print("\n--- Scenarios containing 'News Summary' ---")
        scenarios = RatingScenarios.query.filter(
            RatingScenarios.scenario_name.contains("News Summary")
        ).all()
        if scenarios:
            for s in scenarios:
                print(f"  [EXISTS] {s.scenario_name} (id={s.id}, created_by={s.created_by})")
        else:
            print("  (none)")

        print("\n" + "=" * 60)


# ===================================================================
# SEED
# ===================================================================

def cmd_seed():
    """Seed pre-recording data owned by DEMO_USER."""
    from main import app
    from db import db as _db
    from db.tables import User, UserPrompt
    from db.models.generation import (
        GenerationJob, GeneratedOutput,
        GenerationJobStatus, GeneratedOutputStatus,
    )
    from db.models.llm_model import LLMModel
    from db.models.scenario import UserPromptShare
    from db.seeders.demo_video_data import NEWS_ARTICLES, SAMPLE_SUMMARIES

    with app.app_context():
        demo_user = User.query.filter_by(username=DEMO_USER).first()
        if not demo_user:
            logger.error(f"User '{DEMO_USER}' not found!")
            return False

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
            logger.info(f"Created prompt '{PRESEED_PROMPT_NAME}' (id={preseed.prompt_id})")
        else:
            logger.info(f"Prompt '{PRESEED_PROMPT_NAME}' already exists (id={preseed.prompt_id})")

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
                logger.info(f"Shared '{PRESEED_PROMPT_NAME}' with {COLLAB_USER}")

        _db.session.commit()

        # --- 2. Create completed generation job ---
        existing_job = GenerationJob.query.filter_by(
            name=PRESEED_JOB_NAME, created_by=DEMO_USER
        ).first()
        if existing_job:
            logger.info(f"Job '{PRESEED_JOB_NAME}' already exists (id={existing_job.id})")
        else:
            # Need models
            mistral = LLMModel.query.filter_by(
                model_id='mistralai/Mistral-Small-3.2-24B-Instruct-2506'
            ).first()
            magistral = LLMModel.query.filter_by(
                model_id='mistralai/Magistral-Small-2509'
            ).first()

            if not mistral or not magistral:
                logger.warning("Required LLM models not found, skipping job seeding")
                print("\n[SEED COMPLETE] (without generation job)")
                return True

            # Temporarily create eval prompt for rendering
            eval_content = _build_eval_prompt_content()
            temp_eval = UserPrompt(
                user_id=demo_user.id,
                name="_temp_eval_prompt",
                content=eval_content
            )
            _db.session.add(temp_eval)
            _db.session.flush()

            now = datetime.utcnow()
            total_outputs = len(NEWS_ARTICLES) * 2 * 2  # 10 x 2 prompts x 2 models

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

            # Create outputs
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

            # Remove temp prompt
            _db.session.delete(temp_eval)
            _db.session.commit()
            logger.info(f"Created job '{PRESEED_JOB_NAME}' (id={job.id}) with {total_outputs} outputs")

        print("\n[SEED COMPLETE]")
        return True


# ===================================================================
# CLEANUP
# ===================================================================

def cmd_cleanup():
    """Delete data created during live recording (for re-recording)."""
    from main import app
    from db import db as _db
    from db.tables import User, UserPrompt
    from db.models.generation import GenerationJob, GeneratedOutput
    from db.models.scenario import RatingScenarios, UserPromptShare

    with app.app_context():
        deleted = []

        # --- 1. Delete live prompt "News Summary Eval" (any owner) ---
        live_prompts = UserPrompt.query.filter_by(name=LIVE_PROMPT_NAME).all()
        for lp in live_prompts:
            shares_deleted = UserPromptShare.query.filter_by(
                prompt_id=lp.prompt_id
            ).delete()
            _db.session.delete(lp)
            deleted.append(f"Prompt '{LIVE_PROMPT_NAME}' owner_id={lp.user_id} (+ {shares_deleted} shares)")

        # --- 2. Delete live job "Live Collab Batch Job" ---
        live_job = GenerationJob.query.filter_by(name=LIVE_JOB_NAME).first()
        if live_job:
            outputs_deleted = GeneratedOutput.query.filter_by(job_id=live_job.id).delete()
            _db.session.delete(live_job)
            deleted.append(f"Job '{LIVE_JOB_NAME}' (+ {outputs_deleted} outputs)")

        # --- 3. Delete demo-created scenarios ---
        preseed_job = GenerationJob.query.filter_by(name=PRESEED_JOB_NAME).first()
        preseed_target_id = preseed_job.target_scenario_id if preseed_job else None

        demo_scenarios = RatingScenarios.query.filter(
            RatingScenarios.scenario_name.contains("News Summary")
        ).all()

        for scenario in demo_scenarios:
            if preseed_target_id and scenario.id == preseed_target_id:
                continue
            _db.session.delete(scenario)
            deleted.append(f"Scenario '{scenario.scenario_name}' (id={scenario.id})")

        _db.session.commit()

        if deleted:
            print("\n[CLEANUP] Deleted:")
            for item in deleted:
                print(f"  - {item}")
        else:
            print("\n[CLEANUP] Nothing to clean up.")

        return True


# ===================================================================
# RESET
# ===================================================================

def cmd_reset():
    """Full reset: cleanup + seed."""
    print("\n--- Phase 1: Cleanup ---")
    cmd_cleanup()
    print("\n--- Phase 2: Seed ---")
    cmd_seed()
    print("\n[RESET COMPLETE]")


# ===================================================================
# HELPERS
# ===================================================================

def _build_preseed_prompt_content():
    return {
        "blocks": {
            "Role Definition": {
                "content": "Role definition: You are a professional news editor. Write concise, factual summaries.",
                "position": 0
            },
            "Task Explanation": {
                "content": "Task explanation: Summarize the article in exactly 2 sentences. Preserve key facts, avoid speculation, and do not add new information.",
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
                    "Exactly 2 sentences in plain text. No bullet points. No extra commentary."
                ),
                "position": 2
            }
        }
    }


def _build_eval_prompt_content():
    return {
        "blocks": {
            "Role Definition": {
                "content": "Role definition: You are a senior journalist drafting a short news digest.",
                "position": 0
            },
            "Task Explanation": {
                "content": "Task explanation: Summarize the article in 3-4 sentences. Highlight key facts and implications while staying neutral and factual.",
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
                    "3-4 sentences in plain text. No bullet points. No extra commentary."
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


# ===================================================================
# MAIN
# ===================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Demo Video Data Manager for IJCAI 2026",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  seed      Create pre-seed data (prompt + completed batch job)
  cleanup   Delete live-recorded data (for re-recording)
  reset     Full reset (cleanup + seed)
  status    Show current state of demo data
        """
    )
    parser.add_argument(
        'command',
        choices=['seed', 'cleanup', 'reset', 'status'],
        help='Action to perform'
    )
    args = parser.parse_args()

    commands = {
        'seed': cmd_seed,
        'cleanup': cmd_cleanup,
        'reset': cmd_reset,
        'status': cmd_status,
    }
    commands[args.command]()


if __name__ == '__main__':
    main()
