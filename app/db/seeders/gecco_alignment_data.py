"""
GECCO Alignment Human Evaluation Seeder (v3)

Imports the 124-item A/B comparison dataset from the LLM steering study
(Qwen/Mistral/Gemma, activation steering, axes: cooperation/hopefulness/initiative/openness)
into LLARS as a pairwise comparison scenario.

Item layout per row:
  - EvaluationItem.messages  = parsed dialogue context (Berater/Klient turns)
  - Feature[0] (Option A)    = response_a  (blinded; base_is_response_a in metadata_json)
  - Feature[1] (Option B)    = response_b  (blinded)
  - metadata_json            = {axis, target_pole, target_style, model_path, stratum,
                                 base_is_response_a, seed_id, variant, alpha, layer,
                                 persona_name, hauptanliegen, item_id}

Scenario question template uses {{variable}} substitution rendered per-item:
  e.g. "Beratungsfall {{persona_name}} — Achse: {{axis}} ({{target_pole}}). ..."

Chat IDs start at 32000 to avoid collisions with other seeders.

Idempotent: re-running skips existing items (identified by chat_id + function_type_id).
"""

import json
import os
import re
from datetime import datetime, timedelta

# Path to the source JSON relative to this file — override with GECCO_DATA_PATH env var.
_DEFAULT_DATA_PATH = os.path.join(
    os.path.dirname(__file__),
    '../../../../..',  # project root
    'Development/02_Research_Projects/geccoalignment/llm_ft_comparison'
    '/outputs/human_eval/v3/human_eval_sample.json'
)

CHAT_ID_BASE = 32000
SCENARIO_NAME = 'GECCO Alignment — Human Evaluation v3'

# Config question template; researchers can override via Scenario Wizard after seeding.
QUESTION_TEMPLATE = (
    'Beratungsfall {{persona_name}} — Achse: {{axis}} ({{target_pole}}). '
    'Welche der beiden Antworten passt besser als nächste Berateräußerung?'
)


def _parse_context(context_str: str) -> list[tuple[str, str]]:
    """Split flat 'Role: text\\nRole: text' dialogue into (sender, content) tuples."""
    messages = []
    for line in context_str.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Split on first ': ' to separate role from content
        match = re.match(r'^(Berater|Klient):\s*(.*)', line, re.DOTALL)
        if match:
            messages.append((match.group(1), match.group(2).strip()))
        elif messages:
            # Continuation line without role prefix — append to last message
            last_sender, last_content = messages[-1]
            messages[-1] = (last_sender, last_content + ' ' + line)
    return messages


def seed_gecco_alignment_scenario(db, data_path: str | None = None):
    """
    Create (or update) the GECCO Alignment human evaluation scenario.

    Args:
        db:        SQLAlchemy database instance
        data_path: Path to human_eval_sample.json; defaults to the relative
                   path from the research project directory.
    """
    from db.models import (
        User, EvaluationItem, Message, Feature, FeatureType,
        RatingScenarios, ScenarioUsers, ScenarioItems,
        FeatureFunctionType
    )

    print('\n' + '=' * 60)
    print('Seeding GECCO Alignment Human Evaluation Scenario...')
    print('=' * 60)

    # Resolve data path
    path = data_path or os.environ.get('GECCO_DATA_PATH', _DEFAULT_DATA_PATH)
    if not os.path.exists(path):
        print(f'  SKIP: data file not found at {path}')
        print('  Set GECCO_DATA_PATH env var or call seed_gecco_alignment_scenario(db, path=...)')
        return None

    with open(path, encoding='utf-8') as f:
        raw_items = json.load(f)
    print(f'  Loaded {len(raw_items)} items from {os.path.basename(path)}')

    # Require researcher + admin users (standard LLARS demo users)
    researcher = User.query.filter_by(username='researcher').first()
    admin = User.query.filter_by(username='admin').first()
    if not researcher or not admin:
        print('  ERROR: Required users (researcher/admin) not found — run base seeders first')
        return None

    comparison_type = FeatureFunctionType.query.filter_by(name='comparison').first()
    if not comparison_type:
        print('  ERROR: Comparison function type not found')
        return None

    feature_type = FeatureType.query.filter_by(name='Summary').first()
    if not feature_type:
        feature_type = FeatureType(name='Summary')
        db.session.add(feature_type)
        db.session.flush()

    # ------------------------------------------------------------------ scenario
    scenario = RatingScenarios.query.filter_by(scenario_name=SCENARIO_NAME).first()
    config_json = {
        'question': {'de': QUESTION_TEMPLATE, 'en': QUESTION_TEMPLATE},
        'allow_tie': True,
        'show_source': False,
        'gamification_enabled': False,
        'eval_config': {
            'type': 'comparison',
            'config': {
                'question': {'de': QUESTION_TEMPLATE, 'en': QUESTION_TEMPLATE},
                'allowTie': True,
                'showSource': False,
            }
        }
    }

    if not scenario:
        scenario = RatingScenarios(
            scenario_name=SCENARIO_NAME,
            description=(
                'Paarweise A/B-Bewertung gesteuerter vs. ungesteuerter LLM-Antworten. '
                'Vier Achsen: cooperation, hopefulness, initiative, openness. '
                'n=124, 4 Modelle (Qwen3.5-9B, Qwen3-4B, Mistral-7B, Gemma-4B).'
            ),
            function_type_id=comparison_type.function_type_id,
            created_by=researcher.username,
            config_json=config_json,
        )
        db.session.add(scenario)
        db.session.flush()
        print(f'  Created scenario id={scenario.id}')
    else:
        scenario.config_json = config_json
        print(f'  Updated scenario id={scenario.id}')
    db.session.flush()

    # ------------------------------------------------------------------ users
    def _ensure_scenario_user(user, is_owner=False):
        su = ScenarioUsers.query.filter_by(
            scenario_id=scenario.id, user_id=user.id
        ).first()
        if not su:
            su = ScenarioUsers(
                scenario_id=scenario.id,
                user_id=user.id,
                manager_role='owner' if is_owner else 'none',
                evaluation_role='assessor',
            )
            db.session.add(su)

    _ensure_scenario_user(researcher, is_owner=True)
    _ensure_scenario_user(admin, is_owner=True)
    db.session.flush()

    # ------------------------------------------------------------------ items
    created = 0
    skipped = 0
    base_time = datetime.now() - timedelta(days=30)

    for idx, row in enumerate(raw_items):
        chat_id = CHAT_ID_BASE + idx

        item = EvaluationItem.query.filter_by(
            chat_id=chat_id,
            institut_id=1,
            function_type_id=comparison_type.function_type_id,
        ).first()

        if not item:
            item = EvaluationItem(
                chat_id=chat_id,
                institut_id=1,
                subject=f'Item {row["item_no"]} — {row["axis"]}/{row["target_pole"]}',
                sender='Klient',
                function_type_id=comparison_type.function_type_id,
                metadata_json={
                    'axis': row['axis'],
                    'target_pole': row['target_pole'],
                    'target_style': row['target_style'],
                    'model_path': row['model_path'],
                    'stratum': row['stratum'],
                    'base_is_response_a': row['base_is_response_a'],
                    'seed_id': row['seed_id'],
                    'variant': row['variant'],
                    'alpha': row['alpha'],
                    'layer': row['layer'],
                    'persona_name': row['persona_name'],
                    'hauptanliegen': row['hauptanliegen'],
                    'item_id': row['item_id'],
                    'item_no': row['item_no'],
                },
            )
            db.session.add(item)
            db.session.flush()

            # Dialogue context as messages
            parsed_messages = _parse_context(row['context'])
            for msg_idx, (sender, content) in enumerate(parsed_messages):
                db.session.add(Message(
                    item_id=item.item_id,
                    sender=sender,
                    content=content,
                    timestamp=base_time + timedelta(hours=idx * 2 + msg_idx),
                ))

            # Option A and Option B (blinded — base_is_response_a is in metadata_json)
            db.session.add(Feature(
                item_id=item.item_id,
                type_id=feature_type.type_id,
                model_id='response_a',
                content=row['response_a'],
            ))
            db.session.add(Feature(
                item_id=item.item_id,
                type_id=feature_type.type_id,
                model_id='response_b',
                content=row['response_b'],
            ))

            db.session.flush()
            created += 1
        else:
            skipped += 1

        # Link item to scenario (idempotent)
        si = ScenarioItems.query.filter_by(
            scenario_id=scenario.id, thread_id=item.item_id
        ).first()
        if not si:
            si = ScenarioItems(scenario_id=scenario.id, thread_id=item.item_id)
            db.session.add(si)

    db.session.commit()
    print(f'  Items: {created} created, {skipped} skipped (already exist)')
    print(f'  Scenario URL: /scenarios/{scenario.id}')
    print('=' * 60)
    return scenario
