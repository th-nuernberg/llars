# Chatbot Builder mit Web Crawler RAG Pipeline

!!! warning "Status: Konzept"
    Dieses Projekt befindet sich in der **Konzeptphase**.
    Ersetzt das bisherige chatbot-rag Konzept.

## Übersicht

Ein **integriertes Chatbot-Builder-System** das nahtlos Web Crawling, RAG-Embedding und Chatbot-Konfiguration verbindet. Benutzer können in wenigen Schritten einen vollständigen, auf einer Website basierenden Chatbot erstellen.

**Kernidee:**
```
URL eingeben → Crawlen → Embedden → Konfigurieren → Testen → Veröffentlichen
```

## Dokumentation

| Dokument | Beschreibung | Status |
|----------|--------------|--------|
| [Konzept](konzept.md) | Vollständige Spezifikation mit DB, API, Frontend | Fertig |

## Geplante Features

### Web Crawler (Fixes & Verbesserungen)
- Hash-basierte Dokumenten-Deduplizierung
- n:m Beziehung Collection ↔ Dokumente
- WebSocket Live-Progress

### RAG Pipeline
- Separate `rag_embeddings` Tabelle
- Collection-basierter Embedding-Fortschritt via WebSocket
- Real-time Progress-Anzeige pro Collection

### Chatbot Builder Wizard
- 5-Schritte Wizard: URL → Crawl → Embed → Config → Test
- Generate-Buttons (KI-gestützt) für alle Textfelder
- Kontextbasierte Feldgenerierung

### Admin-Testseite
- Live-Test mit Quellen-Anzeige
- Schnell-Einstellungen (Temperature, RAG-K)
- Statistiken und Analytics

## Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                   Chatbot Builder Wizard                         │
│   [URL] → [Crawl Progress] → [Embed Progress] → [Config] → [Test]│
└─────────────────────────────────────┬───────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend APIs                              │
├─────────────────────────────────────────────────────────────────┤
│  /api/crawler/*        │  /api/rag/*        │  /api/chatbots/*  │
│  /api/chatbot-builder/*│  WebSocket Events  │                   │
└─────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Datenbank (MariaDB)                        │
├─────────────────────────────────────────────────────────────────┤
│  rag_documents ←→ rag_embeddings                                │
│       ↕                                                         │
│  collection_document_links ←→ rag_collections ←→ chatbots       │
└─────────────────────────────────────────────────────────────────┘
```

## Implementierungs-Phasen

1. [ ] **Datenbank-Refactoring** - Neue Tabellen, Migrations
2. [ ] **Embedding Worker** - Collection-basiertes Processing, WebSocket
3. [ ] **Chatbot Builder API** - Create, Generate-Field, Status
4. [ ] **Frontend Wizard** - 5-Schritte Komponenten
5. [ ] **Admin-Testseite** - Tweak-Panel, Live-Chat
6. [ ] **Testing & Polish** - E2E Tests, Performance

## Abgrenzung zum alten chatbot-rag Konzept

| Aspekt | Alt (chatbot-rag) | Neu (chatbot-builder) |
|--------|-------------------|----------------------|
| Fokus | Separate Chatbot + RAG Verwaltung | Integrierter Builder Workflow |
| Crawler | Manuell starten | In Wizard integriert |
| Embedding Progress | Nicht sichtbar | Real-time WebSocket |
| Konfiguration | Manuell alle Felder | KI-gestützte Generierung |
| Testseite | Nur Test-Dialog | Vollständige Admin-Seite |
| Dokumente | Einfache Referenz | Hash-Deduplizierung + n:m |
