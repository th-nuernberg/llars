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
    Chatbot,
    ChatbotCollection,
    ChatbotConversation,
    ChatbotMessage,
    ChatbotMessageRole,
    RAGCollection,
    RAGDocument,
    RAGDocumentChunk,
    CollectionDocumentLink
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

# ChromaDB collection metadata for cosine distance
# IMPORTANT: This ensures proper similarity scoring for both normalized and unnormalized embeddings
CHROMA_COLLECTION_METADATA = {"hnsw:space": "cosine"}


class ChatService:
    """Service for chatbot chat interactions with Multi-Collection RAG"""

    _TOKEN_RE = re.compile(r"[\wäöüÄÖÜß]+", re.UNICODE)
    _PLACEHOLDER_TITLES = {"neuer chat", "new chat"}
    _TITLE_MAX_CHARS = 50
    _TITLE_MAX_WORDS = 8
    _COMPOUND_SUFFIXES = (
        "mitglieder",
        "mitarbeiter",
        "mitarbeitende",
        "ansprechpartner",
        "leitung",
        "kontakt"
    )
    # Query expansion: synonyms and related terms for better lexical recall
    _QUERY_SYNONYMS = {
        # Business/Legal terms
        "inhaber": ["impressum", "betreiber", "verantwortlich", "geschäftsführer"],
        "betreiber": ["impressum", "inhaber", "verantwortlich"],
        "geschäftsführer": ["inhaber", "leitung", "vorstand", "ceo"],
        "chef": ["inhaber", "geschäftsführer", "leitung"],
        "boss": ["inhaber", "geschäftsführer", "leitung"],
        "eigentümer": ["inhaber", "betreiber", "impressum"],
        # Contact terms
        "kontakt": ["email", "telefon", "adresse", "impressum"],
        "email": ["kontakt", "mail", "e-mail"],
        "telefon": ["kontakt", "tel", "anrufen", "nummer"],
        "adresse": ["kontakt", "standort", "anschrift"],
        "anschrift": ["adresse", "standort", "impressum"],
        # Location terms
        "standort": ["adresse", "anschrift", "wo"],
        "öffnungszeiten": ["geöffnet", "uhrzeit", "wann"],
        # Team terms
        "team": ["mitarbeiter", "kollegen", "personal"],
        "mitarbeiter": ["team", "personal", "angestellte"],
    }
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

    @classmethod
    def _normalize_title(cls, title: Optional[str]) -> str:
        return re.sub(r"\s+", " ", str(title or "")).strip().lower()

    @classmethod
    def _is_placeholder_title(cls, title: Optional[str]) -> bool:
        normalized = cls._normalize_title(title)
        if not normalized:
            return True
        return normalized in cls._PLACEHOLDER_TITLES

    @classmethod
    def _build_title_from_message(cls, message: Optional[str]) -> Optional[str]:
        text = str(message or "").strip()
        if not text:
            return None
        first_line = text.splitlines()[0].strip()
        if not first_line:
            return None
        collapsed = re.sub(r"\s+", " ", first_line)
        words = collapsed.split(" ")
        title = " ".join(words[:cls._TITLE_MAX_WORDS])
        truncated_by_words = len(words) > cls._TITLE_MAX_WORDS
        truncated_by_chars = len(title) > cls._TITLE_MAX_CHARS
        if truncated_by_chars:
            title = title[:cls._TITLE_MAX_CHARS]
        if truncated_by_words or truncated_by_chars:
            title = title.rstrip(" .,:;!?-")
            max_len = cls._TITLE_MAX_CHARS - 3
            if max_len > 0 and len(title) > max_len:
                title = title[:max_len].rstrip(" .,:;!?-")
            title = f"{title}..."
        return title

    def _generate_smart_title(self, message: Optional[str], stream_callback=None) -> Optional[str]:
        """
        Generate an intelligent short title using LLM.
        Falls back to simple truncation on error.

        Args:
            message: User message to generate title from
            stream_callback: Optional callback function(delta: str) for streaming title chars
        """
        text = str(message or "").strip()
        if not text:
            return None

        try:
            llm_client = OpenAI(
                api_key=os.environ.get('LITELLM_API_KEY'),
                base_url=os.environ.get('LITELLM_BASE_URL')
            )

            # Always use default model for title generation (fast, reliable)
            model = 'mistralai/Mistral-Small-3.2-24B-Instruct-2506'

            messages = [
                {
                    "role": "system",
                    "content": "Generiere einen sehr kurzen Titel (2-4 Wörter) für diese Chat-Anfrage. "
                               "Antworte NUR mit dem Titel, keine Anführungszeichen, keine Erklärung. "
                               "Beispiele: Öffnungszeiten, Kontaktdaten, Preisanfrage, Technischer Support, Firmeninhaber"
                },
                {
                    "role": "user",
                    "content": text[:500]  # Limit input length
                }
            ]

            logger.debug(f"Generating title with model: {model}")

            # Stream if callback provided
            if stream_callback:
                title = ""
                stream = llm_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=20,
                    temperature=0.3,
                    timeout=10.0,
                    stream=True
                )
                for chunk in stream:
                    choice = chunk.choices[0] if chunk.choices else None
                    delta = getattr(choice, "delta", None) if choice else None
                    # Use extract_delta_text to handle reasoning_content (Magistral) and content
                    delta_text = extract_delta_text(delta)
                    if delta_text:
                        title += delta_text
                        stream_callback(delta_text)
            else:
                response = llm_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=20,
                    temperature=0.3,
                    timeout=10.0
                )
                # Use extract_message_text to handle reasoning_content (Magistral)
                title = extract_message_text(response.choices[0].message).strip()

            # Clean up: remove quotes, limit length
            title = title.strip('"\'„"»«')
            # Remove any trailing punctuation except ...
            title = re.sub(r'[.!?:;,]+$', '', title)
            if len(title) > self._TITLE_MAX_CHARS:
                title = title[:self._TITLE_MAX_CHARS - 3].rstrip(" .,:;!?-") + "..."

            if title:
                logger.info(f"Generated smart title: '{title}' for message: '{text[:50]}...'")
                return title
            else:
                logger.warning(f"Smart title generation returned empty result, using fallback for: '{text[:50]}...'")

        except Exception as e:
            logger.warning(f"Smart title generation failed, using fallback: {e}")

        # Fallback to simple title extraction
        return self._build_title_from_message(message)

    def _maybe_set_conversation_title(self, conversation: ChatbotConversation, message: Optional[str]) -> bool:
        if not self._is_placeholder_title(conversation.title):
            return False
        title = self._generate_smart_title(message)
        if not title:
            return False
        conversation.title = title
        return True

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

    def _requires_sources(self) -> bool:
        if not (self.chatbot.rag_enabled and self.chatbot.collections):
            return False
        settings = self._get_prompt_settings()
        require_citations = bool(getattr(settings, 'rag_require_citations', True))
        if not require_citations:
            return False
        # Allow the default LLARS assistant to answer system questions without RAG sources.
        if self.chatbot.name == 'standard_admin':
            return False
        return True

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
        if self._requires_sources() and not sources and not files:
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
            self._maybe_set_conversation_title(conversation, message)
            db.session.commit()

            return {
                'response': response_text,
                'sources': [],
                'conversation_id': conversation.id,
                'session_id': session_id,
                'title': conversation.title,
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
        self._maybe_set_conversation_title(conversation, message)
        db.session.commit()

        return {
            'response': response_text,
            'sources': sources_to_save if include_sources else [],
            'conversation_id': conversation.id,
            'session_id': session_id,
            'title': conversation.title,
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

        if self._requires_sources() and not sources:
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

        if self._requires_sources() and not sources:
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
            # Build completion kwargs, only include max_tokens if explicitly set
            completion_kwargs = {
                "model": self.chatbot.model_name,
                "messages": messages,
                "temperature": self.chatbot.temperature,
                "top_p": self.chatbot.top_p,
                "stream": True
            }
            if self.chatbot.max_tokens:
                completion_kwargs["max_tokens"] = self.chatbot.max_tokens

            stream = self.llm_client.chat.completions.create(**completion_kwargs)

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
        """
        Extract and expand lexical tokens from query for BM25 search.

        Includes:
        - Stopword filtering
        - Compound word splitting (German: "Teamleiter" -> "team" + "leiter")
        - Synonym expansion (e.g., "inhaber" -> ["impressum", "betreiber", ...])
        """
        tokens = [t.lower() for t in self._TOKEN_RE.findall(query or '')]
        tokens = [t for t in tokens if len(t) >= 3 and t not in self._STOPWORDS_DE]
        if not tokens:
            # Fallback for short terms (e.g. AI, HR, IT) that are still meaningful.
            tokens = [t for t in self._TOKEN_RE.findall(query or '') if len(t) >= 2]
            tokens = [t.lower() for t in tokens if t.lower() not in self._STOPWORDS_DE]
        if tokens:
            expanded = []
            for token in tokens:
                expanded.append(token)

                # Compound word expansion
                if "team" in token and token != "team":
                    expanded.append("team")
                for suffix in self._COMPOUND_SUFFIXES:
                    if token.endswith(suffix) and len(token) > len(suffix) + 2:
                        prefix = token[:-len(suffix)]
                        if len(prefix) >= 3:
                            expanded.append(prefix)
                        expanded.append(suffix)

                # Synonym expansion for better recall
                if token in self._QUERY_SYNONYMS:
                    for synonym in self._QUERY_SYNONYMS[token]:
                        expanded.append(synonym)

            tokens = expanded
        # De-duplicate while keeping order
        seen = set()
        unique: List[str] = []
        for t in tokens:
            if t in seen:
                continue
            seen.add(t)
            unique.append(t)
        # Allow more tokens when synonyms are added
        return unique[:10]

    def _lexical_search_collection(self, collection: RAGCollection, query: str, tokens: List[str], limit: int) -> List[Dict[str, Any]]:
        if not collection or not tokens:
            return []

        try:
            from services.chatbot.lexical_index import LexicalSearchIndex
            results = LexicalSearchIndex.search(query, [collection.id], limit=limit)
            if results:
                for r in results:
                    r['collection_id'] = collection.id
                    if isinstance(r.get('metadata'), dict):
                        r['metadata']['collection_id'] = collection.id
                return results
        except Exception as exc:
            logger.debug(f"[ChatService] Lexical FTS fallback for collection {collection.id}: {exc}")

        from sqlalchemy import or_, and_
        from db.tables import CollectionDocumentLink

        chunk_clauses = [RAGDocumentChunk.content.ilike(f"%{t}%") for t in tokens]
        if not chunk_clauses:
            return []
        doc_meta_clauses = [
            RAGDocument.title.ilike(f"%{t}%") for t in tokens
        ] + [
            RAGDocument.description.ilike(f"%{t}%") for t in tokens
        ] + [
            RAGDocument.filename.ilike(f"%{t}%") for t in tokens
        ] + [
            RAGDocument.original_filename.ilike(f"%{t}%") for t in tokens
        ]

        chunk_match = or_(*chunk_clauses)
        if doc_meta_clauses:
            meta_match = or_(*doc_meta_clauses)
            match_clause = or_(chunk_match, and_(meta_match, RAGDocumentChunk.chunk_index == 0))
        else:
            match_clause = chunk_match

        rows = (
            db.session.query(RAGDocumentChunk, RAGDocument)
            .join(RAGDocument, RAGDocument.id == RAGDocumentChunk.document_id)
            .outerjoin(
                CollectionDocumentLink,
                and_(
                    CollectionDocumentLink.document_id == RAGDocument.id,
                    CollectionDocumentLink.collection_id == collection.id
                )
            )
            .filter(
                or_(
                    CollectionDocumentLink.id.isnot(None),
                    RAGDocument.collection_id == collection.id
                )
            )
            .filter(match_clause)
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
        Retrieve context from multiple collections using semantic (vector) search.

        Pure RAG retrieval - lexical search is only available in Agent/ACT mode.

        Returns:
            Tuple of (context_string, sources_list)
        """
        if not self.rag_pipeline:
            return "", []

        final_k = max(1, int(self.chatbot.rag_retrieval_k or 4))
        # Fetch more candidates for reranking - cross-encoder can surface relevant docs
        # that have lower vector scores but higher semantic relevance
        candidate_k = max(final_k * 8, 32)

        # ═══════════════════════════════════════════════════════════════════
        # Semantic (Vector) Search Only
        # ═══════════════════════════════════════════════════════════════════

        all_results: List[Dict[str, Any]] = []

        for cc in sorted(self.chatbot.collections, key=lambda x: -x.priority):
            collection = cc.collection
            try:
                results = self._search_collection(collection, query, k=candidate_k)
                for result in results:
                    result['score'] *= cc.weight
                    result['collection_id'] = collection.id
                    result['collection_name'] = collection.display_name
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Error searching collection {collection.name}: {e}")

        if not all_results:
            logger.warning(
                f"[ChatService] No RAG results for chatbot {self.chatbot.id} "
                f"(query='{query[:50]}...') using model "
                f"{self.rag_pipeline.model_name if self.rag_pipeline else 'none'}"
            )
            return "", []

        # Sort by semantic score (higher = better)
        all_results.sort(key=lambda x: x['score'], reverse=True)

        logger.info(
            f"[ChatService] Semantic search: {len(all_results)} results for chatbot {self.chatbot.id}"
        )

        # Use all_results directly (renamed from fused_results for compatibility below)
        fused_results = all_results

        # ═══════════════════════════════════════════════════════════════════
        # Filter and Rerank
        # ═══════════════════════════════════════════════════════════════════

        # Take top candidates
        filtered_results = fused_results[:candidate_k]

        # Log top candidates before filtering
        logger.info(f"[ChatService] Top {len(filtered_results)} candidates before relevance filter:")
        for i, r in enumerate(filtered_results[:10]):
            doc_id = r.get('document_id')
            title = r.get('title', 'Unknown')[:40]
            score = r.get('score', 0)
            logger.info(f"[ChatService]   {i+1}. score={score:.4f} doc_id={doc_id} | {title}")

        # Filter by minimum relevance
        min_relevance = self.chatbot.rag_min_relevance
        relevance_filtered = [
            r for r in filtered_results
            if r.get('score', 0) >= min_relevance
        ]

        # If nothing passes minimum, keep best results anyway
        if not relevance_filtered:
            relevance_filtered = filtered_results[:final_k]

        filtered_results = relevance_filtered

        # Optional reranking - use chatbot-specific setting
        try:
            from services.rag.reranker import rerank_results
            settings = self._get_prompt_settings()
            use_cross_encoder = getattr(settings, 'rag_use_cross_encoder', True) if settings else True
            logger.info(f"[ChatService] Reranking {len(filtered_results)} results (cross_encoder={use_cross_encoder})")
            filtered_results = rerank_results(query, filtered_results, use_cross_encoder=use_cross_encoder)
        except Exception as e:
            logger.warning(f"[ChatService] Reranking failed: {e}")

        use_vision = FileProcessor.is_vision_model(self.chatbot.model_name)
        logger.info(f"[ChatService] Vision check: model={self.chatbot.model_name}, use_vision={use_vision}")

        # Count image results before filtering
        image_count_before = sum(1 for r in filtered_results if (r.get('metadata') or {}).get('has_image'))
        logger.info(f"[ChatService] Results before filter: total={len(filtered_results)}, images={image_count_before}")

        if not use_vision:
            filtered_results = [
                r for r in filtered_results
                if not (r.get('metadata') or {}).get('has_image')
            ]
            logger.info(f"[ChatService] After image filter (non-vision): {len(filtered_results)} results")

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
                'screenshot_url': screenshot_url,
                'has_image': bool(metadata.get('has_image')),
                'image_path': metadata.get('image_path'),
                'image_url': metadata.get('image_url'),
                'image_alt_text': metadata.get('image_alt_text'),
                'image_mime_type': metadata.get('image_mime_type')
            })

        context = "\n\n---\n\n".join(context_parts)

        return context, sources

    def _resolve_collection_embedding_model(self, collection: RAGCollection) -> Optional[str]:
        model = (collection.embedding_model or "").strip() if collection else ""
        chunk_model = None

        try:
            chunk_model = (
                db.session.query(RAGDocumentChunk.embedding_model)
                .join(RAGDocument, RAGDocumentChunk.document_id == RAGDocument.id)
                .join(CollectionDocumentLink, CollectionDocumentLink.document_id == RAGDocument.id)
                .filter(
                    CollectionDocumentLink.collection_id == collection.id,
                    RAGDocumentChunk.embedding_model.isnot(None)
                )
                .order_by(RAGDocumentChunk.id.desc())
                .limit(1)
                .scalar()
            )
        except Exception as e:
            logger.debug(f"[ChatService] Could not infer embedding model for collection {collection.id}: {e}")

        if chunk_model:
            chunk_model = str(chunk_model).strip()

        if chunk_model and chunk_model != model:
            collection.embedding_model = chunk_model
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
            model = chunk_model

        if not model and self.rag_pipeline:
            model = self.rag_pipeline.model_name

        return model or None

    # Class-level cache for embeddings per model
    _embeddings_cache: Dict[str, Any] = {}

    @classmethod
    def _get_embeddings_for_model(cls, model_id: str):
        """
        Get embeddings for a specific model with caching.

        Strategy:
        1. Models available via LiteLLM/KIZ (e.g., VDR-2B) -> try API first, fallback to local
        2. Local-only models (sentence-transformers) -> use HuggingFace directly
        3. Other models -> try LiteLLM, fallback to local
        """
        if model_id in cls._embeddings_cache:
            return cls._embeddings_cache[model_id]

        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_openai import OpenAIEmbeddings

        def try_huggingface_local(mid: str):
            """Try loading model locally via HuggingFace."""
            try:
                # For models with custom code (like llamaindex/vdr-2b-multi-v1),
                # add model cache dir to sys.path so custom modules can be imported
                import sys
                cache_dirs = [
                    os.path.expanduser("~/.cache/huggingface/hub"),
                    "/app/storage/models"
                ]
                for cache_dir in cache_dirs:
                    if os.path.exists(cache_dir):
                        for root, dirs, files in os.walk(cache_dir):
                            if 'custom_st.py' in files and root not in sys.path:
                                logger.info(f"Adding custom module path: {root}")
                                sys.path.insert(0, root)

                embeddings = HuggingFaceEmbeddings(
                    model_name=mid,
                    model_kwargs={"device": "cpu", "trust_remote_code": True},
                    encode_kwargs={"normalize_embeddings": True},
                    cache_folder="/app/storage/models"
                )
                cls._embeddings_cache[mid] = embeddings
                logger.info(f"[ChatService] Loaded HuggingFace embeddings locally for {mid}")
                return embeddings
            except Exception as e:
                logger.warning(f"[ChatService] Failed to load HuggingFace embeddings locally for {mid}: {e}")
                return None

        def try_litellm(mid: str):
            """Try loading model via LiteLLM/KIZ API.

            IMPORTANT: For VDR-2B multimodal model, we use LiteLLMDirectEmbeddings
            instead of langchain's OpenAIEmbeddings. This ensures consistency with
            how images are embedded (both use direct HTTP requests).
            """
            litellm_api_key = os.environ.get("LITELLM_API_KEY")
            litellm_base_url = os.environ.get("LITELLM_BASE_URL")

            if not litellm_api_key or not litellm_base_url:
                return None

            # For VDR-2B multimodal model, use direct HTTP embeddings for consistency with images
            if mid == "llamaindex/vdr-2b-multi-v1":
                try:
                    from services.rag.image_embedding_service import LiteLLMDirectEmbeddings

                    logger.info(f"[ChatService] Using LiteLLMDirectEmbeddings for {mid} (multimodal consistency)")
                    embeddings = LiteLLMDirectEmbeddings(model=mid)
                    test_result = embeddings.embed_query("test")
                    if test_result and len(test_result) > 0:
                        cls._embeddings_cache[mid] = embeddings
                        logger.info(f"[ChatService] LiteLLMDirectEmbeddings ready for {mid} (dims={len(test_result)})")
                        return embeddings
                except Exception as e:
                    logger.warning(f"[ChatService] LiteLLMDirectEmbeddings failed for {mid}: {e}")
                    # Fall through to try OpenAIEmbeddings as backup

            # For other models, use langchain's OpenAIEmbeddings
            try:
                embeddings = OpenAIEmbeddings(
                    model=mid,
                    openai_api_key=litellm_api_key,
                    openai_api_base=litellm_base_url
                )
                # Test that it actually works by embedding a short text
                test_result = embeddings.embed_query("test")
                if test_result and len(test_result) > 0:
                    cls._embeddings_cache[mid] = embeddings
                    logger.info(f"[ChatService] Loaded embeddings via LiteLLM for {mid} (dims={len(test_result)})")
                    return embeddings
                else:
                    logger.warning(f"[ChatService] LiteLLM returned empty embeddings for {mid}")
                    return None
            except Exception as e:
                logger.warning(f"[ChatService] LiteLLM embeddings failed for {mid}: {e}")
                return None

        # Models that are available via LiteLLM/KIZ - try API first
        litellm_embedding_models = ["llamaindex/vdr-2b-multi-v1"]

        # Models that should only be loaded locally (no API available)
        local_only_models = model_id.startswith("sentence-transformers/") or "sentence-transformers" in model_id

        # Strategy 1: Local-only models -> HuggingFace directly
        if local_only_models:
            return try_huggingface_local(model_id)

        # Strategy 2: Models available via LiteLLM -> try API first, then local
        if model_id in litellm_embedding_models:
            embeddings = try_litellm(model_id)
            if embeddings:
                return embeddings
            logger.info(f"[ChatService] LiteLLM unavailable for {model_id}, trying local HuggingFace")
            return try_huggingface_local(model_id)

        # Strategy 3: Other models -> try LiteLLM, then local
        embeddings = try_litellm(model_id)
        if embeddings:
            return embeddings
        return try_huggingface_local(model_id)

    def _search_collection(
        self,
        collection: RAGCollection,
        query: str,
        k: int = 4
    ) -> List[Dict]:
        """
        Search a specific collection using ChromaDB.

        Uses the new CollectionEmbedding table to find the best available
        embedding for this collection. This ensures:
        1. Query embeddings ALWAYS match document embeddings (dimension compatibility)
        2. Robust fallback: if preferred model unavailable, use alternate stored embeddings
        3. Clear error messages if no compatible embedding is available
        """
        from langchain_chroma import Chroma
        from services.rag.collection_embedding_service import sanitize_chroma_collection_name
        from services.rag.embedding_model_service import get_best_embedding_for_collection

        # CRITICAL: Use get_best_embedding_for_collection which checks:
        # 1. CollectionEmbedding table for stored embeddings with available models
        # 2. Collection's configured embedding_model
        # 3. Ensures model availability before returning
        embeddings, model_id, chroma_collection_name, dimensions = get_best_embedding_for_collection(
            collection.id
        )

        if embeddings is None:
            # Fallback to legacy method for collections without CollectionEmbedding records
            collection_model = self._resolve_collection_embedding_model(collection) or "sentence-transformers/all-MiniLM-L6-v2"
            embeddings = self._get_embeddings_for_model(collection_model)
            model_id = collection_model
            chroma_collection_name = collection.chroma_collection_name

            if embeddings is None:
                logger.error(
                    f"[ChatService] Could not load any embedding model for collection {collection.id}. "
                    f"RAG retrieval will fail. Please ensure a model is available or re-embed the collection."
                )
                return []

        vectorstore_dir = os.path.join(
            "/app/storage/vectorstore",
            model_id.replace('/', '_')
        )

        try:
            collection_name = chroma_collection_name
            if not collection_name:
                collection_name = sanitize_chroma_collection_name(collection.name, model_id)
                collection.chroma_collection_name = collection_name
                try:
                    db.session.commit()
                except Exception:
                    db.session.rollback()

            logger.debug(f"[ChatService] Searching collection {collection.id} with model {model_id}, chroma={collection_name}")

            vectorstore = Chroma(
                collection_name=collection_name,
                persist_directory=vectorstore_dir,
                embedding_function=embeddings,
                collection_metadata=CHROMA_COLLECTION_METADATA,
            )

            # Perform similarity search with scores
            docs_with_scores = vectorstore.similarity_search_with_score(query, k=k)

            if not docs_with_scores and collection.chroma_collection_name:
                fallback_name = sanitize_chroma_collection_name(collection.name, model_id)
                if fallback_name != collection_name:
                    vectorstore = Chroma(
                        collection_name=fallback_name,
                        persist_directory=vectorstore_dir,
                        embedding_function=embeddings,
                        collection_metadata=CHROMA_COLLECTION_METADATA,
                    )
                    docs_with_scores = vectorstore.similarity_search_with_score(query, k=k)
                    if docs_with_scores:
                        collection.chroma_collection_name = fallback_name
                        try:
                            db.session.commit()
                        except Exception:
                            db.session.rollback()

            results = []
            img_count = sum(1 for d, _ in docs_with_scores if (d.metadata or {}).get('has_image'))
            logger.info(f"[ChatService] _search_collection: Got {len(docs_with_scores)} docs, {img_count} are images")

            for i, (doc, score) in enumerate(docs_with_scores):
                # Get document info from metadata
                metadata = doc.metadata or {}
                if i < 5:  # Log first 5 for debugging
                    logger.info(f"[ChatService] Doc[{i}]: has_image={metadata.get('has_image')}, score={score:.4f}")
                doc_id = metadata.get('document_id')
                filename = metadata.get('filename') or metadata.get('source')
                title = metadata.get('title') or filename or 'Unbekannt'

                if doc_id and (not title or title == 'Unbekannt'):
                    db_doc = RAGDocument.query.get(doc_id)
                    if db_doc:
                        filename = db_doc.filename or filename
                        title = db_doc.title or db_doc.original_filename or filename or title

                # Convert cosine distance to cosine similarity
                # ChromaDB with hnsw:space=cosine returns cosine distance = 1 - cosine_similarity
                # Therefore: cosine_similarity = 1 - cosine_distance
                # Clamp to [0, 1] to handle any numerical edge cases
                similarity = max(0.0, min(1.0, 1 - score))

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
        use_vision = FileProcessor.is_vision_model(self.chatbot.model_name)
        rag_images = []
        if use_vision and sources:
            import os
            seen_paths = set()
            for source in sources:
                if not source.get('has_image'):
                    continue
                image_path = source.get('image_path')
                if not image_path or image_path in seen_paths:
                    continue
                seen_paths.add(image_path)
                try:
                    with open(image_path, 'rb') as f:
                        processed = file_processor.process_file(
                            f.read(),
                            os.path.basename(image_path),
                            model_name=self.chatbot.model_name
                        )
                    if processed.get('type') == 'image' and processed.get('image_data'):
                        rag_images.append(processed)
                except Exception as e:
                    logger.debug(f"[ChatService] Failed to load RAG image {image_path}: {e}")

        user_images = []
        if files:
            user_images = [
                f for f in files
                if f.get('type') == 'image' and f.get('image_data')
            ]

        if use_vision and (rag_images or user_images):
            user_content = []

            if rag_images:
                user_content.append({
                    "type": "text",
                    "text": "Kontextbilder aus der Wissensbasis:"
                })
                for img in rag_images:
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{img.get('mime_type', 'image/jpeg')};base64,{img['image_data']}"
                        }
                    })

            if user_images:
                if rag_images:
                    user_content.append({
                        "type": "text",
                        "text": "Vom Nutzer hochgeladene Bilder:"
                    })
                for img in user_images:
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{img.get('mime_type', 'image/jpeg')};base64,{img['image_data']}"
                        }
                    })

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
            # Build completion kwargs, only include max_tokens if explicitly set
            completion_kwargs = {
                "model": self.chatbot.model_name,
                "messages": messages,
                "temperature": self.chatbot.temperature,
                "top_p": self.chatbot.top_p
            }

            max_tokens = self.chatbot.max_tokens
            if max_tokens:
                model_info = FileProcessor.get_model_info(self.chatbot.model_name)
                if model_info and model_info.get("supports_reasoning"):
                    max_tokens = None
            if max_tokens:
                completion_kwargs["max_tokens"] = max_tokens

            response = self.llm_client.chat.completions.create(**completion_kwargs)

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
