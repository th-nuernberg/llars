"""
Generation Debug Routes.

Debug and test endpoints for batch generation workflows.
These routes help verify data formats and test the full pipeline:
  Batch Generation → Scenario Creation → LLM Evaluation

Usage:
    1. GET /api/generation/debug/inspect-job/<job_id> - Inspect job data
    2. GET /api/generation/debug/inspect-scenario/<scenario_id> - Inspect scenario data
    3. POST /api/generation/debug/test-scenario-creation - Create test scenario
    4. POST /api/generation/debug/add-llm-evaluators - Add LLM evaluators
    5. GET /api/generation/debug/verify-messages/<scenario_id> - Verify message format
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from flask import Blueprint, g, jsonify, request

from auth.decorators import api_key_or_token_required
from db import db
from db.models import (
    EvaluationItem,
    FeatureFunctionType,
    GeneratedOutput,
    GeneratedOutputStatus,
    GenerationJob,
    GenerationJobStatus,
    Message,
    RatingScenarios,
    ScenarioItems,
    ScenarioRoles,
    ScenarioUsers,
    User,
)
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError

logger = logging.getLogger(__name__)

generation_debug_bp = Blueprint(
    'generation_debug',
    __name__,
    url_prefix='/api/generation/debug'
)


# =============================================================================
# INSPECTION ENDPOINTS
# =============================================================================


@generation_debug_bp.route('/inspect-job/<int:job_id>', methods=['GET'])
@api_key_or_token_required
@handle_api_errors(logger_name='generation_debug')
def inspect_job(job_id: int):
    """
    Inspect a generation job with full details.

    Shows:
    - Job config with source items
    - All outputs with their source data
    - Prompt variables that were used
    """
    job = GenerationJob.query.get(job_id)
    if not job:
        raise NotFoundError(f"Job {job_id} not found")

    config = job.config_json or {}

    # Get outputs with details
    outputs = GeneratedOutput.query.filter_by(job_id=job_id).limit(10).all()
    outputs_data = []
    for o in outputs:
        outputs_data.append({
            "id": o.id,
            "source_item_id": o.source_item_id,
            "llm_model_name": o.llm_model_name,
            "prompt_variant_name": o.prompt_variant_name,
            "status": o.status.value if o.status else None,
            "prompt_variables_json": o.prompt_variables_json,
            "content_preview": (o.generated_content or "")[:200],
            "has_messages_in_variables": bool(
                o.prompt_variables_json and
                o.prompt_variables_json.get("messages")
            ),
        })

    return jsonify({
        "success": True,
        "job": {
            "id": job.id,
            "name": job.name,
            "status": job.status.value if job.status else None,
            "total_items": job.total_items,
            "completed_items": job.completed_items,
            "target_scenario_id": job.target_scenario_id,
        },
        "config": {
            "sources_type": config.get("sources", {}).get("type"),
            "sources_items_count": len(config.get("sources", {}).get("items", [])),
            "prompts_count": len(config.get("prompts", [])),
            "llm_models": config.get("llm_models", []),
        },
        "source_items_sample": config.get("sources", {}).get("items", [])[:2],
        "outputs_sample": outputs_data,
    })


@generation_debug_bp.route('/inspect-scenario/<int:scenario_id>', methods=['GET'])
@api_key_or_token_required
@handle_api_errors(logger_name='generation_debug')
def inspect_scenario(scenario_id: int):
    """
    Inspect a scenario with full message details.

    Shows:
    - Scenario config
    - Items with their messages
    - Message sender roles (critical for mail_rating!)
    """
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")

    # Get items
    scenario_items = ScenarioItems.query.filter_by(scenario_id=scenario_id).all()
    item_ids = [si.item_id for si in scenario_items]

    items_data = []
    for item_id in item_ids[:5]:  # Sample first 5
        item = EvaluationItem.query.get(item_id)
        if not item:
            continue

        messages = Message.query.filter_by(item_id=item_id).order_by(Message.timestamp).all()

        items_data.append({
            "item_id": item.item_id,
            "subject": item.subject,
            "sender": item.sender,
            "function_type_id": item.function_type_id,
            "messages": [
                {
                    "message_id": m.message_id,
                    "sender": m.sender,
                    "content_preview": (m.content or "")[:150],
                    "generated_by": m.generated_by,
                    "is_json_blob": m.content and m.content.startswith("[{"),
                }
                for m in messages
            ],
            "message_senders": [m.sender for m in messages],
            "has_correct_roles": any(
                m.sender in ["Ratsuchende", "Beratende", "Client", "Counselor"]
                for m in messages
            ),
        })

    # Analyze issues
    issues = []
    for item_data in items_data:
        senders = item_data["message_senders"]
        if "Content" in senders:
            issues.append(f"Item {item_data['item_id']}: sender='Content' (should be role name)")
        if "Messages" in senders:
            issues.append(f"Item {item_data['item_id']}: sender='Messages' (JSON blob issue)")
        if any(d.get("is_json_blob") for d in item_data["messages"]):
            issues.append(f"Item {item_data['item_id']}: message content is JSON blob")

    return jsonify({
        "success": True,
        "scenario": {
            "id": scenario.id,
            "name": scenario.scenario_name,
            "function_type_id": scenario.function_type_id,
            "config_json": scenario.config_json,
        },
        "items_count": len(item_ids),
        "items_sample": items_data,
        "issues": issues,
        "is_healthy": len(issues) == 0,
    })


@generation_debug_bp.route('/verify-messages/<int:scenario_id>', methods=['GET'])
@api_key_or_token_required
@handle_api_errors(logger_name='generation_debug')
def verify_messages(scenario_id: int):
    """
    Verify all messages in a scenario have correct format.

    Returns detailed analysis of message formats for debugging.
    """
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")

    # Get all items
    scenario_items = ScenarioItems.query.filter_by(scenario_id=scenario_id).all()
    item_ids = [si.item_id for si in scenario_items]

    analysis = {
        "total_items": len(item_ids),
        "total_messages": 0,
        "sender_distribution": {},
        "generated_by_distribution": {},
        "issues": [],
        "sample_messages": [],
    }

    for item_id in item_ids:
        messages = Message.query.filter_by(item_id=item_id).all()
        analysis["total_messages"] += len(messages)

        for msg in messages:
            # Count sender distribution
            sender = msg.sender or "NULL"
            analysis["sender_distribution"][sender] = \
                analysis["sender_distribution"].get(sender, 0) + 1

            # Count generated_by distribution
            gen_by = msg.generated_by or "NULL"
            analysis["generated_by_distribution"][gen_by] = \
                analysis["generated_by_distribution"].get(gen_by, 0) + 1

            # Check for issues
            if msg.sender == "Content":
                analysis["issues"].append({
                    "item_id": item_id,
                    "message_id": msg.message_id,
                    "issue": "sender='Content' should be role name",
                })
            if msg.sender == "Messages":
                analysis["issues"].append({
                    "item_id": item_id,
                    "message_id": msg.message_id,
                    "issue": "sender='Messages' - JSON blob stored incorrectly",
                })
            if msg.content and msg.content.startswith("[{"):
                analysis["issues"].append({
                    "item_id": item_id,
                    "message_id": msg.message_id,
                    "issue": "content is JSON blob, not plain text",
                })

    # Add sample messages
    sample_items = item_ids[:3]
    for item_id in sample_items:
        messages = Message.query.filter_by(item_id=item_id).limit(3).all()
        for msg in messages:
            analysis["sample_messages"].append({
                "item_id": item_id,
                "sender": msg.sender,
                "content_preview": (msg.content or "")[:100],
                "generated_by": msg.generated_by,
            })

    return jsonify({
        "success": True,
        "scenario_id": scenario_id,
        "function_type_id": scenario.function_type_id,
        "analysis": analysis,
        "is_healthy": len(analysis["issues"]) == 0,
    })


# =============================================================================
# TEST SCENARIO CREATION
# =============================================================================


@generation_debug_bp.route('/test-scenario-creation', methods=['POST'])
@api_key_or_token_required
@handle_api_errors(logger_name='generation_debug')
def test_scenario_creation():
    """
    Test creating a scenario from a job with the FIXED format.

    Request body:
    {
        "job_id": 1,
        "scenario_name": "Test Scenario",
        "evaluation_type": "mail_rating",
        "dry_run": true  // If true, don't commit - just show what would be created
    }
    """
    data = request.get_json() or {}

    job_id = data.get("job_id")
    if not job_id:
        raise ValidationError("job_id is required")

    job = GenerationJob.query.get(job_id)
    if not job:
        raise NotFoundError(f"Job {job_id} not found")

    scenario_name = data.get("scenario_name", f"Test from Job {job_id}")
    evaluation_type = data.get("evaluation_type", "mail_rating")
    dry_run = data.get("dry_run", True)

    # Get user
    user = g.authentik_user
    username = user.username if hasattr(user, 'username') else str(user)

    # Get completed outputs
    outputs = GeneratedOutput.query.filter_by(
        job_id=job_id,
        status=GeneratedOutputStatus.COMPLETED
    ).all()

    if not outputs:
        raise ValidationError(f"Job {job_id} has no completed outputs")

    # Get source items from job config
    config = job.config_json or {}
    source_items = {
        item.get('id'): item
        for item in config.get('sources', {}).get('items', [])
    }

    # Preview what would be created
    response_role = data.get("response_role")  # Optional explicit response role
    preview_items = []
    for output in outputs[:5]:
        # Get source data from variables or config
        variables = output.prompt_variables_json or {}
        messages_data = variables.get("messages", [])
        subject = variables.get("subject", "")

        # If no messages in variables, try to get from source_items
        source_idx = variables.get("_source_index")
        if not messages_data and source_idx is not None:
            source_item = list(source_items.values())[source_idx] if source_idx < len(source_items) else {}
            messages_data = source_item.get("messages", [])
            subject = source_item.get("subject", subject)

        # Determine response role using generalized logic
        if response_role:
            gen_role = response_role
        elif messages_data:
            # Collect roles and determine response role
            roles = set(m.get("role") or m.get("sender") for m in messages_data)
            last_role = messages_data[-1].get("role") or messages_data[-1].get("sender") if messages_data else None
            if len(roles) == 2 and last_role:
                gen_role = (roles - {last_role}).pop() if roles - {last_role} else "Response"
            else:
                gen_role = "Response"
        else:
            gen_role = "Generated"

        preview_items.append({
            "output_id": output.id,
            "llm_model": output.llm_model_name,
            "subject": subject,
            "original_messages_count": len(messages_data),
            "original_messages": [
                {"role": m.get("role") or m.get("sender"), "content_preview": m.get("content", "")[:50]}
                for m in messages_data[:3]
            ],
            "generated_response_preview": (output.generated_content or "")[:150],
            "would_create_messages": [
                *[{"sender": m.get("role") or m.get("sender"), "generated_by": m.get("generated_by", "Human")} for m in messages_data],
                {"sender": gen_role, "generated_by": output.llm_model_name}
            ],
        })

    result = {
        "success": True,
        "dry_run": dry_run,
        "job_id": job_id,
        "scenario_name": scenario_name,
        "evaluation_type": evaluation_type,
        "outputs_count": len(outputs),
        "preview_items": preview_items,
        "source_items_in_config": len(source_items),
    }

    if not dry_run:
        # Actually create the scenario using the fixed method
        from services.generation import OutputExportService

        scenario = OutputExportService.create_evaluation_scenario_fixed(
            job_id=job_id,
            scenario_name=scenario_name,
            evaluation_type=evaluation_type,
            created_by=username,
            response_role=response_role,  # Pass explicit response role if provided
        )

        result["created_scenario_id"] = scenario.id
        result["message"] = f"Created scenario {scenario.id}"

    return jsonify(result)


# =============================================================================
# LLM EVALUATOR MANAGEMENT
# =============================================================================


@generation_debug_bp.route('/add-llm-evaluators', methods=['POST'])
@api_key_or_token_required
@handle_api_errors(logger_name='generation_debug')
def add_llm_evaluators():
    """
    Add LLM evaluators to a scenario and trigger evaluation.

    Request body:
    {
        "scenario_id": 7,
        "llm_evaluators": ["mistralai/Mistral-Small-3.2-24B-Instruct-2506"],
        "run_evaluation": true
    }
    """
    data = request.get_json() or {}

    scenario_id = data.get("scenario_id")
    if not scenario_id:
        raise ValidationError("scenario_id is required")

    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")

    llm_evaluators = data.get("llm_evaluators", [])
    run_evaluation = data.get("run_evaluation", False)

    # Update config - need to flag as modified for SQLAlchemy to detect change
    from sqlalchemy.orm.attributes import flag_modified
    config = scenario.config_json or {}
    config["llm_evaluators"] = llm_evaluators
    config["enable_llm_evaluation"] = bool(llm_evaluators)
    scenario.config_json = config
    flag_modified(scenario, "config_json")

    db.session.commit()

    result = {
        "success": True,
        "scenario_id": scenario_id,
        "llm_evaluators": llm_evaluators,
        "config_updated": True,
    }

    if run_evaluation and llm_evaluators:
        try:
            from services.llm.llm_ai_task_runner import LLMAITaskRunner
            LLMAITaskRunner.run_for_scenario_async(scenario_id, model_ids=llm_evaluators)
            result["evaluation_triggered"] = True
        except Exception as e:
            result["evaluation_error"] = str(e)

    return jsonify(result)


@generation_debug_bp.route('/llm-evaluation-status/<int:scenario_id>', methods=['GET'])
@api_key_or_token_required
@handle_api_errors(logger_name='generation_debug')
def llm_evaluation_status(scenario_id: int):
    """
    Check LLM evaluation status for a scenario.
    """
    from db.models import LLMTaskResult, ItemDimensionRating

    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")

    config = scenario.config_json or {}
    llm_evaluators = config.get("llm_evaluators", [])

    # Get items
    scenario_items = ScenarioItems.query.filter_by(scenario_id=scenario_id).all()
    item_ids = [si.item_id for si in scenario_items]

    # Check ratings from LLMs
    llm_ratings = ItemDimensionRating.query.filter(
        ItemDimensionRating.scenario_id == scenario_id,
        ItemDimensionRating.evaluated_by_model.isnot(None)
    ).all()

    # Group by model
    ratings_by_model = {}
    for rating in llm_ratings:
        model = rating.evaluated_by_model or "unknown"
        if model not in ratings_by_model:
            ratings_by_model[model] = []
        ratings_by_model[model].append({
            "item_id": rating.item_id,
            "dimensions": rating.dimension_ratings,
        })

    return jsonify({
        "success": True,
        "scenario_id": scenario_id,
        "configured_evaluators": llm_evaluators,
        "total_items": len(item_ids),
        "ratings_by_model": {
            model: {
                "count": len(ratings),
                "sample": ratings[:2]
            }
            for model, ratings in ratings_by_model.items()
        },
        "total_llm_ratings": len(llm_ratings),
    })


# =============================================================================
# DATA FIX ENDPOINTS
# =============================================================================


@generation_debug_bp.route('/fix-scenario-messages/<int:scenario_id>', methods=['POST'])
@api_key_or_token_required
@handle_api_errors(logger_name='generation_debug')
def fix_scenario_messages(scenario_id: int):
    """
    Fix incorrectly formatted messages in a scenario.

    Fixes:
    - sender="Content" → "Beratende"
    - sender="Messages" → Parse JSON and create proper messages

    Request body:
    {
        "dry_run": true  // If true, don't commit
    }
    """
    import json

    data = request.get_json() or {}
    dry_run = data.get("dry_run", True)

    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f"Scenario {scenario_id} not found")

    # Get all items
    scenario_items = ScenarioItems.query.filter_by(scenario_id=scenario_id).all()
    item_ids = [si.item_id for si in scenario_items]

    fixes_applied = []
    errors = []

    for item_id in item_ids:
        messages = Message.query.filter_by(item_id=item_id).all()

        for msg in messages:
            # Fix sender="Content" → "Beratende"
            if msg.sender == "Content":
                fixes_applied.append({
                    "item_id": item_id,
                    "message_id": msg.message_id,
                    "fix": "sender Content → Beratende",
                })
                if not dry_run:
                    msg.sender = "Beratende"

            # Fix sender="Messages" → Parse JSON
            elif msg.sender == "Messages" and msg.content:
                try:
                    if msg.content.startswith("["):
                        messages_data = json.loads(msg.content)

                        # Delete the JSON blob message
                        fixes_applied.append({
                            "item_id": item_id,
                            "message_id": msg.message_id,
                            "fix": f"Parse JSON blob into {len(messages_data)} messages",
                        })

                        if not dry_run:
                            # Create proper messages from JSON
                            for idx, msg_data in enumerate(messages_data):
                                role = msg_data.get("role", "Ratsuchende")
                                content = msg_data.get("content", "")
                                timestamp_str = msg_data.get("timestamp")

                                # Parse timestamp if present
                                timestamp = None
                                if timestamp_str:
                                    try:
                                        timestamp = datetime.strptime(
                                            timestamp_str, "%d.%m.%Y %H:%M"
                                        )
                                    except ValueError:
                                        timestamp = datetime.utcnow()

                                new_msg = Message(
                                    item_id=item_id,
                                    sender=role,
                                    content=content,
                                    timestamp=timestamp or datetime.utcnow(),
                                    generated_by="Human",
                                )
                                db.session.add(new_msg)

                            # Delete the original JSON blob message
                            db.session.delete(msg)

                except json.JSONDecodeError as e:
                    errors.append({
                        "item_id": item_id,
                        "message_id": msg.message_id,
                        "error": f"JSON parse error: {e}",
                    })

    if not dry_run:
        db.session.commit()

    return jsonify({
        "success": True,
        "scenario_id": scenario_id,
        "dry_run": dry_run,
        "fixes_applied": fixes_applied,
        "fixes_count": len(fixes_applied),
        "errors": errors,
    })


# =============================================================================
# BATCH GENERATION TEST ENDPOINTS
# =============================================================================


@generation_debug_bp.route('/start-test-job', methods=['POST'])
@api_key_or_token_required
@handle_api_errors(logger_name='generation_debug')
def start_test_job():
    """
    Start a test batch generation job.

    Request body:
    {
        "name": "Test Job",
        "prompt_template": "Summarize: {{content}}",
        "llm_models": ["mistralai/Mistral-Small-3.2-24B-Instruct-2506"],
        "items": [
            {"content": "Text to summarize 1"},
            {"content": "Text to summarize 2"}
        ]
    }

    Or use a preset:
    {
        "preset": "mail_rating_demo"
    }
    """
    from services.generation import BatchGenerationService
    from db.models import UserPrompt

    data = request.get_json() or {}
    user = g.authentik_user
    username = user.username if hasattr(user, 'username') else str(user)
    user_id = user.id if hasattr(user, 'id') else 1

    # Helper to create or get a test prompt
    def get_or_create_prompt(name: str, content: str) -> int:
        """Create a UserPrompt for testing if it doesn't exist."""
        existing = UserPrompt.query.filter_by(name=name, user_id=user_id).first()
        if existing:
            return existing.prompt_id

        prompt = UserPrompt(
            user_id=user_id,
            name=name,
            content=content,
        )
        db.session.add(prompt)
        db.session.flush()
        return prompt.prompt_id

    # Check for preset
    preset = data.get("preset")
    if preset == "mail_rating_demo":
        # Create demo mail rating prompt
        template_content = """Du bist ein empathischer Berater. Schreibe eine Antwort auf diese Anfrage:

Betreff: {{subject}}

{{#each messages}}
{{role}}: {{content}}
{{/each}}

Antworte einfühlsam und hilfreich."""

        prompt_id = get_or_create_prompt("Debug: Mail Rating Demo", template_content)

        config = {
            "name": "Mail Rating Demo Job",
            "prompts": [{"template_id": prompt_id, "variant_name": "Standard"}],
            "llm_models": ["mistralai/Mistral-Small-3.2-24B-Instruct-2506"],
            "sources": {
                "type": "manual",
                "items": [
                    {
                        "id": 1,
                        "subject": "Probleme am Arbeitsplatz",
                        "messages": [
                            {"role": "Ratsuchende", "content": "Ich habe Probleme mit meinem Chef. Er kritisiert mich ständig."}
                        ]
                    },
                    {
                        "id": 2,
                        "subject": "Beziehungsprobleme",
                        "messages": [
                            {"role": "Ratsuchende", "content": "Mein Partner und ich streiten uns oft."},
                            {"role": "Beratende", "content": "Können Sie mir mehr darüber erzählen?"},
                            {"role": "Ratsuchende", "content": "Es geht meist um Hausarbeit."}
                        ]
                    }
                ]
            }
        }

    elif preset == "product_description":
        # Product description generation preset
        template_content = """Du bist ein erfahrener Marketing-Texter. Erstelle eine überzeugende Produktbeschreibung.

PRODUKT: {{name}}
KATEGORIE: {{category}}
EIGENSCHAFTEN:
{{#each features}}
- {{this}}
{{/each}}

ZIELGRUPPE: {{target_audience}}

Schreibe eine ansprechende Produktbeschreibung (150-200 Wörter), die:
1. Die Vorteile hervorhebt
2. Emotionen anspricht
3. Zum Kauf motiviert"""

        prompt_id = get_or_create_prompt("Debug: Product Description", template_content)

        config = {
            "name": "Product Description Generator",
            "prompts": [{"template_id": prompt_id, "variant_name": "Marketing"}],
            "llm_models": [
                "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
                "mistralai/Magistral-Small-2509"
            ],
            "sources": {
                "type": "manual",
                "items": [
                    {
                        "id": 1,
                        "name": "EcoBreeze Luftreiniger Pro",
                        "category": "Haushaltsgeräte",
                        "features": [
                            "HEPA-13 Filter entfernt 99.97% aller Partikel",
                            "Ultraleiser Nachtmodus (22 dB)",
                            "Smart-Home kompatibel (Alexa, Google Home)",
                            "Energieeffizient: nur 8W Verbrauch",
                            "Automatische Luftqualitätserkennung"
                        ],
                        "target_audience": "Allergiker und gesundheitsbewusste Familien"
                    },
                    {
                        "id": 2,
                        "name": "ChefMaster Multifunktions-Küchenmaschine",
                        "category": "Küchengeräte",
                        "features": [
                            "12 Automatikprogramme",
                            "1500W starker Motor",
                            "Integrierte Waage (bis 5kg)",
                            "Selbstreinigungsfunktion",
                            "Rezept-App mit 500+ Rezepten"
                        ],
                        "target_audience": "Hobbyköche und vielbeschäftigte Familien"
                    },
                    {
                        "id": 3,
                        "name": "NaturPur Bio-Teemischung",
                        "category": "Lebensmittel",
                        "features": [
                            "100% Bio-zertifiziert",
                            "Handgepflückt aus Nepal",
                            "Ohne künstliche Aromen",
                            "Faire Handelsbedingungen",
                            "Plastikfreie Verpackung"
                        ],
                        "target_audience": "Umweltbewusste Teeliebhaber"
                    }
                ]
            }
        }

    elif preset == "support_response":
        # Customer support response preset
        template_content = """Du bist ein freundlicher Kundenservice-Mitarbeiter. Beantworte die Kundenanfrage professionell.

KUNDE: {{customer_name}}
PRODUKT: {{product}}
PROBLEM: {{issue}}
BISHERIGE KOMMUNIKATION:
{{#each history}}
{{role}}: {{message}}
{{/each}}

Schreibe eine hilfreiche, lösungsorientierte Antwort."""

        prompt_id = get_or_create_prompt("Debug: Support Response", template_content)

        config = {
            "name": "Customer Support Response Generator",
            "prompts": [{"template_id": prompt_id, "variant_name": "Friendly"}],
            "llm_models": ["mistralai/Mistral-Small-3.2-24B-Instruct-2506"],
            "sources": {
                "type": "manual",
                "items": [
                    {
                        "id": 1,
                        "customer_name": "Thomas M.",
                        "product": "SmartWatch Pro",
                        "issue": "Display reagiert nicht auf Touch",
                        "history": [
                            {"role": "Kunde", "message": "Meine Uhr reagiert seit gestern nicht mehr auf Berührungen."},
                            {"role": "Support", "message": "Haben Sie bereits einen Neustart versucht?"},
                            {"role": "Kunde", "message": "Ja, mehrfach. Auch ein Reset hat nicht geholfen."}
                        ]
                    },
                    {
                        "id": 2,
                        "customer_name": "Sandra K.",
                        "product": "Fitness Tracker Lite",
                        "issue": "Schrittzähler ungenau",
                        "history": [
                            {"role": "Kunde", "message": "Der Schrittzähler zeigt viel weniger Schritte an als mein Handy."}
                        ]
                    }
                ]
            }
        }

    else:
        # Build config from request
        items = data.get("items", [])
        if not items:
            raise ValidationError("items are required (or use preset)")

        template = data.get("prompt_template", "Process: {{content}}")
        prompt_id = get_or_create_prompt("Debug: Custom Prompt", template)

        config = {
            "name": data.get("name", "Test Job"),
            "prompts": [{"template_id": prompt_id, "variant_name": "Standard"}],
            "llm_models": data.get("llm_models", ["mistralai/Mistral-Small-3.2-24B-Instruct-2506"]),
            "sources": {
                "type": "manual",
                "items": [{"id": i + 1, **item} for i, item in enumerate(items)]
            }
        }

    # Create job
    job = BatchGenerationService.create_job(
        name=config["name"],
        config=config,
        created_by=username,
    )

    # Start the job in a background thread
    import threading
    from flask import current_app

    def run_job_background(app, job_id):
        with app.app_context():
            try:
                BatchGenerationService.start_job(job_id)
            except Exception as e:
                logger.error(f"[Debug] Background job {job_id} failed: {e}")

    app = current_app._get_current_object()
    thread = threading.Thread(target=run_job_background, args=(app, job.id))
    thread.daemon = True
    thread.start()

    return jsonify({
        "success": True,
        "job_id": job.id,
        "job_name": job.name,
        "status": job.status.value,
        "message": f"Job {job.id} started in background. Use /job-status/{job.id} to monitor.",
    })


@generation_debug_bp.route('/job-status/<int:job_id>', methods=['GET'])
@api_key_or_token_required
@handle_api_errors(logger_name='generation_debug')
def job_status(job_id: int):
    """
    Get the current status of a generation job.
    """
    job = GenerationJob.query.get(job_id)
    if not job:
        raise NotFoundError(f"Job {job_id} not found")

    outputs = GeneratedOutput.query.filter_by(job_id=job_id).all()
    completed = sum(1 for o in outputs if o.status == GeneratedOutputStatus.COMPLETED)
    failed = sum(1 for o in outputs if o.status == GeneratedOutputStatus.FAILED)
    pending = sum(1 for o in outputs if o.status == GeneratedOutputStatus.PENDING)

    return jsonify({
        "success": True,
        "job_id": job.id,
        "name": job.name,
        "status": job.status.value if job.status else None,
        "progress_percent": job.progress_percent,
        "total_items": job.total_items,
        "outputs": {
            "total": len(outputs),
            "completed": completed,
            "failed": failed,
            "pending": pending,
        },
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    })
