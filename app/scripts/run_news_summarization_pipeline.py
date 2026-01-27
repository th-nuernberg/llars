#!/usr/bin/env python3
"""News Summarization Pipeline - Direct DB Access"""

import json
import sys
import os
import time

# Ensure app is in path
sys.path.insert(0, '/app')
os.chdir('/app')

def main():
    # Import Flask app
    from main import app
    from db import db
    from db.models import User, RatingScenarios, EvaluationItem, ScenarioItems, ScenarioUsers, Message
    from db.models import UserPrompt, GenerationJob, GeneratedOutput
    from db.models.scenario import ScenarioRoles
    from datetime import datetime
    from services.generation.batch_generation_service import BatchGenerationService
    from services.generation.generation_worker import GenerationWorker

    with app.app_context():
        print("=" * 60)
        print("NEWS SUMMARIZATION PIPELINE")
        print("=" * 60)

        # ============ PHASE 1: User und Daten ============
        print("\n[1/5] Hole Admin-User...")
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("ERROR: Admin-User nicht gefunden!")
            return
        print(f"   OK: Admin gefunden: ID {admin.id}")

        # ============ PHASE 2: News-Daten importieren ============
        print("\n[2/5] Importiere News-Artikel...")

        data_path = '/app/data/news_articles_sample.json'
        with open(data_path, 'r', encoding='utf-8') as f:
            news_items = json.load(f)

        print(f"   {len(news_items)} Artikel geladen")

        # Erstelle Quell-Szenario
        source_scenario = RatingScenarios(
            scenario_name="News Artikel - Quelle",
            function_type_id=2,
            created_by=admin.username,
            config_json=json.dumps({"description": "Quell-Datensatz fuer News Summarization"})
        )
        db.session.add(source_scenario)
        db.session.flush()
        print(f"   OK: Quell-Szenario erstellt: ID {source_scenario.id}")

        created_items = []
        for idx, item_data in enumerate(news_items):
            eval_item = EvaluationItem(
                subject=item_data['subject'],
                sender='news_import',
                chat_id=1000 + idx  # Numeric ID
            )
            db.session.add(eval_item)
            db.session.flush()

            # Erstelle Message mit dem Content
            message = Message(
                item_id=eval_item.item_id,
                sender='article',
                content=item_data['content'],
                timestamp=datetime.now()
            )
            db.session.add(message)

            scenario_item = ScenarioItems(
                scenario_id=source_scenario.id,
                item_id=eval_item.item_id
            )
            db.session.add(scenario_item)
            created_items.append(eval_item)
            print(f"   + {item_data['id']}: {item_data['subject'][:40]}...")

        scenario_user = ScenarioUsers(
            scenario_id=source_scenario.id,
            user_id=admin.id,
            role=ScenarioRoles.OWNER
        )
        db.session.add(scenario_user)
        db.session.commit()
        print(f"   OK: {len(created_items)} Items importiert")

        # ============ PHASE 3: Prompt erstellen ============
        print("\n[3/5] Erstelle Summarization Prompt...")

        prompt_content = {
            "blocks": {
                "system": {
                    "content": "Du bist ein professioneller Journalist. Fasse Nachrichtenartikel praezise und neutral zusammen.",
                    "position": 0
                },
                "default": {
                    "content": "Fasse den folgenden Artikel in 2-3 Saetzen zusammen.\n\n**Titel:** {{subject}}\n\n**Artikel:**\n{{content}}\n\n**Zusammenfassung:**",
                    "position": 1
                }
            }
        }

        # Füge Variablen zum Content hinzu
        prompt_content['variables'] = ["subject", "content"]

        prompt = UserPrompt(
            name="News Summarization DE",
            user_id=admin.id,
            content=prompt_content  # JSON direkt, kein dumps nötig
        )
        db.session.add(prompt)
        db.session.commit()
        print(f"   OK: Prompt erstellt: ID {prompt.prompt_id}")

        # ============ PHASE 4: Batch Generation Job ============
        print("\n[4/5] Erstelle Batch Generation Job...")

        job_config = {
            "sources": {
                "type": "scenario",
                "scenario_id": source_scenario.id
            },
            "prompts": [{"template_id": prompt.prompt_id, "variant_name": "Standard", "variables": {}}],
            "llm_models": [
                "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
                "mistralai/Magistral-Small-2509"
            ],
            "generation_params": {"temperature": 0.3, "max_tokens": 250},
            "limits": {"max_parallel": 2, "max_cost_usd": 5.0, "max_retries": 2}
        }

        try:
            job = BatchGenerationService.create_job(
                name="News Summarization - Mistral vs Magistral",
                config=job_config,
                created_by=admin.username,
                description="Vergleich Mistral und Magistral"
            )
        except Exception as e:
            print(f"   ERROR: {e}")
            return
        print(f"   OK: Job erstellt: ID {job.id}")
        print(f"   Matrix: {len(created_items)} Items x 2 Modelle = {job.total_items} Outputs")

        print("\n   Starte Generation...")

        # Update job status to RUNNING
        from db.models import GenerationJobStatus
        job.status = GenerationJobStatus.RUNNING
        job.started_at = datetime.now()
        db.session.commit()

        # Run worker synchronously
        print("   Generiere Zusammenfassungen...")
        worker = GenerationWorker(job.id)
        worker.run()

        # Refresh job to get final stats
        db.session.refresh(job)
        print(f"\n   OK: {job.completed_items} erfolgreich, {job.failed_items} fehlgeschlagen")

        # ============ PHASE 5: Ranking-Szenario ============
        print("\n[5/5] Erstelle Ranking-Szenario...")

        ranking_config = {
            "eval_type": "ranking",
            "eval_config": {
                "config": {
                    "type": "buckets",
                    "buckets": [
                        {"id": 1, "name": {"de": "Gut", "en": "Good"}, "color": "#98d4bb"},
                        {"id": 2, "name": {"de": "Moderat", "en": "Moderate"}, "color": "#D1BC8A"},
                        {"id": 3, "name": {"de": "Schlecht", "en": "Poor"}, "color": "#e8a087"}
                    ],
                    "allowTies": True,
                    "dragDrop": True
                }
            },
            "source_job_id": job.id
        }

        ranking_scenario = RatingScenarios(
            scenario_name="News Summary Quality Ranking",
            function_type_id=1,
            created_by=admin.username,
            config_json=json.dumps(ranking_config)
        )
        db.session.add(ranking_scenario)
        db.session.flush()

        from db.models import GeneratedOutputStatus
        outputs = GeneratedOutput.query.filter_by(job_id=job.id, status=GeneratedOutputStatus.COMPLETED).all()

        for output in outputs:
            source_item = EvaluationItem.query.get(output.source_item_id) if output.source_item_id else None
            model_name = output.llm_model_name.split('/')[-1] if output.llm_model_name else "Unknown"

            ranking_item = EvaluationItem(
                subject=f"{model_name}: {source_item.subject[:50] if source_item else 'Summary'}",
                sender=model_name,
                chat_id=2000 + output.id  # Numeric ID
            )
            db.session.add(ranking_item)
            db.session.flush()

            # Message mit generiertem Content
            gen_message = Message(
                item_id=ranking_item.item_id,
                sender=model_name,
                content=output.generated_content or "No content generated",
                timestamp=datetime.now(),
                generated_by=model_name
            )
            db.session.add(gen_message)

            scenario_item = ScenarioItems(scenario_id=ranking_scenario.id, item_id=ranking_item.item_id)
            db.session.add(scenario_item)

        ranking_user = ScenarioUsers(scenario_id=ranking_scenario.id, user_id=admin.id, role=ScenarioRoles.OWNER)
        db.session.add(ranking_user)
        db.session.commit()

        print(f"   OK: Ranking-Szenario erstellt: ID {ranking_scenario.id}")
        print(f"   {len(outputs)} Items importiert")

        print("\n" + "=" * 60)
        print("PIPELINE ABGESCHLOSSEN!")
        print("=" * 60)
        print(f"""
Ergebnisse:
  - Quell-Szenario:   ID {source_scenario.id}
  - Prompt:           ID {prompt.prompt_id}
  - Generation Job:   ID {job.id} ({job.completed_items} Outputs)
  - Ranking-Szenario: ID {ranking_scenario.id}

Oeffne: http://localhost:55080/scenarios/{ranking_scenario.id}/evaluate

Kosten: ${job.total_cost_usd:.4f} USD
""")

if __name__ == '__main__':
    main()
