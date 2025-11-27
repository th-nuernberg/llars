# Chatbot & RAG Collection Management System

**Version:** 1.0 | **Stand:** 26. November 2025 | **Status:** In Entwicklung

---

## 1. Übersicht

### 1.1 Ziele

Das System erweitert LLARS um ein vollständiges **Chatbot-Management mit RAG-Integration**:

1. **Chatbot-Verwaltung**: Anlegen, Konfigurieren und Verwalten verschiedener Chatbots
2. **Collection-Management**: Erstellen und Verwalten von RAG-Collections
3. **Dokument-Management**: Hochladen, Einsehen und Löschen von Dokumenten in Collections
4. **Multi-Collection RAG**: Chatbots können mehrere Collections nutzen
5. **Admin-Dashboard**: Vollständige Verwaltung unter `/admin`

### 1.2 Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Admin Dashboard (/admin)                         │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │   Chatbots   │  │ Collections  │  │  Dokumente   │  │  Stats   │ │
│  │   Tab        │  │   Tab        │  │   Tab        │  │  Tab     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Backend (Flask)                                 │
├─────────────────────────────────────────────────────────────────────┤
│  /api/chatbots/*           │  /api/rag/collections/*                │
│  /api/chatbots/<id>/chat   │  /api/rag/documents/*                  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Datenbank (MariaDB)                            │
├─────────────────────────────────────────────────────────────────────┤
│  chatbots ◄────► chatbot_collections ◄────► rag_collections         │
│                                                    │                │
│  chatbot_conversations                      rag_documents           │
│  chatbot_messages                           rag_document_chunks     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        ChromaDB (Vector Store)                       │
│   llars_general_...  │  llars_faq_...  │  llars_training_...        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Datenbank-Schema

### 2.1 Neue Tabellen

#### `chatbots` - Chatbot-Konfiguration

```sql
CREATE TABLE chatbots (
    id INT PRIMARY KEY AUTO_INCREMENT,

    -- Identifikation
    name VARCHAR(100) NOT NULL UNIQUE,          -- Interner Slug: 'support-bot'
    display_name VARCHAR(255) NOT NULL,         -- UI-Name: 'Support Assistent'
    description TEXT,                           -- Beschreibung

    -- Visuelle Konfiguration
    icon VARCHAR(50) DEFAULT 'mdi-robot',       -- Material Design Icon
    avatar_url VARCHAR(500),                    -- Custom Avatar URL
    color VARCHAR(7) DEFAULT '#5d7a4a',         -- Akzentfarbe (Hex)

    -- LLM-Konfiguration
    system_prompt TEXT NOT NULL,                -- System-Prompt
    model_name VARCHAR(100) DEFAULT 'mistralai/Mistral-Small-3.2-24B-Instruct-2506',
    temperature DECIMAL(3,2) DEFAULT 0.7,       -- 0.0 - 2.0
    max_tokens INT DEFAULT 2048,                -- Max Response Length
    top_p DECIMAL(3,2) DEFAULT 0.9,             -- Nucleus Sampling

    -- RAG-Konfiguration
    rag_enabled BOOLEAN DEFAULT TRUE,           -- RAG aktivieren?
    rag_retrieval_k INT DEFAULT 4,              -- Anzahl Dokumente
    rag_min_relevance DECIMAL(3,2) DEFAULT 0.3, -- Min. Relevanz-Score
    rag_include_sources BOOLEAN DEFAULT TRUE,   -- Quellen anzeigen?

    -- Verhalten
    welcome_message TEXT,                       -- Erste Nachricht
    fallback_message TEXT DEFAULT 'Ich konnte leider keine passende Antwort finden.',
    max_context_messages INT DEFAULT 10,        -- Chat-History Limit

    -- Zugriffskontrolle
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT FALSE,
    allowed_roles JSON,                         -- ['researcher', 'admin']

    -- Audit
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_chatbot_name (name),
    INDEX idx_chatbot_active (is_active)
);
```

#### `chatbot_collections` - M:N Verknüpfung Chatbot ↔ Collection

```sql
CREATE TABLE chatbot_collections (
    id INT PRIMARY KEY AUTO_INCREMENT,
    chatbot_id INT NOT NULL,
    collection_id INT NOT NULL,

    -- Konfiguration
    priority INT DEFAULT 0,                     -- Höher = wichtiger
    weight DECIMAL(3,2) DEFAULT 1.0,            -- Gewichtung 0.1-2.0
    is_primary BOOLEAN DEFAULT FALSE,           -- Haupt-Collection

    -- Audit
    assigned_by VARCHAR(255),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (chatbot_id) REFERENCES chatbots(id) ON DELETE CASCADE,
    FOREIGN KEY (collection_id) REFERENCES rag_collections(id) ON DELETE CASCADE,
    UNIQUE KEY uk_chatbot_collection (chatbot_id, collection_id)
);
```

#### `chatbot_conversations` - Chat-Sessions

```sql
CREATE TABLE chatbot_conversations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    chatbot_id INT NOT NULL,

    -- Session
    session_id VARCHAR(100) NOT NULL UNIQUE,    -- UUID
    username VARCHAR(255),                      -- User (optional)
    title VARCHAR(255),                         -- Auto-generiert aus erster Nachricht

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    message_count INT DEFAULT 0,

    -- Timing
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP,

    FOREIGN KEY (chatbot_id) REFERENCES chatbots(id) ON DELETE CASCADE,
    INDEX idx_conv_session (session_id),
    INDEX idx_conv_chatbot (chatbot_id),
    INDEX idx_conv_user (username)
);
```

#### `chatbot_messages` - Chat-Nachrichten

```sql
CREATE TABLE chatbot_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT NOT NULL,

    -- Nachricht
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,

    -- RAG-Kontext (nur bei assistant)
    rag_context TEXT,                           -- Verwendeter Kontext
    rag_sources JSON,                           -- [{doc_id, title, relevance, excerpt}]

    -- Metriken
    tokens_input INT,
    tokens_output INT,
    response_time_ms INT,

    -- Feedback
    user_rating ENUM('helpful', 'not_helpful', 'incorrect'),
    user_feedback TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (conversation_id) REFERENCES chatbot_conversations(id) ON DELETE CASCADE,
    INDEX idx_msg_conversation (conversation_id),
    INDEX idx_msg_created (created_at)
);
```

### 2.2 Bestehende Tabellen (bereits vorhanden)

Die folgenden Tabellen existieren bereits in `app/db/tables.py`:

- `rag_collections` - RAG-Collection Metadaten
- `rag_documents` - Hochgeladene Dokumente
- `rag_document_chunks` - Einzelne Chunks mit Vector-IDs
- `rag_document_versions` - Versionshistorie
- `rag_retrieval_log` - Query-Logging
- `rag_processing_queue` - Background-Job Queue

---

## 3. Backend API

### 3.1 Chatbot API (`/api/chatbots`)

| Method | Endpoint | Beschreibung | Permission |
|--------|----------|--------------|------------|
| GET | `/api/chatbots` | Liste aller Chatbots | `feature:chatbots:view` |
| GET | `/api/chatbots/<id>` | Chatbot-Details | `feature:chatbots:view` |
| POST | `/api/chatbots` | Chatbot erstellen | `feature:chatbots:edit` |
| PUT | `/api/chatbots/<id>` | Chatbot aktualisieren | `feature:chatbots:edit` |
| DELETE | `/api/chatbots/<id>` | Chatbot löschen | `feature:chatbots:delete` |
| POST | `/api/chatbots/<id>/duplicate` | Chatbot kopieren | `feature:chatbots:edit` |

#### Collection-Zuweisungen

| Method | Endpoint | Beschreibung | Permission |
|--------|----------|--------------|------------|
| GET | `/api/chatbots/<id>/collections` | Zugewiesene Collections | `feature:chatbots:view` |
| POST | `/api/chatbots/<id>/collections` | Collection zuweisen | `feature:chatbots:edit` |
| PUT | `/api/chatbots/<id>/collections/<cid>` | Priorität ändern | `feature:chatbots:edit` |
| DELETE | `/api/chatbots/<id>/collections/<cid>` | Zuweisung entfernen | `feature:chatbots:edit` |

#### Chat-Funktionalität

| Method | Endpoint | Beschreibung | Permission |
|--------|----------|--------------|------------|
| POST | `/api/chatbots/<id>/chat` | Chat-Nachricht senden | `feature:chatbots:view` |
| GET | `/api/chatbots/<id>/conversations` | Alle Gespräche | `feature:chatbots:view` |
| GET | `/api/chatbots/<id>/conversations/<cid>` | Einzelnes Gespräch | `feature:chatbots:view` |
| DELETE | `/api/chatbots/<id>/conversations/<cid>` | Gespräch löschen | `feature:chatbots:edit` |
| POST | `/api/chatbots/<id>/test` | Test ohne Logging | `feature:chatbots:edit` |

#### Statistiken

| Method | Endpoint | Beschreibung | Permission |
|--------|----------|--------------|------------|
| GET | `/api/chatbots/stats/overview` | Globale Übersicht | `feature:chatbots:view` |
| GET | `/api/chatbots/<id>/stats` | Chatbot-Statistiken | `feature:chatbots:view` |

### 3.2 Collection API (`/api/rag/collections`) - Erweitert

| Method | Endpoint | Beschreibung | Permission |
|--------|----------|--------------|------------|
| GET | `/api/rag/collections` | Alle Collections | `feature:rag:view` |
| GET | `/api/rag/collections/<id>` | Collection-Details mit Dokumenten | `feature:rag:view` |
| POST | `/api/rag/collections` | Collection erstellen | `feature:rag:edit` |
| PUT | `/api/rag/collections/<id>` | Collection aktualisieren | `feature:rag:edit` |
| DELETE | `/api/rag/collections/<id>` | Collection löschen (inkl. Dokumente) | `feature:rag:delete` |

### 3.3 Dokument API (`/api/rag/documents`) - Erweitert

| Method | Endpoint | Beschreibung | Permission |
|--------|----------|--------------|------------|
| GET | `/api/rag/documents` | Alle Dokumente (mit Filter) | `feature:rag:view` |
| GET | `/api/rag/documents/<id>` | Dokument-Details | `feature:rag:view` |
| GET | `/api/rag/documents/<id>/content` | Dokument-Inhalt (Text) | `feature:rag:view` |
| GET | `/api/rag/documents/<id>/preview` | PDF-Preview (erste Seiten) | `feature:rag:view` |
| GET | `/api/rag/documents/<id>/download` | Dokument herunterladen | `feature:rag:view` |
| POST | `/api/rag/documents/upload` | Dokument hochladen | `feature:rag:edit` |
| POST | `/api/rag/documents/upload-multiple` | Batch-Upload | `feature:rag:edit` |
| PUT | `/api/rag/documents/<id>` | Metadaten aktualisieren | `feature:rag:edit` |
| DELETE | `/api/rag/documents/<id>` | Dokument löschen | `feature:rag:delete` |
| POST | `/api/rag/documents/<id>/reindex` | Dokument neu indexieren | `feature:rag:edit` |

---

## 4. Frontend-Komponenten

### 4.1 Neue Komponenten-Struktur

```
llars-frontend/src/components/
├── Admin/
│   └── ChatbotAdmin/
│       ├── ChatbotManager.vue          # Hauptcontainer mit Tabs
│       ├── ChatbotList.vue             # Chatbot-Übersicht
│       ├── ChatbotEditor.vue           # Erstellen/Bearbeiten Dialog
│       ├── ChatbotCollectionPicker.vue # Collection-Zuweisung
│       ├── ChatbotPreview.vue          # Live-Test
│       └── ChatbotStats.vue            # Statistiken
│
├── RAG/
│   ├── CollectionManager.vue           # Collection-Verwaltung
│   ├── CollectionEditor.vue            # Collection erstellen/bearbeiten
│   ├── CollectionDocuments.vue         # Dokumente in Collection
│   ├── DocumentUploader.vue            # Upload-Komponente
│   ├── DocumentViewer.vue              # Dokument-Ansicht
│   └── DocumentList.vue                # Dokument-Tabelle
│
└── Chat/
    ├── ChatWidget.vue                  # Chat-Interface
    ├── ChatMessage.vue                 # Einzelne Nachricht
    ├── ChatInput.vue                   # Eingabefeld
    └── ChatSources.vue                 # Quellenangaben
```

### 4.2 Admin-Dashboard Tabs

```
┌─────────────────────────────────────────────────────────────────────┐
│  Admin Dashboard                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  [Chatbots] [Collections] [Dokumente] [Statistiken]                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Tab-Inhalt hier...                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Chatbots Tab

```
┌─────────────────────────────────────────────────────────────────────┐
│  Chatbots                                              [+ Neu]      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 🤖 Support Assistent                    ✅ Aktiv            │   │
│  │ "Beantwortet Support-Anfragen"                               │   │
│  │ Collections: [FAQ] [Docs] [Training]    234 Gespräche       │   │
│  │                                    [Test] [Bearbeiten] [🗑️]  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 🎓 Onboarding Bot                       ✅ Aktiv            │   │
│  │ "Hilft neuen Mitarbeitern"                                   │   │
│  │ Collections: [Onboarding]               45 Gespräche        │   │
│  │                                    [Test] [Bearbeiten] [🗑️]  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.4 Collections Tab

```
┌─────────────────────────────────────────────────────────────────────┐
│  Collections                                           [+ Neu]      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ 📁 FAQ      │  │ 📁 Docs     │  │ 📁 Training │  │ 📁 Intern   │ │
│  │ 156 Docs    │  │ 42 Docs     │  │ 23 Docs     │  │ 89 Docs     │ │
│  │ 12.4 MB     │  │ 8.2 MB      │  │ 3.1 MB      │  │ 15.7 MB     │ │
│  │ [Öffnen]    │  │ [Öffnen]    │  │ [Öffnen]    │  │ [Öffnen]    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.5 Collection-Detail Ansicht (Dokumente)

```
┌─────────────────────────────────────────────────────────────────────┐
│  ← Zurück    Collection: FAQ                    [Upload] [⚙️]       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  156 Dokumente • 12.4 MB • Letzte Änderung: vor 2 Stunden          │
│                                                                     │
│  🔍 [Suchen...                              ] [Typ ▼] [Status ▼]    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ ☐ │ 📄 Passwort-Reset-Anleitung.pdf    │ 245 KB │ ✅ Indexed │   │
│  │   │    Hochgeladen: 24.11.2025          │ 12 Chunks          │   │
│  │   │                          [👁️ Ansehen] [⬇️ Download] [🗑️] │   │
│  ├───┼─────────────────────────────────────────────────────────┤   │
│  │ ☐ │ 📄 Login-Probleme-FAQ.pdf          │ 128 KB │ ✅ Indexed │   │
│  │   │    Hochgeladen: 23.11.2025          │ 8 Chunks           │   │
│  │   │                          [👁️ Ansehen] [⬇️ Download] [🗑️] │   │
│  ├───┼─────────────────────────────────────────────────────────┤   │
│  │ ☐ │ 📄 Account-Erstellung.md           │ 12 KB  │ ⏳ Pending │   │
│  │   │    Hochgeladen: gerade eben         │ -                  │   │
│  │   │                          [👁️ Ansehen] [⬇️ Download] [🗑️] │   │
│  └───┴─────────────────────────────────────────────────────────┘   │
│                                                                     │
│  [☐ Alle auswählen]                     [🗑️ Ausgewählte löschen]    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.6 Dokument-Ansicht Dialog

```
┌─────────────────────────────────────────────────────────────────────┐
│  Passwort-Reset-Anleitung.pdf                               [X]     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Info] [Inhalt] [Chunks]                                          │
│                                                                     │
│  ─── Dokument-Info ─────────────────────────────────────────────── │
│                                                                     │
│  Dateiname:      Passwort-Reset-Anleitung.pdf                      │
│  Größe:          245 KB                                            │
│  Typ:            application/pdf                                   │
│  Hochgeladen:    24.11.2025 14:32                                  │
│  Von:            admin                                             │
│  Status:         ✅ Indexed                                         │
│  Chunks:         12                                                │
│  Abrufe:         47                                                │
│                                                                     │
│  ─── Extrahierter Text (Vorschau) ──────────────────────────────── │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Passwort-Reset Anleitung                                    │   │
│  │                                                             │   │
│  │ 1. Öffnen Sie die Login-Seite                              │   │
│  │ 2. Klicken Sie auf "Passwort vergessen"                    │   │
│  │ 3. Geben Sie Ihre E-Mail-Adresse ein                       │   │
│  │ 4. Prüfen Sie Ihr E-Mail-Postfach                          │   │
│  │ 5. Klicken Sie auf den Reset-Link                          │   │
│  │ ...                                                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│                              [⬇️ Download] [🔄 Neu indexieren] [🗑️]  │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.7 Chatbot-Editor Dialog

```
┌─────────────────────────────────────────────────────────────────────┐
│  Chatbot erstellen                                           [X]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Allgemein] [LLM] [RAG] [Collections] [Vorschau]                   │
│                                                                     │
│  ═══ Allgemein ═════════════════════════════════════════════════   │
│                                                                     │
│  Name (intern)*:    [support-assistant        ]                     │
│  Anzeigename*:      [Support Assistent        ]                     │
│  Beschreibung:      [Beantwortet Support-Fragen]                    │
│                                                                     │
│  Icon: [🤖 ▼]       Farbe: [████ #5d7a4a]                           │
│                                                                     │
│  Willkommensnachricht:                                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Hallo! Ich bin der Support-Assistent. Wie kann ich Ihnen   │   │
│  │ heute helfen?                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ═══ System-Prompt* ════════════════════════════════════════════   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Du bist ein freundlicher Support-Assistent für LLARS.      │   │
│  │                                                             │   │
│  │ Regeln:                                                     │   │
│  │ - Antworte auf Deutsch                                      │   │
│  │ - Nutze die bereitgestellten Dokumente                      │   │
│  │ - Sei höflich und professionell                             │   │
│  │ - Sage ehrlich, wenn du etwas nicht weißt                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  [Template laden ▼]                                                 │
│                                                                     │
│  ☑️ Aktiv    ☐ Öffentlich                                           │
│                                                                     │
│                                        [Abbrechen] [Speichern]      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Services

### 5.1 ChatbotService

```python
# app/services/chatbot/chatbot_service.py

class ChatbotService:
    """Service für Chatbot-Operationen"""

    def get_all_chatbots(self, include_inactive=False) -> List[Chatbot]
    def get_chatbot(self, chatbot_id: int) -> Chatbot
    def create_chatbot(self, data: dict, username: str) -> Chatbot
    def update_chatbot(self, chatbot_id: int, data: dict) -> Chatbot
    def delete_chatbot(self, chatbot_id: int) -> bool
    def duplicate_chatbot(self, chatbot_id: int, username: str) -> Chatbot

    # Collection-Zuweisungen
    def get_collections(self, chatbot_id: int) -> List[ChatbotCollection]
    def assign_collection(self, chatbot_id: int, collection_id: int, **kwargs)
    def update_collection_assignment(self, chatbot_id: int, collection_id: int, **kwargs)
    def remove_collection(self, chatbot_id: int, collection_id: int)

    # Statistiken
    def get_stats(self, chatbot_id: int) -> dict
    def get_overview_stats(self) -> dict
```

### 5.2 ChatService

```python
# app/services/chatbot/chat_service.py

class ChatService:
    """Service für Chat-Interaktionen"""

    def __init__(self, chatbot_id: int):
        self.chatbot = self._load_chatbot(chatbot_id)
        self.rag_pipeline = RAGPipeline()

    def chat(self, message: str, session_id: str, username: str = None) -> dict:
        """Hauptmethode für Chat mit RAG"""

        # 1. Conversation laden/erstellen
        conversation = self._get_or_create_conversation(session_id, username)

        # 2. User-Nachricht speichern
        self._save_message(conversation.id, 'user', message)

        # 3. RAG-Kontext holen (Multi-Collection)
        rag_context, sources = self._get_rag_context(message)

        # 4. Prompt bauen
        prompt = self._build_prompt(conversation, message, rag_context)

        # 5. LLM aufrufen
        response, tokens = self._call_llm(prompt)

        # 6. Assistant-Nachricht speichern
        self._save_message(conversation.id, 'assistant', response, sources)

        return {
            'response': response,
            'sources': sources,
            'conversation_id': conversation.id
        }

    def _get_rag_context(self, query: str) -> Tuple[str, List[dict]]:
        """Multi-Collection RAG mit Gewichtung"""
        all_results = []

        for cc in self.chatbot.collections:
            results = self.rag_pipeline.search(
                query=query,
                collection_name=cc.collection.chroma_collection_name,
                k=self.chatbot.rag_retrieval_k
            )
            for r in results:
                r['score'] *= cc.weight
                r['collection_name'] = cc.collection.display_name
            all_results.extend(results)

        # Sortieren und filtern
        all_results.sort(key=lambda x: x['score'], reverse=True)
        filtered = [r for r in all_results[:self.chatbot.rag_retrieval_k]
                   if r['score'] >= self.chatbot.rag_min_relevance]

        context = "\n\n---\n\n".join([r['content'] for r in filtered])
        return context, filtered
```

### 5.3 RAGService (Erweitert)

```python
# app/services/rag/rag_service.py

class RAGService:
    """Erweiterter Service für RAG-Operationen"""

    # Collections
    def get_all_collections(self) -> List[RAGCollection]
    def get_collection(self, collection_id: int) -> RAGCollection
    def get_collection_with_documents(self, collection_id: int) -> dict
    def create_collection(self, data: dict, username: str) -> RAGCollection
    def update_collection(self, collection_id: int, data: dict) -> RAGCollection
    def delete_collection(self, collection_id: int) -> bool

    # Dokumente
    def get_documents(self, collection_id: int = None, **filters) -> List[RAGDocument]
    def get_document(self, document_id: int) -> RAGDocument
    def get_document_content(self, document_id: int) -> str
    def upload_document(self, file, collection_id: int, username: str) -> RAGDocument
    def delete_document(self, document_id: int) -> bool
    def reindex_document(self, document_id: int) -> bool

    # Suche
    def search(self, query: str, collection_ids: List[int], k: int = 4) -> List[dict]
```

---

## 6. Workflow-Diagramme

### 6.1 Chatbot erstellen

```
Admin klickt [+ Neuer Chatbot]
        │
        ▼
ChatbotEditor Dialog öffnet
        │
        ▼
Admin konfiguriert:
├── Name, Beschreibung
├── System-Prompt
├── LLM-Parameter (Temperature, etc.)
├── RAG-Einstellungen
└── Collections auswählen
        │
        ▼
POST /api/chatbots
        │
        ▼
Backend:
├── Validierung
├── Chatbot in DB speichern
├── Collection-Zuweisungen erstellen
└── Response
        │
        ▼
Chatbot erscheint in Liste
```

### 6.2 Dokument hochladen

```
Admin wählt Collection
        │
        ▼
Klickt [Upload] oder Drag & Drop
        │
        ▼
POST /api/rag/documents/upload
        │
        ▼
Backend:
├── Datei validieren (Typ, Größe)
├── SHA-256 Hash berechnen
├── Duplikat-Check
├── Datei speichern
├── DB-Eintrag (status: pending)
└── Processing Queue
        │
        ▼
Background Worker:
├── Dokument laden (PDF/TXT/MD)
├── Text extrahieren
├── Chunking
├── Embeddings generieren
├── ChromaDB speichern
└── Status: indexed
        │
        ▼
Frontend zeigt Status-Update
```

### 6.3 Chat mit Multi-Collection RAG

```
User sendet Nachricht
        │
        ▼
POST /api/chatbots/{id}/chat
        │
        ▼
ChatService.chat():
        │
        ├──▶ Conversation laden/erstellen
        │
        ├──▶ User-Message speichern
        │
        ├──▶ Für jede Collection des Chatbots:
        │    ├── ChromaDB Similarity Search
        │    ├── Top-K Ergebnisse
        │    └── Gewichtung anwenden
        │
        ├──▶ Ergebnisse mergen & filtern
        │
        ├──▶ Prompt zusammenbauen:
        │    ┌─────────────────────────┐
        │    │ System: {system_prompt} │
        │    │ Context: {rag_context}  │
        │    │ History: {...}          │
        │    │ User: {message}         │
        │    └─────────────────────────┘
        │
        ├──▶ LiteLLM API Call
        │
        └──▶ Response speichern & zurückgeben
```

---

## 7. Permissions

### 7.1 Neue Permissions

```python
# Chatbot-Permissions
'feature:chatbots:view'       # Chatbots sehen und nutzen
'feature:chatbots:edit'       # Chatbots erstellen/bearbeiten
'feature:chatbots:delete'     # Chatbots löschen

# RAG-Permissions (bereits vorhanden, erweitert)
'feature:rag:view'            # Collections/Dokumente sehen
'feature:rag:edit'            # Collections/Dokumente erstellen
'feature:rag:delete'          # Collections/Dokumente löschen
```

### 7.2 Rollen-Zuweisungen

| Rolle | chatbots:view | chatbots:edit | chatbots:delete | rag:view | rag:edit | rag:delete |
|-------|---------------|---------------|-----------------|----------|----------|------------|
| admin | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| researcher | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ |
| viewer | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |

---

## 8. Implementierungsplan

### Phase 1: Datenbank & Backend-Grundlagen
- [ ] Neue Tabellen erstellen (chatbots, chatbot_collections, etc.)
- [ ] Models in tables.py hinzufügen
- [ ] Migrations-Script
- [ ] Neue Permissions registrieren

### Phase 2: Chatbot-API
- [ ] ChatbotService implementieren
- [ ] CRUD-Routes für /api/chatbots
- [ ] Collection-Zuweisungs-Routes
- [ ] Tests

### Phase 3: Chat-Funktionalität
- [ ] ChatService mit Multi-Collection RAG
- [ ] Chat-Route /api/chatbots/{id}/chat
- [ ] Conversation-Management
- [ ] Tests

### Phase 4: RAG-Erweiterungen
- [ ] Dokument-Ansicht Endpoint
- [ ] Dokument-Löschung verbessern (ChromaDB Cleanup)
- [ ] Re-Indexierung
- [ ] Tests

### Phase 5: Frontend - Admin Dashboard
- [ ] ChatbotManager.vue Hauptkomponente
- [ ] ChatbotList.vue
- [ ] ChatbotEditor.vue
- [ ] Integration in /admin

### Phase 6: Frontend - Collection/Dokument Management
- [ ] CollectionManager.vue
- [ ] CollectionDocuments.vue
- [ ] DocumentViewer.vue
- [ ] DocumentUploader.vue

### Phase 7: Frontend - Chat
- [ ] ChatWidget.vue
- [ ] ChatMessage.vue
- [ ] ChatSources.vue
- [ ] Chatbot-Vorschau im Editor

### Phase 8: Testing & Polish
- [ ] End-to-End Tests
- [ ] Performance-Optimierung
- [ ] Dokumentation aktualisieren

---

## 9. Technische Details

### 9.1 LLM-Integration

```python
# Verwendetes Modell (konfigurierbar pro Chatbot)
DEFAULT_MODEL = "mistralai/Mistral-Small-3.2-24B-Instruct-2506"

# LiteLLM Configuration
LITELLM_BASE_URL = os.getenv('LITELLM_BASE_URL')
LITELLM_API_KEY = os.getenv('LITELLM_API_KEY')
```

### 9.2 ChromaDB-Integration

```python
# Persistente Speicherung
CHROMA_PERSIST_DIR = "/app/storage/vectorstore"

# Collection-Naming
# Format: llars_{collection_name}_{embedding_model}
# Beispiel: llars_faq_sentence_transformers_all_MiniLM_L6_v2
```

### 9.3 Datei-Upload

```python
# Erlaubte Dateitypen
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md', 'docx', 'doc'}

# Max. Dateigröße
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Speicherort
UPLOAD_DIR = "/app/rag_docs"
```

---

## 10. Sicherheit

### 10.1 Authentifizierung
- Alle Endpoints erfordern gültigen JWT-Token
- Token-Validierung via Authentik OIDC

### 10.2 Autorisierung
- Permission-basierter Zugriff auf alle Funktionen
- `@require_permission()` Decorator auf allen Routes

### 10.3 Datei-Sicherheit
- Dateitypprüfung (MIME-Type + Extension)
- Größenlimit
- Virus-Scan (optional, future)
- Sichere Dateinamen (UUID-Prefix)

### 10.4 Rate Limiting
- Chat-Endpoint: 30 Anfragen/Minute pro User
- Upload-Endpoint: 10 Anfragen/Minute pro User

---

## 11. Zusammenfassung

| Feature | Status | Beschreibung |
|---------|--------|--------------|
| Chatbot CRUD | 🔲 Geplant | Erstellen, Bearbeiten, Löschen von Chatbots |
| Multi-Collection RAG | 🔲 Geplant | Chatbots mit mehreren Collections |
| Collection Management | 🔲 Geplant | Erstellen, Bearbeiten von Collections |
| Dokument-Upload | ✅ Vorhanden | Erweitern um Ansicht/Löschung |
| Dokument-Ansicht | 🔲 Geplant | Inhalt einsehen, Chunks anzeigen |
| Dokument-Löschung | 🔲 Geplant | Mit ChromaDB Cleanup |
| Chat-Interface | 🔲 Geplant | Vollständiges Chat-Widget |
| Admin-Dashboard | 🔲 Geplant | Unter /admin |
| Statistiken | 🔲 Geplant | Usage-Tracking |

---

**Autor:** Claude (AI Assistant)
**Erstellt:** 26. November 2025
**Projekt:** LLARS - LLM-Assisted Rating System
