# Agentic AI & RAG

Dieses Kapitel beschreibt die theoretischen Grundlagen und praktischen Implementierungen der verschiedenen Agentenarchitekturen in LLARS.

## Übersicht

LLARS implementiert vier zentrale Paradigmen für die Interaktion von LLMs mit externem Wissen und Werkzeugen:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Agentic AI Paradigmen                                │
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
│   Single-Turn       Multi-Turn        Multi-Turn        Multi-Turn        │
│   Retrieval         Iteration         + Reasoning       + Reflection      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Kapitel

| Kapitel | Beschreibung | Status in LLARS |
|---------|--------------|-----------------|
| [RAG](rag.md) | Retrieval Augmented Generation mit Hybrid Search | ✅ Produktiv |
| [ACT](act.md) | Action-Only Agents ohne explizites Reasoning | ✅ Produktiv |
| [ReACT](react.md) | Reasoning + Acting in iterativer Schleife | ✅ Produktiv |
| [ReflAct](reflact.md) | Reflection-basiertes Reasoning mit State-Grounding | ✅ Produktiv |

## Vergleich der Paradigmen

| Aspekt | RAG | ACT | ReACT | ReflAct |
|--------|-----|-----|-------|---------|
| **Reasoning** | Implizit | Keines | Explizit (THOUGHT) | Explizit (REFLECTION) |
| **Iterationen** | 1 | 1-10 | 1-10 | 1-10 |
| **Interpretierbar** | Mittel | Niedrig | Hoch | Sehr hoch |
| **Geschwindigkeit** | Schnell | Schnell | Mittel | Mittel |
| **Komplexe Fragen** | Begrenzt | Begrenzt | Gut | Sehr gut |
| **State-Awareness** | Nein | Nein | Teilweise | Vollständig |

## Wann welches Paradigma?

```
┌─────────────────────────────────────────────────────────────────┐
│                    Entscheidungsbaum                            │
└─────────────────────────────────────────────────────────────────┘

Ist die Frage ein einfacher Fakten-Lookup?
    │
    ├── JA → RAG (Single-Turn, schnellste Antwort)
    │
    └── NEIN → Benötigt Multi-Hop Reasoning?
                    │
                    ├── NEIN → ACT (Schnell, keine Erklärung nötig)
                    │
                    └── JA → Ist Transparenz wichtig?
                                │
                                ├── NEIN → ReACT (Gutes Reasoning)
                                │
                                └── JA → ReflAct (Beste Interpretierbarkeit)
```

## Architektur in LLARS

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
│   │      case 'standard': → _chat_standard() → RAG + Direct LLM         │  │
│   │      case 'act':      → _chat_act()      → Action Loop              │  │
│   │      case 'react':    → _chat_react()    → Thought-Action Loop      │  │
│   │      case 'reflact':  → _chat_reflact()  → Reflection-Action Loop   │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                          │                                  │
└──────────────────────────────────────────┼──────────────────────────────────┘
                                           ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Tool Execution                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│   rag_search()      → ChromaDB + Hybrid Search                             │
│   lexical_search()  → FTS5 BM25 Index                                      │
│   web_search()      → Tavily API (optional)                                │
│   respond()         → Final Answer                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Konfiguration pro Chatbot

Jeder Chatbot kann individuell konfiguriert werden:

```python
# Datenbank: ChatbotPromptSettings
agent_mode: Enum['standard', 'act', 'react', 'reflact']
task_type: Enum['lookup', 'multihop']
agent_max_iterations: int  # Default: 5
tools_enabled: List[str]   # ['rag_search', 'lexical_search', 'respond']
web_search_enabled: bool   # Optional Tavily integration
```

## Weiterführende Literatur

- Lewis et al. (2020): RAG - Retrieval-Augmented Generation
- Yao et al. (2022): ReAct - Synergizing Reasoning and Acting
- Chen et al. (2025): ReflAct - Reflection-Grounded Agent Reasoning
