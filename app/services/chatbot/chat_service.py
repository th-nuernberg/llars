# chat_service.py
"""
Service for handling chat interactions with chatbots including RAG retrieval.
Supports file uploads (images for Vision, documents via OCR).
"""

import os
import logging
import uuid
import time
import re
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from openai import OpenAI
from db.db import db
from db.tables import (
    Chatbot, ChatbotCollection, ChatbotConversation, ChatbotMessage,
    ChatbotMessageRole, RAGCollection, RAGDocument, RAGDocumentChunk
)
from rag_pipeline import RAGPipeline
from services.chatbot.file_processor import FileProcessor, file_processor
from db.models.chatbot import (
    DEFAULT_RAG_CITATION_INSTRUCTIONS,
    DEFAULT_RAG_CONTEXT_ITEM_TEMPLATE,
    DEFAULT_RAG_CONTEXT_PREFIX,
    DEFAULT_RAG_UNKNOWN_ANSWER,
)
from llm.openai_utils import extract_delta_text, extract_message_text

logger = logging.getLogger(__name__)


class ChatService:
    """Service for chatbot chat interactions with Multi-Collection RAG"""

    _TOKEN_RE = re.compile(r"[\wäöüÄÖÜß]+", re.UNICODE)
    _STOPWORDS_DE = {
        'a', 'aber', 'als', 'am', 'an', 'auch', 'auf', 'aus', 'bei', 'bin', 'bis', 'bist', 'da', 'dadurch', 'daher',
        'darum', 'das', 'dass', 'dein', 'deine', 'dem', 'den', 'der', 'des', 'dich', 'die', 'dies', 'diese', 'dieser',
        'dieses', 'dir', 'doch', 'dort', 'du', 'durch', 'ein', 'eine', 'einem', 'einen', 'einer', 'eines', 'er', 'es',
        'euer', 'eure', 'für', 'hatte', 'hatten', 'hattest', 'hattet', 'hier', 'hinter', 'ich', 'ihr', 'ihre', 'im',
        'in', 'ist', 'ja', 'jede', 'jedem', 'jeden', 'jeder', 'jedes', 'jener', 'jenes', 'jetzt', 'kann', 'kannst',
        'können', 'könnt', 'machen', 'mein', 'meine', 'mit', 'muss', 'musst', 'müssen', 'müsst', 'nach', 'nachdem',
        'nein', 'nicht', 'nun', 'oder', 'seid', 'sein', 'seine', 'sich', 'sie', 'sind', 'so', 'soll', 'sollen',
        'sollst', 'sollt', 'sonst', 'soweit', 'sowie', 'und', 'unser', 'unsere', 'unter', 'vom', 'von', 'vor', 'wann',
        'warum', 'was', 'weiter', 'weitere', 'wenn', 'wer', 'werde', 'werden', 'werdet', 'weshalb', 'wie', 'wieder',
        'wieso', 'wir', 'wird', 'wirst', 'wo', 'woher', 'wohin', 'zu', 'zum', 'zur', 'über'
    }

    @staticmethod
    def _render_placeholders(template: str, mapping: Dict[str, Any]) -> str:
        rendered = template or ""
        for key, value in mapping.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, "" if value is None else str(value))
        return rendered

    def _get_prompt_settings(self):
        return getattr(self.chatbot, 'prompt_settings', None)

    def get_unknown_answer(self) -> str:
        settings = self._get_prompt_settings()
        unknown = getattr(settings, 'rag_unknown_answer', None) if settings else None
        if unknown is None or str(unknown).strip() == "":
            return DEFAULT_RAG_UNKNOWN_ANSWER
        return str(unknown)

    def _build_citation_instructions(self) -> str:
        settings = self._get_prompt_settings()
        template = getattr(settings, 'rag_citation_instructions', None) if settings else None
        if template is None or str(template).strip() == "":
            template = DEFAULT_RAG_CITATION_INSTRUCTIONS

        unknown_answer = self.get_unknown_answer()
        rendered = (
            str(template)
            .replace("{{UNKNOWN_ANSWER}}", unknown_answer)
            .replace("{UNKNOWN_ANSWER}", unknown_answer)
        )

        return "\n\n" + rendered.strip() + "\n"

    def _build_numbered_context(self, sources: List[Dict[str, Any]]) -> str:
        if not sources:
            return ""

        settings = self._get_prompt_settings()
        prefix = getattr(settings, 'rag_context_prefix', None) if settings else None
        item_template = getattr(settings, 'rag_context_item_template', None) if settings else None

        if prefix is None or str(prefix).strip() == "":
            prefix = DEFAULT_RAG_CONTEXT_PREFIX
        if item_template is None or str(item_template).strip() == "":
            item_template = DEFAULT_RAG_CONTEXT_ITEM_TEMPLATE

        parts = [f"{str(prefix).strip()}\n"]
        for idx, source in enumerate(sources):
            footnote_id = source.get("footnote_id") or (idx + 1)
            title = source.get("title") or source.get("filename") or "Unbekannt"
            excerpt = source.get("excerpt") or ""

            mapping = {
                "id": footnote_id,
                "title": title,
                "filename": source.get("filename") or "",
                "collection_name": source.get("collection_name") or "",
                "page_number": source.get("page_number") or "",
                "chunk_index": source.get("chunk_index") if source.get("chunk_index") is not None else "",
                "relevance": source.get("relevance") if source.get("relevance") is not None else "",
                "document_id": source.get("document_id") or "",
                "excerpt": excerpt,
            }

            parts.append(self._render_placeholders(str(item_template), mapping).strip())
            parts.append("")  # spacing

        return "\n".join(parts).strip()

    def __init__(self, chatbot_id: int):
        self.chatbot = Chatbot.query.get(chatbot_id)
        if not self.chatbot:
            raise ValueError(f"Chatbot with ID {chatbot_id} not found")

        self.rag_pipeline = RAGPipeline() if self.chatbot.rag_enabled else None

        # Initialize LLM client
        self.llm_client = OpenAI(
            api_key=os.environ.get('LITELLM_API_KEY'),
            base_url=os.environ.get('LITELLM_BASE_URL')
        )

    def chat(
        self,
        message: str,
        session_id: str,
        username: str = None,
        include_sources: bool = True,
        files: List[Dict[str, Any]] = None,
        conversation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Main method for chat interaction with RAG support and file handling.

        Args:
            message: User's message
            session_id: Session ID for conversation tracking
            username: Optional username
            include_sources: Whether to include source references
            files: List of processed file dicts from file_processor

        Returns:
            Dict with response, sources, and metadata
        """
        start_time = time.time()

        # 1. Get or create conversation
        conversation = self._get_or_create_conversation(session_id, username, conversation_id)

        # 2. Save user message
        user_msg = self._save_message(conversation.id, ChatbotMessageRole.USER, message)

        # 3. Get RAG context if enabled
        rag_context = ""
        sources = []
        retrieval_time_ms = None
        if self.chatbot.rag_enabled and self.chatbot.collections:
            retrieval_start = time.time()
            rag_context, sources = self._get_multi_collection_context(message)
            retrieval_time_ms = int((time.time() - retrieval_start) * 1000)

        # If RAG is enabled but no context could be retrieved, avoid hallucinations.
        # File uploads count as additional context, so only short-circuit when there are no files.
        if self.chatbot.rag_enabled and self.chatbot.collections and not sources and not files:
            response_text = self.get_unknown_answer()
            response_time_ms = int((time.time() - start_time) * 1000)
            tokens_input = 0
            tokens_output = 0

            assistant_msg = self._save_message(
                conversation.id,
                ChatbotMessageRole.ASSISTANT,
                response_text,
                rag_context=None,
                rag_sources=[],
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                response_time_ms=response_time_ms,
                stream_metadata={
                    "retrieval_time_ms": retrieval_time_ms,
                    "sources_count": len(sources),
                    "mode": "standard"
                }
            )

            conversation.message_count += 2
            conversation.last_message_at = datetime.now()
            if not conversation.title and len(message) > 0:
                conversation.title = message[:50] + ('...' if len(message) > 50 else '')
            db.session.commit()

            return {
                'response': response_text,
                'sources': [],
                'conversation_id': conversation.id,
                'session_id': session_id,
                'message_id': assistant_msg.id,
                'tokens': {
                    'input': tokens_input,
                    'output': tokens_output
                },
                'response_time_ms': response_time_ms,
                'files_processed': len(files) if files else 0
            }

        # 4. Build prompt with context, history, and files
        messages = self._build_messages(conversation, message, rag_context, files, sources=sources)

        # 5. Call LLM (with vision support if needed)
        has_images = files and any(
            f.get('type') == 'image' and f.get('image_data')
            for f in files
        )
        response_text, tokens_input, tokens_output = self._call_llm(
            messages,
            use_vision=has_images
        )

        # 6. Handle fallback on empty response (some providers may return tool calls / blocks)
        if response_text is None or not str(response_text).strip():
            fallback = (self.chatbot.fallback_message or "").strip()
            response_text = fallback or (self.get_unknown_answer() if self.chatbot.rag_enabled else "")

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # 7. Save assistant message
        sources_to_save = sources if self.chatbot.rag_include_sources else []
        assistant_msg = self._save_message(
            conversation.id,
            ChatbotMessageRole.ASSISTANT,
            response_text,
            rag_context=rag_context if rag_context else None,
            rag_sources=sources_to_save,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            response_time_ms=response_time_ms,
            stream_metadata={
                "retrieval_time_ms": retrieval_time_ms,
                "sources_count": len(sources),
                "mode": "standard"
            }
        )

        # 8. Update conversation
        conversation.message_count += 2
        conversation.last_message_at = datetime.now()
        if not conversation.title and len(message) > 0:
            conversation.title = message[:50] + ('...' if len(message) > 50 else '')
        db.session.commit()

        return {
            'response': response_text,
            'sources': sources_to_save if include_sources else [],
            'conversation_id': conversation.id,
            'session_id': session_id,
            'message_id': assistant_msg.id,
            'tokens': {
                'input': tokens_input,
                'output': tokens_output
            },
            'response_time_ms': response_time_ms,
            'files_processed': len(files) if files else 0
        }

    def test_chat(self, message: str) -> Dict[str, Any]:
        """
        Test chat without saving to database.
        Useful for previewing chatbot responses.
        """
        start_time = time.time()

        # Get RAG context if enabled
        rag_context = ""
        sources = []
        if self.chatbot.rag_enabled and self.chatbot.collections:
            rag_context, sources = self._get_multi_collection_context(message)

        if self.chatbot.rag_enabled and self.chatbot.collections and not sources:
            response_time_ms = int((time.time() - start_time) * 1000)
            return {
                'response': self.get_unknown_answer(),
                'sources': [],
                'tokens': {
                    'input': 0,
                    'output': 0
                },
                'response_time_ms': response_time_ms,
                'test_mode': True
            }

        # Build messages (no history in test mode)
        system_prompt = self.chatbot.system_prompt
        require_citations = bool(getattr(self._get_prompt_settings(), 'rag_require_citations', True))
        if sources and require_citations:
            system_prompt += self._build_citation_instructions()

        messages = [{"role": "system", "content": system_prompt}]

        if sources:
            messages.append({"role": "system", "content": self._build_numbered_context(sources)})
        elif rag_context:
            messages.append({"role": "system", "content": f"Kontext:\n\n{rag_context}"})

        messages.append({"role": "user", "content": message})

        # Call LLM
        response_text, tokens_input, tokens_output = self._call_llm(messages)

        response_time_ms = int((time.time() - start_time) * 1000)

        return {
            'response': response_text,
            'sources': sources if self.chatbot.rag_include_sources else [],
            'tokens': {
                'input': tokens_input,
                'output': tokens_output
            },
            'response_time_ms': response_time_ms,
            'test_mode': True
        }

    def test_chat_stream(self, message: str):
        """
        Stream test chat response tokens (Server-Sent Events friendly).
        Yields dicts with delta chunks and a final done payload.
        """
        start_time = time.time()

        # Get RAG context if enabled
        rag_context = ""
        sources = []
        if self.chatbot.rag_enabled and self.chatbot.collections:
            rag_context, sources = self._get_multi_collection_context(message)

        if self.chatbot.rag_enabled and self.chatbot.collections and not sources:
            response_time_ms = int((time.time() - start_time) * 1000)
            unknown = self.get_unknown_answer()
            yield {"delta": unknown}
            yield {
                "done": True,
                "full_response": unknown,
                "sources": [],
                "tokens": None,
                "response_time_ms": response_time_ms,
                "test_mode": True
            }
            return

        # Build messages (no history in test mode)
        system_prompt = self.chatbot.system_prompt
        require_citations = bool(getattr(self._get_prompt_settings(), 'rag_require_citations', True))
        if sources and require_citations:
            system_prompt += self._build_citation_instructions()

        messages = [{"role": "system", "content": system_prompt}]

        if sources:
            messages.append({"role": "system", "content": self._build_numbered_context(sources)})
        elif rag_context:
            messages.append({"role": "system", "content": f"Kontext:\n\n{rag_context}"})

        messages.append({"role": "user", "content": message})

        try:
            stream = self.llm_client.chat.completions.create(
                model=self.chatbot.model_name,
                messages=messages,
                temperature=self.chatbot.temperature,
                max_tokens=self.chatbot.max_tokens,
                top_p=self.chatbot.top_p,
                stream=True
            )

            accumulated = ""
            for chunk in stream:
                choice = chunk.choices[0] if chunk.choices else None
                delta_obj = getattr(choice, "delta", None) if choice else None
                delta_text = extract_delta_text(delta_obj)
                if not delta_text:
                    continue

                accumulated += delta_text
                yield {"delta": delta_text}

            response_time_ms = int((time.time() - start_time) * 1000)

            yield {
                "done": True,
                "full_response": accumulated,
                "sources": sources if self.chatbot.rag_include_sources else [],
                "tokens": None,
                "response_time_ms": response_time_ms,
                "test_mode": True
            }

        except Exception as e:
            logger.error(f"[ChatService] Streaming test_chat failed: {e}")
            yield {"error": str(e)}

    def _get_or_create_conversation(
        self,
        session_id: str,
        username: str = None,
        conversation_id: Optional[int] = None
    ) -> ChatbotConversation:
        """
        Get existing conversation or create a new one.
        """
        # Prefer explicit conversation_id to avoid session collisions
        if conversation_id:
            conversation = ChatbotConversation.query.filter_by(
                id=conversation_id,
                chatbot_id=self.chatbot.id
            ).first()
            if conversation and conversation.username and username and conversation.username != username:
                logger.warning(f"[ChatService] User {username} attempted to access conversation {conversation_id} owned by {conversation.username}")
                conversation = None
            if conversation:
                return conversation

        conversation = ChatbotConversation.query.filter_by(
            chatbot_id=self.chatbot.id,
            session_id=session_id
        ).first()

        # If a conversation exists but belongs to a different user, isolate by creating a new one
        if conversation and conversation.username and username and conversation.username != username:
            conversation = None

        if not conversation:
            conversation = ChatbotConversation(
                chatbot_id=self.chatbot.id,
                session_id=session_id,
                username=username,
                is_active=True
            )
            db.session.add(conversation)
            db.session.flush()
            logger.info(f"Created new conversation {session_id} for chatbot {self.chatbot.name}")

        return conversation

    def _save_message(
        self,
        conversation_id: int,
        role: ChatbotMessageRole,
        content: str,
        rag_context: str = None,
        rag_sources: List[Dict] = None,
        tokens_input: int = None,
        tokens_output: int = None,
        response_time_ms: int = None,
        agent_trace: Optional[List[Dict[str, Any]]] = None,
        stream_metadata: Optional[Dict[str, Any]] = None
    ) -> ChatbotMessage:
        """
        Save a message to the database.
        """
        message = ChatbotMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            rag_context=rag_context,
            rag_sources=rag_sources,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            response_time_ms=response_time_ms,
            agent_trace=agent_trace,
            stream_metadata=stream_metadata
        )
        db.session.add(message)
        db.session.flush()
        return message

    def _extract_lexical_tokens(self, query: str) -> List[str]:
        tokens = [t.lower() for t in self._TOKEN_RE.findall(query or '')]
        tokens = [t for t in tokens if len(t) >= 3 and t not in self._STOPWORDS_DE]
        # De-duplicate while keeping order
        seen = set()
        unique: List[str] = []
        for t in tokens:
            if t in seen:
                continue
            seen.add(t)
            unique.append(t)
        return unique[:6]

    def _lexical_search_collection(self, collection: RAGCollection, tokens: List[str], limit: int) -> List[Dict[str, Any]]:
        if not collection or not tokens:
            return []

        from sqlalchemy import or_
        from db.tables import CollectionDocumentLink

        clauses = [RAGDocumentChunk.content.ilike(f"%{t}%") for t in tokens]
        if not clauses:
            return []

        rows = (
            db.session.query(RAGDocumentChunk, RAGDocument)
            .join(RAGDocument, RAGDocument.id == RAGDocumentChunk.document_id)
            .join(CollectionDocumentLink, CollectionDocumentLink.document_id == RAGDocument.id)
            .filter(CollectionDocumentLink.collection_id == collection.id)
            .filter(or_(*clauses))
            .order_by(RAGDocumentChunk.document_id.desc(), RAGDocumentChunk.chunk_index.asc())
            .limit(limit)
            .all()
        )

        results: List[Dict[str, Any]] = []
        for chunk, doc in rows:
            filename = doc.filename if doc else None
            title = (
                (doc.title if doc else None)
                or (doc.original_filename if doc else None)
                or filename
                or 'Unbekannt'
            )

            results.append({
                'content': chunk.content,
                # Lexical hits are explicit string matches; assign a high score and let the reranker order them.
                'score': 1.0,
                'document_id': chunk.document_id,
                'title': title,
                'filename': filename,
                'chunk_index': chunk.chunk_index,
                'page_number': chunk.page_number,
                'start_char': chunk.start_char,
                'end_char': chunk.end_char,
                'vector_id': chunk.vector_id,
                'metadata': {
                    'document_id': chunk.document_id,
                    'chunk_index': chunk.chunk_index,
                    'filename': filename,
                    'collection_id': collection.id,
                    'page_number': chunk.page_number,
                    'start_char': chunk.start_char,
                    'end_char': chunk.end_char,
                    'vector_id': chunk.vector_id,
                }
            })

        return results

    def _get_multi_collection_context(self, query: str) -> Tuple[str, List[Dict]]:
        """
        Retrieve context from multiple collections with weighting.

        Returns:
            Tuple of (context_string, sources_list)
        """
        if not self.rag_pipeline:
            return "", []

        # Retrieve more candidates than we finally include in the prompt, so the reranker
        # can surface exact matches (e.g. names, emails) even if they are not in the top-K
        # vector results.
        final_k = max(1, int(self.chatbot.rag_retrieval_k or 4))
        candidate_k = max(final_k * 4, 12)

        all_results = []

        # Query each assigned collection
        for cc in sorted(self.chatbot.collections, key=lambda x: -x.priority):
            collection = cc.collection
            if not collection.chroma_collection_name:
                continue

            try:
                # Use RAG pipeline to search
                results = self._search_collection(
                    collection,
                    query,
                    k=candidate_k
                )

                # Apply weight and add collection info
                for result in results:
                    result['score'] *= cc.weight
                    result['collection_id'] = collection.id
                    result['collection_name'] = collection.display_name

                all_results.extend(results)

            except Exception as e:
                logger.error(f"Error searching collection {collection.name}: {e}")
                continue

        # Lexical fallback for fact lookups that vector search can miss (names, emails, roles).
        lexical_results: List[Dict[str, Any]] = []
        lexical_tokens = self._extract_lexical_tokens(query)
        if lexical_tokens:
            for cc in sorted(self.chatbot.collections, key=lambda x: -x.priority):
                collection = cc.collection
                if not collection:
                    continue
                try:
                    hits = self._lexical_search_collection(collection, lexical_tokens, limit=final_k)
                    for hit in hits:
                        hit['score'] *= cc.weight
                        hit['collection_id'] = collection.id
                        hit['collection_name'] = collection.display_name
                    lexical_results.extend(hits)
                except Exception as e:
                    logger.debug(f"[ChatService] Lexical fallback skipped for collection {collection.id}: {e}")

        if not all_results and not lexical_results:
            logger.warning(f"[ChatService] No RAG results for chatbot {self.chatbot.id} (query='{query[:50]}...') using model {self.rag_pipeline.model_name if self.rag_pipeline else 'none'}")
            return "", []

        # Sort by score and take top K
        all_results.sort(key=lambda x: x['score'], reverse=True)
        top_results = all_results[:candidate_k]

        # Filter by minimum relevance
        filtered_results = [
            r for r in top_results
            if r['score'] >= self.chatbot.rag_min_relevance
        ]

        # If everything is below threshold, keep the best candidates anyway and rely on
        # citation instructions + "unknown answer" to prevent hallucinations.
        if not filtered_results:
            filtered_results = top_results[:final_k]

        # Merge lexical matches (dedupe by vector_id / document+chunk).
        if lexical_results:
            seen = set()
            merged: List[Dict[str, Any]] = []
            for r in filtered_results + lexical_results:
                key = r.get('vector_id') or (r.get('document_id'), r.get('chunk_index'))
                if key in seen:
                    continue
                seen.add(key)
                merged.append(r)
            filtered_results = merged

        # Optional reranking (keeps filtering based on vector score)
        try:
            from services.rag.reranker import rerank_results
            filtered_results = rerank_results(query, filtered_results)
        except Exception as e:
            logger.debug(f"[ChatService] Reranking skipped: {e}")

        filtered_results = filtered_results[:final_k]

        # Build context string
        context_parts = []
        sources = []

        for i, result in enumerate(filtered_results):
            context_parts.append(f"[Dokument {i+1}]\n{result['content']}")

            doc_id = result.get('document_id')
            metadata = result.get('metadata') or {}
            filename = metadata.get('filename') or metadata.get('source')
            title = result.get('title') or filename or 'Unbekannt'

            if doc_id:
                doc = RAGDocument.query.get(doc_id)
                if doc:
                    filename = doc.filename or filename
                    title = doc.title or doc.original_filename or filename or title
                    screenshot_url = doc.screenshot_url or (f"/api/rag/documents/{doc_id}/screenshot" if doc.screenshot_path else None)
                else:
                    screenshot_url = None
            else:
                screenshot_url = None

            sources.append({
                'footnote_id': i + 1,
                'document_id': result.get('document_id'),
                'title': title,
                'filename': filename,
                'collection_name': result.get('collection_name'),
                'relevance': round(result['score'], 3),
                'chunk_index': result.get('chunk_index') if result.get('chunk_index') is not None else metadata.get('chunk_index'),
                'page_number': result.get('page_number') if result.get('page_number') is not None else metadata.get('page_number'),
                'start_char': result.get('start_char') if result.get('start_char') is not None else metadata.get('start_char'),
                'end_char': result.get('end_char') if result.get('end_char') is not None else metadata.get('end_char'),
                'vector_id': result.get('vector_id') if result.get('vector_id') is not None else metadata.get('vector_id'),
                'rerank': result.get('rerank'),
                'excerpt': result['content'],
                'download_url': f"/api/rag/documents/{doc_id}/download" if doc_id else None,
                'content_url': f"/api/rag/documents/{doc_id}/content" if doc_id else None,
                'chunks_url': f"/api/rag/documents/{doc_id}/chunks" if doc_id else None,
                'document_url': f"/api/rag/documents/{doc_id}" if doc_id else None,
                'screenshot_url': screenshot_url
            })

        context = "\n\n---\n\n".join(context_parts)

        return context, sources

    def _search_collection(
        self,
        collection: RAGCollection,
        query: str,
        k: int = 4
    ) -> List[Dict]:
        """
        Search a specific collection using ChromaDB.
        """
        from langchain_chroma import Chroma

        vectorstore_dir = os.path.join(
            "/app/storage/vectorstore",
            self.rag_pipeline.model_name.replace('/', '_')
        )

        try:
            vectorstore = Chroma(
                collection_name=collection.chroma_collection_name,
                persist_directory=vectorstore_dir,
                embedding_function=self.rag_pipeline.embeddings
            )

            # Perform similarity search with scores
            docs_with_scores = vectorstore.similarity_search_with_score(query, k=k)

            results = []
            for doc, score in docs_with_scores:
                # Get document info from metadata
                metadata = doc.metadata or {}
                doc_id = metadata.get('document_id')
                filename = metadata.get('filename') or metadata.get('source')
                title = metadata.get('title') or filename or 'Unbekannt'

                if doc_id and (not title or title == 'Unbekannt'):
                    db_doc = RAGDocument.query.get(doc_id)
                    if db_doc:
                        filename = db_doc.filename or filename
                        title = db_doc.title or db_doc.original_filename or filename or title

                # Convert L2 distance to cosine similarity for normalized vectors
                # For normalized vectors: L2_distance^2 = 2 * (1 - cosine_similarity)
                # Therefore: cosine_similarity = 1 - (L2_distance^2 / 2)
                # Clamp to [0, 1] to handle any numerical edge cases
                similarity = max(0.0, min(1.0, 1 - (score ** 2) / 2))

                results.append({
                    'content': doc.page_content,
                    'score': similarity,
                    'document_id': doc_id,
                    'title': title,
                    'filename': filename,
                    'chunk_index': metadata.get('chunk_index'),
                    'page_number': metadata.get('page_number'),
                    'start_char': metadata.get('start_char'),
                    'end_char': metadata.get('end_char'),
                    'vector_id': metadata.get('vector_id'),
                    'metadata': metadata
                })

            return results

        except Exception as e:
            logger.error(f"Error searching collection {collection.name}: {e}")
            return []

    def _build_messages(
        self,
        conversation: ChatbotConversation,
        current_message: str,
        rag_context: str,
        files: List[Dict[str, Any]] = None,
        *,
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Build the message list for LLM including history, context, and files.
        Supports Vision API format for images.
        """
        messages = []

        # System prompt
        system_prompt = self.chatbot.system_prompt
        require_citations = bool(getattr(self._get_prompt_settings(), 'rag_require_citations', True))
        if sources and require_citations:
            system_prompt += self._build_citation_instructions()

        messages.append({
            "role": "system",
            "content": system_prompt
        })

        # RAG context as system message (prefer numbered sources for citations)
        if sources:
            numbered_context = self._build_numbered_context(sources)
            if numbered_context:
                messages.append({"role": "system", "content": numbered_context})
        elif rag_context:
            messages.append({"role": "system", "content": f"Kontext:\n\n{rag_context}"})

        # Add document content from files (non-image)
        if files:
            doc_text = file_processor.format_for_prompt([
                f for f in files if f.get('type') == 'document' or f.get('text_content')
            ])
            if doc_text:
                messages.append({
                    "role": "system",
                    "content": doc_text
                })

        # Chat history (limited)
        history = ChatbotMessage.query.filter_by(
            conversation_id=conversation.id
        ).order_by(ChatbotMessage.created_at.desc()).limit(
            self.chatbot.max_context_messages * 2  # *2 for user+assistant pairs
        ).all()

        history.reverse()  # Oldest first

        for msg in history:
            role = "user" if msg.role == ChatbotMessageRole.USER else "assistant"
            messages.append({
                "role": role,
                "content": msg.content
            })

        # Current user message (with images if vision model)
        if files and FileProcessor.is_vision_model(self.chatbot.model_name):
            # Build multimodal content
            user_content = []

            # Add images
            for f in files:
                if f.get('type') == 'image' and f.get('image_data'):
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{f.get('mime_type', 'image/jpeg')};base64,{f['image_data']}"
                        }
                    })

            # Add text message
            user_content.append({
                "type": "text",
                "text": current_message
            })

            messages.append({
                "role": "user",
                "content": user_content
            })
        else:
            messages.append({
                "role": "user",
                "content": current_message
            })

        return messages

    def _call_llm(
        self,
        messages: List[Dict[str, Any]],
        use_vision: bool = False
    ) -> Tuple[str, int, int]:
        """
        Call the LLM API and return response with token counts.
        Supports vision models for image analysis.
        """
        try:
            # For vision models with images, we might need to adjust max_tokens
            max_tokens = self.chatbot.max_tokens
            if use_vision and max_tokens < 1000:
                max_tokens = 1000  # Ensure enough tokens for image analysis

            response = self.llm_client.chat.completions.create(
                model=self.chatbot.model_name,
                messages=messages,
                temperature=self.chatbot.temperature,
                max_tokens=max_tokens,
                top_p=self.chatbot.top_p
            )

            response_text = ""
            if getattr(response, 'choices', None):
                response_text = extract_message_text(response.choices[0].message)

            tokens_input = response.usage.prompt_tokens if response.usage else 0
            tokens_output = response.usage.completion_tokens if response.usage else 0

            return response_text, tokens_input, tokens_output

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def supports_vision(self) -> bool:
        """Check if this chatbot's model supports vision."""
        return FileProcessor.is_vision_model(self.chatbot.model_name)

    # ========== Conversation Management Methods ==========

    @staticmethod
    def get_conversations(chatbot_id: int, username: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get conversations for a chatbot, filtered by username for data isolation.

        Args:
            chatbot_id: The chatbot ID
            username: Filter by this user (required for non-admin access)
            limit: Maximum number of conversations to return
        """
        query = ChatbotConversation.query.filter_by(chatbot_id=chatbot_id)

        # SECURITY: Always filter by username to ensure data isolation
        if username:
            query = query.filter_by(username=username)

        conversations = query.order_by(
            ChatbotConversation.last_message_at.desc()
        ).limit(limit).all()

        return [
            {
                'id': c.id,
                'session_id': c.session_id,
                'username': c.username,
                'title': c.title,
                'message_count': c.message_count,
                'is_active': c.is_active,
                'started_at': c.started_at.isoformat() if c.started_at else None,
                'last_message_at': c.last_message_at.isoformat() if c.last_message_at else None
            }
            for c in conversations
        ]

    @staticmethod
    def get_conversation(conversation_id: int, username: str = None, chatbot_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get a single conversation with all messages.

        Args:
            conversation_id: The conversation ID
            username: If provided, verify the conversation belongs to this user

        Returns:
            Conversation dict or None if not found/not authorized
        """
        query = ChatbotConversation.query.filter_by(id=conversation_id)
        if chatbot_id:
            query = query.filter_by(chatbot_id=chatbot_id)
        conversation = query.first()
        if not conversation:
            return None

        # SECURITY: Verify ownership if username is provided
        if username and conversation.username != username:
            logger.warning(f"User {username} attempted to access conversation {conversation_id} owned by {conversation.username}")
            return None

        messages = ChatbotMessage.query.filter_by(
            conversation_id=conversation_id
        ).order_by(ChatbotMessage.created_at.asc()).all()

        return {
            'id': conversation.id,
            'session_id': conversation.session_id,
            'chatbot_id': conversation.chatbot_id,
            'username': conversation.username,
            'title': conversation.title,
            'message_count': conversation.message_count,
            'is_active': conversation.is_active,
            'started_at': conversation.started_at.isoformat() if conversation.started_at else None,
            'last_message_at': conversation.last_message_at.isoformat() if conversation.last_message_at else None,
            'messages': [
                {
                    'id': m.id,
                    'role': m.role.value if hasattr(m.role, 'value') else m.role,
                    'content': m.content,
                    'rag_sources': m.rag_sources,
                    'tokens_input': m.tokens_input,
                    'tokens_output': m.tokens_output,
                    'response_time_ms': m.response_time_ms,
                    'user_rating': m.user_rating,
                    'created_at': m.created_at.isoformat() if m.created_at else None,
                    'agent_trace': m.agent_trace,
                    'stream_metadata': m.stream_metadata
                }
                for m in messages
            ]
        }

    @staticmethod
    def create_conversation(
        chatbot_id: int,
        username: str = None,
        title: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new conversation for a chatbot, scoped to the requesting user.
        """
        session = session_id or str(uuid.uuid4())
        conversation = ChatbotConversation(
            chatbot_id=chatbot_id,
            session_id=session,
            username=username,
            title=title,
            is_active=True
        )
        db.session.add(conversation)
        db.session.commit()

        return {
            'id': conversation.id,
            'session_id': conversation.session_id,
            'chatbot_id': conversation.chatbot_id,
            'username': conversation.username,
            'title': conversation.title,
            'message_count': conversation.message_count,
            'is_active': conversation.is_active,
            'started_at': conversation.started_at.isoformat() if conversation.started_at else None,
            'last_message_at': conversation.last_message_at.isoformat() if conversation.last_message_at else None
        }

    @staticmethod
    def delete_conversation(conversation_id: int, username: str = None) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            conversation_id: The conversation ID
            username: If provided, verify the conversation belongs to this user

        Returns:
            True if deleted, False if not found/not authorized
        """
        conversation = ChatbotConversation.query.get(conversation_id)
        if not conversation:
            return False

        # SECURITY: Verify ownership if username is provided
        if username and conversation.username != username:
            logger.warning(f"User {username} attempted to delete conversation {conversation_id} owned by {conversation.username}")
            return False

        db.session.delete(conversation)
        db.session.commit()

        logger.info(f"User {username or 'admin'} deleted conversation {conversation_id}")
        return True

    @staticmethod
    def rate_message(message_id: int, rating: str, feedback: str = None) -> bool:
        """
        Rate a message (helpful, not_helpful, incorrect).
        """
        message = ChatbotMessage.query.get(message_id)
        if not message:
            return False

        message.user_rating = rating
        message.user_feedback = feedback
        db.session.commit()

        return True
