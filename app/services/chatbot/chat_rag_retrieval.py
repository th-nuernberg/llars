# chat_rag_retrieval.py
"""
Service for RAG retrieval operations including semantic search,
lexical search, embedding model management, and result reranking.
"""

import os
import re
import logging
from typing import List, Dict, Any, Tuple, Optional

from db.database import db
from db.tables import (
    RAGCollection,
    RAGDocument,
    RAGDocumentChunk,
    CollectionDocumentLink
)
from services.chatbot.file_processor import FileProcessor

logger = logging.getLogger(__name__)

# ChromaDB collection metadata for cosine distance
CHROMA_COLLECTION_METADATA = {"hnsw:space": "cosine"}


class ChatRAGRetrieval:
    """Service for RAG retrieval operations."""

    _TOKEN_RE = re.compile(r"[\wäöüÄÖÜß]+", re.UNICODE)
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

    # Class-level cache for embeddings per model
    _embeddings_cache: Dict[str, Any] = {}

    def __init__(self, chatbot, rag_pipeline=None):
        """
        Initialize RAG retrieval service.

        Args:
            chatbot: Chatbot model instance
            rag_pipeline: Optional RAGPipeline instance
        """
        self.chatbot = chatbot
        self.rag_pipeline = rag_pipeline

    def extract_lexical_tokens(self, query: str) -> List[str]:
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

    def lexical_search_collection(
        self,
        collection: RAGCollection,
        query: str,
        tokens: List[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Perform lexical search on a collection using FTS or SQL LIKE fallback.

        Args:
            collection: RAGCollection to search
            query: Original query string
            tokens: Extracted/expanded tokens
            limit: Maximum results

        Returns:
            List of result dicts with content, score, metadata
        """
        if not collection or not tokens:
            return []

        try:
            from services.chatbot.lexical_index import LexicalSearchIndex
            # Enrich query with expanded tokens
            enriched_query = " ".join(tokens)
            logger.debug(f"[ChatRAGRetrieval] Lexical search: original='{query}', enriched='{enriched_query}'")
            results = LexicalSearchIndex.search(enriched_query, [collection.id], limit=limit)
            if results:
                for r in results:
                    r['collection_id'] = collection.id
                    if isinstance(r.get('metadata'), dict):
                        r['metadata']['collection_id'] = collection.id
                return results
        except Exception as exc:
            logger.debug(f"[ChatRAGRetrieval] Lexical FTS fallback for collection {collection.id}: {exc}")

        # SQL LIKE fallback
        sql_results = self._lexical_search_sql_fallback(collection, tokens, limit)
        if sql_results:
            return sql_results

        # Last-resort fallback: search the raw document files when chunks are not
        # available yet or the vectorstore/index is out of sync with the DB.
        return self._lexical_search_file_fallback(collection, tokens, limit)

    def _lexical_search_sql_fallback(
        self,
        collection: RAGCollection,
        tokens: List[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """SQL LIKE-based lexical search fallback."""
        from sqlalchemy import or_, and_

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
                'score': 1.0,  # Lexical hits get high score for reranker
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

    def _lexical_search_file_fallback(
        self,
        collection: RAGCollection,
        tokens: List[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search raw document files when no chunks/index entries are available."""
        from sqlalchemy import and_, or_

        if not collection or not tokens:
            return []

        docs = (
            db.session.query(RAGDocument)
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
            .order_by(RAGDocument.uploaded_at.desc(), RAGDocument.id.desc())
            .limit(max(limit * 10, 40))
            .all()
        )

        results: List[Dict[str, Any]] = []
        lowered_tokens = [t.lower() for t in tokens if t]

        for doc in docs:
            text = self._read_document_file(doc.file_path)
            if not text:
                continue

            title = (
                doc.title
                or doc.original_filename
                or doc.filename
                or 'Unbekannt'
            )
            metadata_text = "\n".join(
                part for part in [
                    title,
                    doc.description or "",
                    doc.original_filename or "",
                    doc.filename or "",
                ] if part
            )
            searchable_text = f"{metadata_text}\n{text}"
            normalized_text = searchable_text.lower()

            matched_tokens = [token for token in lowered_tokens if token in normalized_text]
            if not matched_tokens:
                continue

            excerpt = self._extract_matching_excerpt(text, matched_tokens)
            score = min(1.0, len(set(matched_tokens)) / max(1, len(set(lowered_tokens))))

            results.append({
                'content': excerpt,
                'score': score,
                'document_id': doc.id,
                'title': title,
                'filename': doc.filename,
                'chunk_index': 0,
                'page_number': None,
                'start_char': None,
                'end_char': None,
                'vector_id': None,
                'metadata': {
                    'document_id': doc.id,
                    'filename': doc.filename,
                    'collection_id': collection.id,
                    'matched_tokens': matched_tokens,
                    'source': 'file_fallback',
                }
            })

        results.sort(
            key=lambda item: (
                float(item.get('score') or 0.0),
                len(item.get('content') or ""),
            ),
            reverse=True
        )
        return results[:limit]

    @staticmethod
    def _read_document_file(file_path: Optional[str]) -> str:
        """Read a raw document file for lexical fallback."""
        if not file_path or not os.path.exists(file_path):
            return ""
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                return handle.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="latin-1", errors="replace") as handle:
                    return handle.read()
            except Exception as exc:
                logger.debug(f"[ChatRAGRetrieval] Failed to read document file {file_path}: {exc}")
                return ""
        except Exception as exc:
            logger.debug(f"[ChatRAGRetrieval] Failed to read document file {file_path}: {exc}")
            return ""

    @staticmethod
    def _extract_matching_excerpt(text: str, tokens: List[str], window: int = 220) -> str:
        """Extract a short excerpt around the first token match."""
        if not text:
            return ""

        lower_text = text.lower()
        first_index = -1
        for token in tokens:
            idx = lower_text.find(token)
            if idx != -1 and (first_index == -1 or idx < first_index):
                first_index = idx

        if first_index == -1:
            excerpt = text[: window * 2]
            return excerpt.strip()

        start = max(0, first_index - window)
        end = min(len(text), first_index + window)
        excerpt = text[start:end].strip()
        if start > 0:
            excerpt = f"...{excerpt}"
        if end < len(text):
            excerpt = f"{excerpt}..."
        return excerpt

    def _lexical_fallback_search(self, query: str, final_k: int) -> List[Dict[str, Any]]:
        """Fallback retrieval path when semantic search returns no usable results."""
        tokens = self.extract_lexical_tokens(query)
        if not tokens:
            return []

        all_results: List[Dict[str, Any]] = []
        per_collection_limit = max(final_k * 2, 5)

        for cc in sorted(self.chatbot.collections, key=lambda x: -x.priority):
            collection = cc.collection
            if not collection:
                continue

            try:
                results = self.lexical_search_collection(collection, query, tokens, limit=per_collection_limit)
            except Exception as exc:
                logger.warning(
                    f"[ChatRAGRetrieval] Lexical fallback failed for collection {collection.id}: {exc}"
                )
                continue

            for result in results:
                result['score'] = float(result.get('score') or 0.0) * cc.weight
                result['collection_id'] = collection.id
                result['collection_name'] = collection.display_name
            all_results.extend(results)

        deduped: List[Dict[str, Any]] = []
        seen_keys = set()
        for result in sorted(all_results, key=lambda item: float(item.get('score') or 0.0), reverse=True):
            dedupe_key = (
                result.get('document_id'),
                result.get('chunk_index'),
                result.get('content'),
            )
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            deduped.append(result)

        if deduped:
            logger.info(
                f"[ChatRAGRetrieval] Using lexical fallback for chatbot {self.chatbot.id}: "
                f"{len(deduped)} results for query '{query[:50]}...'"
            )

        return deduped[:final_k]

    def get_multi_collection_context(self, query: str) -> Tuple[str, List[Dict]]:
        """
        Retrieve context from multiple collections using semantic (vector) search.

        Returns:
            Tuple of (context_string, sources_list)
        """
        if not self.rag_pipeline:
            return "", []

        final_k = max(1, int(self.chatbot.rag_retrieval_k or 8))
        candidate_k = max(final_k * 8, 32)

        # Semantic (Vector) Search
        all_results: List[Dict[str, Any]] = []

        for cc in sorted(self.chatbot.collections, key=lambda x: -x.priority):
            collection = cc.collection
            try:
                results = self.search_collection(collection, query, k=candidate_k)
                for result in results:
                    result['score'] *= cc.weight
                    result['collection_id'] = collection.id
                    result['collection_name'] = collection.display_name
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Error searching collection {collection.name}: {e}")

        if not all_results:
            lexical_results = self._lexical_fallback_search(query, final_k)
            if lexical_results:
                return self._build_context_and_sources(lexical_results)

            # Diagnose why both semantic and lexical retrieval came up empty.
            # The most common cause in production is an embedding-model
            # mismatch (collection embedded with model A, runtime only has
            # model B), and the second is no chunks reachable from the
            # collection. Log enough context to tell the two apart from a
            # single warning line.
            #
            # Chunks belong to documents, not collections directly, and a
            # document is reachable via either the explicit CollectionDocumentLink
            # (multi-collection case) or the legacy RAGDocument.collection_id
            # fk — the same OR clause as _lexical_search_sql_fallback above.
            from sqlalchemy import and_, or_
            collection_diag = []
            for cc in self.chatbot.collections or []:
                col = getattr(cc, 'collection', None)
                if not col:
                    continue
                try:
                    chunk_count = (
                        db.session.query(RAGDocumentChunk.id)
                        .join(RAGDocument, RAGDocument.id == RAGDocumentChunk.document_id)
                        .outerjoin(
                            CollectionDocumentLink,
                            and_(
                                CollectionDocumentLink.document_id == RAGDocument.id,
                                CollectionDocumentLink.collection_id == col.id,
                            ),
                        )
                        .filter(or_(
                            CollectionDocumentLink.id.isnot(None),
                            RAGDocument.collection_id == col.id,
                        ))
                        .count()
                    )
                except Exception as exc:
                    logger.debug(
                        "[ChatRAGRetrieval] chunk_count failed for collection %s: %s",
                        col.id, exc,
                    )
                    chunk_count = 'unknown'
                collection_diag.append({
                    'id': col.id,
                    'name': col.name,
                    'chroma_collection_name': getattr(col, 'chroma_collection_name', None),
                    'embedding_status': getattr(col, 'embedding_status', None),
                    'chunks': chunk_count,
                })
            logger.warning(
                "[ChatRAGRetrieval] No RAG results for chatbot=%s query=%r "
                "model=%s collections=%s",
                self.chatbot.id,
                query[:80],
                self.rag_pipeline.model_name if self.rag_pipeline else 'none',
                collection_diag,
            )
            return "", []

        # Sort by semantic score
        all_results.sort(key=lambda x: x['score'], reverse=True)

        logger.info(f"[ChatRAGRetrieval] Semantic search: {len(all_results)} results for chatbot {self.chatbot.id}")

        # Filter and Rerank
        filtered_results = all_results[:candidate_k]

        # Log top candidates
        logger.info(f"[ChatRAGRetrieval] Top {len(filtered_results)} candidates before relevance filter:")
        for i, r in enumerate(filtered_results[:10]):
            doc_id = r.get('document_id')
            title = r.get('title', 'Unknown')[:40]
            score = r.get('score', 0)
            logger.info(f"[ChatRAGRetrieval]   {i+1}. score={score:.4f} doc_id={doc_id} | {title}")

        # Filter by minimum relevance
        min_relevance = self.chatbot.rag_min_relevance
        relevance_filtered = [r for r in filtered_results if r.get('score', 0) >= min_relevance]

        if not relevance_filtered:
            relevance_filtered = filtered_results[:final_k]

        filtered_results = relevance_filtered

        # Optional reranking
        try:
            from services.rag.reranker import rerank_results
            use_cross_encoder = getattr(self.chatbot, 'rag_use_cross_encoder', True)
            reranker_model = getattr(self.chatbot, 'rag_reranker_model', None)
            logger.info(f"[ChatRAGRetrieval] Reranking {len(filtered_results)} results")
            filtered_results = rerank_results(
                query, filtered_results,
                use_cross_encoder=use_cross_encoder,
                model_name=reranker_model
            )
        except Exception as e:
            logger.warning(f"[ChatRAGRetrieval] Reranking failed: {e}")

        # Filter images for non-vision models
        use_vision = FileProcessor.is_vision_model(self.chatbot.model_name)
        if not use_vision:
            filtered_results = [
                r for r in filtered_results
                if not (r.get('metadata') or {}).get('has_image')
            ]

        filtered_results = filtered_results[:final_k]

        if not filtered_results:
            lexical_results = self._lexical_fallback_search(query, final_k)
            if lexical_results:
                return self._build_context_and_sources(lexical_results)

        # Build context and sources
        return self._build_context_and_sources(filtered_results)

    def _build_context_and_sources(
        self,
        results: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict]]:
        """Build context string and sources list from results."""
        context_parts = []
        sources = []

        for i, result in enumerate(results):
            context_parts.append(f"[Dokument {i+1}]\n{result['content']}")

            doc_id = result.get('document_id')
            metadata = result.get('metadata') or {}
            filename = metadata.get('filename') or metadata.get('source')
            title = result.get('title') or filename or 'Unbekannt'

            source_url = None
            screenshot_url = None

            if doc_id:
                doc = RAGDocument.query.get(doc_id)
                if doc:
                    filename = doc.filename or filename
                    title = doc.title or doc.original_filename or filename or title
                    source_url = doc.source_url
                    screenshot_url = doc.screenshot_url or (
                        f"/api/rag/documents/{doc_id}/screenshot" if doc.screenshot_path else None
                    )

            sources.append({
                'footnote_id': i + 1,
                'document_id': result.get('document_id'),
                'title': title,
                'filename': filename,
                'url': source_url,
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

    def search_collection(
        self,
        collection: RAGCollection,
        query: str,
        k: int = 4
    ) -> List[Dict]:
        """
        Search a specific collection using ChromaDB.

        Uses CollectionEmbedding table to find the best available embedding.
        """
        from langchain_chroma import Chroma
        from services.rag.collection_embedding_service import sanitize_chroma_collection_name
        from services.rag.embedding_model_service import get_best_embedding_for_collection

        # Get best embedding for collection
        embeddings, model_id, chroma_collection_name, dimensions = get_best_embedding_for_collection(
            collection.id
        )

        if embeddings is None:
            # Fallback to legacy method
            collection_model = self._resolve_collection_embedding_model(collection) or "sentence-transformers/all-MiniLM-L6-v2"
            embeddings = self._get_embeddings_for_model(collection_model)
            model_id = collection_model
            chroma_collection_name = collection.chroma_collection_name

            if embeddings is None:
                logger.error(
                    f"[ChatRAGRetrieval] Could not load any embedding model for collection {collection.id}."
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

            vectorstore = Chroma(
                collection_name=collection_name,
                persist_directory=vectorstore_dir,
                embedding_function=embeddings,
                collection_metadata=CHROMA_COLLECTION_METADATA,
            )

            # Perform similarity search with scores
            try:
                docs_with_scores = vectorstore.similarity_search_with_score(query, k=k)
            except Exception as search_err:
                if "page_content" in str(search_err) and "None" in str(search_err):
                    # Known LangChain/ChromaDB bug - try raw query
                    docs_with_scores = self._raw_chroma_query_fallback(
                        vectorstore, embeddings, query, k
                    )
                else:
                    raise

            # Try fallback collection name if no results
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

            return self._process_search_results(docs_with_scores)

        except Exception as e:
            logger.error(f"Error searching collection {collection.name}: {e}")
            return []

    def _raw_chroma_query_fallback(self, vectorstore, embeddings, query: str, k: int):
        """Fallback to raw ChromaDB query when LangChain fails."""
        try:
            raw_results = vectorstore._collection.query(
                query_embeddings=[embeddings.embed_query(query)],
                n_results=k,
                include=["documents", "metadatas", "distances"]
            )
            docs_with_scores = []
            if raw_results and raw_results.get("documents"):
                for i, doc_content in enumerate(raw_results["documents"][0]):
                    if doc_content is not None:
                        from langchain_core.documents import Document
                        metadata = raw_results["metadatas"][0][i] if raw_results.get("metadatas") else {}
                        distance = raw_results["distances"][0][i] if raw_results.get("distances") else 0.5
                        docs_with_scores.append((Document(page_content=doc_content, metadata=metadata), distance))
            return docs_with_scores
        except Exception as raw_err:
            logger.error(f"[ChatRAGRetrieval] Raw query recovery failed: {raw_err}")
            return []

    def _process_search_results(self, docs_with_scores) -> List[Dict]:
        """Process ChromaDB search results into standardized format."""
        results = []

        for doc, score in docs_with_scores:
            metadata = doc.metadata or {}
            doc_id = metadata.get('document_id')
            filename = metadata.get('filename') or metadata.get('source')
            title = metadata.get('title') or filename or 'Unbekannt'

            if doc_id and (not title or title == 'Unbekannt'):
                db_doc = RAGDocument.query.get(doc_id)
                if db_doc:
                    filename = db_doc.filename or filename
                    title = db_doc.title or db_doc.original_filename or filename or title

            # Convert cosine distance to similarity
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

    def _resolve_collection_embedding_model(self, collection: RAGCollection) -> Optional[str]:
        """Resolve the embedding model for a collection."""
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
            logger.debug(f"[ChatRAGRetrieval] Could not infer embedding model for collection {collection.id}: {e}")

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

    @classmethod
    def _get_embeddings_for_model(cls, model_id: str):
        """Get embeddings for a specific model with caching."""
        if model_id in cls._embeddings_cache:
            return cls._embeddings_cache[model_id]

        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_openai import OpenAIEmbeddings

        def try_huggingface_local(mid: str):
            """Try loading model locally via HuggingFace."""
            try:
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
                logger.info(f"[ChatRAGRetrieval] Loaded HuggingFace embeddings locally for {mid}")
                return embeddings
            except Exception as e:
                logger.warning(f"[ChatRAGRetrieval] Failed to load HuggingFace embeddings for {mid}: {e}")
                return None

        def try_litellm(mid: str):
            """Try loading model via LiteLLM/KIZ API."""
            litellm_api_key = os.environ.get("LITELLM_API_KEY")
            litellm_base_url = os.environ.get("LITELLM_BASE_URL")

            if not litellm_api_key or not litellm_base_url:
                return None

            # For VDR-2B multimodal model, use direct HTTP embeddings
            if mid == "llamaindex/vdr-2b-multi-v1":
                try:
                    from services.rag.image_embedding_service import LiteLLMDirectEmbeddings
                    embeddings = LiteLLMDirectEmbeddings(model=mid)
                    test_result = embeddings.embed_query("test")
                    if test_result and len(test_result) > 0:
                        cls._embeddings_cache[mid] = embeddings
                        logger.info(f"[ChatRAGRetrieval] LiteLLMDirectEmbeddings ready for {mid}")
                        return embeddings
                except Exception as e:
                    logger.warning(f"[ChatRAGRetrieval] LiteLLMDirectEmbeddings failed for {mid}: {e}")

            try:
                embeddings = OpenAIEmbeddings(
                    model=mid,
                    openai_api_key=litellm_api_key,
                    openai_api_base=litellm_base_url
                )
                test_result = embeddings.embed_query("test")
                if test_result and len(test_result) > 0:
                    cls._embeddings_cache[mid] = embeddings
                    logger.info(f"[ChatRAGRetrieval] Loaded embeddings via LiteLLM for {mid}")
                    return embeddings
            except Exception as e:
                logger.warning(f"[ChatRAGRetrieval] LiteLLM embeddings failed for {mid}: {e}")
            return None

        # Strategy selection
        litellm_models = ["llamaindex/vdr-2b-multi-v1"]
        local_only = model_id.startswith("sentence-transformers/") or "sentence-transformers" in model_id

        if local_only:
            return try_huggingface_local(model_id)

        if model_id in litellm_models:
            embeddings = try_litellm(model_id)
            if embeddings:
                return embeddings
            return try_huggingface_local(model_id)

        embeddings = try_litellm(model_id)
        if embeddings:
            return embeddings
        return try_huggingface_local(model_id)
