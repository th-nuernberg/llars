# Chatbot Wizard

**Version:** 1.0 | **Stand:** Januar 2026

Der Chatbot Wizard ist ein 5-Schritte-Assistent zur Erstellung von RAG-basierten Chatbots. Er crawlt automatisch Websites, erstellt Vektor-Embeddings und generiert KI-gestützt Namen, Icons und System-Prompts.

---

## Übersicht

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Chatbot Wizard                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Schritt 1      Schritt 2      Schritt 3      Schritt 4      Schritt 5     │
│  [URL]    →    [Crawling]  →  [Embedding] →  [Config]    →  [Review]       │
│    ●             ○              ○              ○              ○             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Schritt | Beschreibung |
|---------|--------------|
| 1. URL eingeben | Website-Adresse und Crawler-Optionen |
| 2. Crawling | Automatisches Sammeln von Website-Inhalten |
| 3. Embedding | Vektor-Embeddings für RAG erstellen |
| 4. Konfiguration | Name, System-Prompt, Icon anpassen |
| 5. Fertig | Überprüfen und Chatbot aktivieren |

---

## Schnellstart

!!! tip "Chatbot in 5 Minuten erstellen"
    1. **URL eingeben** → z.B. `https://docs.example.com`
    2. **Crawling starten** → Warten bis abgeschlossen
    3. **Embedding** → Läuft automatisch im Hintergrund
    4. **Konfiguration prüfen** → KI-generierte Felder anpassen
    5. **Fertigstellen** → Chatbot ist einsatzbereit

---

## Schritt 1: URL eingeben

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Website-URL                                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  URL: [https://docs.example.com_______________________________]            │
│                                                                             │
│  Crawler-Einstellungen:                                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Max. Seiten:       [100_______]                                     │  │
│  │  Max. Tiefe:        [3_________]                                     │  │
│  │                                                                      │  │
│  │  ☑ JavaScript ausführen (Playwright)                                 │  │
│  │  ☐ Screenshots erstellen                                             │  │
│  │  ☐ Vision-LLM für Bildanalyse                                        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│                                                    [Weiter →]              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Crawler-Optionen

| Option | Beschreibung | Standard |
|--------|--------------|----------|
| **Max. Seiten** | Maximale Anzahl zu crawlender Seiten | 100 |
| **Max. Tiefe** | Rekursionstiefe für Links | 3 |
| **Playwright** | JavaScript-Rendering für dynamische Seiten | Aus |
| **Screenshots** | Seitenbilder für Vision-Analyse | Aus |
| **Vision-LLM** | KI-gestützte Bildanalyse für Inhalte | Aus |

!!! info "URL-Format"
    URLs werden automatisch korrigiert: `example.com` → `https://example.com`

---

## Schritt 2: Crawling

Der Crawler sammelt Inhalte von der angegebenen Website:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Crawling läuft...                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ████████████████████████░░░░░░░░░░  65%                                   │
│                                                                             │
│  Phase: Seiten crawlen                                                      │
│  URLs entdeckt: 87                                                          │
│  URLs verarbeitet: 56                                                       │
│  Dokumente erstellt: 48                                                     │
│                                                                             │
│  Zuletzt verarbeitet:                                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  ✓ /docs/getting-started                                             │  │
│  │  ✓ /docs/api-reference                                               │  │
│  │  🔄 /docs/tutorials/basics                                           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Crawling-Phasen

| Phase | Beschreibung |
|-------|--------------|
| **Planung** | URL-Struktur analysieren, Sitemap prüfen |
| **Planung fertig** | Link-Graph erstellt |
| **Crawling** | Seiten herunterladen und verarbeiten |
| **Abgeschlossen** | Alle erreichbaren Seiten verarbeitet |

!!! warning "Echtzeit-Updates"
    Der Fortschritt wird live über Socket.IO aktualisiert. Bei Verbindungsabbruch
    kann der Wizard fortgesetzt werden.

---

## Schritt 3: Embedding

Nach dem Crawling werden Vektor-Embeddings erstellt:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Embeddings erstellen...                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ████████████████████░░░░░░░░░░░░░░  52%                                   │
│                                                                             │
│  Dokumente: 48                                                              │
│  Chunks erstellt: 234                                                       │
│  Chunks verarbeitet: 122                                                    │
│                                                                             │
│  Embedding-Modell: llamaindex/vdr-2b-multi-v1                               │
│  Dimensionen: 1024                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Embedding-Prozess

1. **Chunking**: Dokumente werden in kleinere Abschnitte geteilt
2. **Embedding**: Jeder Chunk wird in einen Vektor umgewandelt
3. **Speicherung**: Vektoren werden in ChromaDB gespeichert

!!! tip "Hintergrund-Verarbeitung"
    Embedding läuft im Hintergrund weiter. Sie können zur Konfiguration wechseln,
    während die Verarbeitung noch läuft.

---

## Schritt 4: Konfiguration

KI-generierte Felder können angepasst werden:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Chatbot konfigurieren                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Allgemein                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Name:          [docs_assistant_______________]  [🔄 Generieren]     │  │
│  │  Anzeigename:   [Docs Assistant_______________]  [🔄 Generieren]     │  │
│  │  Icon:          [📚 mdi-book-open_____________]  [🔄 Generieren]     │  │
│  │  Farbe:         [#3498db__] ████                 [🔄 Generieren]     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  System-Prompt                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Du bist ein hilfreicher Assistent für die Example Dokumentation.    │  │
│  │  Beantworte Fragen basierend auf den bereitgestellten Dokumenten.    │  │
│  │  Wenn du die Antwort nicht weißt, sage es ehrlich.                   │  │
│  │                                                          [🔄 Gen.]   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Willkommensnachricht                                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Hallo! Ich bin der Docs Assistant. Wie kann ich Ihnen bei der       │  │
│  │  Example Dokumentation helfen?                       [🔄 Generieren] │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### KI-generierte Felder

| Feld | Beschreibung | KI-Analyse |
|------|--------------|------------|
| **Name** | Interner Name (snake_case) | Basiert auf URL und Inhalten |
| **Anzeigename** | Benutzerfreundlicher Name | Lesbarer Markenname |
| **Icon** | MDI-Icon | Passend zum Themenbereich |
| **Farbe** | HEX-Farbcode | Logo/Branding-Analyse |
| **System-Prompt** | Verhaltensdefinition | RAG-optimierter Prompt |
| **Willkommen** | Begrüßung | Kontextbezogen |

!!! info "Felder regenerieren"
    Klicken Sie auf 🔄 um ein Feld neu zu generieren. Text-Felder werden
    mit Streaming angezeigt.

### Icon-Kategorien

Der Wizard wählt aus kuratierten Icon-Kategorien:

| Kategorie | Beispiel-Icons |
|-----------|---------------|
| Allgemein | robot, chat, message, assistant |
| Business | briefcase, domain, store, handshake |
| Bildung | school, book, graduation-cap |
| Technologie | laptop, code-tags, cog, database |
| Support | help-circle, headset, phone, wrench |
| Gesundheit | hospital, medical-bag, heart-pulse |
| Finanzen | bank, credit-card, wallet, calculator |

---

## Schritt 5: Fertig

Abschließende Überprüfung und Aktivierung:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Chatbot erstellen                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Zusammenfassung                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Name:           docs_assistant                                      │  │
│  │  Anzeigename:    Docs Assistant                                      │  │
│  │  Icon:           📚 mdi-book-open                                    │  │
│  │  Farbe:          #3498db                                             │  │
│  │                                                                      │  │
│  │  Wissensbasis:                                                       │  │
│  │  ├── 48 Dokumente                                                    │  │
│  │  ├── 234 Chunks                                                      │  │
│  │  └── Embedding: 100% ✓                                               │  │
│  │                                                                      │  │
│  │  RAG: Aktiviert (Top-5 Dokumente, Min. Relevanz 0.3)                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│                                       [Chatbot testen]  [Fertigstellen]    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

Nach dem Fertigstellen:
- Chatbot ist sofort einsatzbereit
- Erscheint in der Chatbot-Liste
- Kann im Chat-Interface genutzt werden

---

## RAG-Konfiguration (Erweitert)

Nach der Erstellung können erweiterte RAG-Einstellungen angepasst werden:

### Retrieval-Einstellungen

| Option | Beschreibung | Standard |
|--------|--------------|----------|
| **RAG aktiviert** | RAG-Suche ein/aus | Ein |
| **Dokumente (k)** | Anzahl abgerufener Dokumente | 5 |
| **Min. Relevanz** | Schwellenwert für Ergebnisse | 0.3 |
| **Quellen anzeigen** | Quellen in Antwort einbinden | Ein |

### Reranking (Optional)

| Option | Beschreibung |
|--------|--------------|
| **Cross-Encoder** | Ergebnisse mit Reranker nachsortieren |
| **Reranker-Modell** | Spezifisches Reranking-Modell wählen |

### Zitier-Einstellungen

| Option | Beschreibung |
|--------|--------------|
| **Zitate erfordern** | Antworten müssen Quellen zitieren |
| **Unbekannte Antwort** | Text wenn Antwort nicht in Quellen |
| **Zitat-Template** | Format für Quellenangaben |

**Template-Platzhalter:**
- `{{id}}` - Dokument-ID
- `{{title}}` - Dokumenttitel
- `{{excerpt}}` - Relevanter Textauszug
- `{{page_number}}` - Seitennummer (bei PDFs)

---

## Agenten-Modi (Erweitert)

Für komplexe Anwendungsfälle stehen verschiedene Agenten-Modi zur Verfügung:

### Standard-Modus

```
Frage → LLM → Antwort
```
- Schnellste Antwortzeit
- Direkte RAG-Abfrage
- Für einfache Fragen

### ACT-Modus

```
Frage → AKTION → BEOBACHTUNG → Antwort
```
- Tool-Aufrufe möglich
- Für Faktenabfragen
- 1-2 LLM-Aufrufe

### ReAct-Modus

```
Frage → GEDANKE → AKTION → BEOBACHTUNG → ... → Antwort
```
- Explizites Reasoning
- Nachvollziehbare Schritte
- Für komplexe Fragen

### ReflAct-Modus

```
Aufgabe → REFLEXION → AKTION → BEOBACHTUNG → ... → Antwort
```
- Selbstkorrektur
- Zielorientiert
- Für mehrstufige Probleme

---

## Wizard fortsetzen

Unterbrochene Wizard-Sessions können fortgesetzt werden:

1. **Chatbot-Liste öffnen** → Unvollständige Chatbots haben Status "In Bearbeitung"
2. **Wizard fortsetzen** klicken
3. Server synchronisiert den letzten Stand
4. Weiter beim letzten Schritt

!!! warning "Session-Timeout"
    Wizard-Sessions werden nach längerer Inaktivität bereinigt.
    Der Crawling-Fortschritt bleibt erhalten.

---

## API-Endpunkte

### Wizard-Lifecycle

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/chatbots/wizard` | POST | Wizard starten |
| `/api/chatbots/:id/wizard/crawl` | POST | Crawling starten |
| `/api/chatbots/:id/wizard/generate-field` | POST | Feld generieren |
| `/api/chatbots/:id/wizard/status` | GET | Status abrufen |
| `/api/chatbots/:id/wizard/finalize` | POST | Wizard abschließen |
| `/api/chatbots/:id/wizard/pause` | POST | Wizard pausieren |
| `/api/chatbots/:id/cancel-build` | POST | Wizard abbrechen |

### Session-Management

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/chatbots/wizard/sessions/:id/join` | POST | Session fortsetzen |
| `/api/chatbots/wizard/sessions/:id/data` | PATCH | Daten aktualisieren |

---

## Socket.IO Events

### Crawler-Events

| Event | Beschreibung |
|-------|--------------|
| `crawler:progress` | Fortschritts-Update |
| `crawler:page_crawled` | Seite verarbeitet |
| `crawler:complete` | Crawling abgeschlossen |
| `crawler:error` | Fehler aufgetreten |

### RAG-Events

| Event | Beschreibung |
|-------|--------------|
| `rag:collection_progress` | Embedding-Fortschritt |
| `rag:collection_completed` | Embedding abgeschlossen |
| `rag:document_processed` | Dokument verarbeitet |

---

## Berechtigungen

| Permission | Beschreibung |
|------------|--------------|
| `feature:chatbots:edit` | Chatbots erstellen, Wizard nutzen |
| `feature:chatbots:view` | Chatbots ansehen |
| `feature:chatbots:advanced` | Agenten-Modi nutzen |
| `feature:rag:share` | Collections teilen |

---

## Häufige Fragen

??? question "Wie lange dauert das Crawling?"
    Abhängig von Seitenanzahl und -größe. Typisch: 1-5 Minuten für 100 Seiten.

??? question "Welche Websites können gecrawlt werden?"
    Öffentlich zugängliche Websites. JavaScript-lastige Seiten benötigen
    die Playwright-Option.

??? question "Kann ich später Dokumente hinzufügen?"
    Ja, über den Collection-Manager können jederzeit Dokumente ergänzt werden.

??? question "Was passiert bei Crawling-Fehlern?"
    Fehlerhafte URLs werden übersprungen. Der Wizard zeigt eine Zusammenfassung
    der erfolgreichen und fehlgeschlagenen URLs.

---

## Siehe auch

- [Chatbot & RAG](../projekte/chatbot-builder/index.md) - Technisches Konzept
- [RAG-Pipeline](../agentic-ai/rag.md) - Retrieval-Augmented Generation
- [Prompt Engineering](prompt-engineering.md) - System-Prompts optimieren
