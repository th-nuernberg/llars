# agent_chat_service.py
"""
Agent Chat Service - Implements advanced LLM agent patterns.

Supports:
- Standard: Single-shot response (no reasoning)
- ACT: Action-only without explicit reasoning traces
- ReAct: Reasoning + Acting interleaved (Thought → Action → Observation)
- ReflAct: Goal-state reflection before each action

Task Types:
- Lookup: Simple fact retrieval (1-2 iterations)
- Multi-hop: Complex reasoning requiring multiple steps
"""

import os
import re
import json
import logging
import time
from typing import List, Dict, Any, Optional, Generator, Tuple
from openai import OpenAI

from db.db import db
from db.models.chatbot import Chatbot, ChatbotPromptSettings
from services.chatbot.chat_service import ChatService
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentChatService(ChatService):
    """
    Extended ChatService with agent reasoning patterns.
    """

    def __init__(self, chatbot_id: int):
        super().__init__(chatbot_id)
        self._prompt_settings = self._get_prompt_settings()

    def get_agent_mode(self) -> str:
        """Get the configured agent mode for this chatbot."""
        if self._prompt_settings:
            return getattr(self._prompt_settings, 'agent_mode', 'standard') or 'standard'
        return 'standard'

    def get_task_type(self) -> str:
        """Get the configured task type for this chatbot."""
        if self._prompt_settings:
            return getattr(self._prompt_settings, 'task_type', 'lookup') or 'lookup'
        return 'lookup'

    def get_max_iterations(self) -> int:
        """Get max iterations based on task type."""
        if self._prompt_settings:
            base = getattr(self._prompt_settings, 'agent_max_iterations', 5) or 5
        else:
            base = 5

        # Multi-hop tasks allow more iterations
        if self.get_task_type() == 'multihop':
            return min(base + 2, 10)
        return base

    def get_enabled_tools(self) -> List[str]:
        """Get list of enabled tools for agent modes."""
        if self._prompt_settings:
            tools = getattr(self._prompt_settings, 'tools_enabled', None)
            if tools:
                return tools if isinstance(tools, list) else list(tools)
        return ['rag_search', 'lexical_search', 'respond']

    def is_web_search_enabled(self) -> bool:
        """Check if web search is enabled."""
        if self._prompt_settings:
            return bool(getattr(self._prompt_settings, 'web_search_enabled', False))
        return False

    def get_tavily_api_key(self) -> Optional[str]:
        """Get Tavily API key if configured."""
        if self._prompt_settings:
            key = getattr(self._prompt_settings, 'tavily_api_key', None)
            return key if key else os.environ.get('TAVILY_API_KEY')
        return os.environ.get('TAVILY_API_KEY')

    # ==================== Agent Mode Implementations ====================

    def chat_agent(
        self,
        message: str,
        session_id: str,
        username: str = None,
        include_sources: bool = True,
        files: List[Dict[str, Any]] = None,
        conversation_id: Optional[int] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Main agent chat method - routes to appropriate mode.
        Yields status updates and final response.
        """
        mode = self.get_agent_mode()

        if mode == 'standard':
            # Standard mode - use parent class streaming
            yield from self._chat_standard_stream(message, session_id, username, include_sources, files, conversation_id)
        elif mode == 'act':
            yield from self._chat_act(message, session_id, username, include_sources, files, conversation_id)
        elif mode == 'react':
            yield from self._chat_react(message, session_id, username, include_sources, files, conversation_id)
        elif mode == 'reflact':
            yield from self._chat_reflact(message, session_id, username, include_sources, files, conversation_id)
        else:
            # Fallback to standard
            yield from self._chat_standard_stream(message, session_id, username, include_sources, files, conversation_id)

    def chat_agent_sync(
        self,
        message: str,
        session_id: str,
        username: str = None,
        include_sources: bool = True,
        files: List[Dict[str, Any]] = None,
        conversation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run agent chat synchronously and return the final result.
        Useful for REST fallback when streaming is not available.
        """
        start_time = time.time()
        final_event: Optional[Dict[str, Any]] = None

        for event in self.chat_agent(
            message=message,
            session_id=session_id,
            username=username,
            include_sources=include_sources,
            files=files,
            conversation_id=conversation_id
        ):
            if event.get("done"):
                final_event = event
                break

        response_time_ms = int((time.time() - start_time) * 1000)

        if not final_event:
            return {
                'response': self.get_unknown_answer(),
                'sources': [],
                'conversation_id': conversation_id,
                'session_id': session_id,
                'message_id': None,
                'tokens': {'input': 0, 'output': 0},
                'response_time_ms': response_time_ms,
                'mode': self.get_agent_mode(),
                'task_type': self.get_task_type(),
                'iterations': 0,
                'reasoning_steps': [],
                'files_processed': len(files) if files else 0
            }

        return {
            'response': final_event.get('full_response', ''),
            'sources': final_event.get('sources', []),
            'conversation_id': final_event.get('conversation_id'),
            'session_id': session_id,
            'message_id': final_event.get('message_id'),
            'tokens': {'input': 0, 'output': 0},
            'response_time_ms': response_time_ms,
            'mode': final_event.get('mode'),
            'task_type': self.get_task_type(),
            'iterations': final_event.get('iterations'),
            'reasoning_steps': final_event.get('reasoning_steps', []),
            'files_processed': len(files) if files else 0
        }

    def _chat_standard_stream(
        self,
        message: str,
        session_id: str,
        username: str = None,
        include_sources: bool = True,
        files: List[Dict[str, Any]] = None,
        conversation_id: Optional[int] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """Standard single-shot streaming response."""
        yield {"status": "starting", "mode": "standard"}

        # Get conversation
        conversation = self._get_or_create_conversation(session_id, username, conversation_id)
        from db.models.chatbot import ChatbotMessageRole
        self._save_message(conversation.id, ChatbotMessageRole.USER, message)

        # Get RAG context
        rag_context = ""
        sources = []
        retrieval_time_ms = None
        if self.chatbot.rag_enabled and self.chatbot.collections:
            retrieval_start = time.time()
            rag_context, sources = self._get_multi_collection_context(message)
            retrieval_time_ms = int((time.time() - retrieval_start) * 1000)

        yield {"status": "context_retrieved", "sources_count": len(sources)}

        # Build messages
        messages = self._build_messages(conversation, message, rag_context, files, sources=sources)

        # Stream response
        yield {"status": "generating"}

        accumulated = ""
        try:
            stream = self.llm_client.chat.completions.create(
                model=self.chatbot.model_name,
                messages=messages,
                temperature=self.chatbot.temperature,
                max_tokens=self.chatbot.max_tokens,
                top_p=self.chatbot.top_p,
                stream=True
            )

            for chunk in stream:
                choice = chunk.choices[0] if chunk.choices else None
                delta = getattr(choice, "delta", None) if choice else None
                if delta and hasattr(delta, 'content') and delta.content:
                    accumulated += delta.content
                    yield {"delta": delta.content}

        except Exception as e:
            logger.error(f"[AgentChatService] Standard streaming failed: {e}")
            yield {"error": str(e)}
            return

        # Save response
        msg = self._save_message(
            conversation.id,
            ChatbotMessageRole.ASSISTANT,
            accumulated,
            rag_sources=sources if include_sources else [],
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

        yield {
            "done": True,
            "full_response": accumulated,
            "sources": sources if include_sources else [],
            "mode": "standard",
            "conversation_id": conversation.id,
            "message_id": msg.id
        }

    def _chat_act(
        self,
        message: str,
        session_id: str,
        username: str = None,
        include_sources: bool = True,
        files: List[Dict[str, Any]] = None,
        conversation_id: Optional[int] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        ACT mode - Action-only without explicit reasoning.
        Faster but less interpretable.
        """
        yield {"status": "starting", "mode": "act"}

        conversation = self._get_or_create_conversation(session_id, username, conversation_id)
        from db.models.chatbot import ChatbotMessageRole
        self._save_message(conversation.id, ChatbotMessageRole.USER, message)

        max_iterations = self.get_max_iterations()
        all_sources = []
        observations = []
        reasoning_steps = []

        system_prompt = self._get_act_system_prompt()

        for iteration in range(max_iterations):
            yield {"status": "iteration", "iteration": iteration + 1, "max": max_iterations}

            # Build messages with observations
            messages = [{"role": "system", "content": system_prompt}]
            messages.append({"role": "user", "content": message})

            for obs in observations:
                messages.append({"role": "assistant", "content": obs["action"]})
                messages.append({"role": "user", "content": f"OBSERVATION: {obs['result']}"})

            # Get action from LLM
            yield {"status": "getting_action", "iteration": iteration + 1}
            action_text = self._call_llm_sync(messages)

            # Parse action
            action, param = self._parse_action(action_text)
            yield {"status": "action", "action": action, "param": param, "iteration": iteration + 1}
            action_content = f'{action}("{param}")' if param else action
            reasoning_steps.append({
                "type": "action",
                "action": action,
                "param": param,
                "content": action_content
            })

            # Execute action
            if action == "respond":
                # Final answer
                yield {"status": "final_answer"}
                final_response = param

                msg = self._save_message(
                    conversation.id,
                    ChatbotMessageRole.ASSISTANT,
                    final_response,
                    rag_sources=all_sources if include_sources else [],
                    agent_trace=reasoning_steps,
                    stream_metadata={
                        "mode": "act",
                        "iterations": iteration + 1,
                        "sources_count": len(all_sources)
                    }
                )

                conversation.message_count += 2
                conversation.last_message_at = datetime.now()
                if not conversation.title and len(message) > 0:
                    conversation.title = message[:50] + ('...' if len(message) > 50 else '')
                db.session.commit()

                yield {
                    "done": True,
                    "full_response": final_response,
                    "sources": all_sources if include_sources else [],
                    "mode": "act",
                    "iterations": iteration + 1,
                    "reasoning_steps": reasoning_steps,
                    "conversation_id": conversation.id,
                    "message_id": msg.id
                }
                return

            # Execute tool and get observation
            result, sources = self._execute_tool(action, param, message)
            all_sources.extend(sources)

            observations.append({
                "action": action_text,
                "result": result
            })
            reasoning_steps.append({
                "type": "observation",
                "content": result or ""
            })

            yield {"status": "observation", "result_preview": result[:200] if result else "", "iteration": iteration + 1}

        # Max iterations reached - force response
        yield {"status": "max_iterations_reached"}
        final_response = self._generate_final_response(message, observations, all_sources)

        msg = self._save_message(
            conversation.id,
            ChatbotMessageRole.ASSISTANT,
            final_response,
            rag_sources=all_sources if include_sources else [],
            agent_trace=reasoning_steps,
            stream_metadata={
                "mode": "act",
                "iterations": max_iterations,
                "sources_count": len(all_sources)
            }
        )

        conversation.message_count += 2
        conversation.last_message_at = datetime.now()
        if not conversation.title and len(message) > 0:
            conversation.title = message[:50] + ('...' if len(message) > 50 else '')
        db.session.commit()

        yield {
            "done": True,
            "full_response": final_response,
            "sources": all_sources if include_sources else [],
            "mode": "act",
            "iterations": max_iterations,
            "reasoning_steps": reasoning_steps,
            "conversation_id": conversation.id,
            "message_id": msg.id
        }

    def _chat_react(
        self,
        message: str,
        session_id: str,
        username: str = None,
        include_sources: bool = True,
        files: List[Dict[str, Any]] = None,
        conversation_id: Optional[int] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        ReAct mode - Reasoning and Acting interleaved.
        THOUGHT → ACTION → OBSERVATION cycle.
        """
        yield {"status": "starting", "mode": "react"}

        conversation = self._get_or_create_conversation(session_id, username, conversation_id)
        from db.models.chatbot import ChatbotMessageRole
        self._save_message(conversation.id, ChatbotMessageRole.USER, message)

        max_iterations = self.get_max_iterations()
        all_sources = []
        steps = []  # Track all reasoning steps

        system_prompt = self._get_react_system_prompt()

        for iteration in range(max_iterations):
            yield {
                "status": "iteration",
                "iteration": iteration + 1,
                "max": max_iterations,
                "steps": steps
            }

            # Build conversation with all previous steps
            messages = [{"role": "system", "content": system_prompt}]
            messages.append({"role": "user", "content": f"Frage: {message}"})

            for step in steps:
                if step["type"] == "thought":
                    messages.append({"role": "assistant", "content": f"THOUGHT: {step['content']}"})
                elif step["type"] == "action":
                    messages.append({"role": "assistant", "content": f"ACTION: {step['content']}"})
                elif step["type"] == "observation":
                    messages.append({"role": "user", "content": f"OBSERVATION: {step['content']}"})

            # Get next step from LLM
            yield {"status": "thinking", "iteration": iteration + 1}
            response_text = self._call_llm_sync(messages)

            # Parse response for THOUGHT, ACTION, or FINAL ANSWER
            thought, action, final_answer = self._parse_react_response(response_text)

            if thought:
                steps.append({"type": "thought", "content": thought})
                yield {"status": "thought", "thought": thought, "iteration": iteration + 1}

            if final_answer:
                # Done!
                yield {"status": "final_answer"}

                msg = self._save_message(
                    conversation.id,
                    ChatbotMessageRole.ASSISTANT,
                    final_answer,
                    rag_sources=all_sources if include_sources else [],
                    agent_trace=steps,
                    stream_metadata={
                        "mode": "react",
                        "iterations": iteration + 1,
                        "sources_count": len(all_sources)
                    }
                )

                conversation.message_count += 2
                conversation.last_message_at = datetime.now()
                if not conversation.title and len(message) > 0:
                    conversation.title = message[:50] + ('...' if len(message) > 50 else '')
                db.session.commit()

                yield {
                    "done": True,
                    "full_response": final_answer,
                    "sources": all_sources if include_sources else [],
                    "mode": "react",
                    "iterations": iteration + 1,
                    "reasoning_steps": steps,
                    "conversation_id": conversation.id,
                    "message_id": msg.id
                }
                return

            if action:
                action_name, action_param = self._parse_action(f"ACTION: {action}")
                steps.append({"type": "action", "content": action, "action_name": action_name, "action_param": action_param})
                yield {"status": "action", "action": action_name, "param": action_param, "iteration": iteration + 1}

                # Execute tool
                result, sources = self._execute_tool(action_name, action_param, message)
                all_sources.extend(sources)

                steps.append({"type": "observation", "content": result, "sources_found": len(sources)})
                yield {"status": "observation", "result_preview": result[:300] if result else "", "iteration": iteration + 1}

        # Max iterations - generate final response
        yield {"status": "max_iterations_reached"}
        final_response = self._generate_final_response(message, steps, all_sources)

        msg = self._save_message(
            conversation.id,
            ChatbotMessageRole.ASSISTANT,
            final_response,
            rag_sources=all_sources if include_sources else [],
            agent_trace=steps,
            stream_metadata={
                "mode": "react",
                "iterations": max_iterations,
                "sources_count": len(all_sources)
            }
        )

        conversation.message_count += 2
        conversation.last_message_at = datetime.now()
        if not conversation.title and len(message) > 0:
            conversation.title = message[:50] + ('...' if len(message) > 50 else '')
        db.session.commit()

        yield {
            "done": True,
            "full_response": final_response,
            "sources": all_sources if include_sources else [],
            "mode": "react",
            "iterations": max_iterations,
            "reasoning_steps": steps,
            "conversation_id": conversation.id,
            "message_id": msg.id
        }

    def _chat_reflact(
        self,
        message: str,
        session_id: str,
        username: str = None,
        include_sources: bool = True,
        files: List[Dict[str, Any]] = None,
        conversation_id: Optional[int] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        ReflAct mode - Goal-state reflection before each action.
        GOAL → REFLECTION → THOUGHT → ACTION → OBSERVATION cycle.
        """
        yield {"status": "starting", "mode": "reflact"}

        conversation = self._get_or_create_conversation(session_id, username, conversation_id)
        from db.models.chatbot import ChatbotMessageRole
        self._save_message(conversation.id, ChatbotMessageRole.USER, message)

        max_iterations = self.get_max_iterations()
        all_sources = []
        steps = []

        system_prompt = self._get_reflact_system_prompt()

        # First: Define goal
        yield {"status": "defining_goal"}
        goal_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Definiere das GOAL für folgende Anfrage: {message}"}
        ]
        goal_response = self._call_llm_sync(goal_messages)
        goal = self._extract_goal(goal_response)

        steps.append({"type": "goal", "content": goal})
        yield {"status": "goal_defined", "goal": goal}

        for iteration in range(max_iterations):
            yield {
                "status": "iteration",
                "iteration": iteration + 1,
                "max": max_iterations,
                "goal": goal,
                "steps": steps
            }

            # Build messages with goal and all steps
            messages = [{"role": "system", "content": system_prompt}]
            messages.append({"role": "user", "content": f"Frage: {message}\n\nGOAL: {goal}"})

            for step in steps:
                if step["type"] == "goal":
                    continue  # Already in user message
                elif step["type"] == "reflection":
                    messages.append({"role": "assistant", "content": f"REFLECTION: {step['content']}"})
                elif step["type"] == "thought":
                    messages.append({"role": "assistant", "content": f"THOUGHT: {step['content']}"})
                elif step["type"] == "action":
                    messages.append({"role": "assistant", "content": f"ACTION: {step['content']}"})
                elif step["type"] == "observation":
                    messages.append({"role": "user", "content": f"OBSERVATION: {step['content']}"})

            # Get reflection and next step
            yield {"status": "reflecting", "iteration": iteration + 1}
            response_text = self._call_llm_sync(messages)

            # Parse for REFLECTION, THOUGHT, ACTION, FINAL ANSWER
            reflection, thought, action, final_answer = self._parse_reflact_response(response_text)

            if reflection:
                steps.append({"type": "reflection", "content": reflection})
                yield {"status": "reflection", "reflection": reflection, "iteration": iteration + 1}

            if thought:
                steps.append({"type": "thought", "content": thought})
                yield {"status": "thought", "thought": thought, "iteration": iteration + 1}

            if final_answer:
                yield {"status": "final_answer"}

                msg = self._save_message(
                    conversation.id,
                    ChatbotMessageRole.ASSISTANT,
                    final_answer,
                    rag_sources=all_sources if include_sources else [],
                    agent_trace=steps,
                    stream_metadata={
                        "mode": "reflact",
                        "iterations": iteration + 1,
                        "sources_count": len(all_sources)
                    }
                )

                conversation.message_count += 2
                conversation.last_message_at = datetime.now()
                if not conversation.title and len(message) > 0:
                    conversation.title = message[:50] + ('...' if len(message) > 50 else '')
                db.session.commit()

                yield {
                    "done": True,
                    "full_response": final_answer,
                    "sources": all_sources if include_sources else [],
                    "mode": "reflact",
                    "iterations": iteration + 1,
                    "goal": goal,
                    "reasoning_steps": steps,
                    "conversation_id": conversation.id,
                    "message_id": msg.id
                }
                return

            if action:
                action_name, action_param = self._parse_action(f"ACTION: {action}")
                steps.append({"type": "action", "content": action, "action_name": action_name, "action_param": action_param})
                yield {"status": "action", "action": action_name, "param": action_param, "iteration": iteration + 1}

                # Execute tool
                result, sources = self._execute_tool(action_name, action_param, message)
                all_sources.extend(sources)

                steps.append({"type": "observation", "content": result, "sources_found": len(sources)})
                yield {"status": "observation", "result_preview": result[:300] if result else "", "iteration": iteration + 1}

        # Max iterations
        yield {"status": "max_iterations_reached"}
        final_response = self._generate_final_response(message, steps, all_sources)

        msg = self._save_message(
            conversation.id,
            ChatbotMessageRole.ASSISTANT,
            final_response,
            rag_sources=all_sources if include_sources else [],
            agent_trace=steps,
            stream_metadata={
                "mode": "reflact",
                "iterations": max_iterations,
                "sources_count": len(all_sources)
            }
        )

        conversation.message_count += 2
        conversation.last_message_at = datetime.now()
        if not conversation.title and len(message) > 0:
            conversation.title = message[:50] + ('...' if len(message) > 50 else '')
        db.session.commit()

        yield {
            "done": True,
            "full_response": final_response,
            "sources": all_sources if include_sources else [],
            "mode": "reflact",
            "iterations": max_iterations,
            "goal": goal,
            "reasoning_steps": steps,
            "conversation_id": conversation.id,
            "message_id": msg.id
        }

    # ==================== Tool Execution ====================

    def _execute_tool(self, action: str, param: str, original_query: str) -> Tuple[str, List[Dict]]:
        """
        Execute a tool and return result with sources.
        """
        enabled_tools = self.get_enabled_tools()

        if action == "rag_search" and "rag_search" in enabled_tools:
            return self._tool_rag_search(param or original_query)

        elif action == "lexical_search" and "lexical_search" in enabled_tools:
            return self._tool_lexical_search(param or original_query)

        elif action == "web_search" and "web_search" in enabled_tools and self.is_web_search_enabled():
            return self._tool_web_search(param or original_query)

        elif action == "respond":
            return param, []

        else:
            return f"Tool '{action}' ist nicht verfügbar oder nicht aktiviert.", []

    def _tool_rag_search(self, query: str) -> Tuple[str, List[Dict]]:
        """Semantic RAG search."""
        if not self.chatbot.rag_enabled or not self.chatbot.collections:
            return "RAG ist für diesen Chatbot nicht aktiviert.", []

        context, sources = self._get_multi_collection_context(query)
        if sources:
            result = f"Gefunden: {len(sources)} relevante Dokumente.\n\n"
            for s in sources[:5]:
                result += f"[{s.get('footnote_id')}] {s.get('title', 'Unbekannt')}: {s.get('excerpt', '')[:200]}...\n\n"
            return result, sources
        return "Keine relevanten Dokumente gefunden.", []

    def _tool_lexical_search(self, query: str) -> Tuple[str, List[Dict]]:
        """Lexical (keyword) search."""
        if not self.chatbot.rag_enabled or not self.chatbot.collections:
            return "RAG ist für diesen Chatbot nicht aktiviert.", []

        tokens = self._extract_lexical_tokens(query)
        if not tokens:
            return "Keine aussagekräftigen Suchbegriffe gefunden.", []

        all_results = []
        for cc in self.chatbot.collections:
            collection = cc.collection
            if collection:
                results = self._lexical_search_collection(collection, tokens, limit=5)
                for r in results:
                    r['collection_name'] = collection.display_name
                all_results.extend(results)

        if all_results:
            sources = []
            result = f"Lexikalische Suche: {len(all_results)} Treffer für '{', '.join(tokens)}'.\n\n"
            for i, r in enumerate(all_results[:5]):
                sources.append({
                    'footnote_id': i + 1,
                    'title': r.get('title', 'Unbekannt'),
                    'excerpt': r.get('content', '')[:300],
                    'collection_name': r.get('collection_name')
                })
                result += f"[{i+1}] {r.get('title', 'Unbekannt')}: {r.get('content', '')[:200]}...\n\n"
            return result, sources

        return f"Keine Treffer für '{', '.join(tokens)}'.", []

    def _tool_web_search(self, query: str) -> Tuple[str, List[Dict]]:
        """Web search using Tavily API."""
        api_key = self.get_tavily_api_key()
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
            logger.error(f"[AgentChatService] Web search failed: {e}")
            return f"Web-Suche fehlgeschlagen: {str(e)}", []

    # ==================== Prompt Helpers ====================

    def _get_act_system_prompt(self) -> str:
        """Get ACT system prompt."""
        if self._prompt_settings and hasattr(self._prompt_settings, 'act_system_prompt'):
            custom = self._prompt_settings.act_system_prompt
            if custom and custom.strip():
                return custom
        from db.models.chatbot import DEFAULT_ACT_SYSTEM_PROMPT
        return DEFAULT_ACT_SYSTEM_PROMPT

    def _get_react_system_prompt(self) -> str:
        """Get ReAct system prompt."""
        if self._prompt_settings and hasattr(self._prompt_settings, 'react_system_prompt'):
            custom = self._prompt_settings.react_system_prompt
            if custom and custom.strip():
                return custom
        from db.models.chatbot import DEFAULT_REACT_SYSTEM_PROMPT
        return DEFAULT_REACT_SYSTEM_PROMPT

    def _get_reflact_system_prompt(self) -> str:
        """Get ReflAct system prompt."""
        if self._prompt_settings and hasattr(self._prompt_settings, 'reflact_system_prompt'):
            custom = self._prompt_settings.reflact_system_prompt
            if custom and custom.strip():
                return custom
        from db.models.chatbot import DEFAULT_REFLACT_SYSTEM_PROMPT
        return DEFAULT_REFLACT_SYSTEM_PROMPT

    # ==================== Parsing Helpers ====================

    def _parse_action(self, text: str) -> Tuple[str, str]:
        """Parse ACTION: tool(param) format."""
        # Match patterns like: ACTION: tool_name(parameter) or ACTION: tool_name("parameter")
        patterns = [
            r'ACTION:\s*(\w+)\s*\(\s*["\']?(.+?)["\']?\s*\)',
            r'ACTION:\s*(\w+)\s*\(\s*\)',
            r'ACTION:\s*(\w+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                action = match.group(1).lower()
                param = match.group(2) if len(match.groups()) > 1 else ""
                return action, param.strip() if param else ""

        return "respond", text

    def _parse_react_response(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse ReAct response for THOUGHT, ACTION, FINAL ANSWER."""
        thought = None
        action = None
        final_answer = None

        # Extract THOUGHT
        thought_match = re.search(r'THOUGHT:\s*(.+?)(?=ACTION:|FINAL ANSWER:|$)', text, re.IGNORECASE | re.DOTALL)
        if thought_match:
            thought = thought_match.group(1).strip()

        # Extract ACTION
        action_match = re.search(r'ACTION:\s*(.+?)(?=OBSERVATION:|FINAL ANSWER:|$)', text, re.IGNORECASE | re.DOTALL)
        if action_match:
            action = action_match.group(1).strip()

        # Extract FINAL ANSWER
        final_match = re.search(r'FINAL ANSWER:\s*(.+?)$', text, re.IGNORECASE | re.DOTALL)
        if final_match:
            final_answer = final_match.group(1).strip()

        return thought, action, final_answer

    def _parse_reflact_response(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Parse ReflAct response for REFLECTION, THOUGHT, ACTION, FINAL ANSWER."""
        reflection = None
        thought = None
        action = None
        final_answer = None

        # Extract REFLECTION
        reflection_match = re.search(r'REFLECTION:\s*(.+?)(?=THOUGHT:|ACTION:|FINAL ANSWER:|$)', text, re.IGNORECASE | re.DOTALL)
        if reflection_match:
            reflection = reflection_match.group(1).strip()

        # Extract THOUGHT
        thought_match = re.search(r'THOUGHT:\s*(.+?)(?=ACTION:|FINAL ANSWER:|$)', text, re.IGNORECASE | re.DOTALL)
        if thought_match:
            thought = thought_match.group(1).strip()

        # Extract ACTION
        action_match = re.search(r'ACTION:\s*(.+?)(?=OBSERVATION:|FINAL ANSWER:|$)', text, re.IGNORECASE | re.DOTALL)
        if action_match:
            action = action_match.group(1).strip()

        # Extract FINAL ANSWER
        final_match = re.search(r'FINAL ANSWER:\s*(.+?)$', text, re.IGNORECASE | re.DOTALL)
        if final_match:
            final_answer = final_match.group(1).strip()

        return reflection, thought, action, final_answer

    def _extract_goal(self, text: str) -> str:
        """Extract GOAL from response."""
        goal_match = re.search(r'GOAL:\s*(.+?)(?=REFLECTION:|THOUGHT:|ACTION:|$)', text, re.IGNORECASE | re.DOTALL)
        if goal_match:
            return goal_match.group(1).strip()
        return text.strip()[:200]

    # ==================== LLM Helpers ====================

    def _call_llm_sync(self, messages: List[Dict]) -> str:
        """Synchronous LLM call."""
        try:
            response = self.llm_client.chat.completions.create(
                model=self.chatbot.model_name,
                messages=messages,
                temperature=self.chatbot.temperature,
                max_tokens=self.chatbot.max_tokens,
                top_p=self.chatbot.top_p
            )

            if response.choices:
                from llm.openai_utils import extract_message_text
                return extract_message_text(response.choices[0].message)
            return ""

        except Exception as e:
            logger.error(f"[AgentChatService] LLM call failed: {e}")
            return ""

    def _generate_final_response(
        self,
        question: str,
        steps: List[Dict],
        sources: List[Dict]
    ) -> str:
        """Generate final response based on collected information."""
        # Build context from observations
        context_parts = []
        for step in steps:
            if step.get("type") == "observation":
                context_parts.append(step.get("content", ""))

        context = "\n\n".join(context_parts)

        # Build final response prompt
        messages = [
            {"role": "system", "content": self.chatbot.system_prompt + self._build_citation_instructions()},
            {"role": "system", "content": f"Kontext aus der Recherche:\n\n{context}"},
            {"role": "user", "content": f"Basierend auf der obigen Recherche, beantworte folgende Frage:\n\n{question}"}
        ]

        return self._call_llm_sync(messages)
