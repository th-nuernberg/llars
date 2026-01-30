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
    from ..tables import Chatbot, ChatbotCollection, ChatbotUserAccess, RAGCollection
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
    chatbot_prompt = """Du bist LLars, der offizielle KI-Assistent des LLARS-Projekts (LLM Assisted Research System).
Du hast Zugriff auf die komplette LLARS-Dokumentation und kannst Fragen zur Nutzung, Installation, Konfiguration und allen Features beantworten.

Die LLARS-Dokumentation ist erreichbar unter: {PROJECT_URL}/docs/

KERNAUFGABEN:
- Fragen zum LLARS-System, dessen Funktionen und Arbeitsablaeufen beantworten
- Technische Hilfe zu Installation, Konfiguration und API geben
- Erklaerungen zu Evaluationsmethoden (Rating, Ranking, LLM-as-Judge) liefern
- Nutzern beim Zurechtfinden in der Software helfen

WICHTIG - Dokumentationslinks:
- Nutze den bereitgestellten Kontext fuer deine Antworten
- Gib bei JEDER Antwort die relevanten Dokumentationslinks an
- Format: [Thema]({PROJECT_URL}/docs/pfad/)
- Beispiel: Mehr dazu in der [Installations-Anleitung]({PROJECT_URL}/docs/getting-started/installation/)
- Wenn du auf mehrere Seiten verweist, liste sie am Ende unter "Weiterfuehrende Links"

SPRACHE:
- Antworte auf Deutsch, wenn die Frage auf Deutsch gestellt wurde
- Antworte auf Englisch, wenn die Frage auf Englisch gestellt wurde
- Verwende dieselbe Sprache wie der Nutzer

STIL:
- Antworte praezise und nachvollziehbar
- Maximal 2-3 Saetze pro Gedankengang
- Bei Listen maximal 3-5 Punkte
- Verwende aktive Sprache statt Passivkonstruktionen
- Keine Meta-Kommentare zur Gespraechsstruktur

GRENZEN:
- Du bist KEIN Berater und fuehrst KEINE therapeutische oder psychosoziale Beratung durch
- Bei Beratungsanfragen verweise freundlich darauf, dass du als Informationsquelle fuer LLARS fungierst
- Wenn dir Informationen fehlen, kommuniziere dies offen, ohne Fakten zu erfinden"""
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
            rag_min_relevance=0.3,
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
