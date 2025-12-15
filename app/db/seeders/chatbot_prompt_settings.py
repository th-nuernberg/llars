"""
Chatbot Prompt Settings Seeder

Ensures every chatbot has an associated ChatbotPromptSettings row.
This keeps the DB as the single source of truth for RAG prompt behavior.
"""


def initialize_chatbot_prompt_settings(db):
    from ..tables import Chatbot, ChatbotPromptSettings

    bots = Chatbot.query.all()
    if not bots:
        return

    created = 0
    for bot in bots:
        if bot.prompt_settings:
            continue
        db.session.add(ChatbotPromptSettings(chatbot_id=bot.id))
        created += 1

    if created:
        db.session.commit()
        print(f"  [Chatbots] Added prompt settings for {created} chatbots")

