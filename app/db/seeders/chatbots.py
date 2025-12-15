"""
Chatbot Seeder

Creates a default chatbot on startup that is only visible to admins.
The chatbot is connected to the default RAG collection seeded from `/app/rag_docs`.
"""

from datetime import datetime


def initialize_default_chatbots(db):
    """
    Create the default admin-only chatbot (idempotent).

    Args:
        db: SQLAlchemy database instance
    """
    from ..tables import Chatbot, ChatbotCollection, ChatbotUserAccess, RAGCollection

    print("\n" + "=" * 60)
    print("Initializing Default Chatbots...")
    print("=" * 60)

    default_collection = RAGCollection.query.filter_by(name='general').first()
    if not default_collection:
        print("⚠️  Default RAG collection 'general' not found. Skipping default chatbot seeding.")
        print("=" * 60 + "\n")
        return

    chatbot_name = 'standard_admin'
    chatbot_display_name = 'Standard (Admin)'

    bot = Chatbot.query.filter_by(name=chatbot_name).first()
    created = False

    if not bot:
        bot = Chatbot(
            name=chatbot_name,
            display_name=chatbot_display_name,
            description='Standard-Chatbot basierend auf den vorinstallierten RAG-Dokumenten.',
            icon='mdi-robot',
            color='#5d7a4a',
            system_prompt=(
                "Du bist ein hilfreicher Assistent. Antworte präzise und nachvollziehbar. "
                "Wenn du Informationen aus den bereitgestellten Dokumenten verwendest, "
                "verweise auf die entsprechenden Quellen im Text."
            ),
            model_name='mistralai/Mistral-Small-3.2-24B-Instruct-2506',
            temperature=0.7,
            max_tokens=2048,
            top_p=0.9,
            rag_enabled=True,
            rag_retrieval_k=4,
            rag_min_relevance=0.3,
            rag_include_sources=True,
            welcome_message='Hallo! Wie kann ich helfen?',
            fallback_message='Ich konnte leider keine passende Antwort finden.',
            max_context_messages=10,
            is_active=True,
            is_public=False,
            allowed_roles=None,
            build_status='ready',
            build_error=None,
            source_url=None,
            primary_collection_id=default_collection.id,
            created_by='system',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.session.add(bot)
        db.session.flush()
        created = True

    # Ensure it stays private and uses the default collection
    changed = False
    if bot.is_public:
        bot.is_public = False
        changed = True
    if bot.primary_collection_id != default_collection.id:
        bot.primary_collection_id = default_collection.id
        changed = True

    # Ensure collection assignment exists (primary)
    assignment = ChatbotCollection.query.filter_by(chatbot_id=bot.id, collection_id=default_collection.id).first()
    if not assignment:
        db.session.add(ChatbotCollection(
            chatbot_id=bot.id,
            collection_id=default_collection.id,
            priority=0,
            weight=1.0,
            is_primary=True,
            assigned_by='system',
            assigned_at=datetime.now()
        ))
        changed = True

    # Ensure admin user is explicitly allowed
    access = ChatbotUserAccess.query.filter_by(chatbot_id=bot.id, username='admin').first()
    if not access:
        db.session.add(ChatbotUserAccess(
            chatbot_id=bot.id,
            username='admin',
            granted_by='system'
        ))
        changed = True

    if created or changed:
        db.session.commit()
        if created:
            print(f"✅ Created default chatbot '{chatbot_name}' ({chatbot_display_name})")
        else:
            print(f"✅ Updated default chatbot '{chatbot_name}'")
    else:
        print(f"✅ Default chatbot '{chatbot_name}' already up to date")

    print("=" * 60 + "\n")

