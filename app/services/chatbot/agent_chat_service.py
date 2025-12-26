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
from llm.openai_utils import extract_delta_text

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
                normalized: List[str] = []
                if isinstance(tools, list):
                    normalized = [str(t).strip() for t in tools if str(t).strip()]
                elif isinstance(tools, dict):
                    normalized = [str(k).strip() for k, v in tools.items() if v and str(k).strip()]
                elif isinstance(tools, str):
                    decoded = None
                    try:
                        decoded = json.loads(tools)
                    except Exception:
                        decoded = None
                    if isinstance(decoded, list):
                        normalized = [str(t).strip() for t in decoded if str(t).strip()]
                    elif isinstance(decoded, dict):
                        normalized = [str(k).strip() for k, v in decoded.items() if v and str(k).strip()]
                    else:
                        normalized = [t.strip() for t in tools.split(",") if t.strip()]
                else:
                    normalized = [str(tools).strip()] if str(tools).strip() else []

                if normalized:
                    return [t.lower() for t in normalized]
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

    def _build_completion_kwargs(self, messages: List[Dict], stream: bool = True) -> Dict[str, Any]:
        """Build kwargs for LLM completion, only including max_tokens if explicitly set."""
        kwargs = {
            "model": self.chatbot.model_name,
            "messages": messages,
            "temperature": self.chatbot.temperature,
            "top_p": self.chatbot.top_p,
            "stream": stream
        }
        if self.chatbot.max_tokens:
            kwargs["max_tokens"] = self.chatbot.max_tokens
        return kwargs

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
                'title': None,
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
            'title': final_event.get('title'),
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
                **self._build_completion_kwargs(messages, stream=True)
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
        self._maybe_set_conversation_title(conversation, message)
        db.session.commit()

        yield {
            "done": True,
            "full_response": accumulated,
            "sources": sources if include_sources else [],
            "mode": "standard",
            "conversation_id": conversation.id,
            "title": conversation.title,
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
        enabled_tools = self.get_enabled_tools()

        system_prompt = self._get_act_system_prompt()

        for iteration in range(max_iterations):
            yield {"status": "iteration", "iteration": iteration + 1, "max": max_iterations}

            # Build messages with observations
            messages = [{"role": "system", "content": system_prompt}]
            tool_prompt = self._build_tool_availability_prompt()
            if tool_prompt:
                messages.append({"role": "system", "content": tool_prompt})
            messages.extend(self._build_agent_history_messages(conversation, message))
            messages.append({"role": "user", "content": message})

            for obs in observations:
                messages.append({"role": "assistant", "content": obs["action"]})
                messages.append({"role": "user", "content": f"OBSERVATION: {obs['result']}"})

            # Get action from LLM - NOW WITH STREAMING
            yield {"status": "getting_action", "iteration": iteration + 1}

            # Stream the action text
            action_text = ""
            try:
                stream = self.llm_client.chat.completions.create(
                    **self._build_completion_kwargs(messages, stream=True)
                )
                for chunk in stream:
                    choice = chunk.choices[0] if chunk.choices else None
                    delta = getattr(choice, "delta", None) if choice else None
                    delta_text = extract_delta_text(delta)
                    if delta_text:
                        action_text += delta_text
                        yield {"status": "action_delta", "delta": delta_text, "iteration": iteration + 1}
            except Exception as e:
                logger.error(f"[AgentChatService] ACT action streaming failed: {e}")
                action_text = self._call_llm_sync(messages)

            # Parse action
            action, param = self._parse_action(action_text)
            action, param = self._normalize_action_from_tool_call(
                action,
                param,
                action_text,
                enabled_tools
            )
            yield {"status": "action", "action": action, "param": param, "iteration": iteration + 1}
            action_content = f'{action}("{param}")' if param else action
            normalized_action_text = f'ACTION: {action_content}'
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
                self._maybe_set_conversation_title(conversation, message)
                db.session.commit()

                yield {
                    "done": True,
                    "full_response": final_response,
                    "sources": all_sources if include_sources else [],
                    "mode": "act",
                    "iterations": iteration + 1,
                    "reasoning_steps": reasoning_steps,
                    "conversation_id": conversation.id,
                    "title": conversation.title,
                    "message_id": msg.id
                }
                return

            # Execute tool and get observation
            result, sources = self._execute_tool(action, param, message)
            all_sources.extend(sources)

            observations.append({
                "action": normalized_action_text,
                "result": result
            })
            reasoning_steps.append({
                "type": "observation",
                "content": result or ""
            })

            preview = result[:200] if result else ""
            for chunk in self._stream_preview_chunks(preview):
                yield {"status": "observation_delta", "delta": chunk, "iteration": iteration + 1}
            yield {"status": "observation", "result_preview": preview, "iteration": iteration + 1}

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
        self._maybe_set_conversation_title(conversation, message)
        db.session.commit()

        yield {
            "done": True,
            "full_response": final_response,
            "sources": all_sources if include_sources else [],
            "mode": "act",
            "iterations": max_iterations,
            "reasoning_steps": reasoning_steps,
            "conversation_id": conversation.id,
            "title": conversation.title,
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
        enabled_tools = self.get_enabled_tools()

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
            tool_prompt = self._build_tool_availability_prompt()
            if tool_prompt:
                messages.append({"role": "system", "content": tool_prompt})
            messages.extend(self._build_agent_history_messages(conversation, message))
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
            response_text = ""
            last_thought = ""

            try:
                stream = self.llm_client.chat.completions.create(
                    **self._build_completion_kwargs(messages, stream=True)
                )

                for chunk in stream:
                    choice = chunk.choices[0] if chunk.choices else None
                    delta = getattr(choice, "delta", None) if choice else None
                    delta_text = extract_delta_text(delta)
                    if not delta_text:
                        continue
                    response_text += delta_text
                    thought_partial, _, _ = self._parse_react_response(response_text)
                    if thought_partial and len(thought_partial) > len(last_thought):
                        delta_chunk = thought_partial[len(last_thought):]
                        last_thought = thought_partial
                        yield {"status": "thought_delta", "delta": delta_chunk, "iteration": iteration + 1}
            except Exception as e:
                logger.error(f"[AgentChatService] ReAct streaming failed: {e}")
                response_text = self._call_llm_sync(messages)

            # Parse response for THOUGHT, ACTION, or FINAL ANSWER
            thought, action, final_answer = self._parse_react_response(response_text)
            requires_sources = self._requires_sources()
            has_observation = any(step.get("type") == "observation" for step in steps)
            if final_answer and requires_sources and not has_observation:
                final_answer = None

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
                self._maybe_set_conversation_title(conversation, message)
                db.session.commit()

                yield {
                    "done": True,
                    "full_response": final_answer,
                    "sources": all_sources if include_sources else [],
                    "mode": "react",
                    "iterations": iteration + 1,
                    "reasoning_steps": steps,
                    "conversation_id": conversation.id,
                    "title": conversation.title,
                    "message_id": msg.id
                }
                return

            if action:
                action_name, action_param = self._parse_action(f"ACTION: {action}")
                action_name, action_param = self._normalize_action_from_tool_call(
                    action_name,
                    action_param,
                    action,
                    enabled_tools
                )
                if action_name == "respond":
                    if action_param and (not requires_sources or has_observation):
                        normalized_action_content = (
                            f'{action_name}("{action_param}")' if action_param else action_name
                        )
                        steps.append({
                            "type": "action",
                            "content": normalized_action_content,
                            "action_name": action_name,
                            "action_param": action_param
                        })
                        yield {"status": "action", "action": action_name, "param": action_param, "iteration": iteration + 1}
                        final_answer = action_param
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
                        self._maybe_set_conversation_title(conversation, message)
                        db.session.commit()

                        yield {
                            "done": True,
                            "full_response": final_answer,
                            "sources": all_sources if include_sources else [],
                            "mode": "react",
                            "iterations": iteration + 1,
                            "reasoning_steps": steps,
                            "conversation_id": conversation.id,
                            "title": conversation.title,
                            "message_id": msg.id
                        }
                        return
                    action = None
                    action_name = None
                    action_param = None
                if not action_name:
                    action = None

            if action:
                normalized_action_content = (
                    f'{action_name}("{action_param}")' if action_param else action_name
                )
                steps.append({
                    "type": "action",
                    "content": normalized_action_content,
                    "action_name": action_name,
                    "action_param": action_param
                })
                yield {"status": "action", "action": action_name, "param": action_param, "iteration": iteration + 1}

                # Execute tool
                result, sources = self._execute_tool(action_name, action_param, message)
                all_sources.extend(sources)

                steps.append({"type": "observation", "content": result, "sources_found": len(sources)})
                preview = result[:300] if result else ""
                for chunk in self._stream_preview_chunks(preview):
                    yield {"status": "observation_delta", "delta": chunk, "iteration": iteration + 1}
                yield {"status": "observation", "result_preview": preview, "iteration": iteration + 1}
            elif not final_answer:
                # If the model skips ACTION, force a lookup when citations are required.
                if requires_sources and not any(step.get("type") == "action" for step in steps):
                    fallback_action = None
                    if "rag_search" in enabled_tools:
                        fallback_action = "rag_search"
                    elif "lexical_search" in enabled_tools:
                        fallback_action = "lexical_search"

                    if fallback_action:
                        action_param = message
                        steps.append({
                            "type": "action",
                            "content": fallback_action,
                            "action_name": fallback_action,
                            "action_param": action_param,
                            "auto": True
                        })
                        yield {"status": "action", "action": fallback_action, "param": action_param, "iteration": iteration + 1}

                        result, sources = self._execute_tool(fallback_action, action_param, message)
                        all_sources.extend(sources)

                        steps.append({
                            "type": "observation",
                            "content": result,
                            "sources_found": len(sources),
                            "auto": True
                        })
                        preview = result[:300] if result else ""
                        for chunk in self._stream_preview_chunks(preview):
                            yield {"status": "observation_delta", "delta": chunk, "iteration": iteration + 1}
                        yield {"status": "observation", "result_preview": preview, "iteration": iteration + 1}

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
        self._maybe_set_conversation_title(conversation, message)
        db.session.commit()

        yield {
            "done": True,
            "full_response": final_response,
            "sources": all_sources if include_sources else [],
            "mode": "react",
            "iterations": max_iterations,
            "reasoning_steps": steps,
            "conversation_id": conversation.id,
            "title": conversation.title,
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
        ReflAct mode - World-Grounded Decision Making via Goal-State Reflection.

        Based on the ReflAct paper (arxiv.org/abs/2505.15182):
        - At each step, reflect on the agent's state RELATIVE to the task goal
        - Then decide on the next action based on that reflection
        - Cycle: REFLECTION → ACTION → OBSERVATION (repeat until done)

        Key difference from ReAct:
        - ReAct: "Think about what to do next" (forward-looking planning)
        - ReflAct: "Reflect on current state relative to goal" (state-grounded evaluation)

        The reflection explicitly encodes:
        1. Current state (what we know so far)
        2. What was just discovered
        3. How this relates to completing the task goal
        """
        yield {"status": "starting", "mode": "reflact"}

        conversation = self._get_or_create_conversation(session_id, username, conversation_id)
        from db.models.chatbot import ChatbotMessageRole
        self._save_message(conversation.id, ChatbotMessageRole.USER, message)

        max_iterations = self.get_max_iterations()
        all_sources = []
        steps = []

        # The user's question IS the goal - no separate goal extraction needed
        goal = message

        system_prompt = self._get_reflact_system_prompt()

        for iteration in range(max_iterations):
            yield {
                "status": "iteration",
                "iteration": iteration + 1,
                "max": max_iterations,
                "goal": goal,
                "steps": steps
            }

            # Build conversation history
            messages = [{"role": "system", "content": system_prompt}]
            tool_prompt = self._build_tool_availability_prompt()
            if tool_prompt:
                messages.append({"role": "system", "content": tool_prompt})
            messages.extend(self._build_agent_history_messages(conversation, message))
            messages.append({"role": "user", "content": f"Aufgabe: {message}"})

            # Add previous steps to context
            for step in steps:
                if step["type"] == "reflection":
                    messages.append({"role": "assistant", "content": f"REFLECTION: {step['content']}"})
                elif step["type"] == "action":
                    messages.append({"role": "assistant", "content": f"ACTION: {step['content']}"})
                elif step["type"] == "observation":
                    messages.append({"role": "user", "content": f"OBSERVATION: {step['content']}"})

            # Get reflection and next action
            yield {"status": "reflecting", "iteration": iteration + 1}
            response_text = ""
            last_reflection = ""
            try:
                logger.debug(f"[ReflAct] Starting iteration {iteration + 1}, messages count: {len(messages)}")
                stream = self.llm_client.chat.completions.create(
                    **self._build_completion_kwargs(messages, stream=True)
                )
                for chunk in stream:
                    choice = chunk.choices[0] if chunk.choices else None
                    delta = getattr(choice, "delta", None) if choice else None
                    delta_text = extract_delta_text(delta)
                    if not delta_text:
                        continue
                    response_text += delta_text

                    # Stream reflection as it comes
                    reflection_partial, _, _ = self._parse_reflact_response_v2(response_text)
                    reflection_partial = self._strip_trailing_reflact_fragment(reflection_partial)
                    if reflection_partial and reflection_partial != last_reflection:
                        if reflection_partial.startswith(last_reflection):
                            delta_chunk = reflection_partial[len(last_reflection):]
                            last_reflection = reflection_partial
                            yield {"status": "reflection_delta", "delta": delta_chunk, "iteration": iteration + 1}
                        else:
                            last_reflection = reflection_partial

            except Exception as e:
                logger.error(f"[AgentChatService] ReflAct streaming failed: {e}", exc_info=True)
                response_text = self._call_llm_sync(messages)

            # Handle empty response
            if not response_text.strip():
                logger.warning(f"[ReflAct] Empty response in iteration {iteration + 1}")
                yield {"status": "error", "message": "Leere Antwort vom LLM", "iteration": iteration + 1}
                continue

            # Parse response: REFLECTION, ACTION or FINAL ANSWER
            reflection, action, final_answer = self._parse_reflact_response_v2(response_text)
            reflection = self._strip_trailing_reflact_fragment(reflection)
            final_answer = self._strip_trailing_reflact_fragment(final_answer)

            if reflection:
                steps.append({"type": "reflection", "content": reflection})
                yield {"status": "reflection", "reflection": reflection, "iteration": iteration + 1}

            # Check for final answer
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
                self._maybe_set_conversation_title(conversation, message)
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
                    "title": conversation.title,
                    "message_id": msg.id
                }
                return

            # Execute action if present
            if action:
                action_name, action_param = self._parse_action(f"ACTION: {action}")
                action_name, action_param = self._normalize_action_from_tool_call(
                    action_name,
                    action_param,
                    action,
                    self.get_enabled_tools()
                )
                normalized_action_content = (
                    f'{action_name}("{action_param}")' if action_param else action_name
                )
                steps.append({
                    "type": "action",
                    "content": normalized_action_content,
                    "action_name": action_name,
                    "action_param": action_param
                })
                yield {"status": "action", "action": action_name, "param": action_param, "iteration": iteration + 1}

                # Execute tool
                result, sources = self._execute_tool(action_name, action_param, message)
                all_sources.extend(sources)

                steps.append({"type": "observation", "content": result, "sources_found": len(sources)})
                preview = result[:300] if result else ""
                for chunk in self._stream_preview_chunks(preview):
                    yield {"status": "observation_delta", "delta": chunk, "iteration": iteration + 1}
                yield {"status": "observation", "result_preview": preview, "iteration": iteration + 1}

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
        self._maybe_set_conversation_title(conversation, message)
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
            "title": conversation.title,
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
                results = self._lexical_search_collection(collection, query, tokens, limit=5)
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
        base_prompt = (self.chatbot.system_prompt or "").strip()
        if self._prompt_settings and hasattr(self._prompt_settings, 'act_system_prompt'):
            custom = self._prompt_settings.act_system_prompt
            if custom and custom.strip():
                act_prompt = custom
            else:
                act_prompt = None
        else:
            act_prompt = None
        from db.models.chatbot import DEFAULT_ACT_SYSTEM_PROMPT
        if not act_prompt:
            act_prompt = DEFAULT_ACT_SYSTEM_PROMPT
        if base_prompt:
            return f"{base_prompt}\n\n{act_prompt}"
        return act_prompt

    def _build_agent_history_messages(
        self,
        conversation: "ChatbotConversation",
        current_message: str
    ) -> List[Dict[str, str]]:
        """Return recent chat history for agent modes, excluding the current message."""
        from db.models.chatbot import ChatbotMessage, ChatbotMessageRole

        max_context = getattr(self.chatbot, "max_context_messages", None) or 6
        limit = max_context * 2
        history = ChatbotMessage.query.filter_by(
            conversation_id=conversation.id
        ).order_by(ChatbotMessage.created_at.desc()).limit(limit).all()

        history.reverse()
        if history and history[-1].role == ChatbotMessageRole.USER and history[-1].content == current_message:
            history = history[:-1]

        messages: List[Dict[str, str]] = []
        for msg in history:
            role = "user" if msg.role == ChatbotMessageRole.USER else "assistant"
            messages.append({"role": role, "content": msg.content})
        return messages

    def _build_tool_availability_prompt(self) -> str:
        """Provide tool availability and query guidance for agent modes."""
        tools = [t for t in self.get_enabled_tools() if t]
        if not self.is_web_search_enabled():
            tools = [t for t in tools if t != "web_search"]
        if not tools:
            return ""
        tool_list = ", ".join(tools)
        return (
            f"Verfuegbare Tools fuer diese Session: {tool_list}.\n"
            "Nutze nur diese Tools.\n"
            "Nutze Suchbegriffe aus der aktuellen Nutzerfrage oder dem Verlauf.\n"
            "Wenn die Frage ohne Kontext unklar ist, stelle eine Rueckfrage mit respond.\n"
            "Keine [TOOL_CALLS]-Marker oder JSON-Toolcalls, nur das ACTION-Format."
        )

    def _get_react_system_prompt(self) -> str:
        """Get ReAct system prompt."""
        base_prompt = (self.chatbot.system_prompt or "").strip()
        if self._prompt_settings and hasattr(self._prompt_settings, 'react_system_prompt'):
            custom = self._prompt_settings.react_system_prompt
            if custom and custom.strip():
                react_prompt = custom
            else:
                react_prompt = None
        else:
            react_prompt = None
        if not react_prompt:
            from db.models.chatbot import DEFAULT_REACT_SYSTEM_PROMPT
            react_prompt = DEFAULT_REACT_SYSTEM_PROMPT

        if base_prompt:
            return f"{base_prompt}\n\n{react_prompt}"
        return react_prompt

    def _get_reflact_system_prompt(self) -> str:
        """Get ReflAct system prompt."""
        base_prompt = (self.chatbot.system_prompt or "").strip()
        if self._prompt_settings and hasattr(self._prompt_settings, 'reflact_system_prompt'):
            custom = self._prompt_settings.reflact_system_prompt
            if custom and custom.strip():
                reflact_prompt = custom
            else:
                reflact_prompt = None
        else:
            reflact_prompt = None
        if not reflact_prompt:
            from db.models.chatbot import DEFAULT_REFLACT_SYSTEM_PROMPT
            reflact_prompt = DEFAULT_REFLACT_SYSTEM_PROMPT

        if base_prompt:
            return f"{base_prompt}\n\n{reflact_prompt}"
        return reflact_prompt

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

    def _normalize_action_from_tool_call(
        self,
        action: str,
        param: str,
        action_text: str,
        enabled_tools: Optional[List[str]] = None
    ) -> Tuple[str, str]:
        """Convert embedded tool-call strings into proper actions."""
        if action == "respond" or (enabled_tools and action not in enabled_tools):
            embedded_action, embedded_param = self._parse_embedded_tool_call(param, enabled_tools)
            if not embedded_action:
                embedded_action, embedded_param = self._parse_embedded_tool_call(action_text, enabled_tools)
            if embedded_action:
                return embedded_action, embedded_param
        return action, param

    def _parse_embedded_tool_call(
        self,
        text: Optional[str],
        enabled_tools: Optional[List[str]] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """Extract tool calls from wrapper formats like [TOOL_CALLS]rag_search("q")."""
        if not text:
            return None, None
        candidate = text.strip()
        patterns = [
            (r'\[TOOL_CALLS\]\s*(\w+)\s*\(\s*["\']?(.+?)["\']?\s*\)', False),
            (r'\[TOOL_CALLS\]\s*(\w+)\s*\(\s*\)', False),
            (r'\bTOOL_CALLS\b\s*:?\s*(\w+)\s*\(\s*["\']?(.+?)["\']?\s*\)', False),
            (r'\bTOOL_CALLS\b\s*:?\s*(\w+)\s*\(\s*\)', False),
            (r'^\s*(\w+)\s*\(\s*["\']?(.+?)["\']?\s*\)\s*$', True),
            (r'^\s*(\w+)\s*\(\s*\)\s*$', True),
        ]

        for pattern, enforce_enabled in patterns:
            match = re.search(pattern, candidate, re.IGNORECASE | re.DOTALL)
            if not match:
                continue
            action = match.group(1).lower()
            param = match.group(2) if len(match.groups()) > 1 else ""
            if enforce_enabled and enabled_tools and action not in enabled_tools:
                continue
            return action, (param or "").strip()

        return None, None

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

    def _parse_reflact_response_v2(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse ReflAct response for REFLECTION, ACTION, FINAL ANSWER.

        Based on the ReflAct paper - NO separate THOUGHT step.
        The reflection IS the thinking, grounded in state relative to goal.

        Returns:
            (reflection, action, final_answer)
        """
        reflection = None
        action = None
        final_answer = None

        # Extract REFLECTION - everything until ACTION or FINAL ANSWER
        reflection_match = re.search(
            r'REFLECTION:\s*(.+?)(?=ACTION:|FINAL ANSWER:|THOUGHT:|GOAL:|$)',
            text, re.IGNORECASE | re.DOTALL
        )
        if reflection_match:
            reflection = reflection_match.group(1).strip()
        else:
            # Backwards-compatible: accept legacy THOUGHT label as reflection.
            thought_match = re.search(
                r'THOUGHT:\s*(.+?)(?=ACTION:|FINAL ANSWER:|REFLECTION:|GOAL:|$)',
                text, re.IGNORECASE | re.DOTALL
            )
            if thought_match:
                reflection = thought_match.group(1).strip()

        # Extract ACTION
        action_match = re.search(
            r'ACTION:\s*(.+?)(?=OBSERVATION:|REFLECTION:|FINAL ANSWER:|THOUGHT:|GOAL:|$)',
            text, re.IGNORECASE | re.DOTALL
        )
        if action_match:
            action = action_match.group(1).strip()

        # Extract FINAL ANSWER
        final_match = re.search(
            r'FINAL ANSWER:\s*(.+?)(?=ACTION:|REFLECTION:|THOUGHT:|GOAL:|$)',
            text, re.IGNORECASE | re.DOTALL
        )
        if final_match:
            final_answer = final_match.group(1).strip()

        return reflection, action, final_answer

    def _strip_trailing_reflact_fragment(self, text: Optional[str]) -> Optional[str]:
        """Remove stray ACTION fragments that leak into ReflAct output/streaming."""
        if not text:
            return text
        cleaned = text.rstrip()
        cleaned = re.sub(
            r'(?m)\n\s*(?:A|AC|ACT|ACTI|ACTIO|ACTION)\s*:?\s*$',
            '',
            cleaned
        ).rstrip()
        cleaned = re.sub(
            r'(?m)\s+(?:ACTION|ACTIO|ACTI|ACT|CTION)\s*:?\s*$',
            '',
            cleaned
        ).rstrip()
        return cleaned

    def _extract_goal(self, text: str, allow_partial: bool = False) -> str:
        """
        Extract GOAL from response.

        Args:
            text: The LLM response text
            allow_partial: If True, return partial text even without GOAL: prefix (for streaming).
                          If False, only return text if GOAL: pattern is found.
        """
        if not text:
            return ""

        # Try to match GOAL: pattern
        goal_match = re.search(r'GOAL:\s*(.+?)(?=REFLECTION:|THOUGHT:|ACTION:|$)', text, re.IGNORECASE | re.DOTALL)
        if goal_match:
            return goal_match.group(1).strip()

        # For streaming: only return partial if it looks like a valid goal start
        if allow_partial:
            # Check if we have "GOAL:" prefix and some content after it
            simple_match = re.search(r'GOAL:\s*(.+)', text, re.IGNORECASE | re.DOTALL)
            if simple_match:
                return simple_match.group(1).strip()

        # For final extraction: fallback to cleaned text
        if not allow_partial:
            # Remove any partial "GOAL" prefix that might be there
            cleaned = re.sub(r'^G?O?A?L?:?\s*', '', text.strip(), flags=re.IGNORECASE)
            return cleaned[:200] if cleaned else ""

        return ""

    @staticmethod
    def _stream_preview_chunks(text: str, chunk_size: int = 80) -> List[str]:
        if not text:
            return []
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    # ==================== LLM Helpers ====================

    def _call_llm_sync(self, messages: List[Dict]) -> str:
        """Synchronous LLM call."""
        try:
            response = self.llm_client.chat.completions.create(
                **self._build_completion_kwargs(messages, stream=False)
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
