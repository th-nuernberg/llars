# Admin-Panel Guide

Diese Anleitung dokumentiert alle Funktionen des LLARS Admin-Panels.

!!! info "Zugriff"
    Das Admin-Panel ist unter `/admin` erreichbar und erfordert die Rolle `admin`.

---

## Übersicht

Das Admin-Panel bietet folgende Funktionen:

| Bereich | Beschreibung | Permission |
|---------|--------------|------------|
| **Dashboard** | Systemübersicht und Statistiken | `admin:dashboard:view` |
| **Benutzer** | Benutzerverwaltung | `admin:users:view` |
| **Chatbots** | Chatbot-Aktivitäten | `admin:chatbots:view` |
| **RAG** | Dokument-Management | `admin:rag:view` |
| **Docker Monitor** | Container-Überwachung | `admin:docker:view` |
| **Datenbank** | DB-Explorer | `admin:database:view` |
| **Analytics** | Matomo-Einstellungen | `admin:analytics:view` |
| **System** | Systemeinstellungen | `admin:settings:view` |

---

## Docker Monitor

Der Docker Monitor zeigt Echtzeit-Informationen zu allen LLARS-Containern.

### Funktionen

#### Container-Liste

Zeigt alle Container mit:

- **Status**: Running/Stopped/Restarting
- **CPU-Auslastung**: Prozentuale CPU-Nutzung
- **RAM-Auslastung**: Speicherverbrauch in MB/GB
- **Netzwerk**: Eingehender/Ausgehender Traffic

#### Performance-Charts

Echtzeit-Diagramme für:

- CPU-Verlauf (letzte 5 Minuten)
- Speicher-Verlauf (letzte 5 Minuten)
- Netzwerk-Traffic

#### Container-Logs

Live-Streaming der Container-Logs mit:

- Auto-Scroll
- Filterung nach Log-Level
- Download als Textdatei

### Verwendung

1. Navigiere zu **Admin → Docker Monitor**
2. Wähle einen Container aus der Liste
3. Logs werden automatisch gestreamt
4. Charts aktualisieren sich in Echtzeit

### Technische Details

```javascript
// WebSocket-Verbindung zum Docker Monitor
socket.emit('docker:subscribe')

// Events
socket.on('docker:stats', (data) => {
  // data = { containers: [...], summary: {...} }
})

socket.on('docker:logs', (data) => {
  // data = { container_id, logs: [...] }
})
```

!!! warning "Sicherheitshinweis"
    Der Docker Monitor benötigt Zugriff auf `/var/run/docker.sock`.
    Dies ermöglicht theoretisch Host-Docker-Kontrolle.
    **Nur für vertrauenswürdige Admins aktivieren!**

---

## Datenbank-Explorer

Der DB-Explorer ermöglicht schreibgeschützten Zugriff auf LLARS-Tabellen.

### Funktionen

- **Tabellen-Browser**: Alle Tabellen auflisten
- **Daten-Viewer**: Tabelleninhalte anzeigen
- **Filterung**: Spaltenweise Filterung
- **Sortierung**: Spaltenweise Sortierung
- **Pagination**: Große Tabellen seitenweise anzeigen
- **Export**: CSV-Download

### Verwendung

1. Navigiere zu **Admin → Datenbank**
2. Wähle eine Tabelle aus der Seitenleiste
3. Nutze die Filter- und Sortieroptionen
4. Exportiere bei Bedarf als CSV

### Technische Details

```javascript
// WebSocket-Events für DB Explorer
socket.emit('db:list_tables')
socket.on('db:tables', (tables) => { ... })

socket.emit('db:query', {
  table: 'users',
  limit: 50,
  offset: 0,
  order_by: 'created_at',
  order_dir: 'desc'
})
socket.on('db:result', (data) => { ... })
```

!!! note "Schreibschutz"
    Der DB-Explorer ist **nur lesend**. Datenänderungen sind
    über dieses Interface nicht möglich.

---

## Analytics-Einstellungen

Konfiguration der Matomo-Integration.

### Einstellungen

| Einstellung | Beschreibung | Standard |
|-------------|--------------|----------|
| `tracking_enabled` | Tracking aktivieren | `true` |
| `track_user_id` | User-ID tracken | `false` |
| `track_search` | Suchbegriffe tracken | `true` |
| `cookie_consent_required` | Cookie-Consent erforderlich | `true` |

### API

```http
GET /api/admin/analytics/settings
```

```json
{
  "success": true,
  "settings": {
    "tracking_enabled": true,
    "track_user_id": false,
    "track_search": true,
    "cookie_consent_required": true,
    "matomo_site_id": 1
  }
}
```

```http
PATCH /api/admin/analytics/settings
Content-Type: application/json

{
  "tracking_enabled": false
}
```

---

## Benutzerverwaltung

### Benutzer-Liste

Zeigt alle Benutzer mit:

- Benutzername und E-Mail
- Rollen
- Letzter Login
- Aktionen (Bearbeiten, Deaktivieren)

### Berechtigungen bearbeiten

1. Klicke auf **Bearbeiten** bei einem Benutzer
2. Wähle Rollen aus der Liste
3. Füge individuelle Berechtigungen hinzu/entferne sie
4. Speichern

### Bulk-Aktionen

- Mehrere Benutzer auswählen
- Rolle zuweisen
- Deaktivieren

---

## Chatbot-Aktivitäten

### Übersicht

- Anzahl aktiver Chatbots
- Gesamtzahl Konversationen
- Nachrichten pro Tag (Chart)

### Details pro Chatbot

- Konversations-Statistiken
- Häufigste Fragen
- Durchschnittliche Antwortzeit
- Error-Rate

### Export

- Konversationen als JSON/CSV exportieren
- Zeitraum auswählen
- Nach Chatbot filtern

---

## RAG-Management

### Collections-Übersicht

| Spalte | Beschreibung |
|--------|--------------|
| Name | Collection-Name |
| Dokumente | Anzahl Dokumente |
| Chunks | Anzahl Chunks |
| Größe | Gesamtgröße |
| Status | Indexierungs-Status |

### Dokument-Queue

Zeigt alle Dokumente in der Verarbeitungs-Queue:

- **Pending**: Warten auf Verarbeitung
- **Processing**: Aktuell in Bearbeitung
- **Failed**: Fehlgeschlagen (mit Fehlermeldung)

### Aktionen

- **Reindex**: Dokument neu indexieren
- **Delete**: Dokument löschen
- **Move**: In andere Collection verschieben

---

## System-Einstellungen

### Allgemeine Einstellungen

| Einstellung | Beschreibung |
|-------------|--------------|
| `site_name` | Anzeigename der Instanz |
| `maintenance_mode` | Wartungsmodus aktivieren |
| `registration_enabled` | Selbstregistrierung erlauben |

### LLM-Einstellungen

| Einstellung | Beschreibung |
|-------------|--------------|
| `default_llm_model` | Standard-LLM für neue Chatbots |
| `default_embedding_model` | Standard-Embedding-Modell |
| `litellm_base_url` | LiteLLM Proxy URL |
| `litellm_api_key` | LiteLLM API Key |

### Speicher-Einstellungen

| Einstellung | Beschreibung |
|-------------|--------------|
| `storage_path` | Basis-Speicherpfad |
| `max_upload_size` | Max. Upload-Größe in MB |
| `allowed_file_types` | Erlaubte Dateitypen |

---

## Troubleshooting

### Docker Monitor zeigt keine Daten

1. Prüfe ob `/var/run/docker.sock` gemountet ist
2. Prüfe Docker-Socket-Berechtigungen:
   ```bash
   docker exec llars_flask_service ls -la /var/run/docker.sock
   ```
3. Starte Backend neu:
   ```bash
   docker restart llars_flask_service
   ```

### DB Explorer zeigt Fehler

1. Prüfe MariaDB-Verbindung:
   ```bash
   docker exec llars_flask_service python -c "from db.db import db; print(db.engine.url)"
   ```
2. Prüfe Berechtigungen des DB-Users

### Analytics nicht verfügbar

1. Prüfe Matomo-Container:
   ```bash
   docker logs llars_matomo_service
   ```
2. Prüfe `MATOMO_SITE_ID` in `.env`
