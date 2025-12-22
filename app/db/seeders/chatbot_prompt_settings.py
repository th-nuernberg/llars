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

    bots = Chatbot.query.all()
    if not bots:
        return

    created = 0
    updated = 0
    for bot in bots:
        if bot.prompt_settings:
            if bot.name == 'standard_admin':
                settings = bot.prompt_settings
                if settings.rag_citation_instructions != STANDARD_LLARS_CITATION_INSTRUCTIONS:
                    settings.rag_citation_instructions = STANDARD_LLARS_CITATION_INSTRUCTIONS
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
