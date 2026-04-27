"""
Tests for ChatRAGRetrieval hybrid fallback behavior.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4


def _create_chatbot_with_collection(db, *, rag_enabled: bool = True):
    from db.tables import Chatbot, ChatbotCollection, RAGCollection

    suffix = uuid4().hex[:8]
    collection = RAGCollection(
        name=f"rag_collection_{suffix}",
        display_name=f"RAG Collection {suffix}",
        description="Test collection",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        created_by="test_user",
        is_public=True,
    )
    db.session.add(collection)
    db.session.flush()

    chatbot = Chatbot(
        name=f"chatbot_{suffix}",
        display_name="Test Chatbot",
        system_prompt="Du bist ein hilfreicher Assistent.",
        model_name="test-model",
        created_by="test_user",
        rag_enabled=rag_enabled,
        rag_retrieval_k=4,
        rag_min_relevance=0.3,
    )
    db.session.add(chatbot)
    db.session.flush()

    db.session.add(ChatbotCollection(
        chatbot_id=chatbot.id,
        collection_id=collection.id,
        priority=0,
        weight=1.0,
        is_primary=True,
        assigned_by="test_user",
    ))
    db.session.commit()

    return chatbot, collection


class TestChatRAGRetrievalFallback:
    """Hybrid fallback tests for chatbot retrieval."""

    @patch("services.chatbot.lexical_index.LexicalSearchIndex.search", return_value=[])
    def test_CHATRAG_001_sql_chunk_fallback_when_vector_search_empty(
        self,
        _mock_fts,
        app,
        db,
        app_context,
        tmp_path,
    ):
        from db.tables import CollectionDocumentLink, RAGDocument, RAGDocumentChunk
        from services.chatbot.chat_rag_retrieval import ChatRAGRetrieval

        chatbot, collection = _create_chatbot_with_collection(db)

        file_path = Path(tmp_path) / "kontakt.md"
        file_path.write_text("Allgemeine Informationen", encoding="utf-8")

        document = RAGDocument(
            filename="kontakt.md",
            original_filename="kontakt.md",
            file_path=str(file_path),
            file_size_bytes=file_path.stat().st_size,
            mime_type="text/markdown",
            file_hash=f"hash_{uuid4().hex}",
            title="Kontakt",
            description="Kontaktinformationen",
            status="indexed",
            collection_id=collection.id,
            uploaded_by="test_user",
        )
        db.session.add(document)
        db.session.flush()

        db.session.add(CollectionDocumentLink(
            collection_id=collection.id,
            document_id=document.id,
            link_type="new",
            linked_by="test_user",
        ))
        db.session.add(RAGDocumentChunk(
            document_id=document.id,
            chunk_index=0,
            content="Kontaktieren Sie unser Team per E-Mail oder Telefon.",
            embedding_status="completed",
        ))
        db.session.commit()

        retrieval = ChatRAGRetrieval(chatbot, rag_pipeline=MagicMock(model_name="test-embedding"))
        with patch.object(retrieval, "search_collection", return_value=[]):
            context, sources = retrieval.get_multi_collection_context("Wie kann ich Kontakt aufnehmen?")

        assert sources
        assert sources[0]["title"] == "Kontakt"
        assert "E-Mail" in sources[0]["excerpt"]
        assert "Kontaktieren" in context

    @patch("services.chatbot.lexical_index.LexicalSearchIndex.search", return_value=[])
    def test_CHATRAG_002_file_fallback_when_no_chunks_exist(
        self,
        _mock_fts,
        app,
        db,
        app_context,
        tmp_path,
    ):
        from db.tables import CollectionDocumentLink, RAGDocument
        from services.chatbot.chat_rag_retrieval import ChatRAGRetrieval

        chatbot, collection = _create_chatbot_with_collection(db)

        file_path = Path(tmp_path) / "oeffnungszeiten.md"
        file_path.write_text(
            "Unsere Oeffnungszeiten sind Montag bis Freitag von 9 bis 17 Uhr. "
            "Fuer Termine schreiben Sie bitte eine E-Mail.",
            encoding="utf-8",
        )

        document = RAGDocument(
            filename="oeffnungszeiten.md",
            original_filename="oeffnungszeiten.md",
            file_path=str(file_path),
            file_size_bytes=file_path.stat().st_size,
            mime_type="text/markdown",
            file_hash=f"hash_{uuid4().hex}",
            title="Oeffnungszeiten",
            description="Servicezeiten",
            status="pending",
            collection_id=collection.id,
            uploaded_by="test_user",
        )
        db.session.add(document)
        db.session.flush()

        db.session.add(CollectionDocumentLink(
            collection_id=collection.id,
            document_id=document.id,
            link_type="new",
            linked_by="test_user",
        ))
        db.session.commit()

        retrieval = ChatRAGRetrieval(chatbot, rag_pipeline=MagicMock(model_name="test-embedding"))
        with patch.object(retrieval, "search_collection", return_value=[]):
            context, sources = retrieval.get_multi_collection_context("Wann sind eure Oeffnungszeiten?")

        assert sources
        assert sources[0]["title"] == "Oeffnungszeiten"
        assert "Montag bis Freitag" in sources[0]["excerpt"]
        assert "Oeffnungszeiten" in context
