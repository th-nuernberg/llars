"""
Citation Service for AI Writing Assistant

Provides RAG-based citation finding and citation review functionality.
"""

import logging
import json
import hashlib
from typing import Optional, Dict, Any, List

from llm.litellm_client import LiteLLMClient
from .prompts import CITATION_REVIEW_SYSTEM_PROMPT, CITATION_REVIEW_USER_PROMPT

logger = logging.getLogger(__name__)


class CitationService:
    """Service for citation finding and review using RAG."""

    DEFAULT_LIMIT = 10
    DEFAULT_TEMPERATURE = 0.2

    def __init__(self, model: Optional[str] = None):
        """
        Initialize citation service.

        Args:
            model: Optional model override
        """
        self.llm_client = LiteLLMClient(model=model)
        self._chat_service = None  # Lazy-loaded for RAG search

    @property
    def chat_service(self):
        """Lazy-load ChatService for RAG search capabilities."""
        if self._chat_service is None:
            try:
                from services.chatbot.chat_service import ChatService
                self._chat_service = ChatService()
            except Exception as e:
                logger.warning(f"[CitationService] Could not load ChatService: {e}")
        return self._chat_service

    def find_citations(
        self,
        claim: str,
        context: str = "",
        collection_ids: Optional[List[int]] = None,
        limit: int = DEFAULT_LIMIT,
        format: str = "bibtex"
    ) -> Dict[str, Any]:
        """
        Find relevant citations for a claim using RAG.

        Args:
            claim: The claim/statement that needs a citation
            context: Surrounding text context
            collection_ids: List of RAG collection IDs to search
            limit: Maximum number of citations to return
            format: Citation format (bibtex, apa, mla)

        Returns:
            Dict with ranked citations
        """
        try:
            if not collection_ids:
                return {
                    "citations": [],
                    "message": "Keine Collections ausgewählt"
                }

            if not self.chat_service:
                return {
                    "citations": [],
                    "message": "RAG-Suche nicht verfügbar"
                }

            # Build search query from claim and context
            search_query = claim
            if context:
                search_query = f"{claim} {context[:200]}"

            # Search across collections using ChatService's RAG capabilities
            from db.tables import RAGCollection
            all_results = []
            for collection_id in collection_ids:
                try:
                    collection = RAGCollection.query.get(collection_id)
                    if not collection:
                        continue
                    results = self.chat_service._search_vectorstore(
                        query=search_query,
                        collection=collection,
                        k=limit
                    )
                    if results:
                        for doc, score in results:
                            result = {
                                'content': doc.page_content,
                                'metadata': doc.metadata,
                                'distance': 1 - score,  # Convert similarity to distance
                                'collection_id': collection_id
                            }
                            all_results.append(result)
                except Exception as e:
                    logger.warning(f"Search failed for collection {collection_id}: {e}")

            if not all_results:
                return {
                    "citations": [],
                    "message": "Keine passenden Quellen gefunden"
                }

            # Convert to citations
            citations = []
            for result in all_results[:limit]:
                citation = self._result_to_citation(result, format)
                if citation:
                    citations.append(citation)

            # Sort by relevance (distance, lower is better)
            citations.sort(key=lambda x: 1 - x.get('relevance', 0), reverse=True)

            return {
                "citations": citations[:limit]
            }

        except Exception as e:
            logger.error(f"[CitationService] Error finding citations: {e}")
            return {
                "citations": [],
                "error": str(e)
            }

    def review_citations(
        self,
        content: str
    ) -> Dict[str, Any]:
        """
        Review document for claims that need citations.

        Args:
            content: Full document content

        Returns:
            Dict with warnings and statistics
        """
        try:
            # Truncate if too long
            truncated = content[:10000]

            messages = [
                {"role": "system", "content": CITATION_REVIEW_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": CITATION_REVIEW_USER_PROMPT.format(content=truncated)
                }
            ]

            response = self.llm_client.complete(
                messages=messages,
                temperature=self.DEFAULT_TEMPERATURE,
                max_tokens=2000
            )

            if not response:
                return {
                    "warnings": [],
                    "statistics": {"total_claims": 0, "cited": 0, "uncited": 0}
                }

            # Parse JSON response
            warnings = self._parse_review_response(response)

            # Calculate statistics
            uncited_count = len(warnings)
            # Estimate cited (look for \cite commands)
            import re
            cite_matches = re.findall(r'\\cite\{[^}]+\}', content)
            cited_count = len(cite_matches)

            return {
                "warnings": warnings,
                "statistics": {
                    "total_claims": uncited_count + cited_count,
                    "cited": cited_count,
                    "uncited": uncited_count
                }
            }

        except Exception as e:
            logger.error(f"[CitationService] Error reviewing citations: {e}")
            return {
                "warnings": [],
                "statistics": {"total_claims": 0, "cited": 0, "uncited": 0},
                "error": str(e)
            }

    def ignore_warning(
        self,
        document_id: int,
        text: str,
        user_id: int
    ) -> bool:
        """
        Mark a citation warning as ignored.

        Args:
            document_id: Document ID
            text: Warning text (hashed for storage)
            user_id: User who is ignoring

        Returns:
            Success status
        """
        try:
            from db.database import db
            from db.tables import AICitationIgnore

            text_hash = hashlib.sha256(text.encode()).hexdigest()[:64]

            ignore = AICitationIgnore(
                document_id=document_id,
                text_hash=text_hash,
                ignored_by=user_id
            )
            db.session.add(ignore)
            db.session.commit()
            return True

        except Exception as e:
            logger.error(f"[CitationService] Error ignoring warning: {e}")
            return False

    def get_ignored_warnings(
        self,
        document_id: int
    ) -> List[str]:
        """
        Get list of ignored warning hashes for a document.

        Args:
            document_id: Document ID

        Returns:
            List of text hashes
        """
        try:
            from db.tables import AICitationIgnore

            ignores = AICitationIgnore.query.filter_by(
                document_id=document_id
            ).all()

            return [i.text_hash for i in ignores]

        except Exception as e:
            logger.error(f"[CitationService] Error getting ignores: {e}")
            return []

    def _result_to_citation(
        self,
        result: Dict[str, Any],
        format: str
    ) -> Optional[Dict[str, Any]]:
        """
        Convert search result to citation format.

        Args:
            result: Search result dict
            format: Citation format

        Returns:
            Citation dict or None
        """
        try:
            metadata = result.get('metadata', {})

            # Extract citation info
            title = metadata.get('title', result.get('title', 'Unbekannter Titel'))
            authors = metadata.get('authors', metadata.get('author', 'Unbekannt'))
            if isinstance(authors, str):
                authors = [authors]
            year = metadata.get('year', metadata.get('date', '')[:4] if metadata.get('date') else '')
            source = metadata.get('source', metadata.get('url', ''))

            # Calculate relevance from distance
            distance = result.get('distance', 0.5)
            relevance = max(0, 1 - distance)

            # Generate BibTeX key
            author_part = authors[0].split()[-1].lower() if authors else 'unknown'
            bibtex_key = f"{author_part}{year}"

            # Format citation
            citation = {
                "relevance": round(relevance, 2),
                "title": title,
                "authors": authors,
                "year": year,
                "snippet": result.get('content', '')[:300],
                "collection_name": metadata.get('collection_name', ''),
                "source": source
            }

            # Add format-specific representation
            if format == 'bibtex':
                citation['bibtex'] = self._generate_bibtex(
                    bibtex_key, title, authors, year, source
                )
            elif format == 'apa':
                citation['formatted'] = self._format_apa(
                    title, authors, year, source
                )
            elif format == 'mla':
                citation['formatted'] = self._format_mla(
                    title, authors, year, source
                )

            return citation

        except Exception as e:
            logger.warning(f"Error converting result to citation: {e}")
            return None

    def _generate_bibtex(
        self,
        key: str,
        title: str,
        authors: List[str],
        year: str,
        source: str
    ) -> str:
        """Generate BibTeX entry."""
        author_str = ' and '.join(authors)
        return f"""@article{{{key},
  title = {{{title}}},
  author = {{{author_str}}},
  year = {{{year}}},
  url = {{{source}}}
}}"""

    def _format_apa(
        self,
        title: str,
        authors: List[str],
        year: str,
        source: str
    ) -> str:
        """Format citation in APA style."""
        author_str = ', '.join(authors[:-1])
        if len(authors) > 1:
            author_str += f', & {authors[-1]}'
        elif authors:
            author_str = authors[0]

        return f"{author_str} ({year}). {title}. {source}"

    def _format_mla(
        self,
        title: str,
        authors: List[str],
        year: str,
        source: str
    ) -> str:
        """Format citation in MLA style."""
        author_str = ', '.join(authors)
        return f'{author_str}. "{title}." {year}.'

    def _parse_review_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse the LLM review response.

        Args:
            response: LLM response text

        Returns:
            List of warning dicts
        """
        try:
            # Find JSON array in response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1

            if json_start >= 0 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
                if isinstance(data, list):
                    # Validate and normalize each warning
                    warnings = []
                    for item in data:
                        if isinstance(item, dict) and item.get('text'):
                            warnings.append({
                                "position": {
                                    "line": item.get('line', 0),
                                    "from": 0,
                                    "to": len(item.get('text', ''))
                                },
                                "text": item.get('text', ''),
                                "type": item.get('type', 'factual_claim'),
                                "severity": item.get('severity', 'medium'),
                                "reason": item.get('reason', '')
                            })
                    return warnings

            return []

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to parse review response: {e}")
            return []


# Singleton instance
_citation_service: Optional[CitationService] = None


def get_citation_service() -> CitationService:
    """Get or create singleton CitationService instance."""
    global _citation_service
    if _citation_service is None:
        _citation_service = CitationService()
    return _citation_service
