# Hybrid Search in LLARS

!!! warning "Klarstellung"
    LLARS verwendet **keine echte Hybrid Search mit RRF** im Standard-RAG-Modus.
    Stattdessen gibt es zwei getrennte Such-Strategien je nach Modus.

## Übersicht

| Modus | Semantic Search | Lexical Search | Kombination |
|-------|-----------------|----------------|-------------|
| **Standard RAG** | ✅ Immer | ❌ Nicht verfügbar | - |
| **Agent-Modi** (ACT/ReAct/ReflAct) | ✅ Als Tool | ✅ Als Tool | Agent entscheidet |

## Standard RAG: Nur Semantic Search

```mermaid
flowchart TB
    Q[User Query] --> EMB[Query Embedding]
    EMB --> VS[(ChromaDB)]
    VS --> RES[Kandidaten]
    RES --> RR[Optional: Reranking]
    RR --> FILTER[Min. Relevance Filter]
    FILTER --> TOPK[Top-K]
    TOPK --> CTX[Context für LLM]
```

Der Standard-RAG-Modus verwendet **ausschließlich semantische Suche** (Vektor-Ähnlichkeit):

1. Query wird embedded (VDR-2B oder Fallback)
2. Ähnlichkeitssuche in ChromaDB
3. Optional: Reranking (Lexical Blending oder Cross-Encoder)
4. Top-K Ergebnisse als Kontext

**Kein RRF, keine parallele Lexical Search.**

## Agent-Modi: Zwei separate Tools

In den Agent-Modi (ACT, ReAct, ReflAct) stehen **zwei separate Such-Tools** zur Verfügung:

```mermaid
flowchart TB
    subgraph Agent["Agent Loop"]
        THINK[Agent Reasoning] --> DECIDE{Welches Tool?}
        DECIDE -->|Konzeptuelle Suche| RAG[rag_search Tool]
        DECIDE -->|Exakte Begriffe| LEX[lexical_search Tool]
        RAG --> OBS1[Observation]
        LEX --> OBS2[Observation]
        OBS1 --> THINK
        OBS2 --> THINK
    end
```

### rag_search Tool
- Semantische Suche in ChromaDB
- Gut für konzeptuelle Fragen
- "Was sind die Vorteile von X?"

### lexical_search Tool
- BM25/FTS5 Suche in SQLite
- Gut für exakte Begriffe, Namen, IDs
- "Wer ist Max Mustermann?"

Der Agent entscheidet selbstständig, welches Tool er nutzt - oder beide nacheinander.

## Reranking (Optional)

Nach der initialen Suche kann ein Reranking durchgeführt werden:

```mermaid
flowchart LR
    subgraph "Reranking Modi"
        A[Vector Score] --> B{Modus?}
        B -->|lexical| C["(1-α) × vector + α × overlap"]
        B -->|cross-encoder| D[CrossEncoder Score]
        B -->|off| E[Keine Änderung]
    end
```

### Lexical Blending (Default)

```python
rerank_score = (1 - alpha) * vector_score + alpha * token_overlap
# alpha = 0.15 (default)
```

- Token-Overlap zwischen Query und Chunk-Content
- Leichtgewichtig, keine zusätzlichen Modelle nötig
- Hilft bei exakten Keyword-Matches

### Cross-Encoder

```python
rerank_score = CrossEncoder(query, chunk_content)
```

- Sentence-Transformers CrossEncoder
- Höhere Qualität, aber langsamer
- Erfordert Modell-Download

### Konfiguration

| Umgebungsvariable | Werte | Default |
|-------------------|-------|---------|
| `RAG_RERANK_MODE` | `off`, `lexical`, `cross-encoder` | `lexical` |
| `RAG_RERANK_ALPHA` | 0.0 - 1.0 | 0.15 |

## Query Expansion (Nur Lexical Search)

Für die lexikalische Suche werden Synonyme automatisch hinzugefügt:

| Token | Expandiert zu |
|-------|---------------|
| `inhaber` | `impressum`, `betreiber`, `verantwortlich`, `geschäftsführer` |
| `kontakt` | `email`, `telefon`, `adresse`, `impressum` |
| `chef` | `inhaber`, `geschäftsführer`, `leitung` |

## Vergleich: Standard RAG vs. Agent-Modus

| Aspekt | Standard RAG | Agent-Modus |
|--------|--------------|-------------|
| **Semantic Search** | Automatisch | Als Tool verfügbar |
| **Lexical Search** | ❌ Nicht verfügbar | Als Tool verfügbar |
| **Kombination** | Nur Reranking | Agent wählt iterativ |
| **Latenz** | Niedrig (1 Suche) | Höher (mehrere Iterationen möglich) |
| **Exakte Begriffe** | Nur via Reranking | Lexical Tool |

## Wann welchen Modus nutzen?

```mermaid
flowchart TD
    START[Chatbot-Anwendungsfall] --> Q1{Exakte Begriffe wichtig?}
    Q1 -->|Nein| STANDARD[Standard RAG]
    Q1 -->|Ja| Q2{Komplexe Reasoning nötig?}
    Q2 -->|Nein| RERANK[Standard RAG + Reranking]
    Q2 -->|Ja| AGENT[Agent-Modus]

    STANDARD --> S1["Schnell, einfach<br/>Konzeptuelle Fragen"]
    RERANK --> S2["Schnell + Keyword-Boost<br/>Guter Kompromiss"]
    AGENT --> S3["Flexibel, iterativ<br/>Komplexe Recherche"]
```

## Dateien

| Datei | Funktion |
|-------|----------|
| `app/services/chatbot/chat_service.py` | Semantic Search (Standard RAG) |
| `app/services/chatbot/lexical_index.py` | FTS5 Index (Agent Tool) |
| `app/services/rag/reranker.py` | Lexical Blending / Cross-Encoder |
| `app/services/chatbot/agent_chat_service.py` | Agent-Modi mit beiden Tools |

## Troubleshooting

### Lexical Search findet nichts

1. Prüfen ob Index existiert:
```bash
ls -la app/data/rag/indexes/lexical_index.sqlite
```

2. Index wird lazy beim ersten Zugriff erstellt

### Reranking hat keinen Effekt

- Prüfen: `RAG_RERANK_MODE` Umgebungsvariable
- Cross-Encoder erfordert Modell in `llm_models` Tabelle (type=reranker)

### Agent nutzt falsches Tool

- ReAct/ReflAct Modi zeigen Reasoning - prüfen warum Agent so entscheidet
- System Prompt ggf. anpassen für bessere Tool-Auswahl
