"""
Chatbot Prompt Settings Seeder

Ensures every chatbot has an associated ChatbotPromptSettings row.
This keeps the DB as the single source of truth for RAG prompt behavior.
"""

STANDARD_LLARS_CITATION_INSTRUCTIONS = """
WICHTIG - Quellen nutzen:
- Nutze den Kontext fuer inhaltliche Aussagen, wenn er relevant ist.
- Zitiere verwendete Quellen direkt im Text als [1], [2], ...
- Wenn keine passende Quelle vorhanden ist, beantworte Fragen zu LLARS trotzdem kurz aus deinem Systemwissen.
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
            if bot.name == 'standard_admin':
                if settings.rag_citation_instructions != STANDARD_LLARS_CITATION_INSTRUCTIONS:
                    settings.rag_citation_instructions = STANDARD_LLARS_CITATION_INSTRUCTIONS
                    settings_changed = True

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
        if bot.name == 'standard_admin':
            db.session.add(ChatbotPromptSettings(
                chatbot_id=bot.id,
                rag_citation_instructions=STANDARD_LLARS_CITATION_INSTRUCTIONS
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
