# LLARS - LLM-Assisted Rating System

**Stand:** 20. November 2025
**Version:** 2.0 (mit Keycloak-Integration)

## 📋 Inhaltsverzeichnis

1. [Projekt-Übersicht](#projekt-übersicht)
2. [Architektur](#architektur)
3. [Keycloak-Integration](#keycloak-integration)
4. [Services](#services)
5. [Sicherheit](#sicherheit)
6. [Entwicklung](#entwicklung)
7. [Deployment](#deployment)
8. [API-Dokumentation](#api-dokumentation)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Projekt-Übersicht

LLARS ist ein System zur kollaborativen Bewertung von E-Mails und Szenarien mit Hilfe von Large Language Models (LLMs). Das System unterstützt:

- **Multi-User Collaboration**: Echtzeit-Zusammenarbeit via WebSocket (YJS CRDT)
- **LLM-Integration**: OpenAI-Modelle für intelligente Prompts
- **Role-Based Access Control**: Admin, Rater, Viewer via Keycloak
- **RAG-Pipeline**: Retrieval-Augmented Generation mit ChromaDB
- **Flexible Bewertung**: Verschiedene Ranking-Methoden und Szenarien

### Hauptfunktionen

1. **Mail-Rating**: Bewertung von E-Mails nach verschiedenen Kriterien
2. **Prompt Engineering**: Kollaborative Prompt-Entwicklung mit Echtzeit-Synchronisation
3. **Scenario Management**: Verwaltung und Bewertung von Use-Cases
4. **Admin Dashboard**: Benutzerverwaltung und System-Monitoring

---

## 🏗️ Architektur

### Tech-Stack

#### Backend
- **Framework**: Flask 3.0.0 mit SocketIO 5.3.6
- **Datenbank**: MariaDB 11.2.2
- **Authentication**: Keycloak 26.0.7 mit PostgreSQL 16
- **LLM**: OpenAI API (gpt-4, gpt-3.5-turbo)
- **RAG**: LangChain + ChromaDB + Sentence Transformers

#### Frontend
- **Framework**: Vue.js 3.4.0 + Vuetify 3.5.0
- **Build Tool**: Vite 5.1.0
- **Routing**: Vue Router 4.3.0
- **State**: Keycloak JS Adapter 26.0.7
- **Collaboration**: Socket.IO Client 4.7.4 + Y.js 13.4.7

#### Infrastructure
- **Reverse Proxy**: Nginx (Alpine)
- **Containerization**: Docker Compose
- **Real-time Sync**: YJS Server (Node.js 23)
- **Background Tasks**: Supervisor Service (Python)

### Service-Übersicht

```
┌──────────────────┐
│  nginx (Port 80) │  ← Reverse Proxy + Load Balancer
└─────────┬────────┘
          │
    ┌─────┼─────────────────┬──────────────────┬────────────────┐
    │     │                 │                  │                │
┌───▼──┐ ┌▼────────┐  ┌────▼─────┐  ┌────────▼──────┐  ┌──────▼───────┐
│ Vue  │ │ Flask   │  │ Keycloak │  │ YJS WebSocket │  │  Supervisor  │
│:5173 │ │ :8081   │  │  :8090   │  │     :8082     │  │   Service    │
└──────┘ └─────┬───┘  └────┬─────┘  └───────┬───────┘  └──────┬───────┘
               │           │                 │                 │
        ┌──────┴───────────┴─────────────────┴─────────────────┘
        │
   ┌────▼──────┐        ┌────────────┐
   │  MariaDB  │        │ PostgreSQL │
   │   :3306   │        │   :5432    │
   └───────────┘        └────────────┘
     (LLARS DB)         (Keycloak DB)
```

---

## 🔐 Keycloak-Integration

### Übersicht

Die Keycloak-Integration wurde vollständig implementiert und ersetzt das alte Flask-JWT-Extended System. Alle Authentifizierungsflows laufen nun über Keycloak.

### Konfiguration

**Realm**: `llars`

**Clients**:
- `llars-frontend` (Public Client)
  - Protocol: openid-connect
  - Access Type: public
  - Standard Flow: enabled
  - Direct Access Grants: enabled

- `llars-backend` (Confidential Client)
  - Protocol: openid-connect
  - Access Type: confidential
  - Service Accounts: enabled
  - Client Secret: `llars-backend-secret-change-in-production`

**Rollen**:
- `admin`: Vollzugriff, User-Management, Scenario-Erstellung
- `rater`: Bewertung von Mails, Prompt-Engineering
- `viewer`: Nur Lesezugriff

**Gruppen**:
- `Admin`: Automatisch admin-Rolle
- `Raters`: Automatisch rater-Rolle
- `Standard`: Automatisch viewer-Rolle

### Backend-Implementierung

#### Token-Validierung (`app/auth/keycloak_validator.py`)

```python
from functools import lru_cache
import requests
import jwt
from flask import request, g

KEYCLOAK_URL = os.environ.get('KEYCLOAK_URL')
KEYCLOAK_REALM = os.environ.get('KEYCLOAK_REALM')

@lru_cache(maxsize=1)
def get_public_key():
    """Holt Keycloak Public Key (gecacht)"""
    certs_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
    response = requests.get(certs_url)
    keys = response.json()['keys'][0]
    return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(keys))

def validate_token(token: str):
    """Validiert JWT-Token mit Keycloak Public Key"""
    public_key = get_public_key()
    return jwt.decode(
        token,
        public_key,
        algorithms=['RS256'],
        audience='account',
        options={'verify_signature': True, 'verify_exp': True}
    )
```

#### Decorators (`app/auth/decorators.py`)

```python
def keycloak_required(f):
    """Basis-Authentifizierung: Token muss valide sein"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        if not token:
            return jsonify({'error': 'Missing token'}), 401

        token_payload = validate_token(token)
        if not token_payload:
            return jsonify({'error': 'Invalid token'}), 401

        g.keycloak_token = token_payload
        g.keycloak_user = get_username(token_payload)
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Admin-Only: Prüft admin-Rolle"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not has_role('admin', g.keycloak_token):
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function
```

### Frontend-Implementierung

#### Keycloak-Config (`llars-frontend/src/keycloak.config.js`)

```javascript
export const keycloakConfig = {
  url: import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:8090',
  realm: import.meta.env.VITE_KEYCLOAK_REALM || 'llars',
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'llars-frontend'
}

export const keycloakInitOptions = {
  onLoad: 'check-sso',
  pkceMethod: 'S256',
  flow: 'standard',
  checkLoginIframe: false
}
```

#### Main.js Integration

```javascript
import VueKeyCloak from '@dsb-norge/vue-keycloak-js'
import axios from 'axios'

app.use(VueKeyCloak, {
  config: keycloakConfig,
  init: keycloakInitOptions,
  onReady: (keycloak) => {
    // Axios Interceptor: Füge Bearer Token zu allen Requests hinzu
    axios.interceptors.request.use(config => {
      if (keycloak.authenticated && keycloak.token) {
        config.headers.Authorization = `Bearer ${keycloak.token}`
      }
      return config
    })

    // Automatischer Token-Refresh bei 401
    axios.interceptors.response.use(
      response => response,
      async error => {
        if (error.response?.status === 401) {
          const refreshed = await keycloak.updateToken(30)
          if (refreshed) {
            error.config.headers.Authorization = `Bearer ${keycloak.token}`
            return axios(error.config)
          }
        }
        return Promise.reject(error)
      }
    )
  }
})
```

### YJS WebSocket-Authentifizierung

Der YJS-Server validiert JWT-Tokens bei jeder WebSocket-Verbindung:

```javascript
// yjs-server/auth.js
const jwt = require('jsonwebtoken')
const jwksClient = require('jwks-rsa')

const client = jwksClient({
  jwksUri: `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/certs`,
  cache: true,
  cacheMaxAge: 600000
})

async function authenticateSocket(socket, next) {
  const token = socket.handshake.auth.token

  if (!token) {
    return next(new Error('Authentication required'))
  }

  try {
    const decoded = await verifyToken(token)
    socket.user = extractUserInfo(decoded)
    next()
  } catch (error) {
    next(new Error('Authentication failed'))
  }
}
```

---

## 🚀 Services

### 1. Nginx (Port 80)

**Funktion**: Reverse Proxy und SSL-Termination

**Konfiguration**:
```nginx
upstream frontend {
    server frontend-vue-service:5173;
}

upstream backend {
    server backend-flask-service:8081;
}

upstream keycloak {
    server keycloak-service:8080;
}

upstream yjs {
    server yjs-service:8082;
}

server {
    listen 80;
    server_name localhost;

    # Frontend
    location / {
        proxy_pass http://frontend;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend;
    }

    # Keycloak
    location /auth/ {
        proxy_pass http://keycloak;
    }

    # YJS WebSocket
    location /collab/ {
        proxy_pass http://yjs;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 2. Flask Backend (Port 8081)

**Hauptfunktionen**:
- REST API für CRUD-Operationen
- Keycloak-Token-Validierung
- LLM-Integration (OpenAI)
- RAG-Pipeline (ChromaDB)
- SocketIO für Legacy-Support

**Wichtige Routen**:
```python
# Keycloak-Auth
/auth/keycloak/me          GET   @keycloak_required
/auth/keycloak/validate    GET   Token-Validierung

# Szenarien
/api/admin/scenarios       GET   @admin_required
/api/admin/scenario/<id>   GET   @admin_required
                          POST  @admin_required
                          PUT   @admin_required
                          DELETE @admin_required

# Ratings
/api/ratings              GET   @keycloak_required
/api/rating/<id>          GET   @keycloak_required
                          POST  @keycloak_required

# Rankings
/api/rankings             GET   @keycloak_required
/api/ranking/<id>         POST  @keycloak_required

# User-Prompts
/api/user_prompts         GET   @keycloak_required
/api/user_prompt/<id>     GET   @keycloak_required
                          PUT   @keycloak_required
                          DELETE @keycloak_required
```

**Rate Limiting**:
- Default: 200/Tag, 50/Stunde
- `/auth/keycloak/me`: 100/Stunde
- `/auth/keycloak/validate`: 200/Stunde

### 3. Vue.js Frontend (Port 5173)

**Hauptkomponenten**:
- `Login.vue`: Keycloak-Login (transparent)
- `Home.vue`: Dashboard
- `AdminDashboard.vue`: Admin-Interface
- `PromptEngineering.vue`: Kollaborativer Prompt-Editor
- `RatingOverview.vue`: Mail-Bewertungen
- `RankerDetail.vue`: Detailansicht mit Vergleichen

**Routing Guards**:
```javascript
router.beforeEach((to, from, next) => {
  const keycloak = useKeycloak()

  if (to.meta.requiresAuth && !keycloak.authenticated) {
    next('/login')
  } else if (to.meta.requiresAdmin) {
    const roles = keycloak.tokenParsed?.realm_access?.roles || []
    if (!roles.includes('admin')) {
      next('/Home')
    } else {
      next()
    }
  } else {
    next()
  }
})
```

### 4. YJS WebSocket Server (Port 8082)

**Funktion**: Echtzeit-Kollaboration für Prompt Engineering

**Features**:
- JWT-Authentifizierung bei WebSocket-Verbindung
- Y.js CRDT für konfliktfreie Synchronisation
- Cursor-Tracking zwischen Benutzern
- Automatisches Speichern in MariaDB
- User-Awareness (Farben, Präsenz)

**Events**:
```javascript
// Client → Server
socket.emit('join_room', { room: 'room_123' })
socket.emit('sync_update', { room, update: Uint8Array })
socket.emit('cursor_update', { room, blockId, range })

// Server → Client
socket.on('snapshot_document', (uint8Array) => {...})
socket.on('room_state', ({ users, cursors }) => {...})
socket.on('user_joined', ({ userId, username, color }) => {...})
socket.on('sync_update', ({ update }) => {...})
```

### 5. Keycloak (Port 8090)

**Funktion**: Identity & Access Management

**Admin Console**: `http://localhost:8090/admin`
- Username: `admin`
- Password: `admin_secure_password_123`

**Initial User**:
- Username: `admin`
- Password: `admin123`
- Roles: admin, rater, viewer

### 6. MariaDB (Port 3306)

**Datenbank**: `database_llars`

**Wichtige Tabellen**:
```sql
-- Bewertungsszenarien
CREATE TABLE rating_scenarios (
  scenario_id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255),
  description TEXT,
  created_at TIMESTAMP
);

-- Mail-Bewertungen
CREATE TABLE mail_ratings (
  rating_id INT PRIMARY KEY AUTO_INCREMENT,
  scenario_id INT,
  mail_id VARCHAR(255),
  user_id VARCHAR(255),  -- Keycloak User ID
  rating_value INT,
  comment TEXT,
  created_at TIMESTAMP
);

-- User-Prompts (für YJS)
CREATE TABLE user_prompts (
  prompt_id INT PRIMARY KEY AUTO_INCREMENT,
  user_id VARCHAR(255),  -- Keycloak User ID
  name VARCHAR(255),
  content TEXT,  -- Y.js state as JSON
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Rankings
CREATE TABLE rankings (
  ranking_id INT PRIMARY KEY AUTO_INCREMENT,
  scenario_id INT,
  user_id VARCHAR(255),  -- Keycloak User ID
  method VARCHAR(50),
  result JSON,
  created_at TIMESTAMP
);
```

---

## 🔒 Sicherheit

### Implementierte Maßnahmen

#### 1. Authentifizierung & Autorisierung
- ✅ Keycloak OpenID Connect (OAuth 2.0 + JWT)
- ✅ Token-Signatur-Verifikation mit RS256
- ✅ Token-Expiration-Checks
- ✅ Role-Based Access Control (RBAC)
- ✅ WebSocket JWT-Authentifizierung

#### 2. API-Schutz
- ✅ Alle API-Routen mit `@keycloak_required` geschützt
- ✅ Admin-Routen mit `@admin_required` geschützt
- ✅ Rate Limiting (Flask-Limiter)
  - Default: 200/Tag, 50/Stunde
  - Auth-Endpoints: Spezielle Limits
- ✅ CORS-Konfiguration (nur allowed_origins)

#### 3. Production-Sicherheit
- ✅ Debug-Modus nur in development (`FLASK_ENV=development`)
- ✅ Secrets in `.env` (nicht in Git)
- ✅ `.gitignore` umfassend konfiguriert
- ✅ Docker Port-Isolation (nur nginx exponiert)
- ⚠️ SSL/TLS in Production (noch zu konfigurieren)
- ⚠️ Container als Non-Root (noch zu implementieren)

#### 4. Frontend-Sicherheit
- ✅ Keycloak Token Auto-Refresh
- ✅ Axios Interceptor für Bearer Tokens
- ✅ **XSS-Schutz mit DOMPurify** (vollständig implementiert)
  - `src/utils/sanitize.js`: Zentrale Sanitization-Utility
  - `RankerDetail.vue`: Alle v-html Direktiven geschützt (8 Stellen)
  - `TestPromptDialog.vue`: Prompt-Highlighting sanitized
  - `HistoryGenerationDetail.vue`: Message-Content sanitized
  - Siehe `llars-frontend/SECURITY.md` für Details
- ✅ CSP-Headers via nginx (konfiguriert)

### Noch zu implementieren

1. **Container-Härtung**: Non-Root User in allen Dockerfiles
2. **SSL/TLS**: HTTPS für Production mit Let's Encrypt
3. **Secrets Management**: Vault oder Kubernetes Secrets statt .env
4. **Audit Logging**: Keycloak Event Listeners + DB-Audit-Trail
5. **CSP Enhancement**: Implementierung strikter CSP-Headers

---

## 💻 Entwicklung

### Voraussetzungen

- Docker & Docker Compose
- Node.js 23+ (für lokale YJS-Entwicklung)
- Python 3.10+ (für lokales Backend-Development)

### Setup

```bash
# Repository klonen
git clone <repository-url>
cd llars

# Environment-Variablen konfigurieren
cp .env.example .env
# .env bearbeiten (Secrets, Ports, etc.)

# Development-Modus starten
docker compose up --build

# Production-Modus (nur nginx exponiert)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

### Port-Konfiguration

Alle Ports sind in `.env` konfigurierbar:

```bash
# External Ports (Development)
NGINX_EXTERNAL_PORT=80
FLASK_EXTERNAL_PORT=0        # 0 = Random Port (Debugging)
FRONTEND_EXTERNAL_PORT=0
DB_EXTERNAL_PORT=0
KEYCLOAK_EXTERNAL_PORT=8090
YJS_EXTERNAL_PORT=0

# Internal Ports (Container)
FLASK_INTERNAL_PORT=8081
FRONTEND_INTERNAL_PORT=5173
DB_INTERNAL_PORT=3306
KEYCLOAK_INTERNAL_PORT=8080
YJS_INTERNAL_PORT=8082
```

**Production**: Verwende `docker-compose.prod.yml` - entfernt alle Port-Mappings außer nginx.

### Hot-Reload

- **Frontend**: Vite Dev Server mit Watch-Mode
- **Backend**: Flask Debug-Mode mit Auto-Reload
- **YJS**: Nodemon für Auto-Restart

### Testing

```bash
# Backend Tests
docker compose exec backend-flask-service pytest

# Frontend Tests
cd llars-frontend
npm run test

# E2E Tests
npm run test:e2e
```

### Code-Stil

```bash
# Python (flake8)
docker compose exec backend-flask-service flake8 app/

# JavaScript (ESLint)
cd llars-frontend
npm run lint
```

---

## 🚀 Deployment

### Production Checklist

- [ ] `.env` Secrets ändern (Keycloak Admin, DB-Passwords, Client-Secrets)
- [ ] `PROJECT_STATE=production` setzen
- [ ] `FLASK_ENV=production` setzen
- [ ] SSL/TLS-Zertifikate in `docker/nginx/certs/` ablegen
- [ ] nginx SSL-Konfiguration aktivieren
- [ ] `docker-compose.prod.yml` verwenden
- [ ] Rate Limiting auf Redis umstellen (nicht Memory)
- [ ] Keycloak Realm exportieren und versionieren
- [ ] Backup-Strategie für Datenbanken einrichten
- [ ] Monitoring einrichten (Prometheus, Grafana)
- [ ] Logging aggregieren (ELK Stack)

### Deployment-Command

```bash
# Clean Deployment
docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Logs überwachen
docker compose logs -f

# Health-Checks
curl http://localhost/api/auth/health_check
curl http://localhost:8090/health/ready  # Keycloak
```

### Backup & Restore

```bash
# MariaDB Backup
docker compose exec db-maria-service mysqldump -u root -p database_llars > backup.sql

# PostgreSQL Backup (Keycloak)
docker compose exec keycloak-db-service pg_dump -U keycloak keycloak > keycloak_backup.sql

# Restore
docker compose exec -T db-maria-service mysql -u root -p database_llars < backup.sql
docker compose exec -T keycloak-db-service psql -U keycloak keycloak < keycloak_backup.sql
```

---

## 📚 API-Dokumentation

Siehe `KEYCLOAK_INTEGRATION_STATUS.md` für vollständige API-Dokumentation.

### Authentifizierung

Alle API-Calls (außer `/health_check`) benötigen ein Bearer Token:

```bash
# Token von Keycloak holen
curl -X POST http://localhost:8090/realms/llars/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=llars-frontend" \
  -d "username=admin" \
  -d "password=admin123" \
  -d "grant_type=password"

# API-Call mit Token
curl http://localhost/api/auth/keycloak/me \
  -H "Authorization: Bearer <your-token>"
```

---

## 🐛 Troubleshooting

### Problem: Keycloak startet nicht

```bash
# Logs prüfen
docker compose logs keycloak-service
docker compose logs keycloak-db-service

# Häufige Ursachen:
# - PostgreSQL nicht bereit → Health-Check verlängern
# - Port 8090 belegt → lsof -i :8090
# - realm-import.json Syntax-Fehler
```

### Problem: Frontend kann nicht auf Backend zugreifen

```bash
# CORS prüfen
# In .env: ALLOWED_ORIGINS korrekt gesetzt?

# Nginx-Logs checken
docker compose logs nginx-service

# Backend Health
curl http://localhost:8081/auth/health_check
```

### Problem: WebSocket-Verbindung schlägt fehl

```bash
# Token-Validierung prüfen
# Im Browser Console: Wird Token gesendet?

# YJS-Server Logs
docker compose logs yjs-service

# Keycloak Public Key erreichbar?
curl http://localhost:8090/realms/llars/protocol/openid-connect/certs
```

### Problem: "Invalid Token" bei API-Calls

```bash
# Token abgelaufen? Prüfe exp-Claim
# Frontend sollte automatisch refreshen

# Keycloak-Public-Key korrekt?
# Backend logs checken: app/auth/keycloak_validator.py
```

---

## 📝 Wichtige Dateien & Verzeichnisse

```
llars/
├── app/                          # Flask Backend
│   ├── auth/                     # Keycloak Auth Module
│   │   ├── keycloak_validator.py
│   │   └── decorators.py
│   ├── routes/                   # API Routes
│   │   ├── keycloak_routes.py
│   │   ├── ScenarioRoutes.py
│   │   ├── RatingRoutes.py
│   │   ├── RankingRoutes.py
│   │   └── ...
│   ├── db/                       # Database Models
│   ├── main.py                   # Flask App Entry
│   └── requirements.txt
├── llars-frontend/               # Vue.js Frontend
│   ├── src/
│   │   ├── components/
│   │   ├── router.js
│   │   ├── main.js
│   │   └── keycloak.config.js
│   └── package.json
├── yjs-server/                   # WebSocket Collaboration
│   ├── auth.js                   # JWT Validation
│   ├── server.js
│   ├── websocket.js
│   ├── package.json
│   └── README.md
├── docker/                       # Docker Configurations
│   ├── nginx/
│   │   ├── Dockerfile-nginx
│   │   └── nginx.conf
│   ├── keycloak/
│   │   ├── Dockerfile-keycloak
│   │   └── realm-import.json
│   ├── flask/
│   ├── vue/
│   └── ...
├── docker-compose.yml            # Development
├── docker-compose.prod.yml       # Production Override
├── .env                          # Environment Variables
├── .gitignore
├── KEYCLOAK_INTEGRATION_STATUS.md
└── CLAUDE.md                     # Diese Datei
```

---

## 🔄 Aktueller Status

**Stand: 20. November 2025**

### ✅ Abgeschlossen

1. Keycloak-Integration (100%)
   - Backend-Auth mit JWT-Validierung
   - Frontend transparente Integration
   - WebSocket JWT-Auth
   - Realm-Konfiguration mit Rollen & Gruppen

2. Security-Härtung (85%)
   - Rate Limiting implementiert
   - Debug-Modus für Production deaktiviert
   - .gitignore aktualisiert
   - Port-Konfiguration externalisiert
   - Production-Docker-Compose erstellt

3. API-Schutz (100%)
   - 44 Routes mit Keycloak-Decorators geschützt
   - Admin-Routen separiert
   - User-Lookup via g.keycloak_user

### ⚠️ In Arbeit

1. XSS-Schutz (50%)
   - DOMPurify teilweise implementiert
   - RankerDetail.vue noch zu fixen

2. Container-Härtung (0%)
   - Non-Root User in Dockerfiles

3. Dokumentation (90%)
   - CLAUDE.md erstellt
   - MkDocs Setup ausstehend

### 📋 Nächste Schritte

1. XSS-Fixes in Frontend
2. Non-Root Container-User
3. Vollständiger Systemtest
4. MkDocs Setup für Doku-Portal
5. Git-Branch-Cleanup
6. Production-SSL-Setup

---

## 👥 Kontakte & Support

**Entwickler**: Philipp Steigerwald
**Repository**: [TBD]
**Dokumentation**: Diese Datei + KEYCLOAK_INTEGRATION_STATUS.md

---

**Letzte Aktualisierung**: 20. November 2025
**Version**: 2.0-keycloak
