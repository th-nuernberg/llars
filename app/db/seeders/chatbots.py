"""
Chatbot Seeder

Creates a default chatbot on startup that is visible to all users.
The chatbot is connected to the default RAG collection seeded from `/app/data/rag/standard`.
"""

from datetime import datetime


def initialize_default_chatbots(db):
    """
    Create the default admin-only chatbot (idempotent).

    Args:
        db: SQLAlchemy database instance
    """
    from ..tables import Chatbot, ChatbotCollection, ChatbotUserAccess, RAGCollection, ChatbotPromptSettings
    from ..models.llm_model import LLMModel

    print("\n" + "=" * 60)
    print("Initializing Default Chatbots...")
    print("=" * 60)

    default_collection = RAGCollection.query.filter_by(name='general').first()
    if not default_collection:
        print("⚠️  Default RAG collection 'general' not found. Skipping default chatbot seeding.")
        print("=" * 60 + "\n")
        return

    chatbot_name = 'standard_admin'
    chatbot_display_name = 'LLARS'
    chatbot_description = 'LLARS Systemassistent. Hilft beim Zurechtfinden und beantwortet Fragen zum System.'
    chatbot_prompt = """Du bist LLars, der KI-Assistent des LLARS-Projekts.

DOKUMENTATIONSLINKS:
- Jede Quelle im Kontext endet mit "[Quelle: URL]" - NUR diese URLs sind gueltig
- Gueltige Links beginnen IMMER mit: {PROJECT_URL}/docs/
- URLs wie "example.com" oder "anwalt-muenchen.de" sind NUR Beispiele aus der Doku - NIEMALS als Link verwenden!
- Format: [Titel](URL_AUS_QUELLE)

SPRACHE: Antworte in der Sprache des Nutzers.

STIL: Praezise, max 3-5 Punkte bei Listen."""
    chatbot_welcome = "Hallo! Ich bin LLARS. Wie kann ich dir im System helfen?"

    model_id = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_LLM)
    if not model_id:
        raise RuntimeError("No default LLM model configured in llm_models")

    bot = Chatbot.query.filter_by(name=chatbot_name).first()
    created = False

    if not bot:
        bot = Chatbot(
            name=chatbot_name,
            display_name=chatbot_display_name,
            description=chatbot_description,
            icon='mdi-robot',
            color='#5d7a4a',
            system_prompt=chatbot_prompt,
            model_name=model_id,
            temperature=0.7,
            max_tokens=2048,
            top_p=0.9,
            rag_enabled=True,
            rag_retrieval_k=8,
            rag_min_relevance=0.2,
            rag_include_sources=True,
            welcome_message=chatbot_welcome,
            fallback_message='Ich konnte leider keine passende Antwort finden.',
            max_context_messages=10,
            is_active=True,
            is_public=True,
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

    # Ensure it stays public and uses the default collection
    changed = False
    if not bot.is_public:
        bot.is_public = True
        changed = True
    if bot.primary_collection_id != default_collection.id:
        bot.primary_collection_id = default_collection.id
        changed = True
    if bot.display_name != chatbot_display_name:
        bot.display_name = chatbot_display_name
        changed = True
    if bot.description != chatbot_description:
        bot.description = chatbot_description
        changed = True
    if bot.system_prompt != chatbot_prompt:
        bot.system_prompt = chatbot_prompt
        changed = True
    if bot.welcome_message != chatbot_welcome:
        bot.welcome_message = chatbot_welcome
        changed = True
    if bot.rag_min_relevance != 0.2:
        bot.rag_min_relevance = 0.2
        changed = True

    # Ensure LLARS documentation collection is assigned with higher priority
    docs_collection = RAGCollection.query.filter_by(name='llars-documentation').first()
    if docs_collection:
        docs_assignment = ChatbotCollection.query.filter_by(
            chatbot_id=bot.id, collection_id=docs_collection.id
        ).first()
        if not docs_assignment:
            db.session.add(ChatbotCollection(
                chatbot_id=bot.id,
                collection_id=docs_collection.id,
                priority=0,  # Higher priority (lower number)
                weight=1.5,
                is_primary=False,
                assigned_by='system',
                assigned_at=datetime.now()
            ))
            changed = True
        elif docs_assignment.priority != 0:
            docs_assignment.priority = 0
            docs_assignment.weight = 1.5
            changed = True

    # Ensure general collection assignment exists (lower priority)
    assignment = ChatbotCollection.query.filter_by(chatbot_id=bot.id, collection_id=default_collection.id).first()
    if not assignment:
        db.session.add(ChatbotCollection(
            chatbot_id=bot.id,
            collection_id=default_collection.id,
            priority=1,  # Lower priority (higher number)
            weight=1.0,
            is_primary=True,
            assigned_by='system',
            assigned_at=datetime.now()
        ))
        changed = True
    elif assignment.priority != 1:
        assignment.priority = 1
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

    # Ensure prompt settings include URL in RAG context template
    prompt_settings = ChatbotPromptSettings.query.filter_by(chatbot_id=bot.id).first()
    desired_template = '[{{id}}] {{title}}\nLink: {{url}}\n{{excerpt}}'
    if prompt_settings:
        if prompt_settings.rag_context_item_template != desired_template:
            prompt_settings.rag_context_item_template = desired_template
            changed = True
    else:
        db.session.add(ChatbotPromptSettings(
            chatbot_id=bot.id,
            rag_context_prefix='Kontext aus der Dokumentation:',
            rag_context_item_template=desired_template
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
