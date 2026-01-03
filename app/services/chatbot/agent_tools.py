# agent_tools.py
"""
Agent Tool Execution Module.

Provides tool execution for agent chat modes (ACT, ReAct, ReflAct).
Tools: rag_search, lexical_search, web_search, respond
"""

import logging
import os
from typing import List, Dict, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from services.chatbot.agent_chat_service import AgentChatService

logger = logging.getLogger(__name__)


class AgentToolExecutor:
    """
    Executes agent tools and returns results with sources.

    This class encapsulates tool execution logic to keep the main
    AgentChatService focused on orchestration.
    """

    def __init__(self, service: "AgentChatService"):
        """
        Initialize with reference to parent service.

        Args:
            service: The AgentChatService instance
        """
        self._service = service

    @property
    def chatbot(self):
        return self._service.chatbot

    @property
    def _prompt_settings(self):
        return self._service._prompt_settings

    def execute_tool(
        self,
        action: str,
        param: str,
        original_query: str,
        enabled_tools: List[str]
    ) -> Tuple[str, List[Dict]]:
        """
        Execute a tool and return result with sources.

        Args:
            action: Tool name to execute
            param: Tool parameter
            original_query: Original user query (fallback for param)
            enabled_tools: List of enabled tool names

        Returns:
            Tuple of (result_text, sources_list)
        """
        if action == "rag_search" and "rag_search" in enabled_tools:
            return self.tool_rag_search(param or original_query)

        elif action == "lexical_search" and "lexical_search" in enabled_tools:
            return self.tool_lexical_search(param or original_query)

        elif action == "web_search" and "web_search" in enabled_tools:
            if self._service.is_web_search_enabled():
                return self.tool_web_search(param or original_query)
            return "Web-Suche ist nicht aktiviert.", []

        elif action == "respond":
            return param, []

        else:
            return f"Tool '{action}' ist nicht verfügbar oder nicht aktiviert.", []

    def tool_rag_search(self, query: str) -> Tuple[str, List[Dict]]:
        """
        Semantic RAG search - returns FULL content like standard RAG mode.

        Also calculates quality metrics for adaptive iteration:
        - avg_relevance: Average relevance score of returned documents
        - high_confidence: True if results are good enough for direct answer
        """
        if not self.chatbot.rag_enabled or not self.chatbot.collections:
            return "RAG ist für diesen Chatbot nicht aktiviert.", []

        context, sources = self._service._get_multi_collection_context(query)
        if sources:
            # Calculate quality metrics for adaptive iteration
            relevance_scores = [s.get('relevance', 0) for s in sources]
            avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
            top_relevance = max(relevance_scores) if relevance_scores else 0

            # High confidence if: top result > 0.75 OR average > 0.6 with 3+ results
            high_confidence = top_relevance > 0.75 or (avg_relevance > 0.6 and len(sources) >= 3)

            # Build result with FULL content (like standard RAG)
            result = f"Gefunden: {len(sources)} relevante Dokumente (Durchschnittliche Relevanz: {avg_relevance:.2f}).\n"
            if high_confidence:
                result += "HINWEIS: Hohe Konfidenz - diese Ergebnisse sollten ausreichen für eine Antwort.\n\n"
            else:
                result += "\n"

            for s in sources:
                footnote_id = s.get('footnote_id', '?')
                title = s.get('title', 'Unbekannt')
                relevance = s.get('relevance', 0)
                content = s.get('excerpt', '')
                collection = s.get('collection_name', '')

                result += f"[{footnote_id}] {title}"
                if collection:
                    result += f" (Collection: {collection})"
                result += f" [Relevanz: {relevance:.2f}]\n"
                result += f"{content}\n\n"
                result += "---\n\n"

            # Add metadata to sources for adaptive iteration
            for s in sources:
                s['_high_confidence'] = high_confidence
                s['_avg_relevance'] = avg_relevance

            return result, sources
        return "Keine relevanten Dokumente gefunden.", []

    def tool_lexical_search(self, query: str) -> Tuple[str, List[Dict]]:
        """
        Lexical (keyword) search - returns FULL content like standard RAG mode.

        Also calculates quality metrics for adaptive iteration.
        """
        if not self.chatbot.rag_enabled or not self.chatbot.collections:
            return "RAG ist für diesen Chatbot nicht aktiviert.", []

        tokens = self._service._extract_lexical_tokens(query)
        if not tokens:
            return "Keine aussagekräftigen Suchbegriffe gefunden.", []

        all_results = []
        for cc in self.chatbot.collections:
            collection = cc.collection
            if collection:
                results = self._service._lexical_search_collection(collection, query, tokens, limit=5)
                for r in results:
                    r['collection_name'] = collection.display_name
                all_results.extend(results)

        if all_results:
            sources = []
            # Lexical search has fewer quality signals, use result count as proxy
            high_confidence = len(all_results) >= 3

            result = f"Lexikalische Suche: {len(all_results)} Treffer für '{', '.join(tokens)}'.\n"
            if high_confidence:
                result += "HINWEIS: Mehrere relevante Treffer gefunden.\n\n"
            else:
                result += "\n"

            for i, r in enumerate(all_results[:5]):
                title = r.get('title', 'Unbekannt')
                content = r.get('content', '')
                collection_name = r.get('collection_name', '')

                sources.append({
                    'footnote_id': i + 1,
                    'title': title,
                    'excerpt': content,
                    'collection_name': collection_name,
                    '_high_confidence': high_confidence
                })

                result += f"[{i+1}] {title}"
                if collection_name:
                    result += f" (Collection: {collection_name})"
                result += f"\n{content}\n\n"
                result += "---\n\n"

            return result, sources

        return f"Keine Treffer für '{', '.join(tokens)}'.", []

    def tool_web_search(self, query: str) -> Tuple[str, List[Dict]]:
        """Web search using Tavily API."""
        api_key = self._service.get_tavily_api_key()
        if not api_key:
            return "Web-Suche ist nicht konfiguriert (kein API-Key).", []

        try:
            import requests
            max_results = 5
            if self._prompt_settings:
                max_results = getattr(self._prompt_settings, 'web_search_max_results', 5) or 5

            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": max_results,
                    "include_answer": True,
                    "include_raw_content": False
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            sources = []
            result = f"Web-Suche für '{query}':\n\n"

            if data.get("answer"):
                result += f"Zusammenfassung: {data['answer']}\n\n"

            for i, item in enumerate(data.get("results", [])[:max_results]):
                sources.append({
                    'footnote_id': i + 1,
                    'title': item.get('title', 'Web'),
                    'excerpt': item.get('content', '')[:300],
                    'url': item.get('url'),
                    'source_type': 'web'
                })
                result += f"[{i+1}] {item.get('title', 'Web')}\n{item.get('content', '')[:200]}...\nURL: {item.get('url')}\n\n"

            return result, sources

        except Exception as e:
            logger.error(f"[AgentToolExecutor] Web search failed: {e}")
            return f"Web-Suche fehlgeschlagen: {str(e)}", []


def check_high_confidence(sources: List[Dict]) -> bool:
    """
    Check if search results have high enough confidence for immediate answer.

    Returns True if the agent should generate a final answer immediately
    instead of continuing with more iterations.
    """
    if not sources:
        return False

    # Check for _high_confidence flag set by tool methods
    for s in sources:
        if s.get('_high_confidence'):
            return True

    # Fallback: check relevance scores directly
    relevance_scores = [s.get('relevance', 0) for s in sources if s.get('relevance')]
    if relevance_scores:
        avg_relevance = sum(relevance_scores) / len(relevance_scores)
        top_relevance = max(relevance_scores)
        return top_relevance > 0.75 or (avg_relevance > 0.6 and len(sources) >= 3)

    return False


def stream_preview_chunks(text: str, chunk_size: int = 80) -> List[str]:
    """Split text into chunks for streaming preview."""
    if not text:
        return []
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
