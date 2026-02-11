# Chatbot Builder mit Web Crawler RAG Pipeline

!!! success "Status: Implementiert (Stand Februar 2026)"
    Der Chatbot Builder ist produktiv nutzbar und ersetzt das frühere `chatbot-rag` Konzept.
    Der Wizard führt in 5 Schritten von URL → Crawl → Embedding → Konfiguration → Review.

## Übersicht

Ein **integriertes Chatbot-Builder-System**, das Web Crawling, RAG-Embedding und Chatbot-Konfiguration verbindet. Benutzer können in wenigen Schritten einen vollständigen, auf einer Website basierenden Chatbot erstellen.

**Kernidee:**
```
URL eingeben → Crawlen → Embedden → Konfigurieren → Testen → Veröffentlichen
```

## Dokumentation

| Dokument | Beschreibung | Status |
|----------|--------------|--------|
| [Konzept](konzept.md) | Technische Spezifikation (DB, API, Frontend) | Aktualisiert |
| [Hybrid Search](hybrid-search.md) | Aktueller Such-Stack (Standard + Agent-Tools) | Implementiert |
| [Chatbot Wizard](../../guides/chatbot-wizard.md) | Schritt-für-Schritt-Anleitung | Aktuell |

## Umgesetzte Features

- 5‑Schritte Wizard: URL → Crawl → Embedding → Config → Review
- Web Crawler mit Playwright-Option, Screenshots und optionalem Vision‑LLM
- Hash‑basierte Deduplizierung + n:m Collection ↔ Dokumente
- Collection‑basierter Embedding‑Fortschritt via Socket.IO
- Feld‑Generierung (Name, Display Name, Prompt, Welcome, Icon, Farbe)
- Pause/Resume/Cancel der Build‑Pipeline
- Admin‑Testdialog im Chatbot Manager

## Offene Punkte

- Sitemap.xml‑Discovery im Crawler (geplant)
- Multi‑Collection‑Auswahl im Wizard (aktuell nachträglich im Chatbot Manager)

## Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                   Chatbot Builder Wizard                         │
│   [URL] → [Crawl] → [Embedding] → [Config] → [Review/Test]        │
└─────────────────────────────────────┬───────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend APIs                              │
├─────────────────────────────────────────────────────────────────┤
│  /api/chatbots/wizard/*  /api/chatbots/*  /api/rag/*  /api/crawler/* │
│  Socket.IO Events: wizard:*  crawler:*  rag:*                      │
└─────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Datenbank (MariaDB)                        │
├─────────────────────────────────────────────────────────────────┤
│  rag_documents ↔ rag_document_chunks                             │
│  rag_collections ↔ collection_document_links ↔ rag_documents      │
│  rag_collections ↔ collection_embeddings                          │
│  chatbots ↔ chatbot_collections                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Implementierungsstatus (Kurz)

- Datenbank‑Erweiterungen für Build‑Status und Embedding‑Tracking: umgesetzt
- Wizard‑Backend + Socket.IO Progress: umgesetzt
- Wizard‑Frontend inkl. Resume: umgesetzt
- Admin‑Testdialog: umgesetzt

## Abgrenzung zum alten chatbot-rag Konzept

| Aspekt | Alt (chatbot-rag) | Neu (chatbot-builder) |
|--------|-------------------|----------------------|
| Fokus | Separate Chatbot + RAG Verwaltung | Integrierter Builder Workflow |
| Crawler | Manuell starten | Im Wizard integriert |
| Embedding Progress | Nicht sichtbar | Live via Socket.IO |
| Konfiguration | Manuell alle Felder | KI‑gestützte Generierung |
| Testseite | Einfacher Test‑Dialog | Admin‑Testdialog |
| Dokumente | Einfache Referenz | Hash‑Deduplizierung + n:m |
