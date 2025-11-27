# ChatbotAdmin Komponenten

Dieses Verzeichnis enthält alle Vue 3 Komponenten für die Chatbot-Administration im LLARS-System.

## Komponenten-Übersicht

### 1. ChatbotManager.vue
**Hauptkomponente** für die Chatbot- und RAG-Verwaltung.

**Features:**
- Tabs für Chatbots, Collections und Dokumente
- Stats-Cards mit Übersicht
- Integriert alle anderen ChatbotAdmin-Komponenten
- Orchestriert CRUD-Operationen

**API-Endpoints:**
- `GET /api/chatbots?include_inactive=true` - Chatbots laden
- `GET /api/chatbots/stats/overview` - Statistiken laden
- `POST /api/chatbots` - Chatbot erstellen
- `PUT /api/chatbots/{id}` - Chatbot aktualisieren
- `DELETE /api/chatbots/{id}` - Chatbot löschen
- `POST /api/chatbots/{id}/duplicate` - Chatbot duplizieren

---

### 2. ChatbotList.vue
**Liste** aller Chatbots als Cards.

**Props:**
- `chatbots` (Array) - Liste der Chatbots
- `loading` (Boolean) - Ladezustand

**Emits:**
- `edit(chatbot)` - Chatbot bearbeiten
- `delete(chatbot)` - Chatbot löschen
- `duplicate(chatbot)` - Chatbot duplizieren
- `test(chatbot)` - Chatbot testen
- `manage-collections(chatbot)` - Collections verwalten

**Features:**
- Cards-Layout mit Chatbot-Icon und Farbe
- Status-Badge (aktiv/inaktiv)
- Anzahl Collections und Gespräche
- Aktionsmenü mit allen Funktionen
- Skeleton Loading während des Ladens
- Empty State wenn keine Chatbots vorhanden

---

### 3. ChatbotEditor.vue
**Dialog** zum Erstellen und Bearbeiten von Chatbots.

**Props:**
- `modelValue` (Boolean) - Dialog-Status
- `chatbot` (Object) - Zu bearbeitender Chatbot (null für neuen Chatbot)
- `collections` (Array) - Verfügbare Collections
- `isEdit` (Boolean) - Bearbeitungs-Modus

**Emits:**
- `update:modelValue(boolean)` - Dialog schließen
- `save(chatbotData)` - Änderungen speichern

**Tabs:**

#### Tab 1: Allgemein
- Technischer Name (name)
- Anzeigename (display_name)
- Beschreibung
- Icon-Auswahl (8 Icons verfügbar)
- Farbauswahl (Color-Picker)
- Willkommensnachricht
- Fallback-Nachricht
- Status-Schalter (aktiv/öffentlich)

#### Tab 2: LLM-Einstellungen
- **Prompt-Vorlagen:** 4 vordefinierte Templates (Support, FAQ, Onboarding, Technisch)
- System Prompt (Textarea mit Zeilennummern)
- Modell (z.B. gpt-4, gpt-3.5-turbo)
- Temperatur (Slider 0-2)
- Max. Tokens
- Top P (Nucleus Sampling)

#### Tab 3: RAG
- RAG aktivieren/deaktivieren
- Anzahl Dokumente (k) - Wie viele Dokumente abgerufen werden
- Minimale Relevanz (0-1) - Schwellwert für Dokumenten-Relevanz
- Quellen einbeziehen - Zeigt Quellenangaben in Antworten

#### Tab 4: Collections
- Checkbox-Liste aller verfügbaren Collections
- Zeigt Dokumentenanzahl pro Collection

**Features:**
- Persistent Dialog (schließt nicht bei Klick außerhalb)
- Scrollbar bei viel Inhalt
- Prompt-Editor mit Zeilennummern und Zeichenzähler
- Validierung (Required-Felder)
- Theme-aware (Light/Dark Mode)

---

### 4. ChatbotTestDialog.vue
**Test-Interface** für Chatbots.

**Props:**
- `modelValue` (Boolean) - Dialog-Status
- `chatbot` (Object) - Zu testender Chatbot

**Emits:**
- `update:modelValue(boolean)` - Dialog schließen

**API:**
- `POST /api/chatbots/{id}/test` - Nachricht senden

**Request Body:**
```json
{
  "message": "Benutzer-Nachricht",
  "conversation_history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "response": "Antwort des Chatbots",
  "sources": [
    { "filename": "dokument.pdf", "relevance": 0.85 }
  ],
  "tokens": 150
}
```

**Features:**
- Chat-Interface mit User/Assistant Messages
- Willkommensnachricht beim Start
- Quellenangaben bei RAG-Antworten
- Metadata anzeigen (Response-Zeit, Tokens)
- Statistiken im Footer (Anzahl Nachrichten, Ø Response-Zeit, Token-Gesamt)
- Test-Modus Badge im Header
- Auto-Scroll zu neuen Nachrichten
- Loading-Indikator während der Verarbeitung

---

### 5. CollectionAssignmentDialog.vue
**Dialog** zum Zuweisen von Collections zu einem Chatbot.

**Props:**
- `modelValue` (Boolean) - Dialog-Status
- `chatbot` (Object) - Chatbot dem Collections zugewiesen werden
- `availableCollections` (Array) - Alle verfügbaren Collections

**Emits:**
- `update:modelValue(boolean)` - Dialog schließen
- `save(data)` - Änderungen speichern

**Save Data Structure:**
```json
{
  "collection_ids": [1, 2, 3],
  "priorities": [
    { "collection_id": 1, "priority": 1 },
    { "collection_id": 2, "priority": 2 }
  ]
}
```

**Features:**
- **Zwei-Spalten-Layout:**
  - Links: Zugewiesene Collections (mit Drag & Drop Sortierung)
  - Rechts: Verfügbare Collections (mit Suchfunktion)
- **Drag & Drop:** Reihenfolge der Collections ändern (Priorität)
- **Suchfunktion:** Collections nach Name durchsuchen
- **Prioritäts-Badges:** Anzeige der Priorität (#1, #2, ...)
- **Dokumentenanzahl:** Pro Collection angezeigt
- Abhängigkeit: `vuedraggable` (bereits in package.json)

---

## Styling-Richtlinien

Alle Komponenten folgen den LLARS-Design-Richtlinien:

### Theme-Integration
- Nutzt Vuetify 3 Theme-System
- Unterstützt Light/Dark Mode automatisch
- Farben über CSS-Variablen: `rgb(var(--v-theme-on-surface))`

### Text-Farben
```css
/* Primärtext */
color: rgb(var(--v-theme-on-surface));

/* Sekundärtext */
color: rgba(var(--v-theme-on-surface), 0.75);
```

### Skeleton Loading
Alle Listen-Komponenten nutzen Skeleton Loaders:
```vue
<v-skeleton-loader v-if="loading" type="card" height="280" />
<v-card v-else>...</v-card>
```

### Transitions
```css
.card {
  transition: transform 0.2s, box-shadow 0.2s;
}
.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
}
```

---

## Integration

### In ChatbotManager.vue:

```vue
<script setup>
import ChatbotList from './ChatbotList.vue'
import ChatbotEditor from './ChatbotEditor.vue'
import ChatbotTestDialog from './ChatbotTestDialog.vue'
import CollectionAssignmentDialog from './CollectionAssignmentDialog.vue'
</script>

<template>
  <ChatbotList
    :chatbots="chatbots"
    :loading="loading"
    @edit="openEditDialog"
    @delete="confirmDelete"
    @test="openTestDialog"
    @manage-collections="openCollectionManager"
  />

  <ChatbotEditor
    v-model="dialogs.editor"
    :chatbot="selectedChatbot"
    :collections="collections"
    :is-edit="isEditMode"
    @save="saveChatbot"
  />

  <ChatbotTestDialog
    v-model="dialogs.test"
    :chatbot="selectedChatbot"
  />

  <CollectionAssignmentDialog
    v-model="dialogs.collectionAssignment"
    :chatbot="selectedChatbot"
    :available-collections="collections"
    @save="saveCollectionAssignment"
  />
</template>
```

---

## Backend-Anforderungen

Die Komponenten erwarten folgende Backend-API-Struktur:

### Chatbot-Objekt
```typescript
interface Chatbot {
  id: number
  name: string                    // Technischer Name
  display_name: string            // Anzeigename
  description?: string
  icon?: string                   // MDI-Icon (z.B. 'mdi-robot')
  color?: string                  // Hex-Farbe (z.B. '#b0ca97')
  system_prompt?: string
  model_name?: string
  temperature?: number
  max_tokens?: number
  top_p?: number
  rag_enabled?: boolean
  rag_retrieval_k?: number
  rag_min_relevance?: number
  rag_include_sources?: boolean
  welcome_message?: string
  fallback_message?: string
  is_active: boolean
  is_public: boolean
  conversation_count?: number     // Anzahl Gespräche
  collections?: Collection[]      // Zugewiesene Collections
  created_at?: string
  updated_at?: string
}
```

### Collection-Objekt
```typescript
interface Collection {
  id: number
  name: string
  display_name: string
  document_count?: number
  priority?: number               // Für Sortierung
}
```

---

## Entwicklung

### Neue Features hinzufügen

1. **Neues Feld in ChatbotEditor:**
   - Feld zum entsprechenden Tab hinzufügen
   - `formData` erweitern
   - Validierung hinzufügen (falls nötig)

2. **Neue Aktion in ChatbotList:**
   - Button/MenuItem hinzufügen
   - Emit definieren
   - Event-Handler in ChatbotManager implementieren

### Testing

```bash
# Frontend starten
cd llars-frontend
npm run dev

# Build testen
npm run build
```

---

## Bekannte Dependencies

- **Vue 3.4+**
- **Vuetify 3.5+**
- **axios** - HTTP-Requests
- **vuedraggable** - Drag & Drop (CollectionAssignmentDialog)
- **@mdi/font** - Material Design Icons

---

## Troubleshooting

### Chatbot wird nicht angezeigt
- Prüfen ob `is_active` auf `true` gesetzt ist
- Backend-Logs prüfen: `docker compose logs backend-flask-service`

### Test-Dialog sendet keine Nachrichten
- API-Endpoint `/api/chatbots/{id}/test` prüfen
- Browser-Console für Fehler prüfen
- Network-Tab in DevTools öffnen

### Collections können nicht zugewiesen werden
- `vuedraggable` installiert? `npm install vuedraggable`
- Backend-API für Collection-Assignment vorhanden?

### Styling-Probleme im Light Mode
- CSS-Variable `rgb(var(--v-theme-on-surface))` verwenden
- Nicht hart-codierte Farben nutzen

---

**Stand:** 26. November 2025
**Version:** 1.0
**Autor:** Claude Code
