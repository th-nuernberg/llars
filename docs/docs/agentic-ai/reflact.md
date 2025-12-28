# ReflAct - Reflection-Grounded Agent Reasoning

## Theorie

### Paper

!!! quote "Originalpaper"
    **Kim, J., Rhee, S., Kim, M., et al. (2025)**
    *ReflAct: World-Grounded Decision Making in LLM Agents via Goal-State Reflection*
    **DOI:** [10.48550/arXiv.2505.15182](https://doi.org/10.48550/arXiv.2505.15182)
    **EMNLP 2025 (Main Conference)**

!!! info "Konzept"
    **ReflAct** erweitert ReACT durch zustandsbasierte Reflexion. Statt vorwärtsgerichtet zu planen ("Was soll ich als nächstes tun?"), reflektiert der Agent seinen aktuellen Zustand relativ zum Ziel ("Wo stehe ich im Verhältnis zum Ziel?"). Dies ermöglicht systematische Selbstkorrektur und bessere Ziel-Fokussierung.

### Architektur

```mermaid
flowchart TB
    subgraph iter1[Iteration 1]
        direction LR
        r1[REFLECTION<br/>Wo stehe ich?] --> a1[ACTION<br/>rag_search]
        a1 --> tool1[[Tool Execute]]
        tool1 --> o1[/OBSERVATION/]
    end

    subgraph iter2[Iteration 2]
        direction LR
        r2[REFLECTION<br/>Ziel erreicht?] --> a2[ACTION<br/>respond]
        a2 --> tool2[[Tool Execute]]
        tool2 --> o2[/OBSERVATION/]
    end

    iter1 --> iter2
    iter2 --> final([FINAL ANSWER])

    style r1 fill:#88c4c8,stroke:#5fa8ad,color:#000
    style a1 fill:#D1BC8A,stroke:#b8a06a,color:#000
    style tool1 fill:#b0ca97,stroke:#8fb077,color:#000
    style o1 fill:#a8c5e2,stroke:#7ba3c9,color:#000
    style r2 fill:#88c4c8,stroke:#5fa8ad,color:#000
    style a2 fill:#D1BC8A,stroke:#b8a06a,color:#000
    style tool2 fill:#b0ca97,stroke:#8fb077,color:#000
    style o2 fill:#a8c5e2,stroke:#7ba3c9,color:#000
    style iter1 fill:#f5f5f5,stroke:#88c4c8
    style iter2 fill:#f5f5f5,stroke:#88c4c8
    style final fill:#e8c87a,stroke:#d4a84b,color:#000
```

**ReflAct Loop:** Query → REFLECTION (zustandsbasiert) → ACTION → Tool → OBSERVATION → (Wiederholung oder Antwort)

### Kernkonzept

**REFLECTION → ACTION → OBSERVATION → REFLECTION → ... → FINAL ANSWER**

Der REFLECTION-Schritt ist **zustandsbasiert** (state-grounded):

- "Wo stehe ich gerade relativ zum Ziel?"
- "Was weiß ich bereits?"
- "Was habe ich gerade entdeckt?"
- "Was fehlt noch, um das Ziel zu erreichen?"

### Unterschied zu ReACT

| Aspekt | ReACT (THOUGHT) | ReflAct (REFLECTION) |
|--------|-----------------|---------------------|
| Fokus | Vorwärtsgerichtet | Zustandsbasiert |
| Frage | "Was soll ich als nächstes tun?" | "Wo stehe ich relativ zum Ziel?" |
| Perspektive | Planung | Evaluation |
| State-Awareness | Teilweise | Vollständig |
| Selbstkorrektur | Möglich | Systematisch |

### REFLECTION-Struktur

Jede Reflexion enthält drei Komponenten:

```
REFLECTION:
1. Aktueller Zustand: [Was ich bereits weiß]
2. Letzte Entdeckung: [Was gerade gefunden wurde]
3. Ziel-Relation: [Wie nah bin ich dem Ziel? Was fehlt noch?]
```

### Vorteile gegenüber ReACT

| Vorteil | Beschreibung |
|---------|--------------|
| **Bessere Selbstkorrektur** | Explizite State-Evaluation ermöglicht frühe Fehlererkennung |
| **Ziel-Fokussierung** | Jeder Schritt wird am Ziel gemessen |
| **Transparenz** | Vollständig nachvollziehbarer Reasoning-Prozess |
| **Robustheit** | Weniger anfällig für "Abwege" |

---

## Beispiel

### Query
```
"Wann hat die DG Agentur geöffnet und wie erreiche ich sie?"
```

### ReflAct Trace

```
[Iteration 1]
REFLECTION:
  Aktueller Zustand: Der Benutzer fragt nach Öffnungszeiten UND Kontaktdaten.
                     Ich habe noch keine Informationen.
  Letzte Entdeckung: (Keine - Start der Aufgabe)
  Ziel-Relation: Ich brauche beide Informationen. Zuerst suche ich
                 nach Öffnungszeiten.
ACTION: rag_search("Öffnungszeiten DG Agentur")
OBSERVATION:
  [1] Kontakt: Mo-Fr 9-18 Uhr, Sa nach Vereinbarung
  [2] Wir sind telefonisch unter +49 911 97554990 erreichbar

[Iteration 2]
REFLECTION:
  Aktueller Zustand: Ich habe Öffnungszeiten (Mo-Fr 9-18, Sa Vereinbarung)
                     und eine Telefonnummer (+49 911 97554990).
  Letzte Entdeckung: Dokument [1] enthält bereits Öffnungszeiten,
                     [2] liefert Telefonnummer.
  Ziel-Relation: Öffnungszeiten: ✓ vollständig
                 Kontaktdaten: teilweise (Telefon ✓, Email fehlt, Adresse fehlt)
ACTION: rag_search("Kontakt Email Adresse Impressum")
OBSERVATION:
  [1] Impressum: Telefon +49 911 97554990, Email office@dg-agentur.de
  [2] Adresse: Bahnhofstraße 2, 90402 Nürnberg

[Iteration 3]
REFLECTION:
  Aktueller Zustand: Ich habe alle benötigten Informationen:
                     - Öffnungszeiten: Mo-Fr 9-18 Uhr, Sa nach Vereinbarung
                     - Telefon: +49 911 97554990
                     - Email: office@dg-agentur.de
                     - Adresse: Bahnhofstraße 2, 90402 Nürnberg
  Letzte Entdeckung: Email und Adresse aus dem Impressum.
  Ziel-Relation: ZIEL ERREICHT - Alle Informationen vollständig.
FINAL ANSWER: Die DG Agentur hat Montag bis Freitag von 9-18 Uhr
              geöffnet, Samstag nach Vereinbarung. [1]

              Kontakt:
              - Telefon: +49 911 97554990
              - Email: office@dg-agentur.de
              - Adresse: Bahnhofstraße 2, 90402 Nürnberg [2]
```

### Response
```
Die DG Agentur hat Montag bis Freitag von 9-18 Uhr geöffnet,
Samstag nach Vereinbarung. [1]

Kontakt:
- Telefon: +49 911 97554990
- Email: office@dg-agentur.de
- Adresse: Bahnhofstraße 2, 90402 Nürnberg [2]

Quellen:
[1] Kontakt - DG Agentur
[2] Impressum - DG Agentur
```

---

## Implementierung in LLARS

!!! success "Status: Produktiv"
    ReflAct ist vollständig implementiert und im Produktiveinsatz.

### Architektur

```mermaid
flowchart TB
    subgraph main[_chat_reflact Loop]
        direction TB
        start([Start]) --> refl[Generate REFLECTION]
        refl --> action[Generate ACTION]
        action --> parse[Parse Response]
        parse --> check{FINAL ANSWER?}
        check -->|Nein| exec[Execute Tool]
        exec --> history[Add to History]
        history --> refl
    end
    check -->|Ja| done([Complete])

    style start fill:#98d4bb,stroke:#6bbf9a
    style refl fill:#88c4c8,stroke:#5fa8ad,color:#000
    style action fill:#D1BC8A,stroke:#b8a06a,color:#000
    style parse fill:#a8c5e2,stroke:#7ba3c9,color:#000
    style check fill:#9e9e9e,stroke:#757575,color:#fff
    style exec fill:#b0ca97,stroke:#8fb077,color:#000
    style history fill:#88c4c8,stroke:#5fa8ad,color:#000
    style done fill:#e8c87a,stroke:#d4a84b
    style main fill:#f5f5f5,stroke:#88c4c8
```

### System Prompt

```python
# DEFAULT_REFLACT_SYSTEM_PROMPT (chatbot.py)
"""
Du bist ein ReflAct-Agent. Bei jedem Schritt reflektierst du deinen
aktuellen Zustand RELATIV zum Aufgabenziel, dann wählst du die nächste Aktion.

## ReflAct-Prinzip (basierend auf arxiv.org/abs/2505.15182):
- Nicht "Was soll ich als nächstes tun?" (vorausschauend)
- Sondern "Wo stehe ich relativ zum Ziel?" (zustandsbasiert)

## Deine Reflection muss IMMER enthalten:
1. Aktueller Zustand: Was weißt du bereits?
2. Letzte Entdeckung: Was hast du gerade erfahren?
3. Ziel-Relation: Wie nah bist du dem Ziel? Was fehlt noch?

## Format:
REFLECTION: [Strukturierte Reflexion mit den 3 Punkten]
ACTION: werkzeug_name("parameter")

Wenn du genug Informationen hast:
REFLECTION: [Finale Reflexion - Ziel erreicht]
FINAL ANSWER: [Vollständige Antwort mit Quellenangaben]

Verfügbare Werkzeuge:
- rag_search("suchbegriffe"): Semantische Suche in Dokumenten
- lexical_search("suchbegriffe"): Keyword-basierte Suche
- web_search("suchbegriffe"): Web-Suche (falls aktiviert)
"""
```

### Dateien

| Datei | Funktion |
|-------|----------|
| `app/services/chatbot/agent_chat_service.py` | `_chat_reflact()` (Zeilen 735-920) |
| `app/db/models/chatbot.py` | `DEFAULT_REFLACT_SYSTEM_PROMPT` |

### Code-Auszug

```python
# agent_chat_service.py - _chat_reflact()

def _chat_reflact(self, message: str, ...) -> Generator[Dict, None, None]:
    """
    ReflAct mode - World-Grounded Decision Making via Goal-State Reflection.

    Based on the ReflAct paper (arxiv.org/abs/2505.15182):
    - At each step, reflect on the agent's state RELATIVE to the task goal
    - Then decide on the next action based on that reflection
    - Cycle: REFLECTION → ACTION → OBSERVATION (repeat until done)

    Key difference from ReAct:
    - ReAct: "Think about what to do next" (forward-looking planning)
    - ReflAct: "Reflect on current state relative to goal" (state-grounded evaluation)
    """

    for iteration in range(max_iterations):
        yield {"status": "reflecting", "iteration": iteration + 1}

        # Generate REFLECTION + ACTION (streaming)
        response_text = ""
        for chunk in self._stream_llm_response(messages):
            response_text += chunk
            yield {"status": "reflection_delta", "delta": chunk}

        # Parse response (NO separate THOUGHT step in ReflAct!)
        reflection, action, final_answer = \
            self._parse_reflact_response_v2(response_text)

        if final_answer:
            yield {"status": "complete", "response": final_answer}
            return

        # Execute tool
        observation = self._execute_tool(action)

        # Add to history
        steps.append({"type": "reflection", "content": reflection})
        steps.append({"type": "action", "content": action})
        steps.append({"type": "observation", "content": observation})
```

### Parsing

```python
# _parse_reflact_response_v2()
# Basierend auf dem Paper - KEIN separater THOUGHT-Schritt!

REFLECTION_PATTERN = r"REFLECTION:\s*(.+?)(?=ACTION:|FINAL ANSWER:|$)"
ACTION_PATTERN = r"ACTION:\s*(.+?)(?=OBSERVATION:|REFLECTION:|FINAL ANSWER:|$)"
FINAL_PATTERN = r"FINAL ANSWER:\s*(.+?)(?=ACTION:|REFLECTION:|$)"

# Rückwärtskompatibilität: THOUGHT wird als REFLECTION interpretiert
THOUGHT_AS_REFLECTION = r"THOUGHT:\s*(.+?)(?=ACTION:|FINAL ANSWER:|REFLECTION:|$)"
```

### Konfiguration

```python
# ChatbotPromptSettings
agent_mode: str = "reflact"
task_type: str = "multihop"  # Mehr Iterationen erlaubt
agent_max_iterations: int = 7
tools_enabled: List[str] = ["rag_search", "lexical_search", "web_search", "respond"]

# Custom System Prompt (optional)
reflact_system_prompt: str = "..."
```

### Events (WebSocket)

```python
# Streaming Events
yield {"status": "iteration", "iteration": 1, "max": 7}
yield {"status": "reflecting", "iteration": 1}  # Start Reflection
yield {"status": "reflection_delta", "delta": "Aktueller Zustand..."}  # Streaming
yield {"status": "reflection", "content": "..."}  # Complete REFLECTION
yield {"status": "action", "action": "rag_search", "argument": "..."}
yield {"status": "observation", "content": "..."}
yield {"status": "complete", "response": "...", "sources": [...]}
```

### Logs

```
[AgentChatService] ReflAct iteration 1/7
[ReflAct] Starting iteration 1, messages count: 3
[AgentChatService] REFLECTION: Aktueller Zustand: Der Benutzer fragt...
[AgentChatService] ACTION: rag_search("Öffnungszeiten")
[AgentChatService] Tool executed: rag_search (3 results)
[AgentChatService] ReflAct iteration 2/7
[ReflAct] Starting iteration 2, messages count: 6
[AgentChatService] REFLECTION: Aktueller Zustand: Ich habe Öffnungszeiten...
[AgentChatService] FINAL ANSWER detected
[AgentChatService] ReflAct completed in 2 iterations
```

### Vergleich: ReACT vs ReflAct in LLARS

| Aspekt | ReACT | ReflAct |
|--------|-------|---------|
| Methode | `_chat_react()` | `_chat_reflact()` |
| System Prompt | `DEFAULT_REACT_SYSTEM_PROMPT` | `DEFAULT_REFLACT_SYSTEM_PROMPT` |
| Reasoning-Schritt | THOUGHT (vorwärts) | REFLECTION (zustandsbasiert) |
| Parsing | `_parse_react_response()` | `_parse_reflact_response_v2()` |
| State-Tracking | Implizit | Explizit (3-Punkte-Struktur) |
| Ziel-Evaluation | Nein | Ja (Ziel-Relation) |
| Token/Iteration | ~150-300 | ~200-400 |
| Typische Iterationen | 2-5 | 2-5 |
| Selbstkorrektur | Möglich | Systematisch |

### Wann ReflAct statt ReACT?

| Anwendungsfall | Empfehlung |
|----------------|------------|
| Einfache Lookups | ReACT oder ACT |
| Multi-Hop mit klarem Ziel | ReflAct |
| Komplexe Recherche | ReflAct |
| Maximale Transparenz gewünscht | ReflAct |
| Selbstkorrektur wichtig | ReflAct |
| Minimaler Token-Verbrauch | ACT oder ReACT |
