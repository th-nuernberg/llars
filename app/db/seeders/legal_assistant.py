"""
Legal Assistant Chatbot Seeder

Creates a pre-configured "Rechtsassistent" chatbot with all German federal laws
from the bundled legal documents in /app/data/rag/legal/.
"""

import os
import hashlib
from datetime import datetime
from pathlib import Path


def initialize_legal_assistant(db):
    """
    Initialize the Legal Assistant chatbot with German law documents.
    This runs on every app startup but uses idempotent checks.

    Args:
        db: SQLAlchemy database instance
    """
    from ..tables import (
        RAGCollection, RAGDocument, Chatbot, ChatbotCollection
    )
    from ..models.rag import CollectionDocumentLink
    from ..models.llm_model import LLMModel

    print("\n" + "=" * 60)
    print("Initializing Legal Assistant (Rechtsassistent)...")
    print("=" * 60)

    # Base path for legal documents
    legal_docs_base = Path('/app/data/rag/legal')
    bundesgesetze_dir = legal_docs_base / 'bundesgesetze'
    eu_recht_dir = legal_docs_base / 'eu_recht'

    # Check if legal docs exist
    if not legal_docs_base.exists():
        print(f"  Legal docs directory not found: {legal_docs_base}")
        print("   Run scripts/download_legal_docs.py first to download laws.")
        print("=" * 60 + "\n")
        return

    # Count available PDFs
    bundesgesetze_pdfs = list(bundesgesetze_dir.glob("*.pdf")) if bundesgesetze_dir.exists() else []
    eu_pdfs = list(eu_recht_dir.glob("*.pdf")) if eu_recht_dir.exists() else []
    total_pdfs = len(bundesgesetze_pdfs) + len(eu_pdfs)

    if total_pdfs == 0:
        print("  No legal PDF documents found.")
        print("   Run scripts/download_legal_docs.py first to download laws.")
        print("=" * 60 + "\n")
        return

    print(f"  Found {total_pdfs} legal documents:")
    print(f"    - Bundesgesetze: {len(bundesgesetze_pdfs)}")
    print(f"    - EU-Recht: {len(eu_pdfs)}")

    # ==================== 1. Create RAG Collection ====================
    collection_name = 'deutsche_gesetze'
    collection = RAGCollection.query.filter_by(name=collection_name).first()

    if not collection:
        embedding_model = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_EMBEDDING)
        if not embedding_model:
            raise RuntimeError("No default embedding model configured in llm_models")
        chroma_name = f"llars_deutsche_gesetze_{embedding_model.replace('/', '_')}"
        collection = RAGCollection(
            name=collection_name,
            display_name='Deutsche Gesetze',
            description='Sammlung aller deutschen Bundesgesetze und wichtiger EU-Verordnungen',
            icon='mdi-scale-balance',
            color='#1565C0',
            embedding_model=embedding_model,
            chunk_size=1500,
            chunk_overlap=200,
            retrieval_k=8,
            is_active=True,
            is_public=True,
            created_by='system',
            chroma_collection_name=chroma_name
        )
        db.session.add(collection)
        db.session.commit()
        print(f"  Created collection: '{collection_name}'")
    else:
        print(f"  Collection '{collection_name}' already exists")

    # ==================== 2. Register Documents ====================
    registered = 0
    skipped = 0

    all_pdfs = bundesgesetze_pdfs + eu_pdfs

    for pdf_path in all_pdfs:
        try:
            # Calculate file hash
            with open(pdf_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()

            # Check if already registered
            existing = RAGDocument.query.filter_by(file_hash=file_hash).first()
            if existing:
                # Update collection if not set
                if existing.collection_id != collection.id:
                    existing.collection_id = collection.id
                skipped += 1
                continue

            # Generate title from filename
            filename = pdf_path.name
            title = filename.replace('.pdf', '').replace('_', ' ')

            # Determine category based on path
            if 'eu_recht' in str(pdf_path):
                category = 'eu_recht'
            else:
                category = 'bundesgesetze'

            # Create document entry
            doc = RAGDocument(
                filename=filename,
                original_filename=filename,
                file_path=str(pdf_path),
                file_size_bytes=pdf_path.stat().st_size,
                mime_type='application/pdf',
                file_hash=file_hash,
                title=title,
                description=f'Gesetzestext: {title}',
                language='de',
                status='pending',  # Will be embedded on build
                collection_id=collection.id,
                embedding_model=embedding_model,
                is_public=True,
                uploaded_by='system',
                uploaded_at=datetime.now(),
                metadata={
                    'category': category,
                    'source': 'gesetze-im-internet.de' if category == 'bundesgesetze' else 'eur-lex.europa.eu'
                }
            )
            db.session.add(doc)
            registered += 1

        except Exception as e:
            print(f"    Error processing {pdf_path.name}: {e}")
            continue

    db.session.commit()
    print(f"  Registered {registered} new documents, {skipped} already existed")

    # Ensure all documents in this collection have CollectionDocumentLink entries
    docs_in_collection = RAGDocument.query.filter_by(collection_id=collection.id).all()
    links_created = 0
    for doc in docs_in_collection:
        existing_link = CollectionDocumentLink.query.filter_by(
            collection_id=collection.id,
            document_id=doc.id
        ).first()
        if not existing_link:
            link = CollectionDocumentLink(
                collection_id=collection.id,
                document_id=doc.id,
                link_type='new',
                linked_by='system'
            )
            db.session.add(link)
            links_created += 1
    if links_created > 0:
        db.session.commit()
        print(f"  Created {links_created} collection-document links")

    # Update collection stats
    doc_count = RAGDocument.query.filter_by(collection_id=collection.id).count()
    size_bytes = db.session.query(
        db.func.sum(RAGDocument.file_size_bytes)
    ).filter_by(collection_id=collection.id).scalar() or 0

    collection.document_count = doc_count
    collection.total_size_bytes = size_bytes
    db.session.commit()

    print(f"  Collection stats: {doc_count} documents, {size_bytes / (1024*1024):.1f} MB")

    # ==================== 3. Create Chatbot ====================
    chatbot_name = 'rechtsassistent'
    bot = Chatbot.query.filter_by(name=chatbot_name).first()

    admin_roles = ['admin']

    if not bot:
        llm_model_id = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_LLM)
        if not llm_model_id:
            raise RuntimeError("No default LLM model configured in llm_models")
        bot = Chatbot(
            name=chatbot_name,
            display_name='Rechtsassistent',
            description='KI-Assistent mit Zugriff auf alle deutschen Bundesgesetze und wichtige EU-Verordnungen. Stellt Fragen zu deutschem und europäischem Recht.',
            icon='mdi-scale-balance',
            color='#1565C0',
            system_prompt="""Du bist ein Rechtsassistent mit Zugriff auf deutsche Bundesgesetze und EU-Verordnungen.

WICHTIGE REGELN:
1. Beantworte Fragen NUR basierend auf den bereitgestellten Gesetzestexten.
2. Zitiere IMMER die relevanten Paragraphen und Artikel.
3. Gib die Quellenverweise im Format [1], [2], etc. an.
4. Wenn du etwas nicht aus den Dokumenten beantworten kannst, sage das ehrlich.
5. Gib KEINE rechtlichen Empfehlungen - verweise auf professionelle Rechtsberatung.
6. Erkläre juristische Fachbegriffe verständlich.

FORMAT:
- Beginne mit einer kurzen, verständlichen Antwort
- Zitiere dann die relevanten Gesetzestexte mit Paragraphen
- Weise am Ende auf die Notwendigkeit professioneller Rechtsberatung hin

HINWEIS: Dies ist ein Informationsdienst. Für konkrete Rechtsfragen sollte immer ein Rechtsanwalt konsultiert werden.""",
            model_name=llm_model_id,
            temperature=0.3,  # Lower for factual answers
            max_tokens=4096,  # Longer for legal texts
            top_p=0.9,
            rag_enabled=True,
            rag_retrieval_k=10,  # More context for legal questions
            rag_min_relevance=0.4,
            rag_include_sources=True,
            welcome_message='Willkommen beim Rechtsassistenten. Ich kann Ihnen bei Fragen zu deutschen Bundesgesetzen und EU-Verordnungen helfen. Bitte beachten Sie, dass dies keine Rechtsberatung ersetzt.',
            fallback_message='Zu dieser Frage konnte ich leider keine passenden Gesetzestexte finden. Bitte wenden Sie sich an einen Rechtsanwalt für eine professionelle Beratung.',
            max_context_messages=10,
            is_active=True,
            is_public=False,  # Admin-only
            allowed_roles=admin_roles,
            build_status='draft',  # Needs embedding via Build button
            primary_collection_id=collection.id,
            created_by='system',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.session.add(bot)
        db.session.commit()
        print(f"  Created chatbot: '{chatbot_name}'")
    else:
        # Update collection reference if needed
        changed = False
        if bot.primary_collection_id != collection.id:
            bot.primary_collection_id = collection.id
            changed = True
        if bot.is_public:
            bot.is_public = False
            changed = True
        if bot.allowed_roles != admin_roles:
            bot.allowed_roles = admin_roles
            changed = True
        if changed:
            db.session.commit()
        print(f"  Chatbot '{chatbot_name}' already exists")

    # Ensure collection assignment
    assignment = ChatbotCollection.query.filter_by(
        chatbot_id=bot.id,
        collection_id=collection.id
    ).first()

    if not assignment:
        assignment = ChatbotCollection(
            chatbot_id=bot.id,
            collection_id=collection.id,
            priority=0,
            weight=1.0,
            is_primary=True,
            assigned_by='system',
            assigned_at=datetime.now()
        )
        db.session.add(assignment)
        db.session.commit()
        print(f"  Linked chatbot to collection")

    # Ensure admin user has explicit access
    from ..tables import ChatbotUserAccess
    admin_access = ChatbotUserAccess.query.filter_by(chatbot_id=bot.id, username='admin').first()
    if not admin_access:
        db.session.add(ChatbotUserAccess(
            chatbot_id=bot.id,
            username='admin',
            granted_by='system'
        ))
        db.session.commit()

    print()
    print("  Legal Assistant initialized successfully!")
    print("  Note: Run 'Build' in the chatbot admin to generate embeddings.")
    print("=" * 60 + "\n")
