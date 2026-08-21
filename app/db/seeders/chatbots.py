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

    # The LLARS docs (synced mkdocs markdown) are the primary knowledge base for
    # the assistant. The legacy 'general' collection held a stale single "llars
    # faq" doc with source_url=NULL — that's the source the model invented a
    # /mkdocs/en/faq/ link for. Prefer llars-documentation; only fall back to
    # 'general' on a fresh install where the docs haven't been synced yet.
    docs_collection = RAGCollection.query.filter_by(name='llars-documentation').first()
    general_collection = RAGCollection.query.filter_by(name='general').first()
    default_collection = docs_collection or general_collection
    if not default_collection:
        print("⚠️  No RAG collection (llars-documentation/general) found. Skipping default chatbot seeding.")
        print("=" * 60 + "\n")
        return

    chatbot_name = 'standard_admin'
    chatbot_display_name = 'LLARS'
    chatbot_description = 'LLARS Systemassistent. Hilft beim Zurechtfinden und beantwortet Fragen zum System.'
    chatbot_prompt = """Du bist LLars, der KI-Assistent des LLARS-Projekts.

QUELLEN: Stuetze dich auf den bereitgestellten Kontext. Gib NIEMALS selbst URLs,
Links oder Pfade aus und erfinde keine - die Marker [1], [2], ... werden vom
System automatisch in anklickbare Quellen umgewandelt. Zitiere sparsam und nur,
wenn eine Quelle wirklich relevant ist.

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

    # Assign the LLARS documentation collection as the primary (and only)
    # knowledge base. The legacy 'general' collection is intentionally NOT wired
    # up anymore — it held a stale "llars faq" doc without a source_url that the
    # model cited with an invented /mkdocs/en/faq/ link.
    if docs_collection:
        docs_assignment = ChatbotCollection.query.filter_by(
            chatbot_id=bot.id, collection_id=docs_collection.id
        ).first()
        if not docs_assignment:
            db.session.add(ChatbotCollection(
                chatbot_id=bot.id,
                collection_id=docs_collection.id,
                priority=0,
                weight=1.5,
                is_primary=True,
                assigned_by='system',
                assigned_at=datetime.now()
            ))
            changed = True
        elif docs_assignment.priority != 0 or not docs_assignment.is_primary:
            docs_assignment.priority = 0
            docs_assignment.weight = 1.5
            docs_assignment.is_primary = True
            changed = True

        # Remove the legacy 'general' assignment if it lingers from older seeds.
        if general_collection:
            stale = ChatbotCollection.query.filter_by(
                chatbot_id=bot.id, collection_id=general_collection.id
            ).first()
            if stale:
                db.session.delete(stale)
                changed = True
    else:
        # Fresh install fallback: docs not synced yet — keep 'general' as primary
        # so the assistant still has a knowledge base until the docs sync runs.
        assignment = ChatbotCollection.query.filter_by(
            chatbot_id=bot.id, collection_id=default_collection.id
        ).first()
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

    # RAG context template — deliberately WITHOUT a "Link: {{url}}" line. Feeding
    # raw URLs into the context tempted the model to reproduce/invent them; the
    # [n] markers already become clickable sources in the frontend.
    prompt_settings = ChatbotPromptSettings.query.filter_by(chatbot_id=bot.id).first()
    desired_template = '[{{id}}] {{title}}\n{{excerpt}}'
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
