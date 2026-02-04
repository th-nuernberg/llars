# Agentic AI & RAG

This chapter describes the theoretical foundations and practical implementations of the different agent architectures in LLARS.

## Overview

LLARS implements four core paradigms for the interaction of LLMs with external knowledge and tools:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Agentic AI Paradigms                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐     │
│  │     RAG     │   │     ACT     │   │   ReACT     │   │  ReflAct    │     │
│  │             │   │             │   │             │   │             │     │
│  │  Retrieval  │   │   Action    │   │  Reasoning  │   │ Reflection  │     │
│  │  Augmented  │   │    Only     │   │     +       │   │     +       │     │
│  │ Generation  │   │             │   │   Acting    │   │   Acting    │     │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘     │
│        │                 │                 │                 │             │
│        ▼                 ▼                 ▼                 ▼             │
│   Single-turn       Multi-turn        Multi-turn        Multi-turn        │
│   Retrieval         Iteration         + Reasoning       + Reflection      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Chapters

| Chapter | Description | Status in LLARS |
|---------|-------------|-----------------|
| [RAG](rag.md) | Retrieval Augmented Generation with hybrid search | ✅ Production |
| [ACT](act.md) | Action-only agents without explicit reasoning | ✅ Production |
| [ReACT](react.md) | Reasoning + acting in an iterative loop | ✅ Production |
| [ReflAct](reflact.md) | Reflection-based reasoning with state grounding | ✅ Production |

## Paradigm Comparison

| Aspect | RAG | ACT | ReACT | ReflAct |
|--------|-----|-----|-------|---------|
| **Reasoning** | Implicit | None | Explicit (THOUGHT) | Explicit (REFLECTION) |
| **Iterations** | 1 | 1-10 | 1-10 | 1-10 |
| **Interpretability** | Medium | Low | High | Very high |
| **Speed** | Fast | Fast | Medium | Medium |
| **Complex Questions** | Limited | Limited | Good | Very good |
| **State Awareness** | No | No | Partial | Full |

## Which Paradigm When?

```
┌─────────────────────────────────────────────────────────────────┐
│                    Decision Tree                               │
└─────────────────────────────────────────────────────────────────┘

Is the question a simple fact lookup?
    │
    ├── YES → RAG (single turn, fastest answer)
    │
    └── NO → Does it require multi-hop reasoning?
                    │
                    ├── NO → ACT (fast, no explanation needed)
                    │
                    └── YES → Is transparency important?
                                │
                                ├── NO → ReACT (good reasoning)
                                │
                                └── YES → ReflAct (best interpretability)
```

## Architecture in LLARS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           User Query                                        │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AgentChatService                                     │
│                   (agent_chat_service.py)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   agent_mode = chatbot.prompt_settings.agent_mode                           │
│                                                                             │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │  switch(agent_mode):                                                 │  │
│   │      case 'standard': → _chat_standard() → RAG + direct LLM         │  │
│   │      case 'act':      → _chat_act()      → Action loop              │  │
│   │      case 'react':    → _chat_react()    → Thought-action loop      │  │
│   │      case 'reflact':  → _chat_reflact()  → Reflection-action loop   │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                          │                                  │
└──────────────────────────────────────────┼──────────────────────────────────┘
                                           ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Tool Execution                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│   rag_search()      → ChromaDB + hybrid search                             │
│   lexical_search()  → FTS5 BM25 index                                      │
│   web_search()      → Tavily API (optional)                                │
│   respond()         → Final answer                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Configuration Per Chatbot

Each chatbot can be configured individually:

```python
# Database: ChatbotPromptSettings
agent_mode: Enum['standard', 'act', 'react', 'reflact']
task_type: Enum['lookup', 'multihop']
agent_max_iterations: int  # Default: 5
tools_enabled: List[str]   # ['rag_search', 'lexical_search', 'respond']
web_search_enabled: bool   # Optional Tavily integration
```

## Further Reading

- Lewis et al. (2020): RAG - Retrieval-Augmented Generation
- Yao et al. (2022): ReAct - Synergizing Reasoning and Acting
- Chen et al. (2025): ReflAct - Reflection-Grounded Agent Reasoning
