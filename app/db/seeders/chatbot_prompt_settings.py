"""
Chatbot Prompt Settings Seeder

Ensures every chatbot has an associated ChatbotPromptSettings row.
This keeps the DB as the single source of truth for RAG prompt behavior.
"""

STANDARD_LLARS_CITATION_INSTRUCTIONS = """
WICHTIG - Quellen und Dokumentationslinks:
- Nutze den Kontext fuer inhaltliche Aussagen, wenn er relevant ist.
- Zitiere verwendete Quellen direkt im Text als [1], [2], ...
- Wenn eine Quelle einen Dokumentationslink enthaelt, gib diesen Link in deiner Antwort an.
- Format fuer Dokumentationslinks: [Thema](URL)
- Wenn keine passende Quelle vorhanden ist, beantworte Fragen zu LLARS trotzdem kurz aus deinem Systemwissen.
- Bei mehreren relevanten Seiten, liste sie am Ende unter "Weiterfuehrende Links".
""".strip()

RECHTSASSISTENT_CITATION_INSTRUCTIONS = """
WICHTIG - Gesetzestexte zitieren:
- Zitiere IMMER die relevanten Paragraphen und Artikel mit Gesetzesnamen.
- Nutze Quellenverweise im Format [1], [2], etc.
- Erkläre juristische Fachbegriffe verständlich.
- Weise am Ende auf professionelle Rechtsberatung hin.
""".strip()


def initialize_chatbot_prompt_settings(db):
    from ..tables import Chatbot, ChatbotPromptSettings
    from ..models.chatbot import (
        DEFAULT_REFLECTION_PROMPT,
        DEFAULT_ACT_SYSTEM_PROMPT,
        DEFAULT_REACT_SYSTEM_PROMPT,
        DEFAULT_REFLACT_SYSTEM_PROMPT,
    )

    bots = Chatbot.query.all()
    if not bots:
        return

    created = 0
    updated = 0
    for bot in bots:
        if bot.prompt_settings:
            settings = bot.prompt_settings
            settings_changed = False

            # LLARS Chatbot - Standard RAG mode
            if bot.name == 'standard_admin':
                if settings.rag_citation_instructions != STANDARD_LLARS_CITATION_INSTRUCTIONS:
                    settings.rag_citation_instructions = STANDARD_LLARS_CITATION_INSTRUCTIONS
                    settings_changed = True
                if settings.agent_mode != 'standard':
                    settings.agent_mode = 'standard'
                    settings_changed = True

            # Rechtsassistent - ReflAct mode for multi-hop legal queries
            if bot.name == 'rechtsassistent':
                if settings.rag_citation_instructions != RECHTSASSISTENT_CITATION_INSTRUCTIONS:
                    settings.rag_citation_instructions = RECHTSASSISTENT_CITATION_INSTRUCTIONS
                    settings_changed = True
                if settings.agent_mode != 'reflact':
                    settings.agent_mode = 'reflact'
                    settings_changed = True
                if settings.task_type != 'multihop':
                    settings.task_type = 'multihop'
                    settings_changed = True
                if settings.agent_max_iterations != 8:
                    settings.agent_max_iterations = 8  # More iterations for complex legal queries
                    settings_changed = True

            # Ensure default prompts are set
            if not (settings.reflection_prompt or '').strip():
                settings.reflection_prompt = DEFAULT_REFLECTION_PROMPT
                settings_changed = True
            if not (settings.act_system_prompt or '').strip():
                settings.act_system_prompt = DEFAULT_ACT_SYSTEM_PROMPT
                settings_changed = True
            if not (settings.react_system_prompt or '').strip():
                settings.react_system_prompt = DEFAULT_REACT_SYSTEM_PROMPT
                settings_changed = True
            if not (settings.reflact_system_prompt or '').strip():
                settings.reflact_system_prompt = DEFAULT_REFLACT_SYSTEM_PROMPT
                settings_changed = True

            if settings_changed:
                updated += 1
            continue

        # Create new prompt settings
        if bot.name == 'standard_admin':
            # LLARS - Standard RAG mode
            db.session.add(ChatbotPromptSettings(
                chatbot_id=bot.id,
                agent_mode='standard',
                task_type='lookup',
                rag_citation_instructions=STANDARD_LLARS_CITATION_INSTRUCTIONS
            ))
        elif bot.name == 'rechtsassistent':
            # Rechtsassistent - ReflAct mode for complex legal queries
            db.session.add(ChatbotPromptSettings(
                chatbot_id=bot.id,
                agent_mode='reflact',
                task_type='multihop',
                agent_max_iterations=8,
                rag_citation_instructions=RECHTSASSISTENT_CITATION_INSTRUCTIONS
            ))
        else:
            db.session.add(ChatbotPromptSettings(chatbot_id=bot.id))
        created += 1

    if created or updated:
        db.session.commit()
        if created:
            print(f"  [Chatbots] Added prompt settings for {created} chatbots")
        if updated:
            print(f"  [Chatbots] Updated prompt settings for {updated} chatbots")
