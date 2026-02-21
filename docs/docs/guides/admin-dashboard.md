# Admin Dashboard

**Version:** 1.1 | **Stand:** Januar 2026

Das Admin Dashboard ist die zentrale Verwaltungsoberfläche für LLARS. Administratoren verwalten hier Nutzer, Szenarien, Chatbots, RAG‑Daten, LLM‑Provider, Systemeinstellungen und Live‑Monitoring.

---

## Übersicht

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Admin Dashboard                                                            │
├──────────────┬──────────────────────────────────────────────────────────────┤
│  Navigation  │  Übersicht                                                   │
│  ──────────  │  ─────────────────────────────────────────────────────────   │
│              │                                                              │
│  📊 Übersicht│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  📈 Analytics│  │ Benutzer │ │ Szenarien│ │RAG Docs  │ │Completion│       │
│  🫀 Health   │  │    42    │ │    15    │ │   234    │ │   78%    │       │
│  🖥 System   │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  👥 Benutzer │                                                              │
│  📋 Szenarien│  Letzte Aktivitäten                                          │
│  🤖 Chatbots │  Schnellaktionen                                              │
│  📄 RAG      │  Aktive Szenarien                                             │
│  🔐 Rechte   │                                                              │
│  🔧 LLM      │  System Health                                               │
│  ⚙️ Settings │                                                              │
│  …           │  (weitere Tabs: Presence, Chatbot Activity, Docker, DB, …)   │
└──────────────┴──────────────────────────────────────────────────────────────┘
```

---

## Schnellstart

!!! tip "Wichtigste Admin‑Aufgaben"
    1. **Nutzer verwalten** → Rollen zuweisen, Accounts sperren
    2. **Szenarien überwachen** → Fortschritt prüfen, Engpässe erkennen
    3. **LLM‑Provider & Modelle** → Provider konfigurieren, Kosten prüfen
    4. **System‑Health** → CPU/RAM, Events und Fehlermeldungen im Blick
    5. **RAG & Crawler** → Collections und Dokumente aktuell halten

---

## Bereiche

### Übersicht

Das Overview‑Tab zeigt:

- **KPI‑Karten** (Benutzer, aktive Szenarien, RAG‑Dokumente, Abschlussrate)
- **System‑Health‑Bar** (Kurzstatus)
- **Letzte Aktivitäten** (mit Event‑Detaildialog)
- **Schnellaktionen** (z.B. Matomo öffnen, neues Szenario)
- **Aktive Szenarien** (Tabelle mit Fortschritt)

---

### Analytics (Matomo)

Konfiguration des Matomo‑Trackings:

- Tracking aktivieren/deaktivieren
- User‑ID, Klick‑/Hover‑Tracking, Heartbeat
- Privacy‑Optionen (z.B. Cookie‑Verzicht)
- **Matomo öffnen** Button

---

### Benutzer

Nutzerverwaltung mit Suche und Rollenfilter:

- Benutzer anlegen, sperren/entsperren, löschen
- Rollen zuweisen/entfernen
- Effektive Berechtigungen einsehen

**Benutzer‑Status**

| Status | Beschreibung |
|--------|--------------|
| **Aktiv** | Normaler Account |
| **Gesperrt** | Login deaktiviert |
| **Gelöscht** | Soft‑Delete (Daten erhalten) |

**Rollen (Beispiele)**

| Rolle | Berechtigungen |
|-------|----------------|
| **Admin** | Vollzugriff |
| **Researcher** | Szenarien + Prompt Engineering |
| **Evaluator** | An Evaluationen teilnehmen |
| **Chatbot Manager** | Chatbots und RAG verwalten |

---

### Szenarien

Admin‑Übersicht aller Szenarien:

- Liste mit Typ, Start, Status
- Detail‑Statistiken (Progress, Items, Agreement)

---

### Chatbots

Zentrale Verwaltung aller Chatbots:

- Chatbot‑Wizard starten
- Settings, Collections, Tests
- Zugriff über Rollen/Benutzer steuern

---

### Chatbot Activity

Monitoring von Chatbot‑bezogenen Events:

- Chats, Wizard‑Status, Dokumente, Collections
- Filter nach Zeitraum, Benutzer, Typ

---

### RAG

RAG‑Admin mit Statistiken und Embedding‑Info:

- **Stats**: Dokumente, verarbeitet, Collections, Gesamtgröße
- **Embedding‑Modell**: aktives Modell, Dimensionen, Provider‑Status
- **Tabs**: Dokumente, Collections, Upload

---

### Crawler

Web‑Crawler für RAG‑Ingestion:

- Quellen hinzufügen
- Crawl‑Status und Fehler einsehen
- Defaults über System Settings (Pages/Depth/Timeouts)

---

### Field Prompts (AI Assist)

Prompt‑Vorlagen für KI‑Feldassistenz:

- Defaults seeden
- Prompts erstellen, testen, aktivieren/deaktivieren

---

### Berechtigungen

Mehrtab‑Interface:

- **Rollen** (anzeigen/erstellen)
- **Berechtigungen** (kategorisiert)
- **Chatbots** (Zugriffs‑Allowlist)
- **LLM Modelle** (Zugriffs‑Allowlist)
- **Audit Log** (Änderungen nachvollziehen)

---

### LLM Provider

Provider‑ und Modellverwaltung:

- Quick Connect (OpenAI, Anthropic, LiteLLM, Ollama)
- Provider testen, synchronisieren
- Modelle konfigurieren (Kosten, Kontextfenster, Capabilities)

---

### Referrals

Referral‑System für Einladungen:

- Kampagnen und Links verwalten
- Registrierungen auswerten
- Status: aktiv, archiviert, deaktiviert

---

### Presence

Live‑Nutzer‑Presence:

- Online/Active/Offline‑Status
- Suche und Filter
- Letzte Aktivität und letzter Zugriff

---

### Docker Monitor

Live‑Monitoring der Container:

- Status, Health, CPU/RAM
- Netzwerk‑Traffic (RX/TX)
- Containerliste mit Live‑Updates

---

### DB Explorer

Direkter Blick in DB‑Tabellen (read‑only):

- Tabellenliste mit Suche
- Limit/Filter
- Vorschau der Daten

---

### System Health

Systemstatus mit Metriken:

- Host Metrics (CPU/RAM/Disk)
- API‑Performance
- WebSocket‑Status

---

### System Events

Live‑Event‑Stream mit Filterung:

- Severity‑Filter (info/warn/error)
- Suche nach Typ/Message/User
- Event‑Detaildialog (Entity, ID, JSON‑Copy)

---

### Systemeinstellungen

Globale Konfiguration:

- **Crawler Timeouts** (Crawl + Embedding)
- **Crawler Defaults** (Max Pages/Depth)
- **RAG Chunking** (Chunk Size/Overlap)
- **LLM Logging** (Prompts/Responses, Tasks, Max‑Chars)
- **Referral System** (Enable, Self‑Registration, Default‑Role)
- **AI Assistant** (Enable, Username, Farbe)
- **Zotero OAuth** (Env vs DB Fallback)

---

## API‑Endpunkte

### Benutzer

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/admin/users` | GET | Benutzer auflisten |
| `/api/admin/users` | POST | Benutzer erstellen |
| `/api/admin/users/:username` | PATCH | Benutzer aktualisieren |
| `/api/admin/users/:username` | DELETE | Benutzer löschen |

### Szenarien

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/admin/scenarios` | GET | Szenarien auflisten |
| `/api/admin/scenario_progress_stats/:id` | GET | Fortschritts‑Statistiken |

### Berechtigungen

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/permissions` | GET | Alle Berechtigungen |
| `/api/permissions/roles` | GET/POST | Rollen listen/erstellen |
| `/api/permissions/roles/:role/permissions` | PUT | Rollen‑Berechtigungen setzen |
| `/api/permissions/user/:username` | GET | User‑Permissions + Rollen |
| `/api/permissions/grant` | POST | Permission vergeben |
| `/api/permissions/revoke` | POST | Permission entziehen |
| `/api/permissions/assign-role` | POST | Rolle zuweisen |
| `/api/permissions/unassign-role` | POST | Rolle entfernen |
| `/api/permissions/audit-log` | GET | Audit‑Log |

### LLM

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/llm/providers` | GET/POST | Provider verwalten |
| `/api/llm/providers/:id/test` | POST | Verbindung testen |
| `/api/llm/providers/:id/sync-models` | POST | Modelle synchronisieren |
| `/api/llm/models` | GET/POST | Modelle verwalten |
| `/api/llm/models/:id/set-default` | POST | Default setzen |

### Analytics

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/admin/analytics/settings` | GET/PATCH | Matomo‑Settings |

### System

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/admin/system/settings` | GET/PATCH | Systemeinstellungen |
| `/api/admin/system/events` | GET | Event‑Liste (Filter/Limit) |
| `/api/admin/system/events/stream` | GET | Event‑Stream (SSE) |

### Referrals

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/referral/admin/campaigns` | GET/POST | Kampagnen verwalten |
| `/api/referral/admin/campaigns/:id` | GET/PUT/DELETE | Kampagne lesen/ändern/löschen |
| `/api/referral/admin/campaigns/:id/links` | GET/POST | Links einer Kampagne |
| `/api/referral/admin/links/:id` | GET/PUT/DELETE | Link verwalten |
| `/api/referral/admin/analytics/overview` | GET | Referral‑Overview |
| `/api/referral/admin/registrations` | GET | Registrierungen |

---

## Berechtigungen

| Permission | Beschreibung |
|------------|--------------|
| `admin:users:manage` | Benutzer verwalten |
| `admin:system:configure` | System konfigurieren |
| `admin:permissions:manage` | Berechtigungen verwalten |
| `admin:roles:manage` | Rollen verwalten |
| `admin:field_prompts:manage` | KI‑Prompts verwalten |
| `feature:llm:edit` | LLM‑Modelle bearbeiten |
| `feature:rag:edit` | RAG‑Collections bearbeiten |

---

## Siehe auch

- [Berechtigungssystem](permission-system.md) – Detaillierte Rechte‑Dokumentation
- [Chatbot Wizard](chatbot-wizard.md) – Chatbots erstellen
- [Authentik Setup](authentik-setup.md) – Auth‑Konfiguration
