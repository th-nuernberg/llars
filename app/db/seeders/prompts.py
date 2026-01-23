"""
Demo Prompt Templates Seeder

Creates example prompts for testing the Generation module.
"""
import logging
from db.database import db
from db.tables import User, UserPrompt

logger = logging.getLogger(__name__)


def seed_demo_prompts():
    """
    Seeds demo prompt templates for testing.
    Creates prompts for the admin user.
    """
    logger.info("Seeding demo prompts...")

    # Find admin user
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        logger.warning("Admin user not found, skipping prompt seeding")
        return

    # Define demo prompts
    demo_prompts = [
        # === EMAIL RESPONSE GENERATOR (for Rating/LLM-as-Judge evaluation) ===
        {
            "name": "Email Response Generator (Rating Demo)",
            "content": {
                "blocks": {
                    "system": {
                        "content": """Du bist ein professioneller Berater in einer Online-Beratungsstelle.
Deine Aufgabe ist es, einfühlsame, hilfreiche und professionelle Antworten auf Klientenanfragen zu verfassen.

Wichtige Richtlinien:
- Zeige Empathie und Verständnis für die Situation des Klienten
- Verwende eine warme, aber professionelle Sprache
- Stelle bei Bedarf klärende Fragen
- Biete konkrete Hilfestellungen oder nächste Schritte an
- Halte die Antwort in angemessener Länge (150-400 Wörter)
- Beginne mit einer persönlichen Anrede
- Beende mit einem ermutigenden Gruß""",
                        "position": 0
                    },
                    "task": {
                        "content": """Hier ist der bisherige E-Mail-Verlauf:

Betreff: {{subject}}

{{messages}}

---

Verfasse nun als Berater eine professionelle Antwort auf die letzte Nachricht:""",
                        "position": 1
                    }
                }
            }
        }
    ]

    created_count = 0
    for prompt_data in demo_prompts:
        # Check if prompt already exists
        existing = UserPrompt.query.filter_by(
            user_id=admin_user.id,
            name=prompt_data["name"]
        ).first()

        if existing:
            logger.debug(f"Prompt '{prompt_data['name']}' already exists, skipping")
            continue

        # Create new prompt
        new_prompt = UserPrompt(
            user_id=admin_user.id,
            name=prompt_data["name"],
            content=prompt_data["content"]
        )
        db.session.add(new_prompt)
        created_count += 1
        logger.info(f"Created prompt: {prompt_data['name']}")

    db.session.commit()
    logger.info(f"Demo prompts seeding complete. Created {created_count} new prompts.")


if __name__ == "__main__":
    seed_demo_prompts()
