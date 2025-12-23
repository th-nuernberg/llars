# YJS Server - LLARS Real-time Collaboration

WebSocket-Server für Echtzeit-Kollaboration in LLARS (Prompt Engineering, Markdown Collab) mit YJS CRDT und Authentik JWT-Authentifizierung.

## Features

- **Echtzeit-Kollaboration**: Mehrere Nutzer bearbeiten Dokumente gleichzeitig
- **JWT-Authentifizierung**: Alle Verbindungen via Authentik gesichert
- **User-Awareness**: Cursor-Tracking und Präsenz-Anzeige
- **DB-Persistenz**: Automatisches Speichern in MariaDB
- **Markdown-Tabellen**: Access-Kontrolle für Markdown-Workspaces

## Architektur

```
┌─────────────────┐     nginx (/collab/)     ┌──────────────┐
│  LLARS Frontend │ ────────────────────────> │  YJS Server  │
│  (Vue + YJS)    │ <──────────────────────── │  (Node.js)   │
└─────────────────┘    WebSocket + JWT       └──────────────┘
                                                     │
                                                     │ Persist
                                                     ▼
                                              ┌──────────────┐
                                              │   MariaDB    │
                                              └──────────────┘
```

## Verbindung

### Via nginx (Standard)

Client verbindet über nginx-Proxy auf `/collab/`:

```javascript
import { io } from 'socket.io-client'

const socket = io(window.location.origin, {
  path: '/collab/socket.io/',  // nginx leitet /collab/ → YJS-Server
  auth: {
    token: authToken  // Authentik JWT
  }
})
```

### Direkt (nur Debugging)

Bei Direktverbindung auf Port 8082:

```javascript
const socket = io('http://localhost:8082', {
  path: '/socket.io/',  // Server nutzt Standard-Pfad
  auth: { token: authToken }
})
```

**Wichtig:** nginx entfernt das `/collab/`-Prefix, daher nutzt der Server intern `/socket.io/`.

## Authentication Flow

1. **Client sendet Token** im `auth`-Objekt bei Verbindungsaufbau
2. **Server validiert** via Authentik JWKS-Endpoint (RS256)
3. **Bei Erfolg** erhält Socket User-Informationen:

```javascript
socket.user = {
  username: 'admin',
  odssUserId: 'authentik-uuid',
  email: 'admin@localhost',
  roles: ['authentik Admins'],
  isAdmin: true
}
```

## Event-API

### Client → Server

| Event | Payload | Beschreibung |
|-------|---------|--------------|
| `join_room` | `{ room: 'room_123' }` | Raum beitreten |
| `sync_update` | `{ room, update: Uint8Array }` | YJS-Update senden |
| `cursor_update` | `{ room, blockId, range }` | Cursor-Position |
| `leave_room` | `'room_123'` | Raum verlassen |

### Server → Client

| Event | Payload | Beschreibung |
|-------|---------|--------------|
| `snapshot_document` | `Uint8Array` | Initiales Dokument |
| `room_state` | `{ users, cursors }` | Aktuelle Raum-Nutzer |
| `user_joined` | `{ userId, username, color }` | Nutzer beigetreten |
| `user_left` | `{ userId }` | Nutzer verlassen |
| `sync_update` | `{ update: Uint8Array }` | YJS-Updates |
| `cursor_updated` | `{ userId, cursor }` | Cursor-Änderung |

## Datenbank-Tabellen

### user_prompts (Prompt Engineering)

```sql
CREATE TABLE user_prompts (
  prompt_id INT PRIMARY KEY AUTO_INCREMENT,
  user_id VARCHAR(255),
  name VARCHAR(255),
  content TEXT,  -- YJS state als JSON
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### markdown_collab_* (Markdown Workspaces)

```sql
-- Workspaces
CREATE TABLE markdown_collab_workspaces (
  id INT PRIMARY KEY AUTO_INCREMENT,
  uuid VARCHAR(36) UNIQUE,
  name VARCHAR(255),
  owner_id VARCHAR(255),
  is_public BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Access Control
CREATE TABLE markdown_collab_workspace_access (
  id INT PRIMARY KEY AUTO_INCREMENT,
  workspace_id INT,
  user_id VARCHAR(255),
  role ENUM('viewer', 'editor', 'owner'),
  FOREIGN KEY (workspace_id) REFERENCES markdown_collab_workspaces(id)
);

-- YJS Documents
CREATE TABLE markdown_collab_documents (
  id INT PRIMARY KEY AUTO_INCREMENT,
  workspace_id INT,
  yjs_state LONGBLOB,  -- YJS binary state
  updated_at TIMESTAMP,
  FOREIGN KEY (workspace_id) REFERENCES markdown_collab_workspaces(id)
);
```

## Environment Variables

```bash
# Authentik (JWT-Validierung)
AUTHENTIK_ISSUER_URL=http://authentik-server:9000/application/o/llars-backend/

# Server
PORT=8082

# MariaDB
MYSQL_HOST=db-maria-service
MYSQL_PORT=3306
MYSQL_USER=dev_user
MYSQL_PASSWORD=dev_password_change_me
MYSQL_DATABASE=database_llars
```

## Entwicklung

```bash
# Installation
npm install

# Development (mit nodemon)
npm run dev

# Production
npm start
```

## Fehlerbehandlung

| Fehler | Ursache |
|--------|---------|
| `Authentication required: No token provided` | Token fehlt in `auth` |
| `Authentication failed: jwt expired` | Token abgelaufen → Frontend muss refreshen |
| `Authentication failed: invalid signature` | Falscher Signing Key |
| `Error fetching signing key` | Authentik nicht erreichbar |

## nginx-Konfiguration (Referenz)

```nginx
location /collab/ {
    proxy_pass http://yjs-service:8082/;  # Prefix wird entfernt!
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## Referenzen

- [Y.js Dokumentation](https://docs.yjs.dev/)
- [Socket.IO v4](https://socket.io/docs/v4/)
- [Authentik OIDC](https://docs.goauthentik.io/)
